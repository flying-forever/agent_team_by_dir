@echo off
rem Reset the Agent collaboration space back to its pre-generation state.
rem Conservative by default: removes only generated skeleton files and emptied dirs,
rem keeps task files, artifacts and roster entries.
rem Use "一键重置协作空间.bat --purge --yes" to delete the whole directory.
setlocal
cd /d "%~dp0"

if not exist "%~dp0.tmp" mkdir "%~dp0.tmp" 2>nul
set "TEMP=%~dp0.tmp"
set "TMP=%~dp0.tmp"

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo [ERROR] Python not found. Install Python 3.8+ first.
  rd /s /q "%~dp0.tmp" 2>nul
  pause
  exit /b 2
)

%PY% "%~dp0make_space.py" --reset %*
set "CODE=%ERRORLEVEL%"

rd /s /q "%~dp0.tmp" 2>nul
echo.
pause
exit /b %CODE%
