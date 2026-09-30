#!/usr/bin/env bash
# Event-driven loop: run queued jobs with no LLM, wake Claude only when new results exist.
cd "$(dirname "$0")/.." || exit 1
exec 9>.driver.lock; flock -n 9 || { echo "driver already running"; exit 1; }
set -a; source config.env; set +a
mkdir -p logs

while [ ! -f STOP ]; do
  ran=0
  for _ in $(seq "${BATCH:-6}"); do
    [ -f STOP ] && break
    python3 scripts/run_next.py >> logs/runner.log 2>&1 || break
    ran=$((ran+1))
  done

  total=$(wc -l < results/runs.jsonl)
  seen=$(cat .wake_state 2>/dev/null || echo 0)

  # wake if there are new results, or on the very first pass (agent must seed the queue)
  if [ "$total" -gt "$seen" ] || [ ! -f .wake_state ]; then
    echo "$(date -Is) waking claude (rows $seen -> $total)" >> logs/driver.log
    claude -p "$(cat scripts/wake_prompt.md)" --permission-mode acceptEdits >> logs/claude.log 2>&1
    status=$?
    if [ $status -eq 0 ]; then
      echo "$total" > .wake_state
      git add -A >/dev/null 2>&1 && git commit -qm "auto: wake at row $total" >/dev/null 2>&1
      [ "${PUSH:-0}" = "1" ] && git push -q >/dev/null 2>&1
    else
      echo "$(date -Is) claude exited $status (rate limit?), backing off 30m" >> logs/driver.log
      # keep grinding the queue while Claude is unavailable
      if [ -n "$(ls queue/[0-9]*.json 2>/dev/null)" ]; then continue; fi
      sleep 1800
      continue
    fi
  fi

  # nothing queued and nothing new: idle politely
  if [ -z "$(ls queue/[0-9]*.json 2>/dev/null)" ]; then sleep 900; fi
done
echo "$(date -Is) STOP file found, exiting" >> logs/driver.log
