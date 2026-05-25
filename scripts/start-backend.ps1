# Start the FastAPI backend with auto-reload (mock mode by default).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location "$root\backend"
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000
Pop-Location
