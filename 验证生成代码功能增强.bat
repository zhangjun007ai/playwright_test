@echo off
chcp 65001 >nul
echo 🔍 验证生成代码功能增强
echo ================================

echo [1/5] 检查前端生成代码函数增强...
findstr /C:"ElMessage.info('正在生成测试代码，请稍候...')" "web_ui/frontend/src/views/TestCases/index.vue" >nul
if %errorlevel%==0 (
    echo ✅ 前端生成代码函数已增强
) else (
    echo ❌ 前端生成代码函数未找到增强内容
)

echo [2/5] 检查后端生成代码API增强...
findstr /C:"yaml_files_count" "web_ui/backend/app.py" >nul
if %errorlevel%==0 (
    echo ✅ 后端生成代码API已增强
) else (
    echo ❌ 后端生成代码API未找到增强内容
)

echo [3/5] 检查前端空值检查增强...
findstr /C:"if (!Array.isArray(testCases.value))" "web_ui/frontend/src/views/TestCases/index.vue" >nul
if %errorlevel%==0 (
    echo ✅ 前端空值检查已增强
) else (
    echo ❌ 前端空值检查未找到增强内容
)

echo [4/5] 检查模板安全访问...
findstr /C:"(caseFile.cases || [])" "web_ui/frontend/src/views/TestCases/index.vue" >nul
if %errorlevel%==0 (
    echo ✅ 模板安全访问已修复
) else (
    echo ❌ 模板安全访问未找到修复内容
)

echo [5/5] 检查数据结构验证...
findstr /C:"testCases.value.map(item =>" "web_ui/frontend/src/views/TestCases/index.vue" >nul
if %errorlevel%==0 (
    echo ✅ 数据结构验证已添加
) else (
    echo ❌ 数据结构验证未找到
)

echo.
echo 📋 验证总结:
echo - 增强了生成代码功能，提供详细的进度和结果反馈
echo - 修复了前端空值访问错误
echo - 优化了错误处理和用户体验
echo - 增加了数据结构验证和安全检查

echo.
echo 🧪 建议手动测试:
echo 1. 访问用例管理页面
echo 2. 点击"生成代码"按钮
echo 3. 查看是否显示详细的生成结果对话框
echo 4. 检查浏览器控制台是否还有错误

pause 