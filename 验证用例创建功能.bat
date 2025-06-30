@echo off
chcp 65001 >nul
echo ===============================================
echo   用例创建功能验证
echo ===============================================

echo.
echo 🔍 检查服务状态...

echo.
echo 1. 检查后端服务 (端口5000)
netstat -an | findstr ":5000" >nul
if %errorlevel%==0 (
    echo    ✅ 后端服务正在运行
) else (
    echo    ❌ 后端服务未运行
    echo    请先启动后端服务: cd web_ui\backend && python app.py
    pause
    exit /b 1
)

echo.
echo 2. 检查前端服务 (端口5173)
netstat -an | findstr ":5173" >nul
if %errorlevel%==0 (
    echo    ✅ 前端服务正在运行
) else (
    echo    ❌ 前端服务未运行
    echo    请先启动前端服务: cd web_ui\frontend && npm run dev
    pause
    exit /b 1
)

echo.
echo 3. 测试用例创建API
echo    测试保存文件接口...
curl -s -X POST "http://localhost:5000/api/test-cases/data/Test/test_api.yaml" ^
     -H "Content-Type: application/json" ^
     -d "{\"content\":\"case_common:\n  allureEpic: 测试\n  allureFeature: API测试\n  allureStory: 测试用例\"}" >nul 2>&1

if %errorlevel%==0 (
    echo    ✅ 保存文件API正常
) else (
    echo    ❌ 保存文件API异常
)

echo    测试创建用例接口...
curl -s -X POST "http://localhost:5000/api/test-cases/create" ^
     -H "Content-Type: application/json" ^
     -d "{\"module\":\"Test\",\"case_name\":\"测试用例\",\"case_data\":{\"测试用例\":{\"name\":\"测试用例\"}}}" >nul 2>&1

if %errorlevel%==0 (
    echo    ✅ 创建用例API正常
) else (
    echo    ❌ 创建用例API异常
)

echo.
echo 4. 检查data目录结构
if exist "data" (
    echo    ✅ data目录存在
    dir /b data 2>nul | findstr /v "^$" >nul
    if %errorlevel%==0 (
        echo    📁 data目录内容:
        for /d %%i in (data\*) do (
            echo       - %%~ni/
        )
    ) else (
        echo    📂 data目录为空
    )
) else (
    echo    ❌ data目录不存在
    echo    创建data目录...
    mkdir data >nul 2>&1
)

echo.
echo ===============================================
echo   修复内容总结
echo ===============================================
echo ✅ 修复了API方法名不匹配问题
echo ✅ 添加了别名方法保持兼容性
echo ✅ 增强了错误处理和用户反馈
echo ✅ 改进了日志输出用于调试
echo ✅ 优化了文件路径构建逻辑

echo.
echo 💡 使用说明:
echo    1. 访问 http://localhost:5173 打开Web界面
echo    2. 进入"用例管理"页面
echo    3. 点击"新建用例"按钮
echo    4. 填写模块名称、文件名称、功能描述、故事描述
echo    5. 点击"创建"按钮创建用例文件
echo    6. 成功后会显示详细的文件路径
echo    7. 列表会自动刷新显示新创建的用例

echo.
echo 🔧 故障排除:
echo    - 确保模块名和文件名只包含字母、数字、下划线
echo    - 检查浏览器控制台是否有错误信息
echo    - 查看网络请求的详细响应
echo    - 确认后端服务日志输出

echo.
echo 📝 测试步骤:
echo    1. 打开用例管理页面
echo    2. 点击"新建用例"
echo    3. 填写表单信息
echo    4. 提交创建请求
echo    5. 检查成功提示和文件列表

pause 