"""
Tests for the video analysis. A short synthetic video is rendered with OpenCV
and a fake vision provider is used, so no model, GPU or network is needed:

    cd backend && pytest tests/test_video_analysis.py
"""

import asyncio
import json

import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from app.schemas import LLMVideoFeedback
from app.services.exercise_catalog import CatalogExercise
from app.services.llm import ImageInput, LLMProvider, LLMResponseError, LLMResult
from app.services.llm.providers import anthropic_messages, ollama_messages, openai_messages
from app.services.video import compute_metrics, extract_frames, make_contact_sheet
from app.services.video_analysis import analyze_prepared_video, build_user_prompt, prepare_video

CATALOG = [
    CatalogExercise(
        "pole_climb", "Pole Climb", "technique", "beginner", "pole", ["lats"],
        ["Hände über Kopf greifen", "Knie und Füße klemmen", "Hüfte nach oben ziehen"], True,
    ),
    CatalogExercise("pole_shoulder_shrugs", "Pole Shoulder Shrugs", "strength", "beginner", "pole", ["shoulders"], [], True),
    CatalogExercise("Hamstring_Stretch", "Hamstring Stretch", "stretching", "beginner", "body only", ["hamstrings"]),
]


@pytest.fixture(scope="module")
def video_path(tmp_path_factory):
    """3 s, 20 fps, 320x240 video with a moving white rectangle."""
    path = str(tmp_path_factory.mktemp("video") / "test.avi")
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 20, (320, 240))
    assert writer.isOpened()
    for i in range(60):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        x = 10 + i * 4
        cv2.rectangle(frame, (x, 80), (x + 40, 160), (255, 255, 255), -1)
        writer.write(frame)
    writer.release()
    return path


# --------------------------------------------------------------------------- #
# Frame extraction
# --------------------------------------------------------------------------- #
def test_extract_frames_even_distribution(video_path):
    result = extract_frames(video_path, num_frames=6, max_side=160)
    assert len(result.frames) == 6
    assert [f.number for f in result.frames] == [1, 2, 3, 4, 5, 6]
    times = [f.timestamp_s for f in result.frames]
    assert times == sorted(times)
    assert 0 <= times[0] < 0.5 and 2.5 < times[-1] <= 3.0
    assert result.video.fps == pytest.approx(20, abs=0.5)
    assert all(max(f.width, f.height) <= 160 for f in result.frames)
    assert all(f.jpeg[:2] == b"\xff\xd8" for f in result.frames)  # JPEG magic number


def test_extract_frames_trim(video_path):
    result = extract_frames(video_path, num_frames=4, start_s=1.0, end_s=2.0)
    assert all(1.0 <= f.timestamp_s <= 2.0 for f in result.frames)


def test_extract_more_frames_than_video(video_path):
    result = extract_frames(video_path, num_frames=10, start_s=0, end_s=0.2)
    assert len(result.frames) <= 5
    assert result.warnings


def test_contact_sheet(video_path):
    frames = extract_frames(video_path, num_frames=4).frames
    image = cv2.imdecode(np.frombuffer(make_contact_sheet(frames, tile_side=100), np.uint8), cv2.IMREAD_COLOR)
    assert image.shape[:2] == (200, 200)


# --------------------------------------------------------------------------- #
# Pose metrics (pure geometry, no MediaPipe needed)
# --------------------------------------------------------------------------- #
def test_compute_metrics_straight_and_inverted():
    # upright person: shoulders above hips, straight legs, arms straight down
    upright = {
        11: (0.45, 0.30, 1), 12: (0.55, 0.30, 1), 13: (0.45, 0.40, 1), 14: (0.55, 0.40, 1),
        15: (0.45, 0.50, 1), 16: (0.55, 0.50, 1), 23: (0.47, 0.55, 1), 24: (0.53, 0.55, 1),
        25: (0.47, 0.70, 1), 26: (0.53, 0.70, 1), 27: (0.47, 0.85, 1), 28: (0.53, 0.85, 1),
    }
    m = compute_metrics(1, upright)
    assert m.inverted is False
    assert m.knee_left == pytest.approx(180, abs=1)
    assert m.elbow_right == pytest.approx(180, abs=1)
    # flip vertically → inverted
    flipped = {k: (x, 1 - y, v) for k, (x, y, v) in upright.items()}
    assert compute_metrics(2, flipped).inverted is True


def test_compute_metrics_ignores_low_visibility():
    lm = {i: (0.5, 0.1 * (i % 10), 0.1) for i in range(11, 29)}
    m = compute_metrics(1, lm)
    assert m.knee_left is None and m.inverted is None


# --------------------------------------------------------------------------- #
# Provider payloads
# --------------------------------------------------------------------------- #
IMG = ImageInput(data=b"\xff\xd8abc", label="Frame 1 (t=0.00s)")


def test_openai_payload_contains_data_url():
    msgs = openai_messages("sys", "user", [IMG])
    parts = msgs[1]["content"]
    assert parts[0] == {"type": "text", "text": "user"}
    assert parts[1]["text"] == "Frame 1 (t=0.00s)"
    assert parts[2]["image_url"]["url"].startswith("data:image/jpeg;base64,")


def test_anthropic_payload_images_before_text():
    content = anthropic_messages("user", [IMG])[0]["content"]
    assert content[1]["type"] == "image" and content[1]["source"]["media_type"] == "image/jpeg"
    assert content[-1] == {"type": "text", "text": "user"}


