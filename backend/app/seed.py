"""Command line database utilities.

Usage (from ``backend/``):

    python -m app.seed          # migrate + seed demo directory doctors
    python -m app.seed --reset  # drop every table first (DESTRUCTIVE, dev only)
"""
from __future__ import annotations

import argparse
import sys

from app.db_init import init_db, seed_demo_data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MediSense database utilities")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all tables before migrating (destroys data; development only)",
    )
    args = parser.parse_args(argv)

    if args.reset:
        from app.database import Base, engine

        print("Dropping all tables …")
        Base.metadata.drop_all(bind=engine)

    strategy = init_db()
    print(f"Schema ready via {strategy}.")
    result = seed_demo_data()
    print(
        f"Demo directory doctors inserted: {result['doctors_inserted']} "
        f"(previously {result['existing_doctors']})."
    )
    print("Demo entries are flagged is_demo=True and labelled in the UI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
