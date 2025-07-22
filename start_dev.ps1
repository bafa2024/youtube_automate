# PowerShell script to start AI Video Tool on port 8080

Write-Host "🚀 Starting AI Video Tool on port 8080..." -ForegroundColor Green
Write-Host ""
Write-Host "📱 Web interface: http://localhost:8080" -ForegroundColor Cyan
Write-Host "🔧 API docs: http://localhost:8080/docs" -ForegroundColor Cyan
Write-Host "📊 Health check: http://localhost:8080/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

try {
    python run_dev.py
}
catch {
    Write-Host "Error starting the server: $_" -ForegroundColor Red
    Write-Host "Make sure Python is installed and in your PATH" -ForegroundColor Red
}

Read-Host "Press Enter to exit" 