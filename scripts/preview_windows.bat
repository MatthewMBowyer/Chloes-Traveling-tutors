@echo off
REM Double-click this file on Windows to preview the CTT website.
REM It serves this folder on your own machine and opens the homepage.
REM Close this window (or press Ctrl+C) to stop the preview.

setlocal
set PORT=8010

REM %~dp0 is this file's own folder, so no absolute path is baked in.
cd /d "%~dp0.."

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo Python was not found on this PC.
  echo Install it from https://www.python.org/downloads/ and tick
  echo "Add python.exe to PATH" during setup, then run this file again.
  echo.
  pause
  exit /b 1
)

echo.
echo   Serving the CTT site from:
echo     %CD%
echo   Open in your browser:
echo     http://127.0.0.1:%PORT%/index.html
echo.
echo   Press Ctrl+C or close this window to stop.
echo.

start "" "http://127.0.0.1:%PORT%/index.html"
python -m http.server %PORT% --bind 127.0.0.1

endlocal
