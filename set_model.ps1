# PowerShell script to update AGENT_MODEL in .env file
# Usage: .\set_model.ps1 [model_name]
# Example: .\set_model.ps1 gemini-3-pro-preview

param(
    [string]$ModelName = "gemini-3-pro-preview"
)

$envFile = Join-Path $PSScriptRoot ".env"

Write-Host "🔧 Updating .env file with AGENT_MODEL=$ModelName" -ForegroundColor Cyan

# Check if .env exists
if (-not (Test-Path $envFile)) {
    Write-Host "❌ .env file not found at: $envFile" -ForegroundColor Red
    Write-Host "Creating new .env file..." -ForegroundColor Yellow
    
    # Create basic .env file
    $content = @"
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=ccibt-hack25ww7-706
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_USE_VERTEXAI=True
LOGS_BUCKET_NAME=gs://ccibt-agent-logs

# GCS Data Bucket Settings
GCS_DATA_BUCKET=gs://datasets-ccibt-hack25ww7-706
GCS_DATASET_PREFIX=datasets/uc4-market-activity-prediction-agent

# Agent Memory Settings
GCS_MEMORY_PATH=agent_memory

# Model Configuration
AGENT_MODEL=$ModelName

# Environment
ENVIRONMENT=development
"@
    
    $content | Out-File -FilePath $envFile -Encoding UTF8
    Write-Host "✅ Created .env with AGENT_MODEL=$ModelName" -ForegroundColor Green
    exit 0
}

# Read existing .env file
$lines = Get-Content $envFile

# Check if AGENT_MODEL already exists
$modelFound = $false
$newLines = @()

foreach ($line in $lines) {
    if ($line -match "^AGENT_MODEL=") {
        $newLines += "AGENT_MODEL=$ModelName"
        $modelFound = $true
        Write-Host "✅ Updated existing AGENT_MODEL to: $ModelName" -ForegroundColor Green
    } else {
        $newLines += $line
    }
}

# If AGENT_MODEL doesn't exist, add it
if (-not $modelFound) {
    $newLines += ""
    $newLines += "# Model Configuration"
    $newLines += "AGENT_MODEL=$ModelName"
    Write-Host "✅ Added AGENT_MODEL=$ModelName to .env" -ForegroundColor Green
}

# Write back to file
$newLines | Out-File -FilePath $envFile -Encoding UTF8

Write-Host ""
Write-Host "📝 .env file updated successfully!" -ForegroundColor Green
Write-Host "🔄 Please restart the agent for changes to take effect." -ForegroundColor Yellow
Write-Host ""
Write-Host "To verify, check the logs for:" -ForegroundColor Cyan
Write-Host "  model: $ModelName" -ForegroundColor White
