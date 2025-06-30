@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ===============================================
echo   🚀 Pytest Auto API 智能修复与启动工具
echo ===============================================
echo.

:: 设置颜色变量
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "RESET=[0m"
set "CYAN=[96m"

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo %CYAN%📍 当前目录: %CD%%RESET%
echo.

:: 第一步：检查Python环境
echo %BLUE%🔍 Step 1: 检查Python环境...%RESET%
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED%❌ Python未安装或未添加到PATH%RESET%
    echo %YELLOW%💡 请安装Python 3.7+并添加到系统PATH%RESET%
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo %GREEN%✅ Python版本: !PYTHON_VERSION!%RESET%
)

:: 第二步：检查Node.js环境
echo.
echo %BLUE%🔍 Step 2: 检查Node.js环境...%RESET%
node --version >nul 2>&1
if errorlevel 1 (
    echo %RED%❌ Node.js未安装或未添加到PATH%RESET%
    echo %YELLOW%💡 请安装Node.js 16+并添加到系统PATH%RESET%
    pause
    exit /b 1
) else (
    for /f %%i in ('node --version') do set NODE_VERSION=%%i
    echo %GREEN%✅ Node.js版本: !NODE_VERSION!%RESET%
)

:: 第三步：修复Python依赖
echo.
echo %BLUE%🔧 Step 3: 修复Python依赖...%RESET%
if exist requirements.txt (
    echo %CYAN%📦 安装Python依赖包...%RESET%
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo %YELLOW%⚠️  pip安装失败，尝试使用国内镜像源...%RESET%
        pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet
    )
    echo %GREEN%✅ Python依赖安装完成%RESET%
) else (
    echo %YELLOW%⚠️  未找到requirements.txt，跳过依赖安装%RESET%
)

:: 检查jsonpath包（特殊处理）
python -c "import jsonpath" >nul 2>&1
if errorlevel 1 (
    echo %CYAN%📦 安装缺失的jsonpath包...%RESET%
    pip install jsonpath --quiet
    if errorlevel 1 (
        pip install jsonpath -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet
    )
)

:: 第四步：修复前端依赖
echo.
echo %BLUE%🔧 Step 4: 修复前端依赖...%RESET%
cd web_ui\frontend

if not exist node_modules (
    echo %CYAN%📦 安装前端依赖包...%RESET%
    npm install --silent
    if errorlevel 1 (
        echo %YELLOW%⚠️  npm安装失败，尝试使用cnpm...%RESET%
        cnpm install --silent >nul 2>&1
        if errorlevel 1 (
            echo %YELLOW%⚠️  cnpm不可用，尝试使用yarn...%RESET%
            yarn install --silent >nul 2>&1
        )
    )
) else (
    echo %GREEN%✅ 前端依赖已存在%RESET%
)

cd ..\..

:: 第五步：检查端口占用
echo.
echo %BLUE%🔍 Step 5: 检查端口状态...%RESET%

:: 检查5000端口（后端）
netstat -ano | findstr :5000 >nul 2>&1
if not errorlevel 1 (
    echo %YELLOW%⚠️  端口5000已被占用，尝试停止相关进程...%RESET%
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
        taskkill /PID %%a /F >nul 2>&1
    )
    timeout /t 2 >nul
)

:: 检查5173端口（前端）
netstat -ano | findstr :5173 >nul 2>&1
if not errorlevel 1 (
    echo %YELLOW%⚠️  端口5173已被占用，尝试停止相关进程...%RESET%
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do (
        taskkill /PID %%a /F >nul 2>&1
    )
    timeout /t 2 >nul
)

:: 第六步：启动后端服务
echo.
echo %BLUE%🚀 Step 6: 启动后端服务...%RESET%
start "Pytest Auto API Backend" cmd /c "python web_ui\backend\app.py"

:: 等待后端启动
echo %CYAN%⏳ 等待后端服务启动...%RESET%
:wait_backend
timeout /t 3 >nul
netstat -ano | findstr :5000 >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%⏳ 等待后端服务...%RESET%
    goto wait_backend
)
echo %GREEN%✅ 后端服务已启动 (http://127.0.0.1:5000)%RESET%

:: 第七步：启动前端服务
echo.
echo %BLUE%🚀 Step 7: 启动前端服务...%RESET%
cd web_ui\frontend
start "Pytest Auto API Frontend" cmd /c "npm run dev"

:: 等待前端启动
echo %CYAN%⏳ 等待前端服务启动...%RESET%
:wait_frontend
timeout /t 3 >nul
netstat -ano | findstr :5173 >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%⏳ 等待前端服务...%RESET%
    goto wait_frontend
)
echo %GREEN%✅ 前端服务已启动 (http://127.0.0.1:5173)%RESET%

cd ..\..

:: 第八步：测试服务连通性
echo.
echo %BLUE%🔍 Step 8: 测试服务连通性...%RESET%

:: 简单的连通性测试
timeout /t 5 >nul
echo %CYAN%🌐 正在测试前后端连通性...%RESET%

:: 第九步：打开浏览器
echo.
echo %BLUE%🌐 Step 9: 打开Web界面...%RESET%
timeout /t 3 >nul

:: 尝试打开浏览器
start http://127.0.0.1:5173
if errorlevel 1 (
    start http://127.0.0.1:5173/debug
)

echo.
echo %GREEN%===============================================%RESET%
echo %GREEN%  🎉 启动完成！服务状态：%RESET%
echo %GREEN%===============================================%RESET%
echo %GREEN%  📡 后端API: http://127.0.0.1:5000%RESET%
echo %GREEN%  🖥️  前端界面: http://127.0.0.1:5173%RESET%
echo %GREEN%  🔧 联调测试: http://127.0.0.1:5173/debug%RESET%
echo %GREEN%===============================================%RESET%
echo.
echo %CYAN%💡 小贴士:%RESET%
echo %CYAN%   - 前端界面包含完整的测试用例管理功能%RESET%
echo %CYAN%   - 访问 /debug 页面可以测试前后端API连通性%RESET%
echo %CYAN%   - 按 Ctrl+C 停止服务，或直接关闭命令行窗口%RESET%
echo.
echo %YELLOW%⚠️  注意: 请保持此窗口打开以维持服务运行%RESET%
echo.

pause 