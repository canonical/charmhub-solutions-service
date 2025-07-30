#!/bin/sh

# Exit on error
set -e

# Apply database migrations
flask db upgrade

# Seed the database
python -m tests.seed

# Start the application
flask run --host=$1 --port=$2
