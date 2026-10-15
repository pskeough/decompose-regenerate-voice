"""Add-only, versioned backup of every result file under runs/ and data/.

Rule (2026-09-07, after a sync overwrote runs/chesterton_base4b/gens.jsonl):
nothing that a pipeline stage wrote may exist in one copy only. This copies
every result file to BACKUP_ROOT keeping the relative path; when a source
file has changed since the last copy, the old backup is kept under
<name>.v<timestamp> before the new one is written, and nothing in the
backup is ever deleted. Embeddings (.npy, recomputable in minutes) and
training checkpoints are skipped; adapters, generations, manifests, scores,
judges, summaries, reports and the author data (splits, briefs, guides) are
kept.

    python dr/backup_runs.py            # incremental
    python dr/backup_runs.py --verify   # list source files missing from the backup

Runs from the sync_down step before any extraction, from the end of every
controller, and from a scheduled task every four hours.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr.core import DATA, DR, RUNS, log  # noqa: E402

BACKUP_ROOT = os.environ.get("DR_BACKUP_ROOT", os.path.join(os.path.dirname(DR), "_backup", "decompose_regenerate"))
KEEP_EXT = {".jsonl", ".json", ".md", ".html", ".txt", ".gguf", ".safetensors", ".csv"}
SKIP_DIRS = {"_api_cache", "__pycache__"}


def wanted(path):
    parts = path.replace("\\", "/").split("/")
    if any(p in SKIP_DIRS or p.startswith("checkpoint-") for p in parts):
        return False
    return os.path.splitext(path)[1].lower() in KEEP_EXT


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def same(src, dst):
    if not os.path.exists(dst):
        return False
    s, d = os.stat(src), os.stat(dst)
    if s.st_size != d.st_size:
        return False
    if abs(s.st_mtime - d.st_mtime) < 2:
        return True
    return sha(src) == sha(dst)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--roots", default="runs,data", help="comma-separated subfolders of the project to back up")
    a = ap.parse_args()
    roots = {"runs": RUNS, "data": DATA}
    copied = versioned = unchanged = missing = 0
    bytes_copied = 0
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    for key in [r.strip() for r in a.roots.split(",") if r.strip()]:
        src_root = roots[key]
        for dirpath, dirnames, filenames in os.walk(src_root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith("checkpoint-")]
            for fn in filenames:
                src = os.path.join(dirpath, fn)
                if not wanted(src):
                    continue
                rel = os.path.relpath(src, src_root)
                dst = os.path.join(BACKUP_ROOT, key, rel)
                if a.verify:
                    if not os.path.exists(dst):
                        missing += 1
                        print("missing:", os.path.join(key, rel))
                    continue
                if same(src, dst):
                    unchanged += 1
                    continue
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if os.path.exists(dst):
                    shutil.move(dst, dst + f".v{stamp}")
                    versioned += 1
                shutil.copy2(src, dst)
                copied += 1
                bytes_copied += os.path.getsize(src)
    if a.verify:
        print(f"verify: {missing} source files missing from {BACKUP_ROOT}")
        return 1 if missing else 0
    log(f"backup -> {BACKUP_ROOT}: {copied} copied ({bytes_copied / 1e9:.2f} GB), {versioned} previous versions kept, {unchanged} unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
