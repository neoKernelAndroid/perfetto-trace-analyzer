@echo off
chcp 65001 >nul
REM ========================================
REM Perfetto Trace 分析工具 - 验证安装脚本
REM ========================================

echo.
echo ========================================
echo   Perfetto Trace 分析工具
echo   安装验证脚本 v1.0
echo ========================================
echo.

set ERROR_COUNT=0

REM ========================================
REM 检查 1: Python 环境
REM ========================================
echo [检查 1/5] Python 环境
echo ----------------------------------------

python --version >nul 2>&1
if errorlevel 1 (
    echo [✗ 失败] 未检测到 Python
    echo   请安装 Python 3.8 或更高版本
    set /a ERROR_COUNT+=1
) else (
    echo [✓ 通过] Python 已安装
    python --version
)
echo.

REM ========================================
REM 检查 2: pip 工具
REM ========================================
echo [检查 2/5] pip 工具
echo ----------------------------------------

pip --version >nul 2>&1
if errorlevel 1 (
    echo [✗ 失败] 未检测到 pip
    set /a ERROR_COUNT+=1
) else (
    echo [✓ 通过] pip 已安装
    pip --version
)
echo.

REM ========================================
REM 检查 3: Python 依赖库
REM ========================================
echo [检查 3/5] Python 依赖库
echo ----------------------------------------

echo [检查] openpyxl...
python -c "import openpyxl; print('  版本:', openpyxl.__version__)" 2>nul
if errorlevel 1 (
    echo [✗ 失败] openpyxl 未安装
    set /a ERROR_COUNT+=1
) else (
    echo [✓ 通过] openpyxl 已安装
)

echo [检查] pandas...
python -c "import pandas; print('  版本:', pandas.__version__)" 2>nul
if errorlevel 1 (
    echo [✗ 失败] pandas 未安装
    set /a ERROR_COUNT+=1
) else (
    echo [✓ 通过] pandas 已安装
)

echo [检查] requests...
python -c "import requests; print('  版本:', requests.__version__)" 2>nul
if errorlevel 1 (
    echo [✗ 失败] requests 未安装
    set /a ERROR_COUNT+=1
) else (
    echo [✓ 通过] requests 已安装
)
echo.

REM ========================================
REM 检查 4: trace_processor 工具
REM ========================================
echo [检查 4/5] trace_processor 工具
echo ----------------------------------------

set TRACE_PROCESSOR_FOUND=0

REM 检查 tools 目录
if exist "tools\trace_processor.exe" (
    echo [✓ 通过] trace_processor.exe 存在于 tools 目录
    set TRACE_PROCESSOR_FOUND=1
    
    REM 尝试获取版本信息
    tools\trace_processor.exe --version >nul 2>&1
    if errorlevel 1 (
        echo [警告] 无法获取版本信息，但文件存在
    ) else (
        echo [✓ 通过] trace_processor 可以正常运行
    )
)

REM 检查用户目录
if %TRACE_PROCESSOR_FOUND%==0 (
    if exist "%USERPROFILE%\.local\share\perfetto\trace_processor.exe" (
        echo [✓ 通过] trace_processor.exe 存在于用户目录
        echo   位置: %USERPROFILE%\.local\share\perfetto\
        echo [建议] 复制到 tools 目录以便使用：
        echo   copy "%USERPROFILE%\.local\share\perfetto\trace_processor.exe" "tools\"
        set TRACE_PROCESSOR_FOUND=1
    )
)

REM 如果都没找到
if %TRACE_PROCESSOR_FOUND%==0 (
    echo [✗ 失败] trace_processor.exe 不存在
    echo   期望位置: tools\trace_processor.exe
    echo   或: %USERPROFILE%\.local\share\perfetto\trace_processor.exe
    echo   请运行 setup_trace_processor.bat 下载
    set /a ERROR_COUNT+=1
)
echo.

REM ========================================
REM 检查 5: 工具可执行文件
REM ========================================
echo [检查 5/5] 工具可执行文件
echo ----------------------------------------

if exist "tools\PerfettoAnalyzer.exe" (
    echo [✓ 通过] PerfettoAnalyzer.exe 存在
) else (
    echo [✗ 失败] PerfettoAnalyzer.exe 不存在
    echo   这是主程序，必须存在
    set /a ERROR_COUNT+=1
)

if exist "tools\ThreadCountAnalyzer.exe" (
    echo [✓ 通过] ThreadCountAnalyzer.exe 存在
) else (
    echo [警告] ThreadCountAnalyzer.exe 不存在
    echo   线程数统计功能将不可用
)

if exist "tools\SetupTraceProcessor.exe" (
    echo [✓ 通过] SetupTraceProcessor.exe 存在
) else (
    echo [警告] SetupTraceProcessor.exe 不存在
    echo   需要手动下载 trace_processor
)
echo.

REM ========================================
REM 检查 6: 配置文件
REM ========================================
echo [检查 6/6] 配置文件
echo ----------------------------------------

if exist "configs\mcps_config.json" (
    echo [✓ 通过] mcps_config.json 存在
) else (
    echo [✗ 失败] mcps_config.json 不存在
    echo   配置文件缺失，工具无法运行
    set /a ERROR_COUNT+=1
)
echo.

REM ========================================
REM 检查 7: 目录结构
REM ========================================
echo [检查 7/7] 目录结构
echo ----------------------------------------

if exist "output" (
    echo [✓ 通过] output 目录存在
) else (
    echo [警告] output 目录不存在，将自动创建
    mkdir output
)

if exist "logs" (
    echo [✓ 通过] logs 目录存在
) else (
    echo [警告] logs 目录不存在，将自动创建
    mkdir logs
)

if exist "configs" (
    echo [✓ 通过] configs 目录存在
) else (
    echo [✗ 失败] configs 目录不存在
    set /a ERROR_COUNT+=1
)
echo.

REM ========================================
REM 验证结果
REM ========================================
echo.
echo ========================================
echo   验证结果
echo ========================================
echo.

if %ERROR_COUNT% EQU 0 (
    echo [✓ 成功] 所有检查通过！
    echo.
    echo 工具已准备就绪，可以开始使用。
    echo.
    echo 下一步：
    echo   1. 查看使用文档：README_USAGE.md
    echo   2. 编辑分析脚本：run_cpu_gpu_analysis_quick.bat
    echo   3. 运行分析
) else (
    echo [✗ 失败] 发现 %ERROR_COUNT% 个问题
    echo.
    echo 请根据上述提示解决问题后重新验证。
    echo.
    echo 常见解决方法：
    echo   - Python 未安装：运行 INSTALL.bat 或手动安装 Python
    echo   - 依赖库缺失：运行 install_dependencies.bat
    echo   - trace_processor 缺失：运行 setup_trace_processor.bat
    echo   - 配置文件缺失：检查发布包是否完整
)

echo.
echo ========================================
echo.

pause

