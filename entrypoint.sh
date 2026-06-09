#!/bin/sh

# Exit on error
set -e

if [ -n "$POSTGRESQL_DB_CONNECT_STRING" ]; then
	python3 migrate.py
fi

if [ "$SEED_DB" = "true" ]; then
	python3 -m seed
fi

exec "$@"
