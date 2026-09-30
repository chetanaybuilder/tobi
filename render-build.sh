#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Building frontend..."
npm install
npm run build

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Running database migrations..."
alembic upgrade head
