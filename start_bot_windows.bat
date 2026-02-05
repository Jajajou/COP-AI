@echo off
setlocal EnableDelayedExpansion

title Cop Coffee Assistant - Startup Monitor

echo ========================================================
echo      COP COFFEE ASSISTANT - SYSTEM STARTUP SCRIPT
echo ========================================================

:: --- 1. CHECK & START DOCKER ---
echo [1/6] Checking Docker status...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo    Docker is not running. Attempting to start Docker Desktop...
    
    :: Adjust path if Docker is installed elsewhere
    set "DOCKER_PATH=C:\Program Files\Docker\Docker\Docker Desktop.exe"
    
    if exist "!DOCKER_PATH!" (
        start "" "!DOCKER_PATH!"
    ) else (
        echo    ERROR: Docker Desktop not found at "!DOCKER_PATH!".
        echo    Please start Docker Desktop manually.
        pause
        exit /b 1
    )
    
    echo    Waiting for Docker Engine to initialize...
    :WAIT_DOCKER
    timeout /t 5 /nobreak >nul
    docker info >nul 2>&1
    if !errorlevel! neq 0 (
        echo    ... still waiting for Docker ...
        goto WAIT_DOCKER
    )
    echo    [OK] Docker is active!
) else (
    echo    [OK] Docker is already running.
)

:: --- 2. SETUP ENVIRONMENT ---
cd /d "%~dp0"
echo [2/6] Working directory: %CD%

if not exist ".env" (
    echo    [ERROR] .env file is missing! Please create it before running.
    pause
    exit /b 1
) else (
    echo    [OK] Found .env file.
)

:: --- 3. CHECK UV TOOL ---
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo    [ERROR] 'uv' is not installed or not in PATH.
    echo    Please install it via PowerShell: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    pause
    exit /b 1
) else (
    echo    [OK] Found 'uv' package manager.
)

:: --- 4. START DATABASE ---
echo [3/6] Starting Database Services...
docker compose up -d
if %errorlevel% neq 0 (
    echo    [ERROR] Failed to start database containers. Check Docker logs.
    pause
    exit /b 1
)

:: --- 5. WAIT FOR DATABASE ---
echo [4/6] Waiting for Database to warm up (10s)...
timeout /t 10 /nobreak >nul

:: --- 6. SYNC DEPENDENCIES ---
echo [5/6] Verifying Python dependencies...
call uv sync
if %errorlevel% neq 0 (
    echo    [ERROR] Failed to sync dependencies.
    pause
    exit /b 1
)

:: --- 7. START BOT ---
echo [6/6] Starting Cop Coffee Assistant Bot...
echo ========================================================
echo.
call uv run main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Bot crashed or stopped with error code %errorlevel%.
    pause
) else (
    echo.
    echo [INFO] Bot stopped gracefully.
    pause
)
