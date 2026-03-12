@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
REM ========================================
REM CPU GPU ??????
REM ??????????? trace ??
REM ??: MCPS, GPU MCPS, CPU Usage, ???
REM ========================================

echo ========================================
echo CPU GPU ??????
echo ========================================
echo.

REM Debug: set DEBUG=1 before running to see command trace
if defined DEBUG echo on

REM Base settings
set "BASE_TRACE_DIR=D:\new\hangguan\cpu\test\trace"
set "SCRIPT_DIR=%~dp0"
set "CPU_TYPE=G200"

REM Optional overrides
REM Usage:
REM   batch_analyze_all_traces_cpu_gpu.bat [TraceRootDir] [CPU_TYPE]
if not "%~1"=="" set "BASE_TRACE_DIR=%~1"
if not "%~2"=="" set "CPU_TYPE=%~2"

REM ?? Python ????
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] ??? Python????? Python
    pause
    exit /b 1
)

REM ??????????
if not exist "%BASE_TRACE_DIR%" (
    echo [ERROR] ?????: %BASE_TRACE_DIR%
    pause
    exit /b 1
)

echo [INFO] ??????...
echo [INFO] ????: %BASE_TRACE_DIR%
echo [INFO] CPU ??: %CPU_TYPE%
echo.

REM ????
set /a TOTAL_COUNT=0
set /a SUCCESS_COUNT=0
set /a FAIL_COUNT=0

REM ??????
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set LOG_FILE=%BASE_TRACE_DIR%\batch_analysis_log_%TIMESTAMP%.txt
echo ?????? - %date% %time% > "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM Recursively scan all trace-perfetto-con.html, no fixed subdir assumptions
for /r "%BASE_TRACE_DIR%" %%F in (trace-perfetto-con.html) do (
    set "TRACE_HTML=%%~fF"

    REM Skip incomplete folders: require a raw trace file alongside the html
    set "HAS_RAW_TRACE=0"
    if exist "%%~dpFtrace.perfetto-trace" set "HAS_RAW_TRACE=1"
    if exist "%%~dpFtrace-perfetto.trace" set "HAS_RAW_TRACE=1"
    if "!HAS_RAW_TRACE!"=="0" for %%T in ("%%~dpF*.perfetto-trace") do if exist "%%~fT" set "HAS_RAW_TRACE=1"
    if "!HAS_RAW_TRACE!"=="0" for %%T in ("%%~dpF*.trace") do if exist "%%~fT" set "HAS_RAW_TRACE=1"
    if "!HAS_RAW_TRACE!"=="0" (
        echo [WARN] Skip - no raw trace near html: %%~fF
        echo [WARN] Skip - no raw trace near html: %%~fF>> "%LOG_FILE%"
        echo ---------------------------------------->> "%LOG_FILE%"
        echo ----------------------------------------
    ) else (
        REM Derive animation directory as parent of the directory containing the trace html
        for %%P in ("%%~dpF..") do (
            set "ANIMATION_DIR=%%~fP"
            set "ANIMATION_NAME=%%~nxP"
        )

    REM Extract animation tag: 1.TAG -> TAG ; if no dot, use full name
    set "ANIMATION_TAG="
    for /f "tokens=2 delims=." %%A in ("!ANIMATION_NAME!") do set "ANIMATION_TAG=%%A"
    if "!ANIMATION_TAG!"=="" set "ANIMATION_TAG=!ANIMATION_NAME!"

    call :SetProcessAndThreads "!ANIMATION_TAG!"

    set /a TOTAL_COUNT+=1
    echo.
    echo ========================================
    echo [INFO] Analyzing [!TOTAL_COUNT!]
    echo [INFO] Animation: !ANIMATION_NAME!
    echo [INFO] Tag: !ANIMATION_TAG!
    echo [INFO] HTML: !TRACE_HTML!
    echo [INFO] Config - Process: !PROCESS_NAME!, Threads: !TASK_LIST!
    echo ========================================

    echo.>> "%LOG_FILE%"
    echo ========================================>> "%LOG_FILE%"
    echo [!TOTAL_COUNT!] Animation: !ANIMATION_NAME!>> "%LOG_FILE%"
    echo Tag: !ANIMATION_TAG!>> "%LOG_FILE%"
    echo HTML: !TRACE_HTML!>> "%LOG_FILE%"
    echo Process: !PROCESS_NAME!>> "%LOG_FILE%"
    echo Threads: !TASK_LIST!>> "%LOG_FILE%"

    REM Run GPU + MCPS analysis only, no thread count export
    echo [INFO] GPU+MCPS analysis...
    python "%SCRIPT_DIR%run_gpu_analysis.py" -f "!TRACE_HTML!" -c "%CPU_TYPE%" -t "!TASK_LIST!" -p "!PROCESS_NAME!" -at "!ANIMATION_TAG!" >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [ERROR] GPU+MCPS analysis failed, see log
        echo [ERROR] GPU+MCPS analysis failed>> "%LOG_FILE%"
        set /a FAIL_COUNT+=1
    ) else (
        echo [SUCCESS] GPU+MCPS analysis done
        echo [SUCCESS] GPU+MCPS analysis done>> "%LOG_FILE%"
        set /a SUCCESS_COUNT+=1
    )

    echo ---------------------------------------->> "%LOG_FILE%"
    echo ----------------------------------------
    )
)

