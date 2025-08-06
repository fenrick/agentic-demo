"""Test configuration setup for the repository.

Adds the project's ``src`` directory to ``sys.path`` so test modules can
import application code without requiring the project to be installed as a
package.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Compute the absolute path to the project root and ``src`` directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# Prepend ``src`` to ``sys.path`` if it's not already present.
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
