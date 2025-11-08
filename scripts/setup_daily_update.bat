@echo off
REM Windows Task Scheduler Setup for Daily BTC Data Updates
REM Creates MULTIPLE scheduled tasks throughout the day
REM This ensures data gets updated even if computer was off at specific times

echo ========================================
echo Setting up BTC Data Update Tasks
echo ========================================
echo.

REM Get the current directory
set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%binance_daily_update.py

echo Script location: %PYTHON_SCRIPT%
echo.
echo Creating 4 scheduled tasks per day:
echo   - 2:00 AM
echo   - 8:00 AM
echo   - 2:00 PM
echo   - 8:00 PM
echo.

REM Delete existing tasks if they exist
schtasks /Delete /TN "BTC_Data_Daily_Update" /F >nul 2>&1
schtasks /Delete /TN "BTC_Data_Update_2AM" /F >nul 2>&1
schtasks /Delete /TN "BTC_Data_Update_8AM" /F >nul 2>&1
schtasks /Delete /TN "BTC_Data_Update_2PM" /F >nul 2>&1
schtasks /Delete /TN "BTC_Data_Update_8PM" /F >nul 2>&1

REM Create 4 tasks per day
schtasks /Create /SC DAILY /TN "BTC_Data_Update_2AM" /TR "python %PYTHON_SCRIPT%" /ST 02:00 /F
schtasks /Create /SC DAILY /TN "BTC_Data_Update_8AM" /TR "python %PYTHON_SCRIPT%" /ST 08:00 /F
schtasks /Create /SC DAILY /TN "BTC_Data_Update_2PM" /TR "python %PYTHON_SCRIPT%" /ST 14:00 /F
schtasks /Create /SC DAILY /TN "BTC_Data_Update_8PM" /TR "python %PYTHON_SCRIPT%" /ST 20:00 /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Scheduled tasks created!
    echo.
    echo Tasks created:
    echo   - BTC_Data_Update_2AM  : 2:00 AM daily
    echo   - BTC_Data_Update_8AM  : 8:00 AM daily
    echo   - BTC_Data_Update_2PM  : 2:00 PM daily
    echo   - BTC_Data_Update_8PM  : 8:00 PM daily
    echo.
    echo To run manually:
    echo   python %PYTHON_SCRIPT%
    echo.
    echo To delete all:
    echo   schtasks /Delete /TN "BTC_Data_Update_2AM" /F
    echo   schtasks /Delete /TN "BTC_Data_Update_8AM" /F
    echo   schtasks /Delete /TN "BTC_Data_Update_2PM" /F
    echo   schtasks /Delete /TN "BTC_Data_Update_8PM" /F
) else (
    echo.
    echo [ERROR] Failed to create scheduled tasks
    echo Make sure you run this as Administrator
)

echo.
pause
