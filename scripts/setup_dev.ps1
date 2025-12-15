#!/usr/bin/env pwsh
Write-Host "Creating virtual environment .venv and installing dev dependencies..."
python -m venv .venv
Write-Host "Activating virtual environment and installing requirements..."
. ./.venv/Scripts/Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
Write-Host "Dev setup complete. Activate with: . ./.venv/Scripts/Activate.ps1"
