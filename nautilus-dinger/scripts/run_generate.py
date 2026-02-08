import sys
from pathlib import Path

# Add parent directory to sys.path to find 'builder'
root = Path(__file__).parent.parent.parent
sys.path.append(str(root))

# Load .env from parent directory
from dotenv import load_dotenv
load_dotenv(root / ".env")

from builder.cli import app

if __name__ == "__main__":
    app()
