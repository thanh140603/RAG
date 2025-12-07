#!/bin/bash
# Production startup script

echo "🚀 Starting RAG System in Production Mode..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it from .env.example"
    exit 1
fi

# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

echo "✅ Services started in production mode"
echo "📊 Check logs with: docker-compose -f docker-compose.prod.yml logs -f"

