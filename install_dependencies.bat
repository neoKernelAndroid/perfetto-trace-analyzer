@echo off
chcp 65001 >nul
REM ========================================
REM 安装 Python 依赖库
REM ========================================

echo.
echo ========================================
echo   安装 Python 依赖库
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python！
    echo.
    echo 请先安装 Python 3.8 或更高版本。
    echo.
    pause
    exit /b 1
)

echo [信息] 检测到 Python：
python --version
echo.

REM 检查 pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 pip！
    echo.
    pause
    exit /b 1
)

echo [信息] 检测到 pip：
pip --version
echo.

echo ========================================
echo   开始安装依赖库
echo ========================================
echo.

echo [信息] 需要安装的库：
echo   - openpyxl  (Excel 文件操作)
echo   - pandas    (数据处理)
echo   - requests  (HTTP 请求)
echo.

echo [信息] 使用清华大学镜像源加速下载...
echo.

REM 尝试使用镜像源安装
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple openpyxl pandas requests

if errorlevel 1 (
    echo.
    echo [警告] 镜像源安装失败，尝试使用官方源...
    echo.
    
    REM 使用官方源安装
    pip install openpyxl pandas requests
    
    if errorlevel 1 (
        echo.
        echo [错误] 依赖库安装失败！
        echo.
        echo 可能的原因：
        echo   1. 网络连接问题
        echo   2. pip 版本过旧
        echo   3. 权限不足
        echo.
        echo 解决方法：
        echo   1. 检查网络连接
        echo   2. 升级 pip: python -m pip install --upgrade pip
        echo   3. 使用管理员权限运行
        echo.
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo   验证安装
echo ========================================
echo.

REM 验证 openpyxl
echo [验证] openpyxl...
python -c "import openpyxl; print('  版本:', openpyxl.__version__)" 2>nul
if errorlevel 1 (
    echo [✗] openpyxl 验证失败
) else (
    echo [✓] openpyxl 安装成功
)

REM 验证 pandas
echo [验证] pandas...
python -c "import pandas; print('  版本:', pandas.__version__)" 2>nul
if errorlevel 1 (
    echo [✗] pandas 验证失败
) else (
    echo [✓] pandas 安装成功
)

REM 验证 requests
echo [验证] requests...
python -c "import requests; print('  版本:', requests.__version__)" 2>nul
if errorlevel 1 (
    echo [✗] requests 验证失败
) else (
    echo [✓] requests 安装成功
)

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.

pause




