#!/usr/bin/env pwsh
# Start FitSci local infrastructure (PostgreSQL, RabbitMQ, Ollama).
# Usage: ./scripts/dev.ps1 up | down | logs | migrate | pull-model | status

param(
    [Parameter(Position = 0)]
    [ValidateSet("up", "down", "logs", "migrate", "pull-model", "status")]
    [string]$Command = "up"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[*] Created .env from .env.example — review credentials before VPS deploy."
}

switch ($Command) {
    "up" {
        docker compose up -d
        Write-Host ""
        Write-Host "[*] Infra running. Next steps:"
        Write-Host "    cd backend"
        Write-Host "    uv sync"
        Write-Host "    uv run alembic upgrade head"
        Write-Host "    uv run pytest -m `"not integration`""
        Write-Host ""
        Write-Host "    Pull Gemma model: ./scripts/dev.ps1 pull-model"
        Write-Host "    API in Docker:    docker compose --profile app up -d --build"
    }
    "down" {
        docker compose --profile app down
        docker compose down
    }
    "logs" {
        docker compose logs -f postgres rabbitmq ollama
    }
    "migrate" {
        Push-Location backend
        uv run alembic upgrade head
        Pop-Location
    }
    "pull-model" {
        $model = (Get-Content .env | Where-Object { $_ -match '^GEMMA_MODEL_TAG=' }) -replace 'GEMMA_MODEL_TAG=', ''
        if (-not $model) { $model = "gemma4:12b-q4_k_m" }
        docker compose exec ollama ollama pull $model
    }
    "status" {
        docker compose ps
    }
}
