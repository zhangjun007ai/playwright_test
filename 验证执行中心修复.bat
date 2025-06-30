@echo off
chcp 65001 >nul
echo ===============================================
echo   执行中心功能修复验证
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
)

echo.
echo 2. 检查前端服务 (端口5173)
netstat -an | findstr ":5173" >nul
if %errorlevel%==0 (
    echo    ✅ 前端服务正在运行
) else (
    echo    ❌ 前端服务未运行
    echo    请先启动前端服务: cd web_ui\frontend && npm run dev
)

echo.
echo 3. 检查API连通性
curl -s http://localhost:5000/api/health >nul 2>&1
if %errorlevel%==0 (
    echo    ✅ 后端API连接正常
) else (
    echo    ❌ 后端API连接失败
)

echo.
echo 4. 检查执行中心API
curl -s http://localhost:5000/api/execute/status >nul 2>&1
if %errorlevel%==0 (
    echo    ✅ 执行状态API正常
) else (
    echo    ❌ 执行状态API异常
)

curl -s http://localhost:5000/api/execute/history >nul 2>&1
if %errorlevel%==0 (
    echo    ✅ 执行历史API正常
) else (
    echo    ❌ 执行历史API异常
)

echo.
echo ===============================================
echo   修复内容总结
echo ===============================================
echo ✅ 添加了停止执行API (/api/execute/stop)
echo ✅ 添加了执行历史API (/api/execute/history)
echo ✅ 添加了创建用例API (/api/test-cases/create)
echo ✅ 修正了执行状态API响应格式
echo ✅ 增强了测试执行逻辑和统计功能
echo ✅ 优化了进程管理和错误处理

echo.
echo 💡 使用说明:
echo    1. 访问 http://localhost:5173 打开Web界面
echo    2. 进入"执行中心"页面
echo    3. 点击"开始执行"可以开始测试
echo    4. 可以查看实时日志和执行历史
echo    5. 支持停止正在执行的测试

echo.
echo 🔧 如果还有问题，请检查:
echo    - 确保Python环境正常
echo    - 确保Flask和其他依赖已安装
echo    - 确保项目根目录下有run.py文件
echo    - 检查网络和端口占用情况

pause 