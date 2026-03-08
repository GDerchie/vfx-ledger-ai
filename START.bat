@echo off
title VFX Budget System
cd /d "%~dp0"
echo.
echo  Starting VFX Budget System...
echo  Open browser at:  http://localhost:5000
echo.
start http://localhost:5000
"C:\Users\gderc\AppData\Local\Programs\Python\Python312\python.exe" app.py
pause
