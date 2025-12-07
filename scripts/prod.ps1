# Production startup script for Windows PowerShell

Write-Host "🚀 Starting RAG System in Production Mode..." -ForegroundColor Green

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "❌ .env file not found. Please create it from .env.example" -ForegroundColor Red
    exit 1
}

# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

Write-Host "✅ Services started in production mode" -ForegroundColor Green
Write-Host "📊 Check logs with: docker-compose -f docker-compose.prod.yml logs -f" -ForegroundColor Cyan

