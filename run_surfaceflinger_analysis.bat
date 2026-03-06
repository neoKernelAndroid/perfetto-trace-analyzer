@echo off
chcp 65001 >nul
REM SurfaceFlinger GPU Wait Time 和 Layer Count 分析工具

echo ========================================
echo SurfaceFlinger 分析工具
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

REM 3.openApp_Window_enter - Example 1
set TRACE_FILE=D:\new\hangguan\cpu\trace\3.openApp_Window_enter\1\trace-perfetto-con.html

REM 动效Tag（必填）
set ANIMATION_TAG=openApp_Window_enter

echo 当前配置:
echo   Trace文件: %TRACE_FILE%
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
set CMD=python run_surfaceflinger_analysis.py -f "%TRACE_FILE%" -at "%ANIMATION_TAG%"

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
echo   SurfaceFlinger 分析完成！
echo ========================================
pause

