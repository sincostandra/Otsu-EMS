#!/bin/sh
set -e

# Apply migrations on every boot (safe/idempotent).
python manage.py migrate --noinput

# Optionally seed the demo workforce. Enable by setting RUN_SEED=1
# (idempotent: existing users/employees are reused). Set SEED_RESET=1 to wipe
# non-admin data first and re-seed from scratch.
if [ "${RUN_SEED:-0}" = "1" ]; then
  if [ "${SEED_RESET:-0}" = "1" ]; then
    python manage.py seed_demo --reset
  else
    python manage.py seed_demo
  fi
fi

# Railway (and most PaaS) inject $PORT. WEB_CONCURRENCY tunes worker count.
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout 120
