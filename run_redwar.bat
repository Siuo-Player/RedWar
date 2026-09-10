@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo RedWar - launcher
ECHO ========================================

set "PYTHON=%CD%\venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo [1/3] Virtual environment not found. Creating venv...
    py -m venv venv
    if errorlevel 1 goto :error
)

if not exist "%PYTHON%" (
    echo ERROR: Python virtual environment could not be created.
    goto :error
)

echo [1/3] Installing/updating Python dependencies...
"%PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo [2/3] Building C++ engine...
"%PYTHON%" tools\scripts\build_cpp_engine.py
if errorlevel 1 goto :error

echo [3/3] Starting RedWar...
echo.
"%PYTHON%" main.py
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo RedWar exited with code %EXIT_CODE%.
if not "%EXIT_CODE%"=="0" pause
exit /b %EXIT_CODE%

:error
echo.
echo RedWar could not be started.
echo Check the error above.
pause
exit /b 1
