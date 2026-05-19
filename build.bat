@echo off
setlocal EnableDelayedExpansion
set /p VERSION=<VERSION
pyinstaller --onefile --windowed --icon=feather.ico --name SleepTimer_%VERSION% sleep_timer_gui.py
for /f "tokens=1-3 delims=." %%a in ("%VERSION%") do (
set /a patch=%%c + 1
set NEWVER=%%a.%%b.!patch!
echo !NEWVER! > VERSION
)
