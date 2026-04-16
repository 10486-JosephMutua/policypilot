#!/usr/bin/env bash
set -e

echo "=== PolicyPilot Startup ==="

# Backend
echo "→ Starting Flask backend on :5000"
cd backend
if [ ! -f .env ]; then
  cp .env.example .env
  echo "  ⚠ Created backend/.env from template – add ANTHROPIC_API_KEY"
fi
pip install -r requirements.txt -q
python app.py &

# Frontend
echo "→ Starting React frontend on :3000"
cd ../frontend
if [ ! -f .env ]; then
  cp .env.example .env
fi
npm install --silent
npm start
