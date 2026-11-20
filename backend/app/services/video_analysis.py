"""
Execution feedback for uploaded pole training videos.

Pipeline:
    1. preprocessing (CPU, runs in a worker thread)
       - extract N sharp, evenly distributed key frames (``video.frames``)
       - optional: pose estimation → joint angles per frame (``video.pose``)
    2. grounding
       - reference description of the exercise from the catalog
         (name, level, instructions = how it should look)
       - candidate exercises the model may recommend as drills
    3. call the vision LLM with the frames as images (or one contact sheet)
    4. validate the JSON against ``LLMVideoFeedback``; one retry on failure
    5. post-process: frame numbers → timestamps, recommendations → catalog IDs

The video itself never reaches the LLM – only the extracted JPEG frames.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional

from pydantic import ValidationError

from app.schemas import (
    AnalyzedFrame,
    ExecutionIssue,
    ExerciseRecommendation,
    LLMVideoFeedback,
    VideoAnalysisInfo,
    VideoAnalysisResult,
    VideoFeedback,
    VideoMetadata,
)
from app.services.exercise_catalog import CatalogExercise, load_catalog, select_candidates
from app.services.llm import ImageInput, LLMProvider, LLMResponseError, extract_json
from app.services.video import (
    FrameExtractionResult,
    PoseMetrics,
    estimate_poses,
    extract_frames,
    make_contact_sheet,
    make_thumbnail,
)

logger = logging.getLogger(__name__)

FrameMode = Literal["frames", "grid"]

MAX_ATTEMPTS = int(os.getenv("LLM_MAX_ATTEMPTS", "2"))
DEFAULT_NUM_FRAMES = int(os.getenv("VIDEO_NUM_FRAMES", "8"))
MAX_NUM_FRAMES = int(os.getenv("VIDEO_MAX_FRAMES", "16"))
FRAME_MAX_SIDE = int(os.getenv("VIDEO_FRAME_MAX_SIDE", "768"))
DEFAULT_FRAME_MODE: FrameMode = "grid" if os.getenv("VIDEO_FRAME_MODE", "frames").lower() == "grid" else "frames"
POSE_ENABLED = os.getenv("VIDEO_POSE_ESTIMATION", "false").lower() == "true"

LEVEL_LABELS = {
    "beginner": "Anfänger (0-6 Monate Pole-Erfahrung)",
    "intermediate": "Fortgeschritten (6-24 Monate Pole-Erfahrung)",
    "advanced": "Erfahren (mehr als 2 Jahre Pole-Erfahrung)",
}

SYSTEM_PROMPT = """You are an experienced pole sport coach who gives technique feedback from video.
You receive key frames (still images) extracted in chronological order from a training video of one athlete.
Each frame has a number and a timestamp. Optionally you also receive joint angles measured by a pose estimator.

Rules:
- Judge ONLY what is visible in the frames. If something cannot be seen (body part cut off, bad angle, blur), say so instead of guessing.
- If the frames do not show a pole exercise or a person at all, set "analyzable" to false and explain why in "summary".
- Compare the execution with the reference description of the expected exercise if one is given. Set "matches_expected_exercise" accordingly (null if no exercise was given).
- Reference frames by their number in "frame_numbers" for every issue.
- Prioritise safety: grip, shoulder engagement (active shoulders, no hanging in the joint), controlled entries/exits, neck and lower back. Mark risks with severity "safety" and also list them in "safety_warnings".
- Give concrete, actionable corrections (cues an athlete can apply in the next attempt).
- Pose angles are estimates. Ignore values with low visibility (< 0.5) and never contradict what is clearly visible in the image.
- Recommend up to 4 drills or conditioning exercises from the provided catalog that address the issues; copy their exercise_id exactly.
- "overall_score": 1 (unsafe/incorrect) .. 10 (clean, controlled, competition-ready) relative to the athlete's level; null if not analyzable.
- "confidence": how sure you are given image quality and number of frames.
- Write all human-readable text in German.
- Answer with a single JSON object only, no Markdown, no explanation.

