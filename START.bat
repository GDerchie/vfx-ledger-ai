@echo off
title VFX Budget System — MACHIAVELLI_a004 (Modular)
cd /d "%~dp0"
echo.
echo  Starting VFX Budget System...
echo  [Layout] ForDistribution style active (apply_export_layout.py)
echo  Open browser at:  http://localhost:5100
echo.

:: ── Optional: apply layout to a specific file from command line ──
:: Usage:  START.bat apply  path\to\file.xlsx  [SheetName]  [v2.3]
if /i "%1"=="apply" (
    if "%2"=="" (
        echo  Usage: START.bat apply ^<path\to\file.xlsx^> [sheet_name] [version]
    ) else (
        echo  Applying ForDistribution layout to: %2
        python apply_export_layout.py %2 %3 %4
        echo  Done.
    )
    pause
    exit /b 0
)

start http://localhost:5100
python app.py --port 5100
pause
