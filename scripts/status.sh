#!/usr/bin/env bash
cd "$(dirname "$0")/.."
echo "queued:  $(ls queue/[0-9]*.json 2>/dev/null | wc -l)"
echo "running: $(ls running/*.json 2>/dev/null | wc -l)"
echo "done:    $(ls done/*.json 2>/dev/null | wc -l)"
echo "failed:  $(ls failed/*.json 2>/dev/null | wc -l)"
echo "rows:    $(wc -l < results/runs.jsonl)  (last wake at: $(cat .wake_state 2>/dev/null || echo 0))"
echo "--- driver.log"; tail -n 5 logs/driver.log 2>/dev/null
