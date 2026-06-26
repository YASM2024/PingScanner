@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

call :banner

set "LOG_DIR=%~dp0logs"
set "BUILD_LOG=%LOG_DIR%\build.log"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
> "%BUILD_LOG%" echo Build started: %date% %time%
>> "%BUILD_LOG%" echo.

call :log ""
call :log "--- Step 1: Initialize build log ---"
call :log "Creating the logs directory and starting a new build.log file."

call :log ""
call :log "--- Step 2: Resolve Python ---"
call :log "Use the command-line argument, Python on PATH, or an interactive prompt."

if not "%~1"=="" (
    set "PYTHON_EXE=%~1"
    call :log "Python specified via argument: %PYTHON_EXE%"
) else (
    python --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=python"
        call :log "Using Python from PATH."
    ) else (
        set /p "PYTHON_EXE=Please enter the Python path: "
        if not "!PYTHON_EXE!"=="" call :log "Python path entered: !PYTHON_EXE!"
    )
)

if "%PYTHON_EXE%"=="" (
    call :log "Error: Python path is required."
    pause
    exit /b 1
)

call :log ""
call :log "--- Step 3: Validate Python ---"
call :log "Checking that the selected Python executable is available."

call :log "Checking Python: %PYTHON_EXE%"
"%PYTHON_EXE%" --version >> "%BUILD_LOG%" 2>&1
if errorlevel 1 (
    call :log "Error: Python not found or invalid: %PYTHON_EXE%"
    pause
    exit /b 1
)

set "VENV_DIR=%~dp0.pyenv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

call :log ""
call :log "--- Step 4: Prepare virtual environment ---"
call :log "Create .pyenv if needed, or reuse the existing local environment."

if not exist "%VENV_PYTHON%" (
    call :log "Creating virtual environment: %VENV_DIR%"
    "%PYTHON_EXE%" -m venv "%VENV_DIR%" >> "%BUILD_LOG%" 2>&1
    if errorlevel 1 (
        call :log "Failed to create virtual environment."
        pause
        exit /b 1
    )
) else (
    call :log "Using existing virtual environment: %VENV_DIR%"
)

call :log ""
call :log "--- Step 5: Install build dependencies ---"
call :log "Installing packages listed in required.txt into .pyenv."

call :log "Installing dependencies from required.txt..."
"%VENV_PYTHON%" -m pip install -r "%~dp0required.txt" >> "%BUILD_LOG%" 2>&1
if errorlevel 1 (
    call :log "Failed to install dependencies."
    pause
    exit /b 1
)

call :log ""
call :log "--- Step 6: Build executables ---"
call :log "Running PyInstaller with pingscanner.spec to create the EXE files."

call :log "Building with PyInstaller..."
"%VENV_PYTHON%" -m PyInstaller --clean --noconfirm "%~dp0pingscanner.spec" >> "%BUILD_LOG%" 2>&1
if errorlevel 1 (
    call :log "Build failed."
    pause
    exit /b 1
)

call :log ""
call :log "--- Step 7: Publish build outputs ---"
call :log "Moving EXE files from dist\ to the project root and removing dist\."

if not exist "%~dp0dist\*.exe" (
    call :log "Error: No EXE files found in dist\."
    pause
    exit /b 1
)

move /Y "%~dp0dist\*.exe" "%~dp0" >> "%BUILD_LOG%" 2>&1
if errorlevel 1 (
    call :log "Failed to move EXE files."
    pause
    exit /b 1
)

rmdir /S /Q "%~dp0dist" >> "%BUILD_LOG%" 2>&1
if errorlevel 1 (
    call :log "Failed to remove dist\ directory."
    pause
    exit /b 1
)

call :log ""
call :log "Build complete:"
call :log "  main.exe"
call :log "  export_csv.exe"
call :log "  remark_ui.exe"
call :log ""
call :log "Log written to: %BUILD_LOG%"

pause

endlocal
exit /b 0

:banner
echo =============================================================
echo PingScanner V1.1
echo Created by Miyazaki Yasuo
echo Released on 2026-06-26
echo =============================================================
echo.
exit /b 0

:log
if "%~1"=="" (
    echo.
    >> "%BUILD_LOG%" echo.
) else (
    echo %~1
    >> "%BUILD_LOG%" echo %~1
)
exit /b 0
