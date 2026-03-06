@echo off
chcp 65001 >nul
REM ========================================
REM 下载 trace_processor 工具
REM ========================================

echo.
echo ========================================
echo   下载 trace_processor 工具
echo ========================================
echo.

REM 创建 tools 目录
if not exist "tools" (
    echo [信息] 创建 tools 目录...
    mkdir tools
)

REM 检查是否已存在
if exist "tools\trace_processor.exe" (
    echo [信息] 检测到已存在 trace_processor.exe
    echo.
    
    REM 显示文件信息
    dir "tools\trace_processor.exe" | findstr "trace_processor.exe"
    echo.
    
    choice /C YN /M "是否重新下载"
    if errorlevel 2 (
        echo.
        echo [跳过] 使用现有的 trace_processor.exe
        echo.
        pause
        exit /b 0
    )
    
    echo.
    echo [信息] 删除旧文件...
    del "tools\trace_processor.exe"
)

echo ========================================
echo   下载方式选择
echo ========================================
echo.
echo 请选择下载方式：
echo.
echo   1. 自动下载（推荐，需要网络连接）
echo   2. 手动下载（提供下载链接和说明）
echo   3. 取消
echo.

choice /C 123 /M "请选择"

if errorlevel 3 (
    echo.
    echo [取消] 已取消下载
    echo.
    pause
    exit /b 0
)

if errorlevel 2 goto manual_download
if errorlevel 1 goto auto_download

:auto_download
echo.
echo ========================================
echo   自动下载
echo ========================================
echo.

REM 检查是否有 SetupTraceProcessor.exe
if exist "tools\SetupTraceProcessor.exe" (
    echo [信息] 使用 SetupTraceProcessor.exe 下载...
    echo.
    tools\SetupTraceProcessor.exe
    goto check_result
) else if exist "SetupTraceProcessor.exe" (
    echo [信息] 使用 SetupTraceProcessor.exe 下载...
    echo.
    SetupTraceProcessor.exe
    goto check_result
) else (
    echo [警告] 未找到 SetupTraceProcessor.exe
    echo [信息] 尝试使用 Python 脚本下载...
    echo.
    
    REM 检查是否有 Python 脚本
    if exist "download_trace_processor.py" (
        python download_trace_processor.py
        goto check_result
    ) else (
        echo [错误] 未找到下载工具
        echo [信息] 请使用手动下载方式
        echo.
        goto manual_download
    )
)

:manual_download
echo.
echo ========================================
echo   手动下载说明
echo ========================================
echo.
echo 请按照以下步骤手动下载：
echo.
echo 1. 访问 Perfetto 发布页面：
echo    https://github.com/google/perfetto/releases
echo.
echo 2. 找到最新版本（如 v48.0）
echo.
echo 3. 下载适合 Windows 的版本：
echo    - 文件名：trace_processor-windows-amd64.exe
echo    - 或者：trace_processor.exe
echo.
echo 4. 将下载的文件重命名为：trace_processor.exe
echo.
echo 5. 将文件放到以下目录：
echo    %CD%\tools\
echo.
echo 6. 完整路径应该是：
echo    %CD%\tools\trace_processor.exe
echo.
echo ========================================
echo.

REM 询问是否已完成下载
choice /C YN /M "是否已完成手动下载"

if errorlevel 2 (
    echo.
    echo [取消] 请完成下载后重新运行本脚本
    echo.
    pause
    exit /b 0
)

:check_result
echo.
echo ========================================
echo   验证下载
echo ========================================
echo.

if exist "tools\trace_processor.exe" (
    echo [✓ 成功] trace_processor.exe 已就绪
    echo.
    
    REM 显示文件信息
    echo [信息] 文件信息：
    dir "tools\trace_processor.exe" | findstr "trace_processor.exe"
    echo.
    
    REM 尝试运行获取版本
    echo [信息] 尝试获取版本信息...
    tools\trace_processor.exe --version 2>nul
    if errorlevel 1 (
        echo [警告] 无法获取版本信息，但文件存在
        echo [警告] 这可能是正常的，某些版本不支持 --version 参数
    )
    
    echo.
    echo [成功] trace_processor 安装完成！
) else (
    echo [✗ 失败] trace_processor.exe 不存在
    echo.
    echo 请检查：
    echo   1. 文件是否下载成功
    echo   2. 文件名是否为 trace_processor.exe
    echo   3. 文件是否放在 tools 目录下
    echo.
    echo 完整路径应该是：
    echo   %CD%\tools\trace_processor.exe
    echo.
)

echo.
echo ========================================
echo.

pause




