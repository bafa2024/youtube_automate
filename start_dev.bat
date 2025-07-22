@echo off
echo Starting AI Video Tool on port 8080...
echo.
echo Web interface: http://localhost:8080
echo API docs: http://localhost:8080/docs
echo Health check: http://localhost:8080/health
echo.
echo Press Ctrl+C to stop the server
echo.

python run_dev.py

pause 