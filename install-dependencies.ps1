# Install Python (backend) and npm (frontend) dependencies.
# Run: powershell -ExecutionPolicy Bypass -File .\install-dependencies.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "== S.U.K.U dependency install ==" -ForegroundColor Cyan
Write-Host ("Root: " + $Root)

$Backend = Join-Path $Root "backend"
$VenvPy = Join-Path $Backend ".venv\Scripts\python.exe"
$VenvPip = Join-Path $Backend ".venv\Scripts\pip.exe"

if (-not (Test-Path $Backend)) {
    throw "backend folder not found"
}

Push-Location $Backend
try {
    if (-not (Test-Path $VenvPy)) {
        Write-Host "Creating Python virtual environment (.venv)..." -ForegroundColor Yellow
        python -m venv .venv
        if (-not (Test-Path $VenvPy)) {
            throw "venv failed. Is python on PATH? Try: py -3 -m venv .venv"
        }
    }
    Write-Host "Installing Python packages..." -ForegroundColor Yellow
    & $VenvPip install --upgrade pip
    & $VenvPip install -r requirements.txt
    Write-Host "Backend dependencies OK." -ForegroundColor Green
}
finally {
    Pop-Location
}

$Frontend = Join-Path $Root "frontend"
if (-not (Test-Path $Frontend)) {
    throw "frontend folder not found"
}

Push-Location $Frontend
try {
    Write-Host "Installing npm packages..." -ForegroundColor Yellow
    npm install
    Write-Host "Frontend dependencies OK." -ForegroundColor Green
}
finally {
    Pop-Location
}

Write-Host "Done. Read SETUP_AND_RUN.md to start servers." -ForegroundColor Cyan
