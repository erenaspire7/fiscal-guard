"""Command-line scripts for Fiscal Guard API."""

import os
import subprocess
import sys


def start_api():
    """Start the FastAPI application."""
    # Get the api directory (parent of src/api)
    api_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    print("🚀 Starting Fiscal Guard API...")
    print(f"📁 Working directory: {api_dir}")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API docs will be at: http://localhost:8000/docs")
    print()

    try:
        # Run uvicorn
        result = subprocess.run(
            ["uvicorn", "src.api.main:app", "--reload", "--port", "8000"],
            cwd=api_dir,
            check=True,
        )
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ API server failed with error code {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
        sys.exit(0)
    except FileNotFoundError:
        print("❌ Error: 'uvicorn' command not found.")
        sys.exit(1)
