import logging
import subprocess
import sys
from pathlib import Path

from app.integrations.upstox import configure_logging

configure_logging()

BASE_DIR = Path(__file__).resolve().parent

STATUSES = ["upcoming", "open", "closed", "listed"]


def run_script(script: str) -> None:
    logging.info("Running %s", script)

    result = subprocess.run(
        [sys.executable, str(BASE_DIR / script)],
        cwd=BASE_DIR,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"{script} failed with exit code "
            f"{result.returncode}"
        )


def main(only: str | None = None, retry_failed: bool = False) -> None:
    if only is not None and only not in STATUSES:
        raise ValueError(
            f"Unknown status {only!r}. "
            f"Expected one of: {', '.join(STATUSES)}"
        )

    if retry_failed and only is not None:
        raise ValueError("--retry-failed cannot be combined with --only")

    logging.info("AUGUR IPO SYNC")

    try:
        if not retry_failed:
            # Step 1: Fetch IPO index data
            run_script("get_ipos.py")

        # Step 2: Hydrate IPO details into PostgreSQL
        if retry_failed:
            logging.info("Retrying failed IPOs without re-discovering")
            run_script("hydrate_ipos.py --retry-failed")
        elif only is None:
            run_script("hydrate_ipos.py")
        else:
            # Hydrate a single lifecycle slice without re-discovering.
            logging.info("Hydrating only status=%s", only)
            result = subprocess.run(
                [
                    sys.executable,
                    str(BASE_DIR / "hydrate_ipos.py"),
                    "--only",
                    only,
                ],
                cwd=BASE_DIR,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"hydrate_ipos.py failed with exit code "
                    f"{result.returncode}"
                )

    except Exception as exc:
        logging.error("SYNC FAILED: %s", exc)
        sys.exit(1)

    logging.info("SYNC COMPLETE")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run the Augur IPO sync pipeline."
    )
    parser.add_argument(
        "--only",
        default=None,
        help=(
            "Hydrate a single lifecycle status "
            "(upcoming|open|closed|listed) without re-discovering."
        ),
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry only the IPOs that failed in the previous hydration (reads hydration_failures.json). Skips discovery.",
    )
    args = parser.parse_args()
    main(only=args.only, retry_failed=args.retry_failed)