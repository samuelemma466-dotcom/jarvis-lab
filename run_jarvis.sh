#!/usr/bin/env bash
# Auto-heal wrapper for the JARVIS HUD (v2).
#
# Policy: the assistant must ALWAYS be on screen. Any exit — crash, Gemini
# abort, or a window accidentally closed by hand — is followed by a restart.
#
# To genuinely stop it, run:  ~/jarvis-lab/jarvis-stop
# To bring it back:           ~/jarvis-lab/jarvis-start
#
# Rapid repeated deaths back off exponentially (5s → 10s → ... → 60s) so a
# hard bug can never spin the CPU into a loop.
cd ~/jarvis-lab/jarvis-face-hud
LOG=~/jarvis-lab/jarvis.log
OFF=~/jarvis-lab/jarvis-off

backoff=5
while :; do
  if [ -f "$OFF" ]; then
    echo "$(date '+%F %T') off-switch present — staying down" >> "$LOG"
    rm -f "$OFF"   # consume the switch; next start must be through jarvis-start
    break
  fi
  t0=$(date +%s)
  # -u = unbuffered: the session's own [JARVIS] lines reach the log live,
  # so a deaf session can be diagnosed the moment it happens.
  .venv/bin/python -u main.py >> "$LOG" 2>&1
  code=$?
  ran=$(( $(date +%s) - t0 ))
  echo "$(date '+%F %T') main.py exit=$code (ran ${ran}s)" >> "$LOG"
  [ -f "$OFF" ] && continue
  if [ "$ran" -lt 15 ]; then
    backoff=$(( backoff < 60 ? backoff * 2 : 60 ))
  else
    backoff=5
  fi
  sleep "$backoff"
done
