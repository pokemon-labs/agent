# Day 1 interactive checklist
Run `claude` in this repo (permission prompts on; you approve as it goes).

1. Edit `config.env` (OAK_SRC, OAK_VENV). Confirm `$OAK_VENV/bin/benchmark --help` works.
2. Tell the agent to inventory every console command in `$OAK_VENV/bin` from the oak package and run `--help` on each.
3. Have it read the Oak source and the Python API, then draft `docs/commands.md` and `docs/python-api.md`.
4. **Confirm output formats** by running one tiny `benchmark` and one tiny W/D/L (vs) command
   and pasting real output into the docs. Then fix `parse_output()` in `scripts/run_next.py` and
   `ALLOWED_TOOLS`. Currently a best guess for W/D/L.
5. Write a first `experiments/` script using `oak.search`, run it once by hand, verify the `RESULT` line.
6. Smoke test the pipeline: enqueue 2 tiny jobs, run `python scripts/run_next.py` twice, check `results/runs.jsonl`.
7. Write 2-3 real hypotheses into `hypotheses.md` with success criteria.
8. Test `scripts/driver.sh` in tmux for an hour while you watch. Check `/usage` before and after.
9. Review `.claude/settings.json` with `/permissions`, then launch unattended.
