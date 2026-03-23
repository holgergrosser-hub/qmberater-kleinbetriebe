$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

Write-Host "Starte Google Ads Analyzer Wizard..." -ForegroundColor Cyan

try {
    python .\wizard.py
} catch {
    Write-Host "Fehler beim Start. Prüfe, ob Python installiert ist und im PATH liegt." -ForegroundColor Red
    Write-Host "Test: python --version" -ForegroundColor Yellow
    throw
}

Write-Host "\nFertig. Drücke Enter zum Schließen..." -ForegroundColor Green
[void](Read-Host)
