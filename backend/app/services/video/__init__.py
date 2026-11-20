"""Video preprocessing for the execution feedback (frames, optional pose estimation)."""

from .frames import (
    ExtractedFrame,
    FrameExtractionResult,
    VideoInfo,
    VideoProcessingError,
    extract_frames,
    make_contact_sheet,
    make_thumbnail,
)
from .pose import PoseMetrics, compute_metrics, estimate_poses

__all__ = [
    "ExtractedFrame",
    "FrameExtractionResult",
    "PoseMetrics",
    "VideoInfo",
    "VideoProcessingError",
    "compute_metrics",
    "estimate_poses",
    "extract_frames",
    "make_contact_sheet",
    "make_thumbnail",
]
