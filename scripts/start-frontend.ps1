# Start the Next.js frontend (proxies /api to the backend on :8000).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location "$root\frontend"
npm run dev
Pop-Location
