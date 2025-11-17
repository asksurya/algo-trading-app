#!/bin/bash
set -e
poetry install --no-dev
uvicorn app.main:app --host 0.0.0.0 --port 8080
