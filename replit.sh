#!/bin/bash

# Install dependencies using Poetry
poetry install

# Install prisma
poetry run prisma generate

# Run Prisma migration
poetry run prisma migrate dev

# Start the application with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000