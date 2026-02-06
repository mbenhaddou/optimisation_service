import os
import sys
from pathlib import Path


def pytest_configure():
    # Ensure deterministic hashing in tests that rely on ordering.
    os.environ.setdefault("PYTHONHASHSEED", "0")

    # Ensure repo root is importable for local package imports.
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
