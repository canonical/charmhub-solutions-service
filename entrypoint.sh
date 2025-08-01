#!/bin/sh

# Exit on error
set -e

# Apply database migrations
flask db upgrade

# Seed the database
python -m seed

# Start the application
flask run --host=0.0.0.0
