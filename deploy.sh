#!/bin/bash
set -e

echo "🚀 Starting deployment..."

cd /opt/factora

echo "📥 Pulling latest code..."
git pull origin main

echo "🐳 Rebuilding containers..."
docker compose down
docker compose build --no-cache
docker compose up -d

echo "🔄 Running migrations..."
docker compose exec -T backend python manage.py migrate

echo "✅ Deployment complete!"
