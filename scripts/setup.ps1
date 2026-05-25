# One-time setup: backend venv + frontend deps.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Write-Host "==> Setting up backend venv..." -ForegroundColor Cyan
Push-Location "$root\backend"
python -m venv .venv
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
Pop-Location

Write-Host "==> Installing frontend deps..." -ForegroundColor Cyan
Push-Location "$root\frontend"
npm install
Pop-Location

Write-Host "==> Done. Start the backend and frontend in two terminals:" -ForegroundColor Green
Write-Host "    scripts\start-backend.ps1"
Write-Host "    scripts\start-frontend.ps1"
