#!/usr/bin/env bash
# Same loop as cloud/score_worker.sh but score_runs.py runs with --no-judge:
# the cross-family runs (2026-09-09) are scored on the local card without
# spending OpenRouter credit on the per-run 2AFC judge; judges for those runs
# are launched later, deliberately, with a budget. Stop file: logs/score_stop_nojudge.
cd "/c/Work/Personal/Voice_Style_Retune/decompose_regenerate"
export PYTHONIOENCODING=utf-8
export PATH="/c/Python314:/c/Python314/Scripts:$PATH"
touch logs/score_queue.txt logs/score_done.txt
echo "$(date +%H:%M) score worker (no judge) start"
while :; do
  sed -i 's/\r$//' logs/score_queue.txt logs/score_done.txt 2>/dev/null
  next=""
  while read -r r; do
    r="${r%$'\r'}"; [ -n "$r" ] || continue
    grep -qx "$r" <(tr -d "\r" < logs/score_done.txt) && continue
    next="$r"; break
  done < logs/score_queue.txt
  if [ -z "$next" ]; then
    [ -f logs/score_stop_nojudge ] && break
    sleep 120; continue
  fi
  echo "$(date +%H:%M) scoring $next (no judge)"
  python dr/score_runs.py --runs "$next" --no-judge >> logs/score_worker_runs.log 2>&1 && echo "$next" >> logs/score_done.txt || echo "$(date +%H:%M) FAILED $next"
done
python dr/backup_runs.py
echo "$(date +%H:%M) score worker (no judge) done"
