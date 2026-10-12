import json
import os
import subprocess
import sys
from types import SimpleNamespace

import hydrate_ipos
import sync


def test_sync_modes_and_status_files(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        sync.subprocess, "run",
        lambda args, **kwargs: (calls.append(args) or SimpleNamespace(returncode=0)),
    )
    sync.main()
    sync.main(only="open")
    sync.main(retry_failed=True)
    scripts = [[str(arg) for arg in call[1:]] for call in calls]
    assert scripts == [
        [str(sync.BASE_DIR / "get_ipos.py")],
        [str(sync.BASE_DIR / "hydrate_ipos.py")],
        [str(sync.BASE_DIR / "hydrate_ipos.py"), "--only", "open"],
        [str(sync.BASE_DIR / "hydrate_ipos.py"), "--retry-failed"],
    ]
    monkeypatch.setattr(hydrate_ipos, "IPO_DIR", tmp_path)
    for status in ("open", "listed"):
        (tmp_path / f"{status}.json").write_text(json.dumps({"data": [{"id": status}]}))
    assert hydrate_ipos.load_ipo_ids("open") == ["open"]
    assert hydrate_ipos.load_ipo_ids() == ["listed", "open"]


def test_upstox_import_preserves_container_environment():
    # Import in hydration order, before database configuration is cached.
    result = subprocess.run(
        [sys.executable, "-c", (
            "import app.integrations.upstox; "
            "from app.database import DB_HOST; "
            "assert DB_HOST == 'container-database'"
        )],
        env={**os.environ, "DB_HOST": "container-database"},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
