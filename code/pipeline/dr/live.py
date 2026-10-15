"""List the project's live processes without a WMI/CIM query (those hung on
2026-09-05 under GPU load). Used by stop_all.py and run_author.py, and by an
agent before it relaunches anything: a crashed Claude session does not kill
the background chains it started.

    python dr/live.py
"""
from __future__ import annotations

import datetime as dt
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT = re.compile(r"dr[\/]\w+\.py|llama-server|logs[\/]\w+\.sh")


def project_processes():
    """[(pid, ppid, started 'HH:MM:SS', name, cmdline)] for python, bash and
    llama-server processes whose command line names a project script."""
    import psutil
    out = []
    for p in psutil.process_iter(["pid", "name", "create_time", "cmdline"]):
        try:
            n = (p.info["name"] or "").lower()
            if n not in ("python.exe", "python", "python3", "python3.12", "python3.11", "bash.exe", "bash", "sh.exe", "sh", "llama-server.exe", "llama-server"):
                continue
            cl = " ".join(p.info["cmdline"] or [])
            if n.startswith("llama-server") or PROJECT.search(cl):
                out.append((p.info["pid"], p.ppid(), dt.datetime.fromtimestamp(p.info["create_time"]).strftime("%H:%M:%S"), n, cl))
        except Exception:
            continue
    return sorted(out, key=lambda r: r[2])


def ancestors():
    """This process and every parent above it: a stop script must never kill
    the shell that launched it (stop_all killed its own Bash wrapper on
    2026-09-05 because the wrapper's command line mentioned a chain script)."""
    import psutil
    out = set()
    try:
        p = psutil.Process(os.getpid())
        while p is not None:
            out.add(p.pid)
            p = p.parent()
    except Exception:
        pass
    return out


def find_script(name, exclude_self=True):
    """Python processes whose script argument is <name> (basename match on
    argv[1]). Unlike find(), this cannot match a shell wrapper whose command
    text merely mentions the script, which is what made run_author refuse to
    start on 2026-09-06 01:16."""
    import psutil
    skip = ancestors() if exclude_self else set()
    out = []
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cl = p.info["cmdline"] or []
            if (p.info["name"] or "").lower().startswith("python") and len(cl) > 1                and os.path.basename(cl[1]) == name and p.info["pid"] not in skip:
                out.append((p.info["pid"], p.ppid(), " ".join(cl)))
        except Exception:
            continue
    return out


def find(pattern, exclude_self=True):
    rx = re.compile(pattern)
    skip = ancestors() if exclude_self else set()
    return [r for r in project_processes() if rx.search(r[4]) and r[0] not in skip]


def main():
    rows = project_processes()
    if not rows:
        print("no project processes alive")
    for pid, ppid, t, n, cl in rows:
        print(f"{pid:>6} {ppid:>6} {t} {n:<16} {cl[:120]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
