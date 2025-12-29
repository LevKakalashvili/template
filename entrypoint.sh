#!/bin/bash

export APP_HOST=${APP_HOST:-0.0.0.0}
export APP_PORT=${APP_PORT:-8000}
export UVICORN_WORKERS=${UVICORN_WORKERS:-4}
export LOG_LEVEL=${LOG_LEVEL:-INFO}


if [ "$1" != "pytest" ] && [ -z "$(echo "$@" | grep 'test_')" ]; then
# alembic upgrade head
echo "Apply migrations"
python -m alembic upgrade head || exit 1

echo "Add project templates"
python3 manager.py init_project_templates
fi

if [ "$#" -gt 0 ]; then
  exec "$@"
else
  export GUNICORN_LOG_LEVEL=$(echo $LOG_LEVEL | tr '[:upper:]' '[:lower:]')
  echo "Starting application..."
  # Start server with Gunicorn + UvicornWorker
  exec gunicorn -k uvicorn.workers.UvicornWorker -w $UVICORN_WORKERS -b $APP_HOST:$APP_PORT --log-level $GUNICORN_LOG_LEVEL main:app
fi