JSON format:
{
  "recognized_exercise": "string, what you see",
  "matches_expected_exercise": true | false | null,
  "analyzable": true,
  "overall_score": 7,
  "confidence": "low | medium | high",
  "summary": "string, 2-3 sentences",
  "strengths": ["string"],
  "issues": [
    {
      "title": "string, short",
      "description": "string, what is wrong and why it matters",
      "severity": "minor | moderate | major | safety",
      "body_part": "string, e.g. Schultern",
      "frame_numbers": [2, 3],
      "correction": "string, concrete cue"
    }
  ],
  "safety_warnings": ["string"],
  "recommended_exercises": [
    {"exercise_id": "id from catalog", "name": "string", "reason": "string, which issue it addresses"}
  ],
  "next_steps": "string, what to focus on in the next sessions"
}"""


@dataclass
class PreparedVideo:
    extraction: FrameExtractionResult
    poses: List[PoseMetrics] = field(default_factory=list)
    preprocessing_ms: int = 0
    warnings: List[str] = field(default_factory=list)


def find_exercise(
    catalog: List[CatalogExercise], exercise_id: Optional[str], exercise_name: Optional[str]
) -> Optional[CatalogExercise]:
    if exercise_id:
        for c in catalog:
            if c.id == exercise_id or c.id.lower() == exercise_id.lower():
                return c
    if exercise_name:
        name = exercise_name.strip().lower()
        for c in catalog:
            if c.name.strip().lower() == name:
                return c
    return None


def prepare_video(
    video_path: str,
    num_frames: int = DEFAULT_NUM_FRAMES,
    use_pose: bool = POSE_ENABLED,
    start_s: Optional[float] = None,
    end_s: Optional[float] = None,
) -> PreparedVideo:
    """CPU-bound preprocessing. Call via ``asyncio.to_thread`` from async code."""
    started = time.perf_counter()
    num_frames = max(1, min(MAX_NUM_FRAMES, num_frames))
    extraction = extract_frames(video_path, num_frames=num_frames, max_side=FRAME_MAX_SIDE, start_s=start_s, end_s=end_s)
    warnings = list(extraction.warnings)
    poses: List[PoseMetrics] = []
    if use_pose:
        poses, warning = estimate_poses([(f.number, f.jpeg) for f in extraction.frames])
        if warning:
            warnings.append(warning)
        elif not poses:
            warnings.append("Pose-Schätzung hat in keinem Frame eine Person erkannt.")
    return PreparedVideo(
        extraction=extraction,
        poses=poses,
        preprocessing_ms=int((time.perf_counter() - started) * 1000),
        warnings=warnings,
    )


def build_user_prompt(
    prepared: PreparedVideo,
    exercise: Optional[CatalogExercise],
    exercise_name: Optional[str],
    experience_level: Optional[str],
    user_notes: Optional[str],
    candidates: List[CatalogExercise],
    frame_mode: FrameMode,
) -> str:
    info = prepared.extraction.video
    frames = prepared.extraction.frames
    lines = ["Analyse the execution in this pole training video.", ""]

    lines.append("Expected exercise:")
    if exercise:
        lines.append(f"- {exercise.name} (id: {exercise.id}, category: {exercise.category}, level: {exercise.level})")
        if exercise.instructions:
            lines.append("- Reference / correct execution:")
            lines.extend(f"  {i}. {step}" for i, step in enumerate(exercise.instructions[:12], 1))
    elif exercise_name:
        lines.append(f"- {exercise_name} (not in catalog, use your own expert knowledge as reference)")
    else:
        lines.append("- not specified, identify the exercise yourself")

    lines += [
        "",
        "Athlete:",
        f"- Pole experience: {LEVEL_LABELS.get(experience_level or '', 'not specified')}",
        f"- Notes / question of the athlete: {user_notes or 'none'}",
        "",
        f"Video: {info.duration_s:.1f}s, {info.fps:.0f} fps, {info.width}x{info.height}px.",
    ]
    if frame_mode == "grid":
        lines.append(
            f"You receive ONE contact-sheet image with {len(frames)} tiles in reading order (left→right, top→bottom); "
            "every tile is labelled with #number and timestamp."
        )
    else:
        lines.append(f"You receive {len(frames)} images in chronological order:")
    lines.extend(f"- {f.label}" for f in frames)

    if prepared.poses:
        lines += ["", "Joint angles from pose estimation (180° = fully extended):"]
        lines.extend(f"- {p.prompt_line()}" for p in prepared.poses)

    lines += ["", "Catalog for recommended_exercises (exercise_id | name | category | level | primary muscles):"]
    lines.extend(c.prompt_line() for c in candidates)
    return "\n".join(lines)


def build_images(prepared: PreparedVideo, frame_mode: FrameMode) -> List[ImageInput]:
    frames = prepared.extraction.frames
    if frame_mode == "grid":
        return [ImageInput(data=make_contact_sheet(frames), label=f"Kontaktbogen mit Frames 1-{len(frames)}")]
    return [ImageInput(data=f.jpeg, label=f.label) for f in frames]


def _recommendation_candidates(catalog: List[CatalogExercise], experience_level: Optional[str]) -> List[CatalogExercise]:
    return select_candidates(catalog, experience_level or "beginner", ["strength", "flexibility"], per_goal=12, seed=0)


def _post_process(
    raw: LLMVideoFeedback, prepared: PreparedVideo, catalog: List[CatalogExercise]
) -> tuple[VideoFeedback, List[str]]:
    warnings: List[str] = []
    ts = {f.number: f.timestamp_s for f in prepared.extraction.frames}
    by_id: Dict[str, CatalogExercise] = {c.id.lower(): c for c in catalog}
    by_name: Dict[str, CatalogExercise] = {c.name.strip().lower(): c for c in catalog}

    issues: List[ExecutionIssue] = []
    for issue in raw.issues:
        valid = [n for n in issue.frame_numbers if n in ts]
        if len(valid) != len(issue.frame_numbers):
            warnings.append(f"Problem '{issue.title}': unbekannte Frame-Nummern verworfen.")
        issues.append(
            ExecutionIssue(
                **issue.model_dump(exclude={"frame_numbers"}),
                frame_numbers=valid,
                timestamps_s=[ts[n] for n in valid],
            )
        )

    recommendations: List[ExerciseRecommendation] = []
    for rec in raw.recommended_exercises:
        match = by_id.get((rec.exercise_id or "").lower()) or by_name.get(rec.name.strip().lower())
        if match is None:
            warnings.append(f"Empfohlene Übung nicht im Katalog: {rec.name}")
        recommendations.append(
            ExerciseRecommendation(
                exercise_id=match.id if match else None,
                name=match.name if match else rec.name,
                reason=rec.reason,
                in_catalog=match is not None,
            )
        )

    feedback = VideoFeedback(
        **raw.model_dump(exclude={"issues", "recommended_exercises"}),
        issues=issues,
        recommended_exercises=recommendations,
    )
    if not feedback.analyzable:
        feedback.overall_score = None
    return feedback, warnings


def _data_url(jpeg: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(jpeg).decode("ascii")


async def analyze_prepared_video(
    prepared: PreparedVideo,
    provider: LLMProvider,
    *,
    exercise_id: Optional[str] = None,
    exercise_name: Optional[str] = None,
    experience_level: Optional[str] = None,
    user_notes: Optional[str] = None,
    frame_mode: FrameMode = DEFAULT_FRAME_MODE,
    filename: Optional[str] = None,
    catalog: Optional[List[CatalogExercise]] = None,
) -> VideoAnalysisResult:
    """Send the prepared frames to the vision LLM and build the validated result."""
    catalog = catalog if catalog is not None else load_catalog()
    exercise = find_exercise(catalog, exercise_id, exercise_name)
    candidates = _recommendation_candidates(catalog, experience_level)
    user_prompt = build_user_prompt(
        prepared, exercise, exercise_name, experience_level, user_notes, candidates, frame_mode
    )
    images = build_images(prepared, frame_mode)

    started = time.perf_counter()
    input_tokens = output_tokens = 0
    last_error: Optional[str] = None
    raw: Optional[LLMVideoFeedback] = None
    attempts = 0
    model_name = provider.model

    for attempts in range(1, MAX_ATTEMPTS + 1):
        prompt = user_prompt
        if last_error:
            prompt += (
                "\n\nYour previous answer was invalid:\n"
                f"{last_error}\n"
                "Return the complete feedback again as valid JSON in the required format."
            )
        result = await provider.complete_json_with_images(SYSTEM_PROMPT, prompt, images)
        model_name = result.model
        input_tokens += result.input_tokens or 0
        output_tokens += result.output_tokens or 0
        try:
            raw = LLMVideoFeedback.model_validate(extract_json(result.text))
            break
        except (LLMResponseError, ValidationError) as exc:
            last_error = str(exc)[:1500]
            logger.warning("Vision LLM attempt %d returned invalid feedback: %s", attempts, last_error)

    if raw is None:
        raise LLMResponseError(
            f"Das Modell hat nach {attempts} Versuchen kein gültiges Feedback geliefert. Letzter Fehler: {last_error}"
        )

    feedback, warnings = _post_process(raw, prepared, catalog)
    poses = {p.frame_number: p.to_dict() for p in prepared.poses}
    info = prepared.extraction.video

    return VideoAnalysisResult(
        id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
        exercise_id=exercise.id if exercise else None,
        exercise_name=exercise.name if exercise else exercise_name,
        experience_level=experience_level if experience_level in LEVEL_LABELS else None,
        video=VideoMetadata(
            filename=filename, duration_s=round(info.duration_s, 2), fps=round(info.fps, 2),
            width=info.width, height=info.height,
        ),
        frames=[
            AnalyzedFrame(
                number=f.number, timestamp_s=f.timestamp_s,
                thumbnail=_data_url(make_thumbnail(f)), pose=poses.get(f.number),
            )
            for f in prepared.extraction.frames
        ],
        feedback=feedback,
        analysis=VideoAnalysisInfo(
            provider=provider.name,
            model=model_name,
            duration_ms=int((time.perf_counter() - started) * 1000),
            preprocessing_ms=prepared.preprocessing_ms,
            attempts=attempts,
            frame_mode=frame_mode,
            frames_sent=len(prepared.extraction.frames),
            images_sent=len(images),
            pose_estimation=bool(prepared.poses),
            input_tokens=input_tokens or None,
            output_tokens=output_tokens or None,
            warnings=[*prepared.warnings, *warnings],
        ),
    )


async def analyze_video(
    video_path: str,
    provider: LLMProvider,
    *,
    num_frames: int = DEFAULT_NUM_FRAMES,
    use_pose: bool = POSE_ENABLED,
    start_s: Optional[float] = None,
    end_s: Optional[float] = None,
    **kwargs,
) -> VideoAnalysisResult:
    """Full pipeline: preprocessing in a worker thread, then the LLM call."""
    prepared = await asyncio.to_thread(prepare_video, video_path, num_frames, use_pose, start_s, end_s)
    return await analyze_prepared_video(prepared, provider, **kwargs)


__all__ = [
    "SYSTEM_PROMPT",
    "PreparedVideo",
    "analyze_prepared_video",
    "analyze_video",
    "build_images",
    "build_user_prompt",
    "find_exercise",
    "prepare_video",
]
