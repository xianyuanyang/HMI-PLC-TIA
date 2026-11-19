@echo off
chcp 65001 >nul
title TIA Panel - Local Bridge Server
cd /d "%~dp0"
echo ============================================================
echo   TIA Portal Control Panel - Local Bridge
echo ============================================================
echo.
rem ---- Find a REAL python (skip Microsoft Store placeholder) ----
set "PYEXE="
call :TRYPY "%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if defined PYEXE goto FOUND
call :TRYPY "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if defined PYEXE goto FOUND
call :TRYPY "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if defined PYEXE goto FOUND
call :TRYPY "C:/Python313/python.exe"
if defined PYEXE goto FOUND
py -3 --version >nul 2>&1
if not errorlevel 1 (
  set "PYEXE=py -3"
  goto FOUND
)
echo [ERROR] No real Python found.
echo Please install Python 3 from python.org and check 'Add to PATH'.
pause
exit /b 1

:TRYPY
if not exist %1 exit /b 0
%1 --version >nul 2>&1
if errorlevel 1 exit /b 0
set "PYEXE=%~1"
exit /b 0

:FOUND
echo Using Python: %PYEXE%
echo Starting server... Browser will open automatically.
echo Keep this window OPEN. Close it to stop the server.
echo.
%PYEXE% -u server.py > panel_debug.log 2>&1
echo.
echo [Server exited] Last diagnostics (panel_debug.log):
echo ------------------------------------------------------------
type panel_debug.log
echo ------------------------------------------------------------
pause
