"""Hardware and software stamp written into every generation manifest and
training run.json, so a run made on a cloud card carries the same record as
one made on the 5060 Ti and the paper can report compute per checklist.
"""
from __future__ import annotations

import os
import platform
import socket
import subprocess


def stamp() -> dict:
    d = {"host": socket.gethostname(), "platform": platform.platform(), "python": platform.python_version()}
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
                           capture_output=True, text=True, timeout=20)
        d["gpu"] = r.stdout.strip().splitlines()[0] if r.stdout.strip() else None
    except Exception:
        d["gpu"] = None
    for mod in ("torch", "transformers", "peft", "numpy", "gguf"):
        try:
            d[mod] = __import__(mod).__version__
        except Exception:
            d[mod] = None
    try:
        import torch
        d["cuda"] = torch.version.cuda
    except Exception:
        d["cuda"] = None
    d["llama_server"] = os.environ.get("DR_LLAMA_SERVER", "local-default-b10435")
    d["cloud"] = bool(os.environ.get("DR_CLOUD"))
    return d
