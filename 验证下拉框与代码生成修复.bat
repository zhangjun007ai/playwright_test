@echo off
chcp 65001 >nul
echo 🔍 验证下拉框与代码生成功能修复
echo ========================================

echo [1/6] 检查CreateWizard动态模块获取...
findstr /C:"loadAvailableModules" "web_ui/frontend/src/views/TestCases/CreateWizard.vue" >nul
if %errorlevel%==0 (
    echo ✅ CreateWizard已添加动态模块获取
) else (
    echo ❌ CreateWizard动态模块获取未找到
)

echo [2/6] 检查模块列表自动更新...
findstr /C:"await loadAvailableModules()" "web_ui/frontend/src/views/TestCases/CreateWizard.vue" >nul
if %errorlevel%==0 (
    echo ✅ 用例创建后自动更新模块列表
) else (
    echo ❌ 模块列表自动更新未找到
)

echo [3/6] 检查Editor结构树点击增强...
findstr /C:"nodeTemplates" "web_ui/frontend/src/views/TestCases/Editor.vue" >nul
if %errorlevel%==0 (
    echo ✅ Editor结构树点击功能已增强
) else (
    echo ❌ Editor结构树点击增强未找到
)

echo [4/6] 检查代码格式化增强...
findstr /C:"代码格式化成功" "web_ui/frontend/src/views/TestCases/Editor.vue" >nul
if %errorlevel%==0 (
    echo ✅ 代码格式化功能已增强
) else (
    echo ❌ 代码格式化增强未找到
)

echo [5/6] 检查YAML验证增强...
findstr /C:"结构验证通过" "web_ui/frontend/src/views/TestCases/Editor.vue" >nul
if %errorlevel%==0 (
    echo ✅ YAML验证功能已增强
) else (
    echo ❌ YAML验证增强未找到
)

echo [6/6] 检查生命周期钩子添加...
findstr /C:"onMounted(() =>" "web_ui/frontend/src/views/TestCases/CreateWizard.vue" >nul
if %errorlevel%==0 (
    echo ✅ 生命周期钩子已正确添加
) else (
    echo ❌ 生命周期钩子未找到
)

echo.
echo 📋 修复总结:
echo - 下拉框模块数据现在动态获取，新建模块自动更新
echo - Editor结构树点击现在提供实用功能
echo - 代码格式化和验证功能大幅增强
echo - 错误处理更加友好和详细
echo - 数据同步机制确保用户体验流畅

echo.
echo 🧪 建议手动测试:
echo 1. 打开创建向导，检查模块下拉框内容
echo 2. 创建新模块的用例，完成后再次创建
echo 3. 验证新模块出现在下拉框中
echo 4. 在Editor中点击结构树节点
echo 5. 测试代码格式化和验证功能
echo 6. 检查浏览器控制台是否无错误

echo.
echo 💡 用户行为测试场景:
echo [场景1] 创建新模块 → 验证下拉框更新
echo [场景2] 编辑器功能 → 验证增强功能
echo [场景3] 代码生成 → 验证错误处理

pause 