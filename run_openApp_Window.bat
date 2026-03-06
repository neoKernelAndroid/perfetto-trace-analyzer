@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ========================================
echo MCPS Parser Tool - openApp_Window Test
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python and add it to PATH.
    echo.
    pause
    exit /b 1
)

if not exist "start_analyse_mcps.py" (
    echo [ERROR] start_analyse_mcps.py not found
    echo Current directory: %CD%
    echo.
    pause
    exit /b 1
)

set "TRACE_FILE=D:\new\hangguan\cpu\trace\3.luncher_app\2\trace-perfetto-con.html"
set "CPU_TYPE=G200"
set "THREAD_NAME=wmshell.anim,ndroid.systemui,RenderThread"
set "PROCESS_NAME=com.android.systemui"
set "ANIMATION_TAG=openApp_Window"

echo Configuration:
echo   Trace file: %TRACE_FILE%
echo   CPU type: %CPU_TYPE%
echo   Thread names: %THREAD_NAME%
echo   Process name: %PROCESS_NAME%
echo   Animation tag: %ANIMATION_TAG%
echo.

if not exist "%TRACE_FILE%" (
    echo [ERROR] Trace file not found: %TRACE_FILE%
    echo.
    pause
    exit /b 1
)

echo Starting analysis...
echo.

python start_analyse_mcps.py -f "%TRACE_FILE%" -c "%CPU_TYPE%" -t "%THREAD_NAME%" -p "%PROCESS_NAME%" -at "%ANIMATION_TAG%"

if errorlevel 1 (
    echo.
    echo ========================================
    echo [FAILED] Analysis failed
    echo Please check logs directory for details
    echo ========================================
) else (
    echo.
    echo ========================================
    echo [SUCCESS] Analysis completed!
    echo Excel file generated in trace file directory
    echo ========================================
)
pause

