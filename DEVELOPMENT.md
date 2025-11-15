# Development Scripts

## Backend (FastAPI)

### Setup
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Run Backend
```powershell
# Make sure .env is configured with API keys
python main.py

# Or use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run on: http://localhost:8000

## Frontend (React + Vite)

### Setup
```powershell
cd frontend

# Install dependencies (choose one)
npm install
# or
bun install
```

### Run Frontend
```powershell
cd frontend

# Development mode
npm run dev
# or
bun run dev
```

Frontend will run on: http://localhost:5173

## Running Both Together

### PowerShell Script (Windows)
```powershell
# Terminal 1 - Backend
.\venv\Scripts\Activate.ps1
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Quick Start Script
Create `start-dev.ps1`:
```powershell
# Start backend in background
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd $PSScriptRoot; .\venv\Scripts\Activate.ps1; python main.py"

# Wait for backend to start
Start-Sleep -Seconds 3

# Start frontend in background
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "cd $PSScriptRoot\frontend; npm run dev"

Write-Host "Backend: http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
```

Run with: `.\start-dev.ps1`

## Environment Variables

### Backend (.env in root)
```env
GROQ_API_KEY=your_groq_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
HOST=0.0.0.0
PORT=8000
DEBUG=True
LLM_MODEL=llama-3.3-70b-versatile
ELEVENLABS_MODEL=scribe_v1
```

### Frontend (.env in frontend/)
```env
VITE_API_BASE_URL=http://localhost:8000
```

## Testing

### Backend API
```powershell
# Test health endpoint
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/api/chat `
  -H "Content-Type: application/json" `
  -d '{"message": "Hello!"}'
```

### Frontend
Open browser to http://localhost:5173 and test:
1. Text chat functionality
2. Voice recording (requires microphone permission)
3. Dark/light theme toggle
4. Download chat history

## Building for Production

### Backend
```powershell
# Run with production settings
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend
```powershell
cd frontend

# Build
npm run build

# Preview build
npm run preview
```

Build output will be in `frontend/dist/`

## Common Issues

### Backend won't start
- Check if .env file exists with API keys
- Verify virtual environment is activated
- Check if port 8000 is already in use

### Frontend can't connect to backend
- Verify backend is running on http://localhost:8000
- Check frontend/.env has correct VITE_API_BASE_URL
- Check browser console for CORS errors

### Voice recording not working
- Grant microphone permissions in browser
- Use Chrome/Edge (best compatibility)
- Check if using HTTPS in production
