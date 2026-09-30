#!/usr/bin/env python3
"""Atomically add a job to queue/. Args after `--` are passed to the tool."""
import argparse, json, re, time
from common import ROOT

ap = argparse.ArgumentParser()
ap.add_argument("--id", required=True)
ap.add_argument("--tool", required=True, help="an Oak console command, or 'python'")
ap.add_argument("--script", help="for --tool python: path under experiments/")
ap.add_argument("--hypothesis", default="")
ap.add_argument("--notes", default="")
ap.add_argument("--priority", type=int, default=50, help="lower runs first")
ap.add_argument("args", nargs=argparse.REMAINDER)
a = ap.parse_args()

if not re.fullmatch(r"[A-Za-z0-9_.-]+", a.id):
    ap.error("id must match [A-Za-z0-9_.-]+")
rest = a.args[1:] if a.args and a.args[0] == "--" else a.args
job = {"id": a.id, "tool": a.tool, "args": rest, "hypothesis": a.hypothesis, "notes": a.notes}
if a.tool == "python":
    if not a.script:
        ap.error("--script required for python jobs")
    job["script"] = a.script

q = ROOT / "queue"
q.mkdir(exist_ok=True)
name = f"{a.priority:03d}-{int(time.time()*1000)}-{a.id}.json"
tmp = q / f".tmp-{name}"
tmp.write_text(json.dumps(job, indent=1))
tmp.rename(q / name)
print("queued", name)
