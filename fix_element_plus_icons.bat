@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo [96m======================================================[0m
echo [92m         Element Plus图标自动修复工具 v1.0[0m
echo [96m======================================================[0m
echo.

echo [94m🔍 正在检查Element Plus图标导入错误...[0m

set "FRONTEND_DIR=web_ui\frontend\src"

if not exist "%FRONTEND_DIR%" (
    echo [91m❌ 前端源码目录不存在: %FRONTEND_DIR%[0m
    pause
    exit /b 1
)

echo [92m✅ 前端目录存在[0m

echo [94m🔧 正在检查常见图标错误...[0m

:: 检查Network图标错误
findstr /r /s /i "Network" "%FRONTEND_DIR%\*.vue" "%FRONTEND_DIR%\*.js" "%FRONTEND_DIR%\*.ts" >nul 2>&1
if not errorlevel 1 (
    echo [93m⚠️  发现 Network 图标使用，这个图标不存在[0m
    echo [93m   建议替换为: Connection, Link, Service[0m
) else (
    echo [92m✅ Network 图标检查通过[0m
)

:: 检查Magic图标错误
findstr /r /s /i "\bMagic\b" "%FRONTEND_DIR%\*.vue" "%FRONTEND_DIR%\*.js" "%FRONTEND_DIR%\*.ts" >nul 2>&1
if not errorlevel 1 (
    echo [93m⚠️  发现 Magic 图标使用，应该是 MagicStick[0m
) else (
    echo [92m✅ Magic 图标检查通过[0m
)

:: 检查其他常见错误图标
set "WRONG_ICONS=Internet Globe Net Web Api"
for %%i in (%WRONG_ICONS%) do (
    findstr /r /s /i "\b%%i\b" "%FRONTEND_DIR%\*.vue" "%FRONTEND_DIR%\*.js" "%FRONTEND_DIR%\*.ts" >nul 2>&1
    if not errorlevel 1 (
        echo [93m⚠️  发现可能错误的图标: %%i[0m
    )
)

echo.
echo [94m🧪 正在测试前端编译...[0m

cd web_ui\frontend
if errorlevel 1 (
    echo [91m❌ 无法进入前端目录[0m
    pause
    exit /b 1
)

echo [96m⏳ 运行编译测试...[0m
call npm run build --silent 2>build_errors.txt
if errorlevel 1 (
    echo [93m⚠️  编译过程中发现错误，检查 build_errors.txt[0m
    findstr /i "icon" build_errors.txt >nul 2>&1
    if not errorlevel 1 (
        echo [91m🔍 发现图标相关错误:[0m
        findstr /i "icon" build_errors.txt
    )
) else (
    echo [92m✅ 编译测试通过[0m
    if exist build_errors.txt del build_errors.txt
)

cd ..\..

echo.
echo [94m📋 Element Plus可用图标速查:[0m
echo [96m   网络相关: Connection, Link, Service[0m
echo [96m   魔法相关: MagicStick[0m  
echo [96m   系统相关: Setting, Tools, Operation[0m
echo [96m   媒体相关: Monitor, VideoPlay, Camera[0m
echo [96m   文档相关: DocumentAdd, Document, Folder[0m

echo.
echo [96m======================================================[0m
echo [92m              检查完成！[0m
echo [96m======================================================[0m
echo [96m💡 常见修复建议:[0m
echo [96m   1. Network → Connection 或 Link[0m
echo [96m   2. Magic → MagicStick[0m
echo [96m   3. 查看官方图标库: https://element-plus.org/zh-CN/component/icon.html[0m
echo [96m======================================================[0m

pause 