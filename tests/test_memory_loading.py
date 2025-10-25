import os, sqlite3, tempfile, shutil
from pathlib import Path
import pytest

def test_memory_db_bootstrap_creates_file_and_tables():
    # temp DB path
    tmpdir = tempfile.mkdtemp(prefix="mordzix_mem_")
    try:
        db_path = os.path.join(tmpdir, "mem.db")
        os.environ["MEM_DB"] = db_path  # make sure config picks it up
        # Import after setting env
        from core.memory import MemoryDatabase
        mdb = MemoryDatabase(db_path=db_path)
        assert os.path.exists(db_path), "SQLite file should be created"
        # Check schema exists
        con = sqlite3.connect(db_path)
        cur = con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        names = {r[0] for r in cur.fetchall()}
        required = {"memory_nodes","memory_episodes","memory_analytics"}
        assert required.issubset(names), f"Required tables missing: {required - names}"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
