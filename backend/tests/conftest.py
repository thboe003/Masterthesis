import sys
from pathlib import Path

# Make ``app`` importable when running ``pytest`` from the backend folder or the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
