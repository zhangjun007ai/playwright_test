@echo off
chcp 65001 >nul
echo ========================================
echo    Pytest Auto API 自动化测试平台
echo    正在启动服务，请稍等...
echo ========================================
echo.

:: 获取脚本所在目录
set SCRIPT_DIR=%~dp0

:: 切换到项目目录并运行启动脚本
cd /d "%SCRIPT_DIR%"
call start_services.bat

:: 如果出错，暂停显示错误信息
if %errorlevel% neq 0 (
    echo.
    echo 启动失败，请检查错误信息...
    pause
) 