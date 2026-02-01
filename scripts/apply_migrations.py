#!/usr/bin/env python3
"""
Apply SQL migrations in migrations/ directory to the database specified by
DATABASE_URL or SUPABASE_DATABASE_URL.

Usage: python scripts/apply_migrations.py
"""

import os
import sys
from urllib.parse import urlparse
from pathlib import Path

import pg8000


def get_conn_params(url: str):
    p = urlparse(url)
    if p.scheme not in ("postgres", "postgresql"):
        raise ValueError("DB URL scheme must be postgres:// or postgresql://")
    return {
        "host": p.hostname,
        "port": p.port or 5432,
        "database": p.path.lstrip("/"),
        "user": p.username,
        "password": p.password,
        "ssl": True,
    }


def main():
    url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DATABASE_URL")
    if not url:
        print("DATABASE_URL not set. Set DATABASE_URL or SUPABASE_DATABASE_URL to your connection string.")
        sys.exit(1)

    try:
        params = get_conn_params(url)
    except Exception as e:
        print(f"Invalid DATABASE_URL: {e}")
        sys.exit(1)

    migrations_dir = Path(__file__).resolve().parent.parent / "migrations"
    sql_files = sorted(migrations_dir.glob("*.sql"))
    if not sql_files:
        print("No migrations found in", migrations_dir)
        return

    conn = pg8000.connect(**params)
    cursor = conn.cursor()

    try:
        for f in sql_files:
            print("Applying", f.name)
            sql = f.read_text(encoding="utf-8")
            cursor.execute(sql)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Error applying migrations:", e)
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

    print("All migrations applied successfully.")


if __name__ == '__main__':
    main()
