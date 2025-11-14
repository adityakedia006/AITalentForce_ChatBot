# Quick Start Script for AI Voice Assistant
# This script starts both the backend and frontend

Write-Host "🚀 Starting AI Voice Assistant..." -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "✅ Activating virtual environment..." -ForegroundColor Green
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "⚠️  No virtual environment found. Using global Python..." -ForegroundColor Yellow
}

Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ Error: .env file not found!" -ForegroundColor Red
    Write-Host "Please create a .env file with your API keys:" -ForegroundColor Yellow
    Write-Host "  GROQ_API_KEY=your_groq_key_here"
    Write-Host "  ELEVENLABS_API_KEY=your_elevenlabs_key_here"
    Write-Host ""
    exit 1
}

Write-Host "✅ Environment file found" -ForegroundColor Green
Write-Host ""

# Start backend
Write-Host "🔧 Starting FastAPI Backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python main.py"

# Wait for backend to start
Write-Host "⏳ Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check if backend is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "✅ Backend is running!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Backend might not be ready yet, but continuing..." -ForegroundColor Yellow
}

Write-Host ""

# Start frontend
Write-Host "🎨 Starting Streamlit Frontend..." -ForegroundColor Cyan
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", "streamlit run streamlit_app.py"

Write-Host ""
Write-Host "✨ AI Voice Assistant is starting!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "📍 Streamlit UI: http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tip: Both windows will open in new PowerShell tabs" -ForegroundColor Cyan
Write-Host "💡 Press Ctrl+C in each window to stop the servers" -ForegroundColor Cyan
Write-Host ""
