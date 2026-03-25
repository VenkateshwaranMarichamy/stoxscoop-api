from __future__ import annotations


def run_seed() -> None:
    """Legacy seed removed with the old ORM; create data via ``POST /api/v1/*``."""

    print("Seed skipped — use /api/v1/batches and /api/v1/events to load data.")


if __name__ == "__main__":
    run_seed()
