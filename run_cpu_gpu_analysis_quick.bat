@echo off
chcp 65001 >nul

echo ========================================
echo CPU GPU Analysis Tool - Quick Mode
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)
REM ============================================
REM Configuration - Modify these parameters
REM ============================================

REM 1.LAUNCHER_ALL_APPS_SCROLL
REM set TRACE_FILE=D:\new\hangguan\cpu\trace\1.LAUNCHER_ALL_APPS_SCROLL\2\trace-perfetto-con.html

REM CPU type
REM set CPU_TYPE=G200

REM Process name
REM set PROCESS_NAME=com.transsion.launcher3

REM Task list
REM set TASK_LIST=ssion.launcher3,RenderThread

REM Animation tag
REM set ANIMATION_TAG=LAUNCHER_ALL_APPS_SCROLL


REM 2.closeApp_Window_enter
set TRACE_FILE=D:\new\hangguan\cpu\trace\2.closeApp_Window_enter\1\trace-perfetto-con.html

REM CPU
set CPU_TYPE=G200

REM Process name
set PROCESS_NAME=com.android.systemui

REM Task list
set TASK_LIST=wmshell.anim,ndroid.systemui,RenderThread

REM Animation tag
set ANIMATION_TAG=closeApp_Window_enter


REM ============================================
REM Configuration - Modify these parameters
REM ============================================

REM Trace file path (required)
REM set TRACE_FILE=D:\new\hangguan\cpu\trace\3.openApp_Window_enter\2\trace-perfetto-con.html

REM CPU type (required)
REM set CPU_TYPE=G200

REM Process name (optional, leave empty to analyze all processes)
REM set PROCESS_NAME=com.android.systemui

REM Task list (required, comma separated)
REM set TASK_LIST=wmshell.anim,ndroid.systemui,RenderThread

REM Animation tag (optional, leave empty for full trace analysis)
REM set ANIMATION_TAG=openApp_Window_enter

REM ============================================
REM No need to modify below
REM ============================================

echo Current Configuration:
echo   Trace File: %TRACE_FILE%
echo   CPU Type: %CPU_TYPE%
echo   Process Name: %PROCESS_NAME%
echo   Task List: %TASK_LIST%
echo   Animation Tag: %ANIMATION_TAG%
echo.

REM Check if trace file exists
if not exist "%TRACE_FILE%" (
    echo ERROR: Trace file not found: %TRACE_FILE%
    echo Please modify TRACE_FILE parameter in this script
    pause
    exit /b 1
)

REM Build command
set CMD=python run_gpu_analysis.py -f "%TRACE_FILE%" -c "%CPU_TYPE%" -t "%TASK_LIST%"

if not "%PROCESS_NAME%"=="" (
    set CMD=%CMD% -p "%PROCESS_NAME%"
)

if not "%ANIMATION_TAG%"=="" (
    set CMD=%CMD% -at "%ANIMATION_TAG%"
)

echo Executing command: %CMD%
echo.

REM Run analysis
%CMD%

if errorlevel 1 (
    echo.
    echo Analysis failed, please check logs
    pause
    exit /b 1
)

echo.
echo ========================================
echo   GPU/CPU Analysis Complete!
echo ========================================
echo.

pause
