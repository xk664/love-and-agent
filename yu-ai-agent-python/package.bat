@echo off
REM =============================================================================
REM Yu AI Agent - Package Script for Cloud Deployment
REM =============================================================================
REM Usage: package.bat
REM Output: dist\yu-ai-agent-python-YYYYMMDD_HHMMSS.tar.gz
REM =============================================================================

setlocal enabledelayedexpansion

echo ========================================
echo  Yu AI Agent - Package Builder
echo ========================================
echo.

REM Get timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%

REM Set paths
set PROJECT_DIR=%~dp0
set DIST_DIR=%PROJECT_DIR%dist
set PACKAGE_NAME=yu-ai-agent-python
set OUTPUT_FILE=%DIST_DIR%\%PACKAGE_NAME%-%TIMESTAMP%.tar.gz

REM Clean dist directory
if exist "%DIST_DIR%" (
    echo Cleaning dist directory...
    rmdir /s /q "%DIST_DIR%"
)
mkdir "%DIST_DIR%" 2>nul

echo Project Directory: %PROJECT_DIR%
echo Output File: %OUTPUT_FILE%
echo.

REM Verify required files
echo Verifying required files...
set MISSING=0

if exist "%PROJECT_DIR%main.py" (
    echo   [OK] main.py
) else (
    echo   [MISSING] main.py
    set MISSING=1
)

if exist "%PROJECT_DIR%app" (
    echo   [OK] app
) else (
    echo   [MISSING] app
    set MISSING=1
)

if exist "%PROJECT_DIR%config" (
    echo   [OK] config
) else (
    echo   [MISSING] config
    set MISSING=1
)

if exist "%PROJECT_DIR%requirements.txt" (
    echo   [OK] requirements.txt
) else (
    echo   [MISSING] requirements.txt
    set MISSING=1
)

if %MISSING%==1 (
    echo.
    echo Error: Missing required files!
    exit /b 1
)

echo.
echo Creating package...

REM Create temporary staging directory
set TEMP_DIR=%TEMP%\%PACKAGE_NAME%-%TIMESTAMP%
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"

REM Copy files
echo Copying files...
xcopy /E /I /Q "%PROJECT_DIR%main.py" "%TEMP_DIR%\main.py" >nul
xcopy /E /I /Q "%PROJECT_DIR%app" "%TEMP_DIR%\app" >nul
xcopy /E /I /Q "%PROJECT_DIR%config" "%TEMP_DIR%\config" >nul
xcopy /E /I /Q "%PROJECT_DIR%requirements.txt" "%TEMP_DIR%\requirements.txt" >nul

REM Create tar.gz
echo Creating tar.gz archive...
cd /d "%TEMP_DIR%"
tar -czf "%OUTPUT_FILE%" *
if %errorlevel% ne 0 (
    echo Error: tar command failed!
    cd /d "%PROJECT_DIR%"
    rmdir /s /q "%TEMP_DIR%"
    exit /b 1
)
cd /d "%PROJECT_DIR%"

REM Cleanup
rmdir /s /q "%TEMP_DIR%"

REM Get file size
for %%A in ("%OUTPUT_FILE%") do set SIZE=%%~zA
set /a SIZE_MB=%SIZE% / 1048576

echo.
echo ========================================
echo  Package Created Successfully!
echo ========================================
echo.
echo File: %OUTPUT_FILE%
echo Size: %SIZE_MB% MB
echo.
echo Next Steps:
echo 1. Upload to cloud server:
echo    scp "%OUTPUT_FILE%" user@server:/path/to/deploy/
echo.
echo 2. On cloud server, extract and build:
echo    tar -xzf %PACKAGE_NAME%-%TIMESTAMP%.tar.gz
echo    docker build -t %PACKAGE_NAME%:latest .
echo.

endlocal
