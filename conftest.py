import sys
from pathlib import Path

# This runs before any test module is imported
scripts_dir = str(Path(__file__).parent / 'scripts')
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)
