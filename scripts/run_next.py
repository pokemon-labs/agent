#!/usr/bin/env python3
"""Run the next queued job. Exit 0 = ran one job (pass or fail), 1 = queue empty."""
import json, os, re, subprocess, sys, time
from pathlib import Path
from common import ROOT, load_config

cfg = load_config()
VENV = Path(cfg.get("OAK_VENV", ""))
OAK_SRC = Path(cfg.get("OAK_SRC", ""))
TIMEOUT = int(cfg.get("JOB_TIMEOUT", 1800))
MAX_LOG = 20_000
# TODO(Day 1): confirm the exact names of Oak console commands (incl. the W/D/L one).
ALLOWED_TOOLS = {"benchmark", "vs"}

def oak_version():
    try:
        rev = subprocess.check_output(["git", "-C", str(OAK_SRC), "rev-parse", "--short", "HEAD"],
                                      text=True, stderr=subprocess.DEVNULL).strip()
        dirty = subprocess.call(["git", "-C", str(OAK_SRC), "diff", "--quiet"]) != 0
        return rev + ("-dirty" if dirty else "")
    except Exception:
        return "unknown"

def build_cmd(job):
    args = [str(a) for a in job.get("args", [])]
    if job["tool"] == "python":
        script = (ROOT / job["script"]).resolve()
        if not script.is_relative_to((ROOT / "experiments").resolve()):
            raise ValueError("scripts must live in experiments/")
        return [str(VENV / "bin" / "python"), str(script), *args]
    if job["tool"] not in ALLOWED_TOOLS:
        raise ValueError(f"tool not allowed: {job['tool']}")
    return [str(VENV / "bin" / job["tool"]), *args]

def parse_output(stdout):
    """Best-effort structured parsing. Raw stdout is always logged too. Fix on Day 1."""
    parsed = {}
    # benchmark: "861ms. 32000 iterations."
    ms = re.findall(r"(\d+)\s*ms\.\s*(\d+)\s*iterations", stdout)
    if ms:
        parsed["benchmark"] = [{"ms": int(m), "iterations": int(i)} for m, i in ms]
    # W/D/L: GUESS at format, e.g. "W: 10 D: 2 L: 8" or "10/2/8" -> verify on Day 1
    m = re.search(r"[Ww](?:ins?)?\D{0,3}(\d+)\D+[Dd](?:raws?)?\D{0,3}(\d+)\D+[Ll](?:oss(?:es)?)?\D{0,3}(\d+)", stdout)
    if m:
        parsed["wdl_guess"] = {"w": int(m[1]), "d": int(m[2]), "l": int(m[3])}
    for line in stdout.splitlines():           # experiment scripts: RESULT {json}
        if line.startswith("RESULT "):
            try:
                parsed["result"] = json.loads(line[7:])
            except json.JSONDecodeError:
                parsed["result_error"] = "bad RESULT json"
    return parsed

def main():
    for d in ("queue", "running", "done", "failed", "results"):
        (ROOT / d).mkdir(exist_ok=True)
    jobs = sorted(ROOT.joinpath("queue").glob("[0-9]*.json"))
    if not jobs:
        return 1
    running = ROOT / "running" / jobs[0].name
    jobs[0].rename(running)
    row = {"ts": time.time(), "file": running.name, "oak_version": oak_version(),
           "load_at_start": round(os.getloadavg()[0], 2)}
    ok = False
    try:
        job = json.loads(running.read_text())
        row["job"] = job
        cmd = build_cmd(job)
        row["cmd"] = cmd
        t0 = time.time()
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=TIMEOUT)
        row.update(wall_s=round(time.time() - t0, 2), exit=p.returncode,
                   stdout=p.stdout[-MAX_LOG:], stderr=p.stderr[-MAX_LOG:],
                   parsed=parse_output(p.stdout))
        ok = p.returncode == 0
    except subprocess.TimeoutExpired:
        row["error"] = f"timeout after {TIMEOUT}s"
    except Exception as e:
        row["error"] = repr(e)
    with open(ROOT / "results" / "runs.jsonl", "a") as f:
        f.write(json.dumps(row) + "\n")
    running.rename(ROOT / ("done" if ok else "failed") / running.name)
    return 0

sys.exit(main())
