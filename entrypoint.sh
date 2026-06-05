#!/bin/sh

# Exit on error
set -e

# Wait for database to accept connections (max ~60s by default)
max_retries="${DB_WAIT_RETRIES:-60}"
i=0
until python -c 'import os, psycopg2; psycopg2.connect(os.environ["POSTGRESQL_DB_CONNECT_STRING"]).close()'; do
  i=$((i + 1))
  if [ "$i" -ge "$max_retries" ]; then
    echo "Database not ready after ${max_retries}s, exiting." >&2
    exit 1
  fi
  echo "Waiting for database..."
  sleep 1
done

# Apply database migrations
flask db upgrade

# Seed the database
python -m seed

# Start the application
flask run --host=$1 --port=$2
