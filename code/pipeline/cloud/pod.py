"""Scripted RunPod pod control for the cloud runner, through the runpod SDK.
Reads RUNPOD_API_KEY from the project env file (C:\\LocalAI\\LLM\\eval\\.env) or
the environment. Nothing here spends money without an explicit `create`.

    python cloud/pod.py gpus                         # available GPU types with prices
    python cloud/pod.py create --gpu "NVIDIA L40S" --disk 80 --name dr-8b
    python cloud/pod.py status [--id ID]             # pods, their ssh host:port, cost/hr
    python cloud/pod.py ssh --id ID                  # prints the ssh command
    python cloud/pod.py stop --id ID                 # stop (disk kept, billed for storage)
    python cloud/pod.py terminate --id ID            # delete (nothing billed afterwards)
    python cloud/pod.py balance                      # account credit and current spend per hour
    python cloud/pod.py rest-status                  # pods via the REST API (works when the GraphQL SDK hangs, 2026-09-09 17:40)
    python cloud/pod.py rest-terminate --id ID       # terminate via REST; the termination path must never depend on the SDK alone

Image: RunPod's PyTorch template. cloud/setup.sh asserts the torch version
and reinstalls the pinned one if the template drifted (seen 2026: a
pytorch 2.8 template shipping torch 2.4).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ENV_FILE = r"C:\LocalAI\LLM\eval\.env"
IMAGE = os.environ.get("DR_POD_IMAGE", "runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04")


def api_key():
    k = os.environ.get("RUNPOD_API_KEY")
    if not k and os.path.exists(ENV_FILE):
        for line in open(ENV_FILE, encoding="utf-8"):
            if line.startswith("RUNPOD_API_KEY="):
                k = line.split("=", 1)[1].strip().strip("'\"<>")   # tolerate <key>, "key", stray spaces
    if not k:
        raise SystemExit(f"RUNPOD_API_KEY not set; add it to {ENV_FILE}")
    return k


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["gpus", "create", "status", "ssh", "stop", "terminate", "balance", "rest-status", "rest-terminate"])
    ap.add_argument("--id", default="")
    ap.add_argument("--gpu", default="NVIDIA L40S")
    ap.add_argument("--disk", type=int, default=80, help="container disk GB (models + workspace; no network volume)")
    ap.add_argument("--name", default="dr-cloud")
    ap.add_argument("--cloud", default="SECURE", choices=["SECURE", "COMMUNITY"])
    a = ap.parse_args()
    # ---- REST paths (2026-09-09 19:15): the runpod SDK's `import runpod` hangs on this
    # machine, so create / status / ssh / terminate go through rest.runpod.io and never
    # import the SDK. Output formats are unchanged; the launch scripts parse them.
    if a.cmd in ("create", "status", "ssh", "terminate"):
        import urllib.request, urllib.error
        def rest(method, path, body=None):
            data = json.dumps(body).encode() if body is not None else None
            req = urllib.request.Request("https://rest.runpod.io/v1" + path, data=data, method=method,
                                         headers={"Authorization": "Bearer " + api_key(), "Content-Type": "application/json", "User-Agent": "dr-cloud/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    txt = r.read().decode("utf-8")
            except urllib.error.HTTPError as e:
                txt = e.read().decode("utf-8", "replace")
                raise SystemExit(f"REST {method} {path} -> HTTP {e.code}: {txt[:300]}" + (" (balance is too low)" if any(k in txt.lower() for k in ("balance", "insufficient", "credit")) else ""))
            return json.loads(txt) if txt.strip() else {}
        def ssh_of(pod):
            ip = pod.get("publicIp") or ""
            pm = pod.get("portMappings") or {}
            port = pm.get("22") or pm.get(22)
            if not port:
                for x in ((pod.get("runtime") or {}).get("ports") or []):
                    if x.get("privatePort") == 22:
                        ip, port = x.get("ip") or ip, x.get("publicPort")
            return (ip, port) if ip and port else (None, None)
        def gpu_of(pod):
            m = pod.get("machine") or {}
            return m.get("gpuDisplayName") or m.get("gpuTypeId") or pod.get("gpuTypeId") or ",".join(pod.get("gpuTypeIds") or []) or "?"
        if a.cmd == "create":
            body = {"name": a.name, "imageName": IMAGE, "cloudType": a.cloud, "gpuTypeIds": [a.gpu], "gpuCount": 1,
                    "containerDiskInGb": a.disk, "volumeInGb": 0, "ports": ["22/tcp"], "supportPublicIp": True, "computeType": "GPU",
                    "env": {"DR_CLOUD": "1", "PUBLIC_KEY": open(os.path.expanduser("~/.ssh/dr_runpod.pub")).read().strip()}}   # PUBLIC_KEY: RunPod templates append it to authorized_keys
            pod = rest("POST", "/pods", body)
            print(json.dumps(pod, indent=1)[:1200])
            print("")
            print(f"created pod {pod.get('id')}; wait ~1-2 min then: python cloud/pod.py status --id {pod.get('id')}")
            return 0
        if a.cmd == "terminate":
            if not a.id:
                raise SystemExit("--id required")
            rest("DELETE", f"/pods/{a.id}")
            print(f"terminated {a.id}")
            return 0
        pods = [rest("GET", f"/pods/{a.id}")] if a.id else (lambda d: d if isinstance(d, list) else d.get("pods") or d.get("data") or [])(rest("GET", "/pods"))
        if a.cmd == "status":
            for pod in pods:
                ip, port = ssh_of(pod)
                ssh = f"{ip}:{port}" if ip else "(no ssh port yet)"
                print(f"{pod.get('id')}  {pod.get('name')}  {pod.get('desiredStatus')}  gpu={gpu_of(pod)}  ${pod.get('costPerHr')}/h  ssh={ssh}")
            if not pods:
                print("no pods")
            return 0
        if a.cmd == "ssh":
            if not pods:
                raise SystemExit("no such pod")
            ip, port = ssh_of(pods[0])
            if not ip:
                raise SystemExit("pod has no public ssh port yet")
            print(f"ssh -i ~/.ssh/dr_runpod -p {port} root@{ip}")
            print(f"HOST={ip} PORT={port}")
            return 0
    if a.cmd in ("rest-status", "rest-terminate"):
        # 2026-09-09: the SDK's GraphQL calls, and later `import runpod` itself, hung for
        # minutes while two pods billed; rest.runpod.io answered in half a second. These
        # commands run before the SDK is imported and never depend on it.
        import urllib.request
        hdr = {"Authorization": f"Bearer {api_key()}", "User-Agent": "dr-cloud/1.0"}
        if a.cmd == "rest-status":
            with urllib.request.urlopen(urllib.request.Request("https://rest.runpod.io/v1/pods", headers=hdr), timeout=60) as r:
                d = json.load(r)
            pods = d if isinstance(d, list) else d.get("pods") or d.get("data") or []
            for p in pods:
                print(f"{p.get('id')}  {p.get('name')}  {p.get('desiredStatus')}  ${p.get('costPerHr')}/h")
            if not pods:
                print("no pods")
            return 0
        if not a.id:
            raise SystemExit("--id required")
        req = urllib.request.Request(f"https://rest.runpod.io/v1/pods/{a.id}", headers=hdr, method="DELETE")
        with urllib.request.urlopen(req, timeout=60) as r:
            print(f"terminated {a.id} (HTTP {r.status})")
        return 0
    if a.cmd == "balance":
        # GraphQL over urllib with the documented api_key parameter and a user agent
        # (the bare urllib call got 403 without one); the SDK is not imported here.
        import urllib.request
        body = json.dumps({"query": "{ myself { clientBalance currentSpendPerHr } }"}).encode()
        req = urllib.request.Request("https://api.runpod.io/graphql?api_key=" + api_key(), data=body,
                                     headers={"Content-Type": "application/json", "User-Agent": "dr-cloud/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        m = (d.get("data") or {}).get("myself") or {}
        if not m:
            print("balance query failed:", json.dumps(d)[:200]); return 1
        print(f"balance USD {m.get('clientBalance')}  spend USD {m.get('currentSpendPerHr')}/h")
        return 0
    import runpod
    runpod.api_key = api_key()

    if a.cmd == "gpus":
        for g in runpod.get_gpus():
            try:
                d = runpod.get_gpu(g["id"])
                lp = d.get("lowestPrice") or {}
                print(f"{g['id']:<28} {d.get('memoryInGb','?'):>4} GB  min ${lp.get('minimumBidPrice','?')}/h spot  ${lp.get('uninterruptablePrice','?')}/h on-demand  secure={d.get('secureCloud')} community={d.get('communityCloud')}")
            except Exception as e:
                print(f"{g['id']:<28} ({e})")
        return 0
    if a.cmd == "create":
        pod = runpod.create_pod(name=a.name, image_name=IMAGE, gpu_type_id=a.gpu, cloud_type=a.cloud,
                                container_disk_in_gb=a.disk, volume_in_gb=0, ports="22/tcp",
                                env={"DR_CLOUD": "1", "PUBLIC_KEY": open(os.path.expanduser("~/.ssh/dr_runpod.pub")).read().strip()},
                                support_public_ip=True)   # PUBLIC_KEY: RunPod templates append it to authorized_keys
        print(json.dumps(pod, indent=1)[:1500])
        print(f"\ncreated pod {pod.get('id')}; wait ~1-2 min then: python cloud/pod.py status --id {pod.get('id')}")
        return 0
    pods = runpod.get_pods()
    if a.id:
        pods = [p for p in pods if p["id"] == a.id]
    if a.cmd == "status":
        for p in pods:
            rt = p.get("runtime") or {}
            ports = [x for x in (rt.get("ports") or []) if x.get("privatePort") == 22]
            ssh = f"{ports[0]['ip']}:{ports[0]['publicPort']}" if ports else "(no ssh port yet)"
            print(f"{p['id']}  {p.get('name')}  {p.get('desiredStatus')}  gpu={p.get('machine', {}).get('gpuDisplayName')}  ${p.get('costPerHr')}/h  ssh={ssh}")
        return 0
    if not a.id:
        raise SystemExit("--id required")
    if a.cmd == "ssh":
        p = pods[0]
        ports = [x for x in ((p.get("runtime") or {}).get("ports") or []) if x.get("privatePort") == 22]
        if not ports:
            raise SystemExit("pod has no public ssh port yet")
        print(f"ssh -i ~/.ssh/dr_runpod -p {ports[0]['publicPort']} root@{ports[0]['ip']}")
        print(f"HOST={ports[0]['ip']} PORT={ports[0]['publicPort']}")
        return 0
    if a.cmd == "stop":
        print(runpod.stop_pod(a.id))
    if a.cmd == "terminate":
        runpod.terminate_pod(a.id)
        print(f"terminated {a.id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
