#!/bin/bash
# Quick-start script for local development
set -e

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from example — edit it before production use."
fi

pip install -r requirements.txt -q
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