def test_ollama_payload_images_list():
    msgs = ollama_messages("sys", "user", [IMG])
    assert msgs[1]["images"] == [IMG.b64()]
    assert "Frame 1" in msgs[1]["content"]


def test_text_only_payloads_unchanged():
    assert openai_messages("s", "u")[1]["content"] == "u"
    assert anthropic_messages("u") == [{"role": "user", "content": "u"}]
    assert "images" not in ollama_messages("s", "u")[1]


# --------------------------------------------------------------------------- #
# Analysis pipeline with a fake vision model
# --------------------------------------------------------------------------- #
class FakeVisionProvider(LLMProvider):
    name = "fake"

    def __init__(self, answers):
        super().__init__("fake-vision")
        self.answers = list(answers)
        self.calls = []

    async def complete_json(self, system_prompt, user_prompt):  # pragma: no cover - not used
        raise NotImplementedError

    async def complete_json_with_images(self, system_prompt, user_prompt, images):
        self.calls.append((user_prompt, images))
        return LLMResult(text=self.answers.pop(0), provider=self.name, model=self.model, input_tokens=100, output_tokens=50)


def feedback_json(**overrides):
    data = {
        "recognized_exercise": "Pole Climb",
        "matches_expected_exercise": True,
        "analyzable": True,
        "overall_score": "6.6",
        "confidence": "mittel",
        "summary": "Solider Climb, Schultern teilweise passiv.",
        "strengths": ["Gute Fußklemme"],
        "issues": [
            {
                "title": "Passive Schultern", "description": "Hängt im Schultergelenk.",
                "severity": "Sicherheit", "body_part": "Schultern", "frame_numbers": ["#2", 3, 99],
                "correction": "Schultern aktiv nach unten ziehen.",
            }
        ],
        "safety_warnings": ["Schultern aktiv halten"],
        "recommended_exercises": [
            {"exercise_id": "POLE_SHOULDER_SHRUGS", "name": "Shrugs", "reason": "Schulteraktivierung"},
            {"exercise_id": "invented", "name": "Fantasieübung", "reason": "-"},
        ],
        "next_steps": "Schulteraktivierung üben.",
    }
    data.update(overrides)
    return json.dumps(data)


def test_analysis_pipeline(video_path):
    prepared = prepare_video(video_path, num_frames=4, use_pose=False)
    provider = FakeVisionProvider(["no json at all", feedback_json()])
    result = asyncio.run(
        analyze_prepared_video(
            prepared, provider, exercise_id="pole_climb", experience_level="beginner",
            user_notes="Sind meine Schultern aktiv?", catalog=CATALOG, filename="test.avi",
        )
    )
    # retry after invalid answer
    assert result.analysis.attempts == 2
    assert result.analysis.input_tokens == 200
    # 4 individual images were sent, each labelled
    prompt, images = provider.calls[0]
    assert len(images) == 4 and images[0].label.startswith("Frame 1")
    assert "Knie und Füße klemmen" in prompt  # reference instructions from the catalog
    assert "Sind meine Schultern aktiv?" in prompt
    # normalisation + post-processing
    fb = result.feedback
    assert fb.overall_score == 7 and fb.confidence == "medium"
    issue = fb.issues[0]
    assert issue.severity == "safety"
    assert issue.frame_numbers == [2, 3]  # 99 dropped
    assert len(issue.timestamps_s) == 2
    assert fb.recommended_exercises[0].exercise_id == "pole_shoulder_shrugs"
    assert fb.recommended_exercises[1].in_catalog is False
    assert any("Frame-Nummern" in w for w in result.analysis.warnings)
    assert result.exercise_name == "Pole Climb"
    assert len(result.frames) == 4 and result.frames[0].thumbnail.startswith("data:image/jpeg;base64,")


def test_grid_mode_sends_one_image(video_path):
    prepared = prepare_video(video_path, num_frames=6, use_pose=False)
    provider = FakeVisionProvider([feedback_json()])
    result = asyncio.run(analyze_prepared_video(prepared, provider, frame_mode="grid", catalog=CATALOG))
    assert len(provider.calls[0][1]) == 1
    assert result.analysis.images_sent == 1 and result.analysis.frames_sent == 6


def test_not_analyzable_has_no_score(video_path):
    prepared = prepare_video(video_path, num_frames=2, use_pose=False)
    provider = FakeVisionProvider([feedback_json(analyzable=False, issues=[], recommended_exercises=[])])
    result = asyncio.run(analyze_prepared_video(prepared, provider, catalog=CATALOG))
    assert result.feedback.overall_score is None


def test_gives_up_after_max_attempts(video_path):
    prepared = prepare_video(video_path, num_frames=2, use_pose=False)
    provider = FakeVisionProvider(["{}", "{}"])
    with pytest.raises(LLMResponseError):
        asyncio.run(analyze_prepared_video(prepared, provider, catalog=CATALOG))


def test_unknown_exercise_name_in_prompt(video_path):
    prepared = prepare_video(video_path, num_frames=2, use_pose=False)
    prompt = build_user_prompt(prepared, None, "Ayesha", "advanced", None, CATALOG, "frames")
    assert "Ayesha (not in catalog" in prompt


def test_llm_feedback_schema_coerces_single_frame():
    fb = LLMVideoFeedback.model_validate(json.loads(feedback_json(issues=[
        {"title": "x", "description": "y", "severity": "hoch", "frame_numbers": 4, "correction": "z"}
    ])))
    assert fb.issues[0].frame_numbers == [4] and fb.issues[0].severity == "major"
