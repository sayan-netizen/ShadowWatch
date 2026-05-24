#!/usr/bin/env pwsh
# dev.ps1 — Start both backend and frontend for local development
# Usage: .\dev.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   ShadowWatch — Local Dev Server     ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Activate Python venv and start Flask backend ─────────────────────────────
Write-Host "[1/2] Starting Flask backend on http://localhost:5000 ..." -ForegroundColor Yellow

$backendJob = Start-Job -ScriptBlock {
    Set-Location "$using:PSScriptRoot\backend"
    if (Test-Path "venv\Scripts\Activate.ps1") {
        & "venv\Scripts\Activate.ps1"
    }
    python run.py
}

Start-Sleep -Seconds 2   # Give Flask a moment to boot

# ── Start Vite frontend ───────────────────────────────────────────────────────
Write-Host "[2/2] Starting Vite frontend on http://localhost:5173 ..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop both servers." -ForegroundColor Gray
Write-Host ""

try {
    Set-Location "$PSScriptRoot\frontend"
    npm run dev
} finally {
    # Clean up backend job when frontend is stopped
    Write-Host "`nStopping backend..." -ForegroundColor Yellow
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -ErrorAction SilentlyContinue
}
