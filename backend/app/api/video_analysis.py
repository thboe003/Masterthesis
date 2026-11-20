"""Video analysis endpoints: upload a training video, get execution feedback."""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.schemas import VideoAnalysisResult
from app.services.exercise_catalog import load_catalog
from app.services.llm import LLMProvider, LLMResponseError, LLMUnavailableError, get_vision_provider
from app.services.video import VideoProcessingError
from app.services import video_analysis as va

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/video-analysis", tags=["video-analysis"])

MAX_UPLOAD_MB = int(os.getenv("VIDEO_MAX_UPLOAD_MB", "200"))
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}
CHUNK = 1024 * 1024


def vision_provider_dependency() -> LLMProvider:
    try:
        return get_vision_provider()
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


async def _save_upload(video: UploadFile) -> str:
    """Stream the upload into a temp file (size-limited). Caller deletes the file."""
    suffix = Path(video.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Dateiformat '{suffix or '?'}' nicht unterstützt. Erlaubt: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )
    if video.content_type and not (video.content_type.startswith("video/") or video.content_type == "application/octet-stream"):
        raise HTTPException(status_code=415, detail=f"Kein Video (Content-Type {video.content_type}).")

    limit = MAX_UPLOAD_MB * CHUNK
    size = 0
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="pole_video_")
    try:
        with os.fdopen(fd, "wb") as out:
            while chunk := await video.read(CHUNK):
                size += len(chunk)
                if size > limit:
                    raise HTTPException(status_code=413, detail=f"Video ist größer als {MAX_UPLOAD_MB} MB.")
                out.write(chunk)
    except BaseException:
        _remove(path)
        raise
    if size == 0:
        _remove(path)
        raise HTTPException(status_code=400, detail="Leere Datei hochgeladen.")
    return path


def _remove(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


async def _prepare(path: str, num_frames: int, use_pose: bool, start_s, end_s) -> va.PreparedVideo:
    try:
        return await asyncio.to_thread(va.prepare_video, path, num_frames, use_pose, start_s, end_s)
    except VideoProcessingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/analyze", response_model=VideoAnalysisResult)
async def analyze_video(
    video: UploadFile = File(..., description="Trainingsvideo (mp4, mov, webm, ...)"),
    exercise_id: Optional[str] = Form(None),
    exercise_name: Optional[str] = Form(None),
    experience_level: Optional[str] = Form(None),
    user_notes: Optional[str] = Form(None, max_length=1000),
    num_frames: int = Form(va.DEFAULT_NUM_FRAMES, ge=1, le=va.MAX_NUM_FRAMES),
    frame_mode: str = Form(va.DEFAULT_FRAME_MODE),
    use_pose: Optional[bool] = Form(None),
    start_s: Optional[float] = Form(None, ge=0),
    end_s: Optional[float] = Form(None, ge=0),
    provider: LLMProvider = Depends(vision_provider_dependency),
) -> VideoAnalysisResult:
    """
    Upload a pole training video and get feedback on the execution.

    The video is reduced to ``num_frames`` key frames which are sent as images
    to the vision model configured with ``VISION_LLM_PROVIDER`` /
    ``VISION_LLM_MODEL``. The video is stored only temporarily and deleted
    after the analysis.
    """
    mode = "grid" if frame_mode == "grid" else "frames"
    path = await _save_upload(video)
    try:
        prepared = await _prepare(path, num_frames, va.POSE_ENABLED if use_pose is None else use_pose, start_s, end_s)
    finally:
        _remove(path)

    try:
        return await va.analyze_prepared_video(
            prepared,
            provider,
            exercise_id=exercise_id or None,
            exercise_name=(exercise_name or "").strip() or None,
            experience_level=experience_level or None,
            user_notes=(user_notes or "").strip() or None,
            frame_mode=mode,  # type: ignore[arg-type]
            filename=video.filename,
        )
    except LLMUnavailableError as exc:
        logger.error("Vision LLM unavailable: %s", exc)
        raise HTTPException(
            status_code=503, detail=f"Vision-Modell {provider.name}/{provider.model} nicht nutzbar: {exc}"
        ) from exc
    except LLMResponseError as exc:
        logger.error("Vision LLM returned unusable output: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/frames-preview")
async def frames_preview(
    video: UploadFile = File(...),
    num_frames: int = Form(va.DEFAULT_NUM_FRAMES, ge=1, le=va.MAX_NUM_FRAMES),
    frame_mode: str = Form(va.DEFAULT_FRAME_MODE),
    use_pose: Optional[bool] = Form(None),
    exercise_id: Optional[str] = Form(None),
    exercise_name: Optional[str] = Form(None),
    experience_level: Optional[str] = Form(None),
    user_notes: Optional[str] = Form(None),
    start_s: Optional[float] = Form(None, ge=0),
    end_s: Optional[float] = Form(None, ge=0),
) -> Dict[str, Any]:
    """
    Show exactly what the vision model would receive (images + prompts),
    without calling it. Useful for debugging and for the thesis appendix.
    """
    mode = "grid" if frame_mode == "grid" else "frames"
    path = await _save_upload(video)
    try:
        prepared = await _prepare(path, num_frames, va.POSE_ENABLED if use_pose is None else use_pose, start_s, end_s)
    finally:
        _remove(path)

    catalog = load_catalog()
    exercise = va.find_exercise(catalog, exercise_id, exercise_name)
    candidates = va._recommendation_candidates(catalog, experience_level)
    images = va.build_images(prepared, mode)  # type: ignore[arg-type]
    return {
        "video": prepared.extraction.video.__dict__,
        "warnings": prepared.warnings,
        "preprocessing_ms": prepared.preprocessing_ms,
        "images": [
            {"label": img.label, "bytes": len(img.data), "data_url": img.data_url()} for img in images
        ],
        "poses": [p.to_dict() for p in prepared.poses],
        "system_prompt": va.SYSTEM_PROMPT,
        "user_prompt": va.build_user_prompt(
            prepared, exercise, exercise_name, experience_level, user_notes, candidates, mode  # type: ignore[arg-type]
        ),
    }


@router.get("/exercises")
async def analyzable_exercises() -> List[Dict[str, Any]]:
    """Pole exercises/moves that can be selected as "expected exercise" (no DB needed)."""
    items = [c for c in load_catalog() if c.is_pole_sport]
    items.sort(key=lambda c: ({"beginner": 0, "intermediate": 1, "advanced": 2}.get(c.level, 3), c.name))
    return [{"id": c.id, "name": c.name, "level": c.level, "category": c.category} for c in items]


@router.get("/info")
async def video_info(provider: LLMProvider = Depends(vision_provider_dependency)) -> Dict[str, Any]:
    """Configured vision model and limits."""
    return {
        **provider.describe(),
        "default_num_frames": va.DEFAULT_NUM_FRAMES,
        "max_num_frames": va.MAX_NUM_FRAMES,
        "frame_mode": va.DEFAULT_FRAME_MODE,
        "pose_estimation": va.POSE_ENABLED,
        "max_upload_mb": MAX_UPLOAD_MB,
        "allowed_extensions": sorted(ALLOWED_EXTENSIONS),
    }
