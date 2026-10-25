@echo off
rem Double-click to install the custom nodes and models this workflow needs.
rem Start ComfyUI first. Extra options are passed on, e.g.  install.bat --check
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 install.py %*
    goto :end
)
where python >nul 2>nul
if %errorlevel%==0 (
    python install.py %*
    goto :end
)
echo Python 3 wasn't found. Install it from https://www.python.org/downloads/
echo or run this with ComfyUI portable's Python:
echo   path\to\ComfyUI_windows_portable\python_embeded\python.exe install.py
:end
pause
