@echo off
REM Start Web Interface for Media Tool (Windows)

echo.
echo ========================================
echo   Media Tool Web Interface
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install flask werkzeug yt-dlp
echo.

REM Create necessary directories
if not exist "uploads" mkdir uploads
if not exist "outputs" mkdir outputs

echo ========================================
echo   Starting Web Server...
echo ========================================
echo.
echo Open your browser at: http://localhost:5000
echo.
echo Press CTRL+C to stop the server
echo.
echo ========================================
echo.

REM Start the Flask app
python web_app.py

pause

