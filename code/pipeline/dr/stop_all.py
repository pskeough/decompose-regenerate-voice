"""Stop every project process cleanly so a later re-run resumes.

Kills, in this order: controllers (night_0905, run_author, overnight,
patrick_night, followup, chain), stage scripts (s3, s4, s5, s5b, s1, s2),
llama-server. Nothing on disk is touched: generation rows, training
checkpoints, judge verdicts and controller state all survive, and re-running
the same controller command continues from the last completed unit.

    python dr/stop_all.py
    python dr/stop_all.py --keep-api      # leave judges / briefs / frontier running
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dr.core import log  # noqa: E402

CONTROLLERS = r"night_0905|run_author|overnight\.py|patrick_night|followup_0904|chain\.py|size_curve|rescore_normalised|logs[\/]\w+\.sh"
GPU = r"s3_generate|s4_train|s5_score|make_replay|transfer_control|cross_attribution|punct_sensitivity"
API = r"s5b_judge|s1_decompose|s2_conditioning"


def kill(pattern):
    """psutil-based: the CIM query this used to run hung under GPU load."""
    import psutil
    from dr.live import find
    # bash rows only when they run a chain script directly; a `bash -c` wrapper
    # (a Claude tool shell) merely quotes the command text and is never a target
    hits = [h for h in find(pattern) if not (h[3].startswith("bash") and " -c " in h[4])]
    for pid, ppid, t, n, cl in hits:
        try:
            psutil.Process(pid).kill()
        except Exception as e:
            log(f"  could not kill {pid}: {e}")
    log(f"killed [{pattern[:30]}...]: " + ("; ".join(f"{pid} {cl[:70]}" for pid, _, _, _, cl in hits) or "none"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keep-api", action="store_true")
    a = ap.parse_args()
    kill(CONTROLLERS)
    kill(GPU)
    if not a.keep_api:
        kill(API)
    subprocess.run(["taskkill", "/F", "/IM", "llama-server.exe"], capture_output=True)
    log("llama-server killed (if any)")
    r = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader"], capture_output=True, text=True)
    log(f"GPU memory now: {r.stdout.strip()}")
    log("resume with the same controller command; completed units are skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
