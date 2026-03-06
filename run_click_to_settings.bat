@echo off
chcp 65001 >nul
REM 点击到Settings第一帧的MCPS分析

echo ========================================
echo 点击到Settings第一帧 - MCPS分析
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM ============================================
REM 配置区域 - 请根据实际情况修改以下参数
REM ============================================

REM Trace文件路径（必填）
set TRACE_FILE=D:\new\hangguan\cpu\trace\CLICK_TO_SETTINGS\trace-perfetto-con.html

REM CPU类型（必填）
set CPU_TYPE=G200

REM 进程名（可选，留空则统计所有进程）
REM 注意：这里可以指定launcher3或settings，或者留空统计所有
set PROCESS_NAME=

REM 任务列表（必填，逗号分隔）
REM 建议包含launcher3和settings的主要线程
set TASK_LIST=ssion.launcher3,android.settings,RenderThread

REM 动效Tag（使用新配置）
set ANIMATION_TAG=CLICK_TO_SETTINGS_FIRST_DOFRAME

REM ============================================
REM 以下内容无需修改
REM ============================================

echo 当前配置:
echo   Trace文件: %TRACE_FILE%
echo   CPU类型: %CPU_TYPE%
echo   进程名: %PROCESS_NAME%
echo   任务列表: %TASK_LIST%
echo   动效Tag: %ANIMATION_TAG%
echo.

REM 检查trace文件是否存在
if not exist "%TRACE_FILE%" (
    echo 错误: Trace文件不存在: %TRACE_FILE%
    echo 请修改脚本中的 TRACE_FILE 参数
    pause
    exit /b 1
)

REM 构建命令
set CMD=python run_gpu_analysis.py -f "%TRACE_FILE%" -c "%CPU_TYPE%" -t "%TASK_LIST%"

if not "%PROCESS_NAME%"=="" (
    set CMD=%CMD% -p "%PROCESS_NAME%"
)

if not "%ANIMATION_TAG%"=="" (
    set CMD=%CMD% -at "%ANIMATION_TAG%"
)

echo 执行命令: %CMD%
echo.

REM 运行分析
%CMD%

if errorlevel 1 (
    echo.
    echo 分析失败，请检查日志
    pause
    exit /b 1
)

echo.
echo ========================================
echo   分析完成！
echo ========================================
echo.
pause




