@echo off
chcp 65001 >nul
echo 🔍 验证Editor.vue错误修复
echo ================================

echo [1/6] 检查filePath计算属性修复...
findstr /C:"typeof path !== 'string'" "web_ui/frontend/src/views/TestCases/Editor.vue" >nul
if %errorlevel%==0 (
    echo ✅ filePath计算属性已修复
) else (
    echo ❌ filePath计算属性修复未找到
)

echo [2/6] 检查fileName计算属性修复...
findstr /C:"const parts = path.split('/')" "web_ui/frontend/src/views/TestCases/Editor.vue" >nul
if %errorlevel%==0 (
    echo ✅ fileName计算属性已修复
) else (
    echo ❌ fileName计算属性修复未找到
)

echo [3/6] 检查loadFile函数错误处理...
findstr /C:"console.warn('无效的文件路径:'," "web_ui/frontend/src/views/TestCases/Editor.vue" >nul
if %errorlevel%==0 (
    echo ✅ loadFile函数错误处理已增强
) else (
    echo ❌ loadFile函数错误处理未找到
)

echo [4/6] 检查saveFile函数错误处理...
findstr /C:"throw new Error('无效的文件路径')" "web_ui/frontend/src/views/TestCases/Editor.vue" >nul
if %errorlevel%==0 (
    echo ✅ saveFile函数错误处理已增强
) else (
    echo ❌ saveFile函数错误处理未找到
)

echo [5/6] 检查extractConfigFromYaml安全性...
findstr /C:"typeof parsed !== 'object'" "web_ui/frontend/src/views/TestCases/Editor.vue" >nul
if %errorlevel%==0 (
    echo ✅ extractConfigFromYaml安全性已增强
) else (
    echo ❌ extractConfigFromYaml安全性增强未找到
)

echo [6/6] 检查生命周期钩子优化...
findstr /C:"验证路由参数" "web_ui/frontend/src/views/TestCases/Editor.vue" >nul
if %errorlevel%==0 (
    echo ✅ 生命周期钩子已优化
) else (
    echo ❌ 生命周期钩子优化未找到
)

echo.
echo 📋 修复总结:
echo - 修复了filePath.value.split错误
echo - 增强了所有计算属性的空值检查
echo - 优化了文件加载和保存的错误处理
echo - 添加了路由参数验证和监听
echo - 增强了YAML配置提取的安全性

echo.
echo 🧪 建议测试:
echo 1. 直接访问Editor页面（无路径参数）
echo 2. 访问无效的文件路径
echo 3. 编辑YAML文件内容
echo 4. 检查浏览器控制台是否还有错误

pause 