# Inverse Theremin - Quick Start Script (Windows PowerShell)

Write-Host "================================"
Write-Host "Inverse Theremin - Quick Start"
Write-Host "================================`n"

# Check if virtual environment exists
if (-Not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt

# Check for .env file
if (-Not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Please edit .env with your configuration:" -ForegroundColor Cyan
    Write-Host "  - HOME_ASSISTANT_URL"
    Write-Host "  - HOME_ASSISTANT_TOKEN"
    Write-Host "`nEdit config/default_config.json for advanced settings`n"
}

# Run the main application
Write-Host "`nStarting Inverse Theremin..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Gray

python main.py
