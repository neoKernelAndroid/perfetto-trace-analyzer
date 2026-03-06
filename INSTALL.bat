@echo off
chcp 65001 >nul
REM ========================================
REM Perfetto Trace 分析工具 - 一键安装脚本
REM ========================================

echo.
echo ========================================
echo   Perfetto Trace 分析工具
echo   一键安装脚本 v1.0
echo ========================================
echo.

REM 设置颜色（如果支持）
color 0A

echo [信息] 开始安装，请稍候...
echo.

REM ========================================
REM 步骤 1: 检查 Python 环境
REM ========================================
echo ========================================
echo [1/4] 检查 Python 环境
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python！
    echo.
    echo 请先安装 Python 3.8 或更高版本：
    echo   1. 访问 https://www.python.org/downloads/
    echo   2. 下载并安装 Python 3.11 或更高版本
    echo   3. 安装时务必勾选 "Add Python to PATH"
    echo.
    echo 安装完成后，请重新运行本脚本。
    echo.
    pause
    exit /b 1
)

echo [成功] 检测到 Python：
python --version
echo.

REM 检查 pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 pip！
    echo.
    echo 请重新安装 Python，确保包含 pip。
    echo.
    pause
    exit /b 1
)

echo [成功] 检测到 pip：
pip --version
echo.

REM ========================================
REM 步骤 2: 安装 Python 依赖库
REM ========================================
echo ========================================
echo [2/4] 安装 Python 依赖库
echo ========================================
echo.

echo [信息] 正在安装依赖库：openpyxl, pandas, requests
echo [信息] 使用清华大学镜像源加速下载...
echo.

pip install -i https://pypi.tuna.tsinghua.edu.cn/simple openpyxl pandas requests

if errorlevel 1 (
    echo.
    echo [警告] 使用镜像源安装失败，尝试使用官方源...
    echo.
    pip install openpyxl pandas requests
    
    if errorlevel 1 (
        echo.
        echo [错误] 依赖库安装失败！
        echo.
        echo 请尝试手动安装：
        echo   pip install openpyxl pandas requests
        echo.
        pause
        exit /b 1
    )
)

echo.
echo [成功] 依赖库安装完成！
echo.

REM 验证依赖库
echo [信息] 验证依赖库安装...
python -c "import openpyxl, pandas, requests; print('[成功] 所有依赖库验证通过')" 2>nul
if errorlevel 1 (
    echo [警告] 依赖库验证失败，但可能不影响使用
)
echo.

REM ========================================
REM 步骤 3: 下载 trace_processor 工具
REM ========================================
echo ========================================
echo [3/4] 下载 trace_processor 工具
echo ========================================
echo.

REM 检查 tools 目录是否存在
if not exist "tools" (
    echo [信息] 创建 tools 目录...
    mkdir tools
)

REM 检查是否已存在 trace_processor
if exist "tools\trace_processor.exe" (
    echo [信息] 检测到已存在 trace_processor.exe
    echo.
    choice /C YN /M "是否重新下载"
    if errorlevel 2 (
        echo [跳过] 使用现有的 trace_processor.exe
        goto skip_download
    )
)

echo [信息] 正在下载 trace_processor...
echo [信息] 这可能需要几分钟，请耐心等待...
echo.

REM 检查是否有 SetupTraceProcessor.exe
if exist "tools\SetupTraceProcessor.exe" (
    tools\SetupTraceProcessor.exe
) else if exist "SetupTraceProcessor.exe" (
    SetupTraceProcessor.exe
) else (
    echo [警告] 未找到 SetupTraceProcessor.exe
    echo.
    echo 请手动下载 trace_processor：
    echo   1. 访问 https://github.com/google/perfetto/releases
    echo   2. 下载 trace_processor-windows-amd64.exe
    echo   3. 重命名为 trace_processor.exe
    echo   4. 放到 tools 目录下
    echo.
    echo 按任意键继续安装其他组件...
    pause >nul
    goto skip_download
)

:skip_download

REM 验证 trace_processor
if exist "tools\trace_processor.exe" (
    echo.
    echo [成功] trace_processor 已就绪
    echo.
    
    REM 尝试获取版本信息
    tools\trace_processor.exe --version 2>nul
    if errorlevel 1 (
        echo [信息] 无法获取版本信息，但文件存在
    )
) else (
    echo.
    echo [警告] trace_processor 未安装
    echo [警告] 工具可能无法正常工作
    echo.
)

echo.

REM ========================================
REM 步骤 4: 创建必要的目录
REM ========================================
echo ========================================
echo [4/4] 创建必要的目录
echo ========================================
echo.

if not exist "output" (
    echo [信息] 创建 output 目录...
    mkdir output
)

if not exist "logs" (
    echo [信息] 创建 logs 目录...
    mkdir logs
)

if not exist "configs" (
    echo [信息] 创建 configs 目录...
    mkdir configs
)

echo [成功] 目录结构创建完成
echo.

REM ========================================
REM 安装完成
REM ========================================
echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.

echo [信息] 安装摘要：
echo   ✓ Python 环境：已检测
echo   ✓ 依赖库：已安装
if exist "tools\trace_processor.exe" (
    echo   ✓ trace_processor：已安装
) else (
    echo   ✗ trace_processor：未安装（需要手动安装）
)
echo   ✓ 目录结构：已创建
echo.

echo ========================================
echo   下一步操作
echo ========================================
echo.
echo 1. 运行验证脚本检查安装：
echo    双击运行 verify_installation.bat
echo.
echo 2. 查看使用文档：
echo    打开 README_USAGE.md
echo.
echo 3. 开始使用工具：
echo    编辑 run_cpu_gpu_analysis_quick.bat
echo    配置 Trace 文件路径和分析参数
echo    双击运行开始分析
echo.

echo ========================================
echo.

pause




