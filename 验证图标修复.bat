@echo off
chcp 65001 >nul

echo [96m======================================================[0m
echo [92m          Element Plus图标修复验证[0m
echo [96m======================================================[0m
echo.

echo [94m🔍 验证修复结果...[0m

:: 检查是否还有Network图标的使用
findstr /r /s /i "Network" "web_ui\frontend\src\*.vue" >nul 2>&1
if not errorlevel 1 (
    echo [91m❌ 仍然发现 Network 图标使用[0m
    findstr /r /s /i "Network" "web_ui\frontend\src\*.vue"
) else (
    echo [92m✅ Network 图标已成功替换[0m
)

:: 检查Connection图标是否正确导入
findstr /r /s /i "Connection" "web_ui\frontend\src\*.vue" >nul 2>&1
if not errorlevel 1 (
    echo [92m✅ Connection 图标已正确使用[0m
) else (
    echo [93m⚠️  未发现 Connection 图标使用[0m
)

:: 检查导入语句
findstr /r /s /i "@element-plus/icons-vue" "web_ui\frontend\src\*.vue" >nul 2>&1
if not errorlevel 1 (
    echo [92m✅ Element Plus图标库导入正常[0m
    echo [96m📋 当前导入的图标:[0m
    findstr /r /s /i "import.*@element-plus/icons-vue" "web_ui\frontend\src\*.vue" | findstr /v "node_modules"
) else (
    echo [93m⚠️  未发现 Element Plus图标导入[0m
)

echo.
echo [96m======================================================[0m
echo [92m              验证完成！[0m
echo [96m======================================================[0m
echo [96m💡 如果验证通过，可以尝试启动前端服务:[0m
echo [96m   cd web_ui\frontend[0m
echo [96m   npm run dev[0m
echo [96m======================================================[0m

pause 