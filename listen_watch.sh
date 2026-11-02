#!/usr/bin/env bash
# JARVIS listening watchdog v2.
#
# WHY: the assistant's capture can detach when the default microphone changes
# (earbuds connecting/disconnecting, phone stealing the headset). When that
# happens the app still looks alive, but it hears nothing — the exact
# "listening stopped again" symptom. This loop measures the mic and repairs
# the chain.
#
# EVERY 12 s:
#   1. record 1.5 s from the CURRENT default source and log the peak
#      (a live voice trace; ~0 means no signal reaches the laptop at all),
#   2. if the assistant process or its capture consumer vanished three checks
#      in a row, restart the app through the auto-heal wrapper,
#   3. if the wrapper itself died (and no manual stop flag), start it again.

LOG=~/jarvis-lab/listen.log
WAV=/tmp/opencode/watch.wav
OFF=~/jarvis-lab/jarvis-off
MISSING=0

echo "$(date '+%F %T') watchdog v2 start" >> "$LOG"

while :; do
  ts=$(date '+%F %T')

  # ── 1. microphone sample ────────────────────────────────────────────────
  if timeout 4 arecord -f S16_LE -r 16000 -d 1 -D default > "$WAV.tmp" 2>/dev/null; then
    peak=$(python3 - "$WAV.tmp" <<'PY'
import struct, sys, wave
try:
    w = wave.open(sys.argv[1], 'rb')
    n = w.getnframes()
    v = struct.unpack('<%dh' % (n * w.getnchannels()), w.readframes(n))
    print(max((abs(x) for x in v), default=0))
except Exception:
    print(-1)
PY
)
    mv -f "$WAV.tmp" "$WAV"
    echo "$ts peak=$peak" >> "$LOG"
    [ "$peak" = "-1" ] && MISSING=$((MISSING + 1))
  else
    echo "$ts capture FAILED" >> "$LOG"
    MISSING=$((MISSING + 1))
  fi

  # ── 2. is the assistant alive and attached to a microphone? ─────────────
  app_alive=0
  pgrep -f "python -u mai[n]" >/dev/null 2>&1 && app_alive=1

  if [ "$app_alive" = 1 ]; then
    if pactl list source-outputs 2>/dev/null | grep -q "python3.13"; then
      MISSING=0
    else
      MISSING=$((MISSING + 1))
      echo "$ts capture consumer NOT attached ($MISSING/3)" >> "$LOG"
    fi
  else
    echo "$ts assistant process absent ($MISSING/3)" >> "$LOG"
    MISSING=$((MISSING + 1))
  fi

  # ── 3. repair ───────────────────────────────────────────────────────────
  if [ -f "$OFF" ]; then
    MISSING=0                      # deliberately stopped; never fight the user
  elif [ "$MISSING" -ge 3 ]; then
    echo "$ts repair: restarting assistant" >> "$LOG"
    if pgrep -f "run_jarvis[.]sh" >/dev/null 2>&1; then
      for p in $(pgrep -f "python -u mai[n]" 2>/dev/null); do kill "$p" 2>/dev/null; done
    else
      bash "$HOME/jarvis-lab/jarvis-start" >/dev/null 2>&1
    fi
    MISSING=0
    sleep 5
  fi

  # ── 4. keep the wrapper itself alive (it can be killed with a shell) ────
  if [ ! -f "$OFF" ] && ! pgrep -f "run_jarvis[.]sh" >/dev/null 2>&1; then
    echo "$ts wrapper absent — starting it" >> "$LOG"
    bash "$HOME/jarvis-lab/jarvis-start" >/dev/null 2>&1
  fi

  sleep 12
done
