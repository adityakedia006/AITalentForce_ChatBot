# AI Chatbot Development Startup Script
# This script starts both the backend and frontend servers

Write-Host "🚀 Starting AI Voice Chatbot Development Environment" -ForegroundColor Cyan
Write-Host ""

# Check if backend .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Warning: .env file not found in root directory" -ForegroundColor Yellow
    Write-Host "   Please create .env with GROQ_API_KEY and ELEVENLABS_API_KEY" -ForegroundColor Yellow
    Write-Host ""
}

# Check if frontend .env exists
if (-not (Test-Path "frontend\.env")) {
    Write-Host "⚠️  Warning: frontend\.env file not found" -ForegroundColor Yellow
    Write-Host "   Creating default frontend\.env..." -ForegroundColor Yellow
    "VITE_API_BASE_URL=http://localhost:8000" | Out-File -FilePath "frontend\.env" -Encoding UTF8
    Write-Host "   ✓ Created frontend\.env" -ForegroundColor Green
    Write-Host ""
}

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "⚠️  Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "   ✓ Virtual environment created" -ForegroundColor Green
    Write-Host ""
}

# Check if node_modules exists in frontend
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "⚠️  Frontend dependencies not installed. Installing..." -ForegroundColor Yellow
    Push-Location frontend
    npm install
    Pop-Location
    Write-Host "   ✓ Frontend dependencies installed" -ForegroundColor Green
    Write-Host ""
}

Write-Host "Starting Backend Server..." -ForegroundColor Green
Start-Process pwsh -ArgumentList "-NoExit", "-Command", @"
`$host.UI.RawUI.WindowTitle = 'Backend - FastAPI Server'
Write-Host '🔧 Backend Server (FastAPI)' -ForegroundColor Cyan
Write-Host '========================' -ForegroundColor Cyan
Write-Host ''
cd '$PSScriptRoot'
.\venv\Scripts\Activate.ps1
Write-Host '✓ Virtual environment activated' -ForegroundColor Green
Write-Host 'Starting server on http://localhost:8000' -ForegroundColor Green
Write-Host ''
python main.py
"@

Write-Host "✓ Backend server starting..." -ForegroundColor Green
Write-Host ""

# Wait for backend to start
Write-Host "Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "Starting Frontend Server..." -ForegroundColor Green
Start-Process pwsh -ArgumentList "-NoExit", "-Command", @"
`$host.UI.RawUI.WindowTitle = 'Frontend - React + Vite'
Write-Host '⚛️  Frontend Server (React + Vite)' -ForegroundColor Cyan
Write-Host '=================================' -ForegroundColor Cyan
Write-Host ''
cd '$PSScriptRoot\frontend'
Write-Host '✓ Changed to frontend directory' -ForegroundColor Green
Write-Host 'Starting development server...' -ForegroundColor Green
Write-Host ''
npm run dev
"@

Write-Host "✓ Frontend server starting..." -ForegroundColor Green
Write-Host ""

Start-Sleep -Seconds 2

Write-Host "✅ Development Environment Started!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Services:" -ForegroundColor Cyan
Write-Host "   Backend API:  http://localhost:8000" -ForegroundColor White
Write-Host "   Frontend App: http://localhost:5173" -ForegroundColor White
Write-Host "   API Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C in each terminal window to stop the servers" -ForegroundColor Yellow
Write-Host ""
Write-Host "💡 Tip: Check both terminal windows for logs and errors" -ForegroundColor Cyan
