@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 设置颜色变量（Windows控制台颜色代码）
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "MAGENTA=[95m"
set "CYAN=[96m"
set "WHITE=[97m"
set "RESET=[0m"

echo %CYAN%========================================%RESET%
echo %CYAN%   Pytest Auto API 自动化测试框架%RESET%
echo %CYAN%   智能一键启动脚本 v2.0%RESET%
echo %CYAN%========================================%RESET%
echo.

:: 检查Python环境
echo %BLUE%[1/6] 检查Python环境...%RESET%
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%❌ 错误: 未找到Python环境%RESET%
    echo %YELLOW%请先安装Python 3.7+并添加到系统PATH中%RESET%
    echo %YELLOW%下载地址: https://www.python.org/downloads/%RESET%
    pause
    exit /b 1
)
python --version
echo %GREEN%✅ Python环境检查通过%RESET%
echo.

:: 检查和安装Python依赖
echo %BLUE%[2/6] 检查Python依赖...%RESET%
echo %YELLOW%正在检查关键依赖模块...%RESET%

:: 检查jsonpath模块
python -c "import jsonpath" >nul 2>&1
if %errorlevel% neq 0 (
    echo %YELLOW%⚠ 检测到缺失依赖，正在自动安装...%RESET%
    echo %CYAN%执行命令: pip install -r requirements.txt%RESET%
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo %RED%❌ Python依赖安装失败%RESET%
        echo %YELLOW%请手动执行: pip install -r requirements.txt%RESET%
        pause
        exit /b 1
    )
    echo %GREEN%✅ Python依赖安装成功%RESET%
) else (
    echo %GREEN%✅ Python依赖检查通过%RESET%
)
echo.

:: 检查Node.js环境和前端依赖
echo %BLUE%[3/6] 检查前端环境...%RESET%
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%❌ 错误: 未找到Node.js环境%RESET%
    echo %YELLOW%请先安装Node.js 16+并添加到系统PATH中%RESET%
    echo %YELLOW%下载地址: https://nodejs.org/%RESET%
    pause
    exit /b 1
)
echo Node.js版本: 
node --version
echo npm版本: 
npm --version

:: 检查前端依赖
cd web_ui\frontend
if not exist "node_modules" (
    echo %YELLOW%⚠ 检测到前端依赖未安装，正在自动安装...%RESET%
    echo %CYAN%执行命令: npm install%RESET%
    npm install
    if %errorlevel% neq 0 (
        echo %RED%❌ 前端依赖安装失败%RESET%
        echo %YELLOW%请手动执行: cd web_ui\frontend && npm install%RESET%
        cd ..\..
        pause
        exit /b 1
    )
    echo %GREEN%✅ 前端依赖安装成功%RESET%
) else (
    echo %GREEN%✅ 前端依赖检查通过%RESET%
)
cd ..\..
echo.

:: 启动后端服务
echo %BLUE%[4/6] 启动后端服务...%RESET%
echo %CYAN%启动地址: http://127.0.0.1:5000%RESET%
start "Pytest API 后端服务" cmd /c "echo %MAGENTA%Pytest Auto API 后端服务%RESET% && echo %CYAN%服务地址: http://127.0.0.1:5000%RESET% && echo. && python web_ui/backend/app.py && pause"

:: 等待后端服务启动
echo %YELLOW%等待后端服务启动...%RESET%
timeout /t 5 /nobreak >nul

:: 检查后端服务健康状态
echo %YELLOW%检查后端服务状态...%RESET%
for /L %%i in (1,1,10) do (
    curl -s http://127.0.0.1:5000/api/health >nul 2>&1
    if !errorlevel! equ 0 (
        echo %GREEN%✅ 后端服务启动成功%RESET%
        goto backend_ok
    )
    echo %YELLOW%等待后端服务响应... ^(%%i/10^)%RESET%
    timeout /t 2 /nobreak >nul
)
echo %YELLOW%⚠ 无法确认后端服务状态，但继续启动前端...%RESET%

:backend_ok
echo.

:: 启动前端服务
echo %BLUE%[5/6] 启动前端服务...%RESET%
echo %CYAN%启动地址: http://127.0.0.1:5173%RESET%
cd web_ui\frontend
start "Pytest API 前端界面" cmd /c "echo %MAGENTA%Pytest Auto API 前端界面%RESET% && echo %CYAN%访问地址: http://127.0.0.1:5173%RESET% && echo %YELLOW%按Ctrl+C可停止服务%RESET% && echo. && npm run dev"
cd ..\..

:: 等待前端服务启动
echo %YELLOW%等待前端服务启动...%RESET%
timeout /t 8 /nobreak >nul

:: 启动完成
echo %BLUE%[6/6] 服务启动完成！%RESET%
echo.
echo %GREEN%========================================%RESET%
echo %GREEN%   🎉 所有服务启动成功！%RESET%
echo %GREEN%========================================%RESET%
echo.
echo %CYAN%📡 服务地址:%RESET%
echo %WHITE%   后端API: %YELLOW%http://127.0.0.1:5000%RESET%
echo %WHITE%   前端界面: %YELLOW%http://127.0.0.1:5173%RESET%
echo.
echo %CYAN%🚀 功能特性:%RESET%
echo %WHITE%   ✓ 测试用例管理%RESET%
echo %WHITE%   ✓ 代码自动生成%RESET%
echo %WHITE%   ✓ 测试执行监控%RESET%
echo %WHITE%   ✓ 报告查看分析%RESET%
echo.
echo %MAGENTA%💡 使用提示:%RESET%
echo %WHITE%   • 保持此窗口开启以维持服务运行%RESET%
echo %WHITE%   • 在各服务窗口按Ctrl+C可停止对应服务%RESET%
echo %WHITE%   • 如遇问题请查看各服务窗口的错误信息%RESET%
echo.

:: 询问是否自动打开浏览器
echo %CYAN%是否自动打开浏览器访问Web界面？%RESET%
echo %WHITE%按任意键打开浏览器，或等待10秒后自动打开...%RESET%
timeout /t 10 >nul
start http://127.0.0.1:5173

echo.
echo %GREEN%🌟 欢迎使用 Pytest Auto API 自动化测试框架！%RESET%
echo %YELLOW%如有问题，请参考项目文档或提交Issue%RESET%
echo.
pause 