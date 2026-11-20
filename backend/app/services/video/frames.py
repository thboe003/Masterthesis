"""
Key-frame extraction from training videos.

LLMs in this project receive images, not videos. A video is therefore reduced
to a small number of representative frames:

1. The (optionally trimmed) video is split into ``num_frames`` equal segments.
2. In every segment a few candidate frames are decoded.
3. The sharpest candidate (variance of the Laplacian) is kept, which avoids
   motion-blurred frames during spins.
4. Frames are downscaled (``max_side``) and JPEG-encoded to keep the token
   cost of the vision model low.

Optionally the frames can be combined into a single contact sheet ("grid"),
which costs fewer image tokens but gives the model less detail per frame.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional


class VideoProcessingError(Exception):
    """The video could not be opened or decoded."""


@dataclass
class ExtractedFrame:
    number: int  # 1-based, the number the LLM uses to reference the frame
    frame_index: int  # index in the original video
    timestamp_s: float
    jpeg: bytes
    width: int
    height: int
    sharpness: float

    @property
    def label(self) -> str:
        return f"Frame {self.number} (t={self.timestamp_s:.2f}s)"


@dataclass
class VideoInfo:
    duration_s: float
    fps: float
    frame_count: int
    width: int
    height: int


@dataclass
class FrameExtractionResult:
    video: VideoInfo
    frames: List[ExtractedFrame] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _cv2():
    try:
        import cv2  # noqa: WPS433 – optional heavy dependency, imported lazily
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise VideoProcessingError(
            "OpenCV ist nicht installiert. Bitte `pip install opencv-python-headless` ausführen."
        ) from exc
    return cv2


def _resize(cv2, image, max_side: int):
    h, w = image.shape[:2]
    scale = max_side / max(h, w)
    if scale >= 1:
        return image
    return cv2.resize(image, (int(round(w * scale)), int(round(h * scale))), interpolation=cv2.INTER_AREA)


def _sharpness(cv2, image) -> float:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def encode_jpeg(image, quality: int = 85) -> bytes:
    cv2 = _cv2()
    ok, buffer = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        raise VideoProcessingError("Frame konnte nicht als JPEG kodiert werden.")
    return buffer.tobytes()


def decode_jpeg(data: bytes):
    import numpy as np

    cv2 = _cv2()
    return cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)


def read_video_info(path: str) -> VideoInfo:
    cv2 = _cv2()
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise VideoProcessingError("Video konnte nicht geöffnet werden (Format/Codec nicht unterstützt?).")
    try:
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    finally:
        cap.release()
    if fps <= 0 or frame_count <= 0:
        raise VideoProcessingError("Video enthält keine lesbaren Frames.")
    return VideoInfo(duration_s=frame_count / fps, fps=fps, frame_count=frame_count, width=width, height=height)


def extract_frames(
    path: str,
    num_frames: int = 8,
    max_side: int = 768,
    jpeg_quality: int = 85,
    start_s: Optional[float] = None,
    end_s: Optional[float] = None,
    candidates_per_segment: int = 3,
) -> FrameExtractionResult:
    """Extract ``num_frames`` sharp, evenly distributed frames from a video file."""
    if num_frames < 1:
        raise ValueError("num_frames must be >= 1")
    cv2 = _cv2()
    info = read_video_info(path)
    warnings: List[str] = []

    first = 0
    last = info.frame_count - 1
    if start_s is not None:
        first = max(0, min(last, int(start_s * info.fps)))
    if end_s is not None:
        last = max(first, min(last, int(end_s * info.fps)))
    span = last - first + 1

    if span < num_frames:
        warnings.append(f"Video hat nur {span} Frames im gewählten Bereich, es werden alle verwendet.")
        num_frames = span

    segment = span / num_frames
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise VideoProcessingError("Video konnte nicht geöffnet werden.")

    frames: List[ExtractedFrame] = []
    try:
        for seg in range(num_frames):
            seg_start = first + seg * segment
            k = max(1, min(candidates_per_segment, int(segment)))
            # candidates spread inside the segment, centred
            indices = sorted({int(seg_start + (i + 0.5) * segment / k) for i in range(k)})
            best = None
            for idx in indices:
                idx = min(idx, last)
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ok, image = cap.read()
                if not ok or image is None:
                    continue
                image = _resize(cv2, image, max_side)
                score = _sharpness(cv2, image)
                if best is None or score > best[0]:
                    best = (score, idx, image)
            if best is None:
                warnings.append(f"Segment {seg + 1}: kein Frame lesbar.")
                continue
            score, idx, image = best
            h, w = image.shape[:2]
            frames.append(
                ExtractedFrame(
                    number=len(frames) + 1,
                    frame_index=idx,
                    timestamp_s=round(idx / info.fps, 3),
                    jpeg=encode_jpeg(image, jpeg_quality),
                    width=w,
                    height=h,
                    sharpness=round(score, 1),
                )
            )
    finally:
        cap.release()

    if not frames:
        raise VideoProcessingError("Es konnten keine Frames aus dem Video gelesen werden.")
    return FrameExtractionResult(video=info, frames=frames, warnings=warnings)


def make_contact_sheet(frames: List[ExtractedFrame], columns: Optional[int] = None, tile_side: int = 384) -> bytes:
    """
    Combine frames into one JPEG grid with the frame number drawn on every tile.

    Fewer image tokens than individual frames; useful for comparing token cost
    vs. feedback quality in the evaluation.
    """
    import numpy as np

    cv2 = _cv2()
    if not frames:
        raise ValueError("no frames")
    columns = columns or math.ceil(math.sqrt(len(frames)))
    rows = math.ceil(len(frames) / columns)
    tiles = []
    for f in frames:
        img = _resize(cv2, decode_jpeg(f.jpeg), tile_side)
        canvas = np.zeros((tile_side, tile_side, 3), dtype=np.uint8)
        h, w = img.shape[:2]
        y0, x0 = (tile_side - h) // 2, (tile_side - w) // 2
        canvas[y0:y0 + h, x0:x0 + w] = img
        cv2.rectangle(canvas, (0, 0), (150, 32), (0, 0, 0), -1)
        cv2.putText(canvas, f"#{f.number} {f.timestamp_s:.1f}s", (6, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        tiles.append(canvas)
    while len(tiles) < rows * columns:
        tiles.append(np.zeros((tile_side, tile_side, 3), dtype=np.uint8))
    grid = np.vstack([np.hstack(tiles[r * columns:(r + 1) * columns]) for r in range(rows)])
    return encode_jpeg(grid, 85)


def make_thumbnail(frame: ExtractedFrame, max_side: int = 320) -> bytes:
    cv2 = _cv2()
    return encode_jpeg(_resize(cv2, decode_jpeg(frame.jpeg), max_side), 75)
