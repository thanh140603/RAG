#!/bin/bash
# Development startup script

echo "🚀 Starting RAG System in Development Mode..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Please update .env with your configuration"
fi

# Start services with docker-compose
docker-compose -f docker-compose.dev.yml up --build

