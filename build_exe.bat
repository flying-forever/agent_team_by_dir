@echo off
rem Optional: build make-space.exe next to this script (PyInstaller, onefile).
rem Needs Python 3.8+ and network on first run (downloads PyInstaller into _build\pylibs).
setlocal
cd /d "%~dp0"

if not exist "%~dp0_build" mkdir "%~dp0_build"

echo [1/2] Installing PyInstaller into _build\pylibs ...
python -m pip install --disable-pip-version-check --no-warn-script-location ^
  --target "%~dp0_build\pylibs" pyinstaller
if errorlevel 1 goto fail

echo [2/2] Building make-space.exe ...
set "PYTHONPATH=%~dp0_build\pylibs"
python -m PyInstaller --noconfirm --onefile --console --clean ^
  --name make-space ^
  --distpath "%~dp0_build\dist" ^
  --workpath "%~dp0_build\work" ^
  --specpath "%~dp0_build" ^
  "%~dp0make_space.py"
if errorlevel 1 goto fail

copy /y "%~dp0_build\dist\make-space.exe" "%~dp0make-space.exe" >nul
if errorlevel 1 goto fail

echo.
echo Done: %~dp0make-space.exe
echo Double-click it to generate .\workspace next to itself.
pause
exit /b 0

:fail
echo.
echo [ERROR] build failed. See the messages above.
pause
exit /b 1
