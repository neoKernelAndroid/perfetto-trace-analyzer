@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
REM ========================================
REM CPU GPU 批量分析工具
REM 自动解析指定目录下所有 trace 文件
REM 包括: MCPS, GPU MCPS, CPU Usage, 线程数
REM ========================================

echo ========================================
echo CPU GPU 批量分析工具
echo ========================================
echo.

REM 设置基础路径
set BASE_TRACE_DIR=D:\new\hangguan\cpu\test\trace
set SCRIPT_DIR=%~dp0
set CPU_TYPE=G200

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

REM 检查基础目录是否存在
if not exist "%BASE_TRACE_DIR%" (
    echo [ERROR] 目录不存在: %BASE_TRACE_DIR%
    pause
    exit /b 1
)

echo [INFO] 开始批量分析...
echo [INFO] 基础目录: %BASE_TRACE_DIR%
echo [INFO] CPU 类型: %CPU_TYPE%
echo.

REM 统计变量
set /a TOTAL_COUNT=0
set /a SUCCESS_COUNT=0
set /a FAIL_COUNT=0

REM 创建日志文件
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set LOG_FILE=%BASE_TRACE_DIR%\batch_analysis_log_%TIMESTAMP%.txt
echo 批量分析日志 - %date% %time% > "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM 遍历所有动效目录
for /d %%D in ("%BASE_TRACE_DIR%\*") do (
    set ANIMATION_DIR=%%D
    set ANIMATION_NAME=%%~nxD
    
    REM 提取动效标签（去掉前面的数字和点）
    for /f "tokens=2 delims=." %%A in ("!ANIMATION_NAME!") do set ANIMATION_TAG=%%A
    
    REM 如果没有点分隔符，直接使用整个名称
    if "!ANIMATION_TAG!"=="" set ANIMATION_TAG=!ANIMATION_NAME!
    
    echo ========================================
    echo [INFO] 正在处理动效: !ANIMATION_NAME!
    echo [INFO] 动效标签: !ANIMATION_TAG!
    echo ======================================== >> "%LOG_FILE%"
    echo 动效: !ANIMATION_NAME! >> "%LOG_FILE%"
    echo 标签: !ANIMATION_TAG! >> "%LOG_FILE%"
    echo. >> "%LOG_FILE%"
    
    REM 根据动效名称设置进程和线程
    call :SetProcessAndThreads "!ANIMATION_TAG!"
    
    echo [INFO] 配置 - 进程: !PROCESS_NAME!, 线程: !TASK_LIST!
    echo.
    
    REM 遍历该动效下的所有子目录 (1, 2, 3, ...)
    for /d %%S in ("%%D\*") do (
        set TRACE_SUBDIR=%%S
        set TRACE_HTML=%%S\trace-perfetto-con.html
        set TRACE_PERFETTO=%%S\trace.perfetto-trace
        
        REM 检查 HTML trace 文件是否存在
        if exist "!TRACE_HTML!" (
            set /a TOTAL_COUNT+=1
            echo.
            echo [INFO] 正在分析 [!TOTAL_COUNT!]: %%~nxS
            echo [INFO] 文件: !TRACE_HTML!
            echo. >> "%LOG_FILE%"
            echo 文件 [!TOTAL_COUNT!]: !TRACE_HTML! >> "%LOG_FILE%"
            
            REM 运行 MCPS 和 GPU 分析
            echo [INFO] 步骤 1/2: 分析 MCPS 和 GPU...
            python "%SCRIPT_DIR%run_gpu_analysis.py" -f "!TRACE_HTML!" -c "%CPU_TYPE%" -t "!TASK_LIST!" -p "!PROCESS_NAME!" -at "!ANIMATION_TAG!" >nul 2>&1
            
            if errorlevel 1 (
                echo [ERROR] MCPS 分析失败
                echo [ERROR] MCPS 分析失败 >> "%LOG_FILE%"
                set /a FAIL_COUNT+=1
            ) else (
                echo [SUCCESS] MCPS 分析完成
                echo [SUCCESS] MCPS 分析完成 >> "%LOG_FILE%"
            )
            
            REM 运行线程数统计
            if exist "!TRACE_PERFETTO!" (
                echo [INFO] 步骤 2/2: 统计线程数...
                python "%SCRIPT_DIR%export_thread_count_to_excel.py" "!TRACE_PERFETTO!" >nul 2>&1
                
                if errorlevel 1 (
                    echo [WARN] 线程数统计失败
                    echo [WARN] 线程数统计失败 >> "%LOG_FILE%"
                ) else (
                    echo [SUCCESS] 线程数统计完成
                    echo [SUCCESS] 线程数统计完成 >> "%LOG_FILE%"
                    set /a SUCCESS_COUNT+=1
                )
            ) else (
                echo [WARN] 未找到 perfetto-trace 文件，跳过线程数统计
                echo [WARN] 未找到 perfetto-trace 文件 >> "%LOG_FILE%"
            )
            
            echo ----------------------------------------
        ) else (
            echo [WARN] 未找到 trace 文件: %%~nxS
            echo [WARN] 未找到 trace 文件: %%S >> "%LOG_FILE%"
        )
    )
    
    echo.
)

REM 输出统计结果
echo.
echo ========================================
echo 批量分析完成！
echo ========================================
echo 总计: %TOTAL_COUNT% 个 trace 文件
echo 成功: %SUCCESS_COUNT% 个
echo 失败: %FAIL_COUNT% 个
echo.
echo 日志文件: %LOG_FILE%
echo ========================================

echo. >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"
echo 统计结果: >> "%LOG_FILE%"
echo 总计: %TOTAL_COUNT% 个 >> "%LOG_FILE%"
echo 成功: %SUCCESS_COUNT% 个 >> "%LOG_FILE%"
echo 失败: %FAIL_COUNT% 个 >> "%LOG_FILE%"

pause
exit /b 0

REM ========================================
REM 子程序：根据动效标签设置进程和线程
REM ========================================
:SetProcessAndThreads
set TAG=%~1

REM 默认值
set PROCESS_NAME=
set TASK_LIST=RenderThread

REM 根据动效标签设置配置
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

echo [WARN] 未知的动效标签: %TAG%，使用默认配置

:EndSetConfig
goto :eof
