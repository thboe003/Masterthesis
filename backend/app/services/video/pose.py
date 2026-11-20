"""
Optional pose estimation for the extracted frames.

Vision LLMs are good at describing a scene but weak at measuring angles. A
classic pose estimator (MediaPipe Pose) delivers body keypoints per frame;
from them we compute joint angles (e.g. knee extension, leg split) and pass
them to the LLM as additional *numerical* context ("hybrid approach").

MediaPipe is optional (``pip install mediapipe``) and enabled with
``VIDEO_POSE_ESTIMATION=true``. Without it the analysis works with images only.

Note: pose estimators are trained mostly on upright people. In inverted pole
moves the detection quality drops – every metric therefore carries the mean
landmark visibility, and the prompt tells the LLM to treat values with low
visibility as unreliable.
"""

from __future__ import annotations

import logging
import math
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

Point = Tuple[float, float, float]  # x, y (normalised, y points down), visibility

# MediaPipe Pose landmark indices
L_SHOULDER, R_SHOULDER = 11, 12
L_ELBOW, R_ELBOW = 13, 14
L_WRIST, R_WRIST = 15, 16
L_HIP, R_HIP = 23, 24
L_KNEE, R_KNEE = 25, 26
L_ANKLE, R_ANKLE = 27, 28


@dataclass
class PoseMetrics:
    frame_number: int
    visibility: float  # mean visibility of the used landmarks (0..1)
    inverted: Optional[bool] = None  # hips above shoulders in the image
    elbow_left: Optional[float] = None
    elbow_right: Optional[float] = None
    shoulder_left: Optional[float] = None
    shoulder_right: Optional[float] = None
    hip_left: Optional[float] = None
    hip_right: Optional[float] = None
    knee_left: Optional[float] = None
    knee_right: Optional[float] = None
    leg_split: Optional[float] = None  # angle between both thighs

    def to_dict(self) -> Dict:
        return {k: v for k, v in asdict(self).items() if v is not None}

    def prompt_line(self) -> str:
        parts = [f"Frame {self.frame_number}: Sichtbarkeit {self.visibility:.2f}"]
        if self.inverted is not None:
            parts.append("kopfüber" if self.inverted else "aufrecht")
        labels = {
            "elbow_left": "Ellbogen L", "elbow_right": "Ellbogen R",
            "shoulder_left": "Schulter L", "shoulder_right": "Schulter R",
            "hip_left": "Hüfte L", "hip_right": "Hüfte R",
            "knee_left": "Knie L", "knee_right": "Knie R",
            "leg_split": "Beinspreizung",
        }
        for key, label in labels.items():
            value = getattr(self, key)
            if value is not None:
                parts.append(f"{label} {value:.0f}°")
        return ", ".join(parts)


def _angle(a: Point, b: Point, c: Point) -> float:
    """Angle ABC in degrees (at point b)."""
    v1 = (a[0] - b[0], a[1] - b[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    n1, n2 = math.hypot(*v1), math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return float("nan")
    cos = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
    return math.degrees(math.acos(cos))


def compute_metrics(frame_number: int, landmarks: Dict[int, Point], min_visibility: float = 0.5) -> PoseMetrics:
    """Joint angles from landmarks. Angles whose points are not visible enough are left out."""

    def ang(a: int, b: int, c: int) -> Optional[float]:
        pts = [landmarks.get(i) for i in (a, b, c)]
        if any(p is None or p[2] < min_visibility for p in pts):
            return None
        value = _angle(*pts)  # type: ignore[arg-type]
        return None if math.isnan(value) else round(value, 1)

    used = [L_SHOULDER, R_SHOULDER, L_ELBOW, R_ELBOW, L_WRIST, R_WRIST, L_HIP, R_HIP, L_KNEE, R_KNEE, L_ANKLE, R_ANKLE]
    vis = [landmarks[i][2] for i in used if i in landmarks]
    metrics = PoseMetrics(frame_number=frame_number, visibility=round(sum(vis) / len(vis), 2) if vis else 0.0)

    metrics.elbow_left = ang(L_SHOULDER, L_ELBOW, L_WRIST)
    metrics.elbow_right = ang(R_SHOULDER, R_ELBOW, R_WRIST)
    metrics.shoulder_left = ang(L_ELBOW, L_SHOULDER, L_HIP)
    metrics.shoulder_right = ang(R_ELBOW, R_SHOULDER, R_HIP)
    metrics.hip_left = ang(L_SHOULDER, L_HIP, L_KNEE)
    metrics.hip_right = ang(R_SHOULDER, R_HIP, R_KNEE)
    metrics.knee_left = ang(L_HIP, L_KNEE, L_ANKLE)
    metrics.knee_right = ang(R_HIP, R_KNEE, R_ANKLE)

    hips = [landmarks.get(L_HIP), landmarks.get(R_HIP)]
    shoulders = [landmarks.get(L_SHOULDER), landmarks.get(R_SHOULDER)]
    if all(p is not None and p[2] >= min_visibility for p in hips + shoulders):
        hip_y = (hips[0][1] + hips[1][1]) / 2  # type: ignore[index]
        shoulder_y = (shoulders[0][1] + shoulders[1][1]) / 2  # type: ignore[index]
        metrics.inverted = hip_y < shoulder_y
        mid_hip = ((hips[0][0] + hips[1][0]) / 2, hip_y, 1.0)  # type: ignore[index]
        lk, rk = landmarks.get(L_KNEE), landmarks.get(R_KNEE)
        if lk and rk and lk[2] >= min_visibility and rk[2] >= min_visibility:
            value = _angle(lk, mid_hip, rk)
            metrics.leg_split = None if math.isnan(value) else round(value, 1)
    return metrics


class PoseEstimator:
    """Thin wrapper around MediaPipe Pose (legacy ``solutions`` API)."""

    def __init__(self, model_complexity: int = 1):
        try:
            import mediapipe as mp  # noqa: WPS433
        except ImportError as exc:
            raise RuntimeError("mediapipe ist nicht installiert (`pip install mediapipe`).") from exc
        self._mp = mp
        self._model_complexity = model_complexity

    def estimate(self, jpeg_frames: List[Tuple[int, bytes]]) -> List[PoseMetrics]:
        import cv2

        from .frames import decode_jpeg

        results: List[PoseMetrics] = []
        with self._mp.solutions.pose.Pose(static_image_mode=True, model_complexity=self._model_complexity) as pose:
            for number, data in jpeg_frames:
                image = cv2.cvtColor(decode_jpeg(data), cv2.COLOR_BGR2RGB)
                out = pose.process(image)
                if not out.pose_landmarks:
                    continue
                landmarks = {
                    i: (lm.x, lm.y, float(getattr(lm, "visibility", 1.0)))
                    for i, lm in enumerate(out.pose_landmarks.landmark)
                }
                results.append(compute_metrics(number, landmarks))
        return results


def estimate_poses(jpeg_frames: List[Tuple[int, bytes]]) -> Tuple[List[PoseMetrics], Optional[str]]:
    """Run pose estimation if available. Returns (metrics, warning)."""
    try:
        return PoseEstimator().estimate(jpeg_frames), None
    except Exception as exc:  # optional feature – never break the analysis
        logger.warning("Pose estimation skipped: %s", exc)
        return [], f"Pose-Schätzung übersprungen: {exc}"
