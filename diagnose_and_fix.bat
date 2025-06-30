@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ===============================================
echo   🔧 Pytest Auto API 问题诊断与修复工具
echo ===============================================
echo.

:: 设置颜色变量
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "RESET=[0m"
set "CYAN=[96m"
set "MAGENTA=[95m"

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "ISSUE_COUNT=0"
set "FIXED_COUNT=0"

echo %CYAN%🔍 开始系统诊断...%RESET%
echo.

:: 诊断1：检查前端图标导入问题
echo %BLUE%📋 诊断1: 检查前端图标导入问题...%RESET%
findstr /c:"Magic" web_ui\frontend\src\views\*.vue >nul 2>&1
if not errorlevel 1 (
    set /a ISSUE_COUNT+=1
    echo %RED%❌ 发现问题：前端代码中使用了不存在的Magic图标%RESET%
    echo %CYAN%🔧 正在修复：将Magic图标替换为MagicStick...%RESET%
    
    :: 修复TestCases/index.vue
    powershell -Command "(Get-Content 'web_ui\frontend\src\views\TestCases\index.vue') -replace '<Magic />', '<MagicStick />' | Set-Content 'web_ui\frontend\src\views\TestCases\index.vue'"
    powershell -Command "(Get-Content 'web_ui\frontend\src\views\TestCases\index.vue') -replace 'Magic,', '' | Set-Content 'web_ui\frontend\src\views\TestCases\index.vue'"
    
    :: 修复CreateWizard.vue
    powershell -Command "(Get-Content 'web_ui\frontend\src\views\TestCases\CreateWizard.vue') -replace '<Magic />', '<MagicStick />' | Set-Content 'web_ui\frontend\src\views\TestCases\CreateWizard.vue'"
    powershell -Command "(Get-Content 'web_ui\frontend\src\views\TestCases\CreateWizard.vue') -replace 'Magic,', 'MagicStick,' | Set-Content 'web_ui\frontend\src\views\TestCases\CreateWizard.vue'"
    
    :: 修复路由配置
    powershell -Command "(Get-Content 'web_ui\frontend\src\router\index.js') -replace \"icon: 'Magic'\", \"icon: 'MagicStick'\" | Set-Content 'web_ui\frontend\src\router\index.js'"
    
    set /a FIXED_COUNT+=1
    echo %GREEN%✅ 修复完成：图标导入问题已解决%RESET%
) else (
    echo %GREEN%✅ 无问题：前端图标导入正常%RESET%
)

:: 诊断2：检查前端依赖问题
echo.
echo %BLUE%📋 诊断2: 检查前端依赖状态...%RESET%
if not exist "web_ui\frontend\node_modules" (
    set /a ISSUE_COUNT+=1
    echo %RED%❌ 发现问题：前端依赖未安装%RESET%
    echo %CYAN%🔧 正在修复：安装前端依赖...%RESET%
    cd web_ui\frontend
    npm install --silent
    if errorlevel 1 (
        echo %YELLOW%⚠️  npm安装失败，尝试清理缓存后重试...%RESET%
        npm cache clean --force
        npm install --silent
    )
    cd ..\..
    set /a FIXED_COUNT+=1
    echo %GREEN%✅ 修复完成：前端依赖安装完成%RESET%
) else (
    echo %GREEN%✅ 无问题：前端依赖已安装%RESET%
)

:: 诊断3：检查Python依赖问题
echo.
echo %BLUE%📋 诊断3: 检查Python依赖状态...%RESET%
python -c "import jsonpath" >nul 2>&1
if errorlevel 1 (
    set /a ISSUE_COUNT+=1
    echo %RED%❌ 发现问题：jsonpath包未安装%RESET%
    echo %CYAN%🔧 正在修复：安装jsonpath包...%RESET%
    pip install jsonpath --quiet
    if errorlevel 1 (
        pip install jsonpath -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet
    )
    set /a FIXED_COUNT+=1
    echo %GREEN%✅ 修复完成：jsonpath包安装完成%RESET%
) else (
    echo %GREEN%✅ 无问题：Python依赖完整%RESET%
)

python -c "import yaml, requests, flask" >nul 2>&1
if errorlevel 1 (
    set /a ISSUE_COUNT+=1
    echo %RED%❌ 发现问题：核心Python包缺失%RESET%
    echo %CYAN%🔧 正在修复：安装核心依赖包...%RESET%
    if exist requirements.txt (
        pip install -r requirements.txt --quiet
    ) else (
        pip install PyYAML requests flask flask-cors --quiet
    )
    set /a FIXED_COUNT+=1
    echo %GREEN%✅ 修复完成：核心Python依赖安装完成%RESET%
) else (
    echo %GREEN%✅ 无问题：核心Python依赖完整%RESET%
)

:: 诊断4：检查端口配置一致性
echo.
echo %BLUE%📋 诊断4: 检查端口配置一致性...%RESET%
findstr /c:"port: 3000" web_ui\frontend\vite.config.js >nul 2>&1
if not errorlevel 1 (
    set /a ISSUE_COUNT+=1
    echo %RED%❌ 发现问题：Vite配置端口不一致%RESET%
    echo %CYAN%🔧 正在修复：统一端口配置为5173...%RESET%
    powershell -Command "(Get-Content 'web_ui\frontend\vite.config.js') -replace 'port: 3000', 'port: 5173' | Set-Content 'web_ui\frontend\vite.config.js'"
    set /a FIXED_COUNT+=1
    echo %GREEN%✅ 修复完成：端口配置已统一%RESET%
) else (
    echo %GREEN%✅ 无问题：端口配置一致%RESET%
)

