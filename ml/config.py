"""
ML Pipeline for Pole Sport Training Plan Generation
Master's Thesis - Applied Artificial Intelligence
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
ML_DIR = PROJECT_ROOT / "ml"
MODELS_DIR = ML_DIR / "models"
DATA_DIR = ML_DIR / "data"
CONFIG_DIR = PROJECT_ROOT / "configs"

# Ensure directories exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ML Configuration
class MLConfig:
    """Configuration for ML model training and inference."""
    
    # Model Configuration
    MODEL_NAME = "pole-training-generator"
    MODEL_VERSION = "0.1.0"
    TRANSFORMER_BASE = "distilbert-base-uncased"
    HIDDEN_SIZE = 256
    NUM_LAYERS = 3
    DROPOUT_RATE = 0.2
    
    # Training Configuration
    BATCH_SIZE = 32
    LEARNING_RATE = 1e-4
    NUM_EPOCHS = 10
    VALIDATION_SPLIT = 0.2
    RANDOM_SEED = 42
    
    # Data Configuration
    MAX_SEQ_LENGTH = 512
    VOCAB_SIZE = 30522
    
    # Inference
    NUM_BEAMS = 5
    MAX_LENGTH = 200
    TEMPERATURE = 0.7
    TOP_P = 0.9


if __name__ == "__main__":
    print(f"ML Pipeline initialized at {ML_DIR}")
    print(f"Configuration: {MLConfig.__dict__}")