REM Summary output
echo.
echo ========================================
echo Batch analysis finished
echo ========================================
echo Total traces: %TOTAL_COUNT%
echo Success: %SUCCESS_COUNT%
echo Failed : %FAIL_COUNT%
echo.
echo Log file: %LOG_FILE%
echo ========================================

echo. >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"
echo Summary: >> "%LOG_FILE%"
echo Total traces: %TOTAL_COUNT% >> "%LOG_FILE%"
echo Success: %SUCCESS_COUNT% >> "%LOG_FILE%"
echo Failed : %FAIL_COUNT% >> "%LOG_FILE%"

pause
exit /b 0

REM ========================================
REM ?????????????????
REM ========================================
:SetProcessAndThreads
set TAG=%~1

REM ???
set PROCESS_NAME=
set TASK_LIST=RenderThread

REM ??????????
if /i "%TAG%"=="LAUNCHER_ALL_APPS_SCROLL" (
    set PROCESS_NAME=com.transsion.launcher3
    set TASK_LIST=ssion.launcher3,RenderThread
    goto :EndSetConfig
)
if /i "%TAG%"=="closeApp_Window_enter" (
    set PROCESS_NAME=com.android.systemui
    set TASK_LIST=wmshell.anim,ndroid.systemui,RenderThread
    goto :EndSetConfig
)
if /i "%TAG%"=="openApp_Window_enter" (
    set PROCESS_NAME=com.android.systemui
    set TASK_LIST=wmshell.anim,ndroid.systemui,RenderThread
    goto :EndSetConfig
)
if /i "%TAG%"=="LAUNCHER_APP_SWIPE_TO_RECENTS" (
    set PROCESS_NAME=com.transsion.launcher3
    set TASK_LIST=ssion.launcher3,RenderThread
    goto :EndSetConfig
)
if /i "%TAG%"=="LOCKSCREEN_UNLOCK_ANIMATION" (
    set PROCESS_NAME=com.android.systemui
    set TASK_LIST=RenderThread,ndroid.systemui
    goto :EndSetConfig
)
if /i "%TAG%"=="NOTIFICATION_SHADE_EXPAND_COLLAPSE" (
    set PROCESS_NAME=com.android.systemui
    set TASK_LIST=RenderThread,ndroid.systemui
    goto :EndSetConfig
)
if /i "%TAG%"=="TRAN_CUJ_LAUNCHER_ANIMATION_SCROLL_HOME" (
    set PROCESS_NAME=com.transsion.launcher3
    set TASK_LIST=ssion.launcher3,RenderThread
    goto :EndSetConfig
)
if /i "%TAG%"=="TRAN_CUJ_LAUNCHER_ANIMATION_SWIPE_UP_TO_HOME" (
    set PROCESS_NAME=com.transsion.launcher3
    set TASK_LIST=ssion.launcher3,RenderThread
    goto :EndSetConfig
)
if /i "%TAG%"=="TRAN_CUJ_NOTIFICATION_SHADE_QS_EXPAND_COLLAPSE" (
    set PROCESS_NAME=com.android.systemui
    set TASK_LIST=ndroid.systemui,RenderThread
    goto :EndSetConfig
)
if /i "%TAG%"=="VOLUME_CONTROL" (
    set PROCESS_NAME=com.android.systemui
    set TASK_LIST=ndroid.systemui,RenderThread
    goto :EndSetConfig
)

echo [WARN] ???????: %TAG%???????

:EndSetConfig
goto :eof

