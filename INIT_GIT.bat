@echo off
chcp 65001 >nul
REM ========================================
REM Git Repository Initialization Script
REM ========================================

echo.
echo ========================================
echo   Git Repository Initialization
echo ========================================
echo.

REM Check if Git is installed
where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [Error] Git is not installed!
    echo Please download and install Git from: https://git-scm.com/downloads
    echo.
    pause
    exit /b 1
)

echo [OK] Git is installed
echo.

REM Check if already a git repository
if exist ".git" (
    echo [Warning] This directory is already a Git repository.
    echo.
    choice /C YN /M "Do you want to reinitialize"
    if errorlevel 2 (
        echo [Cancelled] Operation cancelled.
        pause
        exit /b 0
    )
    rmdir /s /q .git
)

echo ========================================
echo Step 1: Initialize Git Repository
echo ========================================
echo.

git init
if %ERRORLEVEL% NEQ 0 (
    echo [Error] Failed to initialize Git repository
    pause
    exit /b 1
)

echo [OK] Git repository initialized
echo.

echo ========================================
echo Step 2: Configure Git User
echo ========================================
echo.

set /p GIT_USERNAME="Enter your name: "
set /p GIT_EMAIL="Enter your email: "

git config user.name "%GIT_USERNAME%"
git config user.email "%GIT_EMAIL%"

echo [OK] Git user configured
echo   Name: %GIT_USERNAME%
echo   Email: %GIT_EMAIL%
echo.

echo ========================================
echo Step 3: Add Files
echo ========================================
echo.

echo [Info] Checking files to be added...
git status --short
echo.

git add .
if %ERRORLEVEL% NEQ 0 (
    echo [Error] Failed to add files
    pause
    exit /b 1
)

echo [OK] Files added
echo.

echo ========================================
echo Step 4: Create Initial Commit
echo ========================================
echo.

git commit -m "Initial release v1.0 - Perfetto Trace Analyzer"
if %ERRORLEVEL% NEQ 0 (
    echo [Error] Failed to create commit
    pause
    exit /b 1
)

echo [OK] Initial commit created
echo.

echo ========================================
echo Step 5: Choose Remote Repository
echo ========================================
echo.

echo Select your platform:
echo   1. GitHub
echo   2. Gitee
echo   3. Both GitHub and Gitee
echo   4. Skip (configure later)
echo.

choice /C 1234 /M "Your choice"
set CHOICE=%ERRORLEVEL%

if %CHOICE%==4 (
    echo.
    echo [Info] Skipped remote repository configuration
    goto :FINISH
)

echo.

if %CHOICE%==1 goto :GITHUB
if %CHOICE%==2 goto :GITEE
if %CHOICE%==3 goto :BOTH

:GITHUB
echo ========================================
echo Configure GitHub Remote
echo ========================================
echo.
set /p GITHUB_USERNAME="Enter your GitHub username: "
set GITHUB_REPO=https://github.com/%GITHUB_USERNAME%/perfetto-trace-analyzer.git

git remote add origin %GITHUB_REPO%
git branch -M main

echo.
echo [OK] GitHub remote configured
echo   Repository: %GITHUB_REPO%
echo.
echo [Info] To push to GitHub, run:
echo   git push -u origin main
echo.
goto :FINISH

:GITEE
echo ========================================
echo Configure Gitee Remote
echo ========================================
echo.
set /p GITEE_USERNAME="Enter your Gitee username: "
set GITEE_REPO=https://gitee.com/%GITEE_USERNAME%/perfetto-trace-analyzer.git

git remote add origin %GITEE_REPO%

echo.
echo [OK] Gitee remote configured
echo   Repository: %GITEE_REPO%
echo.
echo [Info] To push to Gitee, run:
echo   git push -u origin master
echo.
goto :FINISH

:BOTH
echo ========================================
echo Configure GitHub and Gitee Remotes
echo ========================================
echo.
set /p GITHUB_USERNAME="Enter your GitHub username: "
set /p GITEE_USERNAME="Enter your Gitee username: "

set GITHUB_REPO=https://github.com/%GITHUB_USERNAME%/perfetto-trace-analyzer.git
set GITEE_REPO=https://gitee.com/%GITEE_USERNAME%/perfetto-trace-analyzer.git

git remote add github %GITHUB_REPO%
git remote add gitee %GITEE_REPO%
git branch -M main

echo.
echo [OK] Both remotes configured
echo   GitHub: %GITHUB_REPO%
echo   Gitee: %GITEE_REPO%
echo.
echo [Info] To push to both platforms, run:
echo   git push -u github main
echo   git push -u gitee master
echo.

:FINISH
echo ========================================
echo   Initialization Complete!
echo ========================================
echo.

echo [Summary]
echo   - Git repository initialized
echo   - Initial commit created
echo   - Remote repository configured (if selected)
echo.

echo [Next Steps]
echo   1. Create repository on GitHub/Gitee (if not done yet)
echo   2. Push your code:
if %CHOICE%==1 echo      git push -u origin main
if %CHOICE%==2 echo      git push -u origin master
if %CHOICE%==3 (
    echo      git push -u github main
    echo      git push -u gitee master
)
echo   3. Create a release/tag on the platform
echo.

echo [Documentation]
echo   - See GIT_OPENSOURCE_GUIDE.md for detailed instructions
echo   - See README.md for project documentation
echo.

pause

