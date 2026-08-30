"""PyInstaller entry point.

Running main.py directly breaks relative imports once frozen (no parent
package). This tiny script puts src on the path and imports wallforge as a
real package so `from .core...` works inside it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wallforge.main import main

if __name__ == "__main__":
    raise SystemExit(main())
