@echo off
rem One-click launcher: generate the collaboration skeleton next to this file.
rem Prefers make-space.exe; falls back to make_space.py via py -3 / python.
rem Sets TEMP/TMP to a local .tmp folder: onefile exes extract there, and
rem %TEMP% is often blocked by Defender's controlled-folder protection.
setlocal
cd /d "%~dp0"

if exist "%~dp0make-space.exe" (
  if not exist "%~dp0.tmp" mkdir "%~dp0.tmp"
  set "TEMP=%~dp0.tmp"
  set "TMP=%~dp0.tmp"
  "%~dp0make-space.exe" %*
  set "RC=%ERRORLEVEL%"
  rd /s /q "%~dp0.tmp" 2>nul
  goto done
)

set "PY="
py -3 -c "import sys" >nul 2>nul && set "PY=py -3"
if not defined PY (
  python -c "import sys" >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo [ERROR] Python 3 not found.
  echo Install Python 3.8+ and retry, or run build_exe.bat once to get make-space.exe.
  set "RC=2"
  goto done
)

%PY% "%~dp0make_space.py" %*
set "RC=%ERRORLEVEL%"

:done
if "%~1"=="" pause
exit /b %RC%
