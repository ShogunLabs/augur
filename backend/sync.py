import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def run_script(script: str) -> None:
    print()
    print("=" * 60)
    print(f"Running {script}")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, str(BASE_DIR / script)],
        cwd=BASE_DIR,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"{script} failed with exit code "
            f"{result.returncode}"
        )


def main() -> None:
    print("=" * 60)
    print("AUGUR IPO SYNC")
    print("=" * 60)

    try:
        # Step 1: Fetch IPO index data
        run_script("get_ipos.py")

        # Step 2: Hydrate IPO details into PostgreSQL
        run_script("hydrate_ipos.py")

    except Exception as exc:
        print()
        print("SYNC FAILED")
        print(exc)
        sys.exit(1)

    print()
    print("=" * 60)
    print("SYNC COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()