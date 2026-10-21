"""Run the patch CLI directly from a source checkout, without installation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from z30_extensions.cli import main

if __name__ == '__main__':
    raise SystemExit(main())
