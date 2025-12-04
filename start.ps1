# Script para iniciar Backend y Frontend simultáneamente
# Ejecutar con: .\start.ps1

Write-Host "🚀 Iniciando RAC Assistant..." -ForegroundColor Green
Write-Host ""

# Verificar si Python está instalado
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python no encontrado. Por favor instala Python 3.10+" -ForegroundColor Red
    exit 1
}

# Verificar si Node.js está instalado
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js encontrado: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js no encontrado. Por favor instala Node.js 18+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📦 Verificando dependencias..." -ForegroundColor Cyan

# Verificar si node_modules existe
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "⚠ Instalando dependencias de frontend..." -ForegroundColor Yellow
    Set-Location frontend
    npm install --legacy-peer-deps
    Set-Location ..
}

Write-Host ""
Write-Host "🔧 Iniciando servicios..." -ForegroundColor Cyan
Write-Host ""

# Iniciar Backend en una nueva ventana de PowerShell
Write-Host "🐍 Iniciando Backend (FastAPI)..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; Write-Host '🐍 Backend FastAPI' -ForegroundColor Blue; Write-Host ''; python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

# Esperar 3 segundos para que el backend inicie
Start-Sleep -Seconds 3

# Iniciar Frontend en una nueva ventana de PowerShell
Write-Host "⚛️  Iniciando Frontend (React + Vite)..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; Write-Host '⚛️  Frontend React + Vite' -ForegroundColor Magenta; Write-Host ''; npm run dev"

Write-Host ""
Write-Host "✅ Servicios iniciados!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 URLs:" -ForegroundColor Cyan
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/api/docs" -ForegroundColor White
Write-Host "   Frontend: http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "💡 Presiona Ctrl+C en cada ventana para detener los servicios" -ForegroundColor Yellow
Write-Host ""
