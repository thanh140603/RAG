# Development startup script for Windows PowerShell

Write-Host "🚀 Starting RAG System in Development Mode..." -ForegroundColor Green

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "⚠️  .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✅ Please update .env with your configuration" -ForegroundColor Green
}

# Start services with docker-compose
docker-compose -f docker-compose.dev.yml up --build

