@echo off
setlocal
cd /d "%~dp0"
set /p VERSION=<VERSION
python -m PyInstaller --noconfirm sleep_timer.spec
if errorlevel 1 exit /b 1
echo Built dist\SleepTimer_%VERSION%.exe
rem VERSION identifies this release; bump it deliberately, not after each build.
