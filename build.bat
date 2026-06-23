@echo off
setlocal
cd /d "%~dp0"

"%~dp0pyenv\Scripts\pyinstaller.exe" --clean --noconfirm "%~dp0pingscanner.spec"
pause
if errorlevel 1 (
    echo Build failed.
    exit /b 1
)

echo.
echo Build complete:
echo   dist\main.exe
echo   dist\export_csv.exe
echo   dist\remark_ui.exe

endlocal
