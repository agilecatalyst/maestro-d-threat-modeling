import os
import sys
from pathlib import Path

os.environ.setdefault(
    "DATABASE_URL", "postgresql://maestro:maestro@localhost:5432/maestro_d"
)
os.environ.setdefault("API_RATE_LIMIT_ENABLED", "false")

API_DIR = Path(__file__).resolve().parent.parent / "backend" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))
