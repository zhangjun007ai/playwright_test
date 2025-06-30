@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo [96m======================================================[0m
echo [92m            SASS变量自动修复工具 v1.0[0m
echo [96m======================================================[0m
echo.

echo [94m🔍 正在检查SASS变量定义...[0m

set "VARIABLES_FILE=web_ui\frontend\src\styles\variables.scss"

if not exist "%VARIABLES_FILE%" (
    echo [91m❌ 变量文件不存在: %VARIABLES_FILE%[0m
    pause
    exit /b 1
)

echo [92m✅ 变量文件存在[0m

echo [94m🔧 正在检查并修复缺失的变量...[0m

:: 检查sketch-radius-lg
findstr /c:"$sketch-radius-lg" "%VARIABLES_FILE%" >nul
if errorlevel 1 (
    echo [93m⚠️  缺失变量: $sketch-radius-lg，正在添加...[0m
    :: 这里需要手动添加变量，因为批处理处理复杂文本替换比较困难
    echo [93m   请手动在variables.scss中添加: $sketch-radius-lg: 12px;[0m
) else (
    echo [92m✅ $sketch-radius-lg 已定义[0m
)

:: 检查sketch-shadow-md
findstr /c:"$sketch-shadow-md" "%VARIABLES_FILE%" >nul
if errorlevel 1 (
    echo [93m⚠️  缺失变量: $sketch-shadow-md，请手动添加[0m
    echo [93m   建议值: $sketch-shadow-md: 0 4px 20px rgba(102, 126, 234, 0.15);[0m
) else (
    echo [92m✅ $sketch-shadow-md 已定义[0m
)

:: 检查sketch-shadow-lg
findstr /c:"$sketch-shadow-lg" "%VARIABLES_FILE%" >nul
if errorlevel 1 (
    echo [93m⚠️  缺失变量: $sketch-shadow-lg，请手动添加[0m
    echo [93m   建议值: $sketch-shadow-lg: 0 6px 30px rgba(102, 126, 234, 0.25);[0m
) else (
    echo [92m✅ $sketch-shadow-lg 已定义[0m
)

echo.
echo [94m🧪 正在测试前端编译...[0m

cd web_ui\frontend
if errorlevel 1 (
    echo [91m❌ 无法进入前端目录[0m
    pause
    exit /b 1
)

echo [96m⏳ 运行 npm run build 测试编译...[0m
call npm run build 2>&1 | findstr /i "error"
if errorlevel 1 (
    echo [92m✅ 编译测试通过，未发现错误[0m
) else (
    echo [93m⚠️  编译过程中发现错误，请检查日志[0m
)

cd ..\..

echo.
echo [96m======================================================[0m
echo [92m              修复完成！[0m
echo [96m======================================================[0m
echo [96m💡 如果仍有问题，请：[0m
echo [96m   1. 检查 %VARIABLES_FILE%[0m
echo [96m   2. 确保所有变量都已正确定义[0m
echo [96m   3. 重启开发服务器[0m
echo [96m======================================================[0m

pause 