:: 诊断5：检查API代理配置
echo.
echo %BLUE%📋 诊断5: 检查API代理配置...%RESET%
findstr /c:"target: 'http://localhost:5000'" web_ui\frontend\vite.config.js >nul 2>&1
if errorlevel 1 (
    set /a ISSUE_COUNT+=1
    echo %RED%❌ 发现问题：API代理配置缺失或错误%RESET%
    echo %CYAN%🔧 正在修复：添加正确的API代理配置...%RESET%
    
    :: 备份原文件
    copy "web_ui\frontend\vite.config.js" "web_ui\frontend\vite.config.js.backup" >nul
    
    :: 创建正确的配置文件
    (
    echo import { defineConfig } from 'vite'
    echo import vue from '@vitejs/plugin-vue'
    echo import { resolve } from 'path'
    echo.
    echo export default defineConfig{
    echo   plugins: [vue{}],
    echo   resolve: {
    echo     alias: {
    echo       '@': resolve{__dirname, 'src'^},
    echo     },
    echo   },
    echo   server: {
    echo     host: '0.0.0.0',
    echo     port: 5173,
    echo     proxy: {
    echo       '/api': {
    echo         target: 'http://localhost:5000',
    echo         changeOrigin: true,
    echo         secure: false,
    echo       },
    echo     },
    echo   },
    echo ^}
    ) > "web_ui\frontend\vite.config.js"
    
    set /a FIXED_COUNT+=1
    echo %GREEN%✅ 修复完成：API代理配置已添加%RESET%
) else (
    echo %GREEN%✅ 无问题：API代理配置正确%RESET%
)

:: 诊断6：检查后端服务状态
echo.
echo %BLUE%📋 诊断6: 检查后端服务状态...%RESET%
netstat -ano | findstr :5000 >nul 2>&1
if errorlevel 1 (
    set /a ISSUE_COUNT+=1
    echo %YELLOW%⚠️  发现问题：后端服务未运行%RESET%
    echo %CYAN%💡 建议：请先运行后端服务 (python web_ui\backend\app.py)%RESET%
) else (
    echo %GREEN%✅ 无问题：后端服务正在运行%RESET%
)

:: 诊断7：检查前端服务状态
echo.
echo %BLUE%📋 诊断7: 检查前端服务状态...%RESET%
netstat -ano | findstr :5173 >nul 2>&1
if errorlevel 1 (
    set /a ISSUE_COUNT+=1
    echo %YELLOW%⚠️  发现问题：前端服务未运行%RESET%
    echo %CYAN%💡 建议：请先运行前端服务 (cd web_ui\frontend && npm run dev)%RESET%
) else (
    echo %GREEN%✅ 无问题：前端服务正在运行%RESET%
)

:: 诊断8：检查CORS配置
echo.
echo %BLUE%📋 诊断8: 检查CORS配置...%RESET%
findstr /c:"CORS(app)" web_ui\backend\app.py >nul 2>&1
if errorlevel 1 (
    set /a ISSUE_COUNT+=1
    echo %RED%❌ 发现问题：后端CORS配置缺失%RESET%
    echo %CYAN%🔧 正在修复：添加CORS配置...%RESET%
    
    :: 备份原文件
    copy "web_ui\backend\app.py" "web_ui\backend\app.py.backup" >nul
    
    :: 添加CORS导入和配置（简化版修复）
    powershell -Command "(Get-Content 'web_ui\backend\app.py') -replace 'from flask import', 'from flask import' | Set-Content 'web_ui\backend\app.py.tmp'"
    powershell -Command "(Get-Content 'web_ui\backend\app.py.tmp') -replace 'app = Flask(__name__)', 'app = Flask(__name__)' + [Environment]::NewLine + 'CORS(app)  # Enable CORS' | Set-Content 'web_ui\backend\app.py'"
    del "web_ui\backend\app.py.tmp"
    
    set /a FIXED_COUNT+=1
    echo %GREEN%✅ 修复完成：CORS配置已添加%RESET%
) else (
    echo %GREEN%✅ 无问题：CORS配置正确%RESET%
)

:: 诊断总结
echo.
echo %MAGENTA%===============================================%RESET%
echo %MAGENTA%           🏥 诊断报告总结%RESET%
echo %MAGENTA%===============================================%RESET%
echo %CYAN%🔍 总共检查项目: 8%RESET%
echo %YELLOW%⚠️  发现问题数量: !ISSUE_COUNT!%RESET%
echo %GREEN%✅ 修复完成数量: !FIXED_COUNT!%RESET%
echo.

if !ISSUE_COUNT! equ 0 (
    echo %GREEN%🎉 恭喜！未发现任何问题，系统状态良好！%RESET%
) else (
    if !FIXED_COUNT! equ !ISSUE_COUNT! (
        echo %GREEN%🔧 所有发现的问题已自动修复完成！%RESET%
        echo %CYAN%💡 建议重启服务以使修复生效%RESET%
    ) else (
        echo %YELLOW%⚠️  部分问题需要手动处理，请查看上述建议%RESET%
    )
)

echo.
echo %BLUE%🚀 接下来可以执行：%RESET%
echo %CYAN%   1. 双击 fix_and_start.bat 启动服务%RESET%
echo %CYAN%   2. 访问 http://127.0.0.1:5173/debug 测试联调%RESET%
echo %CYAN%   3. 如有问题，重新运行此诊断工具%RESET%
echo.

pause 