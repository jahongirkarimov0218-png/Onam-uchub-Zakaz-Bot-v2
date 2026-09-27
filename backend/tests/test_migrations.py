import sqlite3
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_alembic_upgrade_head_creates_all_seven_tables(tmp_path):
    db_path = tmp_path / "migrated.db"
    env = {
        **__import__("os").environ,
        "DATABASE_URL": f"sqlite+aiosqlite:///{db_path}",
    }
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(BACKEND_DIR),
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    finally:
        conn.close()
    table_names = {row[0] for row in rows}

    assert {
        "categories",
        "products",
        "uploads",
        "orders",
        "order_items",
        "order_status_history",
        "order_admin_messages",
    }.issubset(table_names)
