#!/bin/sh

# Exit on error
set -e

# Wait for database to accept connections
until python -c 'import os, psycopg2; psycopg2.connect(os.environ["POSTGRESQL_DB_CONNECT_STRING"]).close()'; do
  echo "Waiting for database..."
  sleep 1
done

# Apply database migrations
flask db upgrade

# Seed the database
python -m seed

# Start the application
flask run --host=$1 --port=$2
