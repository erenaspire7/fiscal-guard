"""Command-line scripts for Fiscal Guard core."""

import os
import subprocess
import sys


def run_migrations():
    """Run database migrations using Alembic."""
    # Get the core directory (parent of src/core)
    core_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    print("🔄 Running database migrations...")
    print(f"📁 Working directory: {core_dir}")

    try:
        # Run alembic upgrade head
        result = subprocess.run(
            ["alembic", "upgrade", "head"], cwd=core_dir, check=True
        )
        print("✅ Migrations completed successfully!")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed with error code {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("❌ Error: 'alembic' command not found.")
        sys.exit(1)
