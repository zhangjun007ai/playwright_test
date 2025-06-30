@echo off
chcp 65001 >nul

echo [96m======================================================[0m
echo [92m        创建向导功能验证测试 v1.0[0m
echo [96m======================================================[0m
echo.

echo [94m🔍 验证创建向导修复功能...[0m

:: 检查文件是否存在
if not exist "web_ui\frontend\src\views\TestCases\CreateWizard.vue" (
    echo [91m❌ CreateWizard.vue 文件不存在[0m
    pause
    exit /b 1
)

echo [92m✅ CreateWizard.vue 文件存在[0m

:: 检查关键功能是否已修复
echo [94m🔧 检查按钮功能修复...[0m

:: 检查路由导入
findstr /c "useRouter" "web_ui\frontend\src\views\TestCases\CreateWizard.vue" >nul
if not errorlevel 1 (
    echo [92m✅ 路由功能已导入[0m
) else (
    echo [91m❌ 缺少路由功能导入[0m
)

:: 检查API服务导入
findstr /c "apiService" "web_ui\frontend\src\views\TestCases\CreateWizard.vue" >nul
if not errorlevel 1 (
    echo [92m✅ API服务已导入[0m
) else (
    echo [91m❌ 缺少API服务导入[0m
)

:: 检查runTest函数
findstr /c "router.push('/execution')" "web_ui\frontend\src\views\TestCases\CreateWizard.vue" >nul
if not errorlevel 1 (
    echo [92m✅ 立即执行测试按钮功能正常[0m
) else (
    echo [91m❌ 立即执行测试按钮功能有问题[0m
)

:: 检查editCase函数
findstr /c "/test-cases/editor/" "web_ui\frontend\src\views\TestCases\CreateWizard.vue" >nul
if not errorlevel 1 (
    echo [92m✅ 编辑用例按钮功能正常[0m
) else (
    echo [91m❌ 编辑用例按钮功能有问题[0m
)

:: 检查createAnother函数
findstr /c "createdCaseInfo.value = null" "web_ui\frontend\src\views\TestCases\CreateWizard.vue" >nul
if not errorlevel 1 (
    echo [92m✅ 创建新用例按钮功能正常[0m
) else (
    echo [91m❌ 创建新用例按钮功能有问题[0m
)

:: 检查真实API调用
findstr /c "apiService.createTestCaseFile" "web_ui\frontend\src\views\TestCases\CreateWizard.vue" >nul
if not errorlevel 1 (
    echo [92m✅ 真实API创建功能已实现[0m
) else (
    echo [91m❌ 缺少真实API创建功能[0m
)

:: 检查用例信息展示
findstr /c "el-descriptions" "web_ui\frontend\src\views\TestCases\CreateWizard.vue" >nul
if not errorlevel 1 (
    echo [92m✅ 用例信息展示功能已添加[0m
) else (
    echo [91m❌ 缺少用例信息展示功能[0m
)

echo.
echo [94m🧪 前端编译测试...[0m

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
    type build_errors.txt | head -20
) else (
    echo [92m✅ 编译测试通过[0m
    if exist build_errors.txt del build_errors.txt
)

cd ..\..

echo.
echo [94m📋 功能测试建议:[0m
echo [96m   1. 启动前后端服务[0m
echo [96m   2. 访问 http://localhost:5173/test-cases/wizard[0m
echo [96m   3. 完成用例创建流程[0m
echo [96m   4. 测试三个按钮的跳转功能[0m
echo [96m   5. 验证用例文件是否真正创建[0m

echo.
echo [94m🔗 相关路由:[0m
echo [96m   - 创建向导: /test-cases/wizard[0m
echo [96m   - 执行中心: /execution[0m
echo [96m   - 用例编辑: /test-cases/editor/{path}[0m
echo [96m   - 用例管理: /test-cases[0m

echo.
echo [96m======================================================[0m
echo [92m              验证完成！[0m
echo [96m======================================================[0m
echo [96m💡 注意事项:[0m
echo [96m   - 确保后端API服务正常运行[0m
echo [96m   - 测试真实的用例创建和文件保存[0m
echo [96m   - 验证路由跳转是否正确[0m
echo [96m   - 检查用例信息展示是否完整[0m
echo [96m======================================================[0m

pause 