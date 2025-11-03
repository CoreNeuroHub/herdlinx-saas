@echo off
REM ############################################################################
REM # HerdLinx Server UI - Windows Startup Script
REM #
REM # Usage:
REM #   start-server.bat                 # Start with defaults
REM #   start-server.bat dev             # Start in development mode
REM #   start-server.bat prod            # Start in production mode
REM #   start-server.bat help            # Show help
REM #
REM ############################################################################

setlocal enabledelayedexpansion

REM Color codes (using for loop workaround)
for /F %%A in ('copy /Z "%~f0" nul') do set "BS=%%A"

REM Get script directory
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR:~0,-9%

REM Set default mode
set MODE=%1
if "%MODE%"=="" set MODE=default

REM Virtual environment path
set VENV_DIR=%PROJECT_ROOT%venv
set LOG_DIR=%PROJECT_ROOT%logs

echo.
echo ===============================================================
echo   HerdLinx Server UI Startup
echo ===============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Install from: https://www.python.org/
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo [OK] %%i

REM Setup virtual environment
if not exist "%VENV_DIR%" (
    echo [INFO] Creating virtual environment...
    python -m venv "%VENV_DIR%"
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Activate virtual environment
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    exit /b 1
)
echo [OK] Virtual environment activated

REM Install dependencies
echo.
echo [INFO] Installing dependencies...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -r "%PROJECT_ROOT%requirements.txt"
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    exit /b 1
)
echo [OK] Dependencies installed

REM Setup environment file
if exist "%PROJECT_ROOT%.env" (
    echo [OK] .env file already exists
) else (
    echo [INFO] Creating .env file...
    (
        echo # HerdLinx Server UI Configuration
        echo IS_SERVER_UI=True
        echo FLASK_ENV=development
        echo.
        echo # Database
        echo SQLALCHEMY_DATABASE_URI=sqlite:///office_app/office_app.db
        echo.
        echo # Pi Backend Connection
        echo REMOTE_PI_HOST=192.168.1.100
        echo REMOTE_PI_PORT=5001
        echo PI_API_KEY=hxb_your_api_key_here
        echo USE_SSL_FOR_PI=True
        echo USE_SELF_SIGNED_CERT=True
        echo.
        echo # Sync Configuration
        echo DB_SYNC_INTERVAL=10
        echo.
        echo # Server
        echo PORT=5000
        echo HOST=0.0.0.0
        echo.
        echo # Logging
        echo LOG_LEVEL=INFO
        echo.
        echo # Debug
        echo DEBUG=False
    ) > "%PROJECT_ROOT%.env"
    echo [OK] .env file created
    echo.
    echo [WARNING] Edit .env and set:
    echo   - REMOTE_PI_HOST: Your Raspberry Pi's IP address
    echo   - PI_API_KEY: API key from Pi backend (from setup.sh output^)
    echo.
)

REM Create logs directory
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo [OK] Logs directory ready: %LOG_DIR%

REM Load .env file
if exist "%PROJECT_ROOT%.env" (
    for /f "delims==" %%A in ('findstr /v "^#" "%PROJECT_ROOT%.env"') do (
        for /f "tokens=1,* delims==" %%B in ("%%A") do (
            set "%%B=%%C"
        )
    )
)

REM Set mode-specific variables
if /i "%MODE%"=="dev" (
    set FLASK_ENV=development
    set DEBUG=True
    set LOG_LEVEL=DEBUG
    echo [INFO] Starting in DEVELOPMENT mode ^(debug enabled^)
) else if /i "%MODE%"=="prod" (
    set FLASK_ENV=production
    set DEBUG=False
    set LOG_LEVEL=WARNING
    echo [INFO] Starting in PRODUCTION mode
) else if /i "%MODE%"=="help" (
    echo.
    echo HerdLinx Server UI Startup Script
    echo.
    echo Usage:
    echo   start-server.bat [dev^|prod^|help]
    echo.
    echo Options:
    echo   dev      Start in development mode ^(debug logging^)
    echo   prod     Start in production mode ^(minimal logging^)
    echo   help     Show this help message
    echo.
    echo Environment Variables:
    echo   IS_SERVER_UI        Set to True
    echo   REMOTE_PI_HOST      Pi backend IP address
    echo   REMOTE_PI_PORT      Pi backend port ^(default: 5001^)
    echo   PI_API_KEY          API key for Pi authentication
    echo   DB_SYNC_INTERVAL    Sync interval in seconds ^(default: 10^)
    echo.
    exit /b 0
)

REM Start application
echo.
echo ===============================================================
echo HerdLinx Server UI is starting...
echo ===============================================================
echo.
echo Web Server:  http://localhost:5000
echo Username:    admin
echo Password:    admin
echo Database:    %PROJECT_ROOT%office_app\office_app.db
echo Logs:        %LOG_DIR%
echo Mode:        %FLASK_ENV%
echo.
echo Press Ctrl+C to stop
echo.

cd /d "%PROJECT_ROOT%"
python -m office_app.run

endlocal
