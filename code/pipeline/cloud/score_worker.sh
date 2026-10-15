#!/usr/bin/env bash
# Consume logs/score_queue.txt on the local card: score each pulled run
# (anchor = its author's base at the same tag), start its judge (sample 0),
# and mark it done in logs/score_done.txt. Runs until logs/score_stop exists
# and the queue is drained.
cd "/c/Work/Personal/Voice_Style_Retune/decompose_regenerate"
export PYTHONIOENCODING=utf-8
export PATH="/c/Python314:/c/Python314/Scripts:$PATH"
touch logs/score_queue.txt logs/score_done.txt
echo "$(date +%H:%M) score worker start"
while true; do
  sed -i 's/\r$//' logs/score_queue.txt logs/score_done.txt 2>/dev/null
  next=""
  while read -r r; do
    r="${r%$'\r'}"
    [ -n "$r" ] || continue
    grep -qx "$r" <(tr -d "\r" < logs/score_done.txt) && continue
    next="$r"; break
  done < logs/score_queue.txt
  if [ -z "$next" ]; then
    [ -f logs/score_stop ] && break
    sleep 60; continue
  fi
  echo "$(date +%H:%M) scoring $next"
  python dr/score_runs.py --runs "$next" >> logs/score_worker_runs.log 2>&1 && echo "$next" >> logs/score_done.txt || echo "$(date +%H:%M) FAILED $next"
done
python dr/backup_runs.py
echo "$(date +%H:%M) score worker done"
