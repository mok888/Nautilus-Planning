import sys
from pathlib import Path

# Add project root to sys.path to find 'builder' package
# Path: nautilus-dinger/nautilus_adapter/cli.py
# parent: nautilus_adapter/
# parent.parent: nautilus-dinger/
# parent.parent.parent: Root/ (where builder/ resides)
root = Path(__file__).resolve().parent.parent.parent
if str(root) not in sys.path:
    sys.path.append(str(root))

try:
    from builder.cli import app
except ImportError:
    # Fallback or error message if builder is missing
    def app():
        print("ERROR: 'builder' package not found. Ensure you are running from the Nautilus-Planning root.")
        sys.exit(1)

def main():
    app()

if __name__ == "__main__":
    main()
