"""Apply the portfolio SQLite schema updates from server.py.

Usage:
    python migrate_schema.py
    python migrate_schema.py --database /path/to/portfolio.db
"""

import argparse
import os
import sqlite3
from datetime import datetime
from pathlib import Path


# Import the application without running its automatic startup initialization.
# This script invokes init_db() explicitly after selecting and backing up the DB.
os.environ["PORTFOLIO_SKIP_AUTO_DB_INIT"] = "1"

import server  # noqa: E402


BASE_DIR = Path(__file__).resolve().parent


def schema_snapshot(database_path):
    if not database_path.exists():
        return {}

    with sqlite3.connect(database_path) as conn:
        tables = [
            row[0]
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            )
        ]
        return {
            table: {
                row[1]
                for row in conn.execute(
                    f'PRAGMA table_info("{table}")'
                ).fetchall()
            }
            for table in tables
        }


def back_up_database(database_path, backup_dir):
    if not database_path.exists():
        return None

    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_path = backup_dir / f"{database_path.stem}-{timestamp}.db"

    with sqlite3.connect(database_path) as source:
        with sqlite3.connect(backup_path) as destination:
            source.backup(destination)

    return backup_path


def describe_changes(before, after):
    changes = []
    for table in sorted(after.keys() - before.keys()):
        changes.append(f"created table: {table}")

    for table in sorted(after.keys() & before.keys()):
        for column in sorted(after[table] - before[table]):
            changes.append(f"added column: {table}.{column}")

    return changes


def parse_args():
    parser = argparse.ArgumentParser(
        description="Back up and migrate the portfolio SQLite schema."
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=BASE_DIR / "portfolio.db",
        help="SQLite database path (default: project portfolio.db)",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=BASE_DIR / "db_backups",
        help="Backup directory (default: project db_backups)",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip the automatic backup",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    database_path = args.database.expanduser().resolve()
    backup_dir = args.backup_dir.expanduser().resolve()

    before = schema_snapshot(database_path)
    backup_path = None
    if not args.no_backup:
        backup_path = back_up_database(database_path, backup_dir)

    server.DATABASE_PATH = database_path
    server.init_db()

    after = schema_snapshot(database_path)
    changes = describe_changes(before, after)

    print(f"Migration complete: {database_path}")
    if backup_path:
        print(f"Backup created: {backup_path}")
    elif not before:
        print("No backup was needed because the database did not exist.")

    if changes:
        for change in changes:
            print(f"- {change}")
    else:
        print("Schema was already up to date.")


if __name__ == "__main__":
    main()
