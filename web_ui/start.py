#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pytest Auto API Web UI 启动脚本
一键启动前端和后端服务
"""

import os
import sys
import time
import subprocess
import threading
import webbrowser
from pathlib import Path

def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║    ____        _            _      _         _               ║
    ║   |  _ \ _   _| |_ ___  ___| |_   / \  _   _| |_ ___         ║
    ║   | |_) | | | | __/ _ \/ __| __| / _ \| | | | __/ _ \        ║
    ║   |  __/| |_| | ||  __/\__ \ |_ / ___ \ |_| | || (_) |       ║
    ║   |_|    \__, |\__\___||___/\__/_/   \_\__,_|\__\___/        ║
    ║          |___/                                               ║
    ║                                                              ║
    ║              API 自动化测试框架 Web UI                        ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")
    
    # 检查 Python 版本
    if sys.version_info < (3, 7):
        print("❌ Python 版本过低，需要 Python 3.7+")
        return False
    
    # 检查必要的 Python 包
    required_packages = ['flask', 'flask_cors']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少 Python 包: {', '.join(missing_packages)}")
        print("请运行: pip install flask flask-cors")
        return False
    
    # 检查 Node.js 和 npm
    try:
        subprocess.run(['node', '--version'], check=True, capture_output=True)
        subprocess.run(['npm', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ 未找到 Node.js 或 npm，请先安装 Node.js")
        return False
    
    print("✅ 依赖检查通过")
    return True

def install_frontend_dependencies():
    """安装前端依赖"""
    frontend_dir = Path(__file__).parent / 'frontend'
    package_json = frontend_dir / 'package.json'
    node_modules = frontend_dir / 'node_modules'
    
    if not package_json.exists():
        print("❌ 未找到 package.json 文件")
        return False
    
    if not node_modules.exists():
        print("📦 安装前端依赖...")
        try:
            subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)
            print("✅ 前端依赖安装完成")
        except subprocess.CalledProcessError:
            print("❌ 前端依赖安装失败")
            return False
    else:
        print("✅ 前端依赖已存在")
    
    return True

def start_backend():
    """启动后端服务"""
    print("🚀 启动后端服务...")
    backend_dir = Path(__file__).parent / 'backend'
    app_file = backend_dir / 'app.py'
    
    if not app_file.exists():
        print("❌ 未找到后端应用文件")
        return None
    
    try:
        # 启动 Flask 应用
        process = subprocess.Popen(
            [sys.executable, str(app_file)],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # 等待后端启动
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ 后端服务启动成功 (http://localhost:5000)")
            return process
        else:
            print("❌ 后端服务启动失败")
            return None
            
    except Exception as e:
        print(f"❌ 启动后端服务时出错: {e}")
        return None

def start_frontend():
    """启动前端服务"""
    print("🚀 启动前端服务...")
    frontend_dir = Path(__file__).parent / 'frontend'
    
    try:
        # 启动 Vite 开发服务器
        process = subprocess.Popen(
            ['npm', 'run', 'dev'],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # 等待前端启动
        time.sleep(5)
        
        if process.poll() is None:
            print("✅ 前端服务启动成功 (http://localhost:3000)")
            return process
        else:
            print("❌ 前端服务启动失败")
            return None
            
    except Exception as e:
        print(f"❌ 启动前端服务时出错: {e}")
        return None

def open_browser():
    """打开浏览器"""
    print("🌐 打开浏览器...")
    time.sleep(2)  # 等待服务完全启动
    try:
        webbrowser.open('http://localhost:3000')
        print("✅ 浏览器已打开")
    except Exception as e:
        print(f"❌ 打开浏览器失败: {e}")
        print("请手动访问: http://localhost:3000")

def monitor_processes(backend_process, frontend_process):
    """监控进程状态"""
    try:
        while True:
            time.sleep(5)
            
            # 检查后端进程
            if backend_process and backend_process.poll() is not None:
                print("❌ 后端服务已停止")
                break
            
            # 检查前端进程
            if frontend_process and frontend_process.poll() is not None:
                print("❌ 前端服务已停止")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号，正在关闭服务...")
        
        # 停止进程
        if backend_process:
            backend_process.terminate()
            print("✅ 后端服务已停止")
        
        if frontend_process:
            frontend_process.terminate()
            print("✅ 前端服务已停止")
        
        print("👋 服务已全部停止")

def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 安装前端依赖
    if not install_frontend_dependencies():
        sys.exit(1)
    
    # 启动后端服务
    backend_process = start_backend()
    if not backend_process:
        sys.exit(1)
    
    # 启动前端服务
    frontend_process = start_frontend()
    if not frontend_process:
        if backend_process:
            backend_process.terminate()
        sys.exit(1)
    
    # 打开浏览器
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    print("\n" + "="*60)
    print("🎉 Pytest Auto API Web UI 启动成功!")
    print("📱 前端地址: http://localhost:3000")
    print("🔧 后端地址: http://localhost:5000")
    print("📖 使用说明: 请查看 README.md")
    print("⏹️  停止服务: 按 Ctrl+C")
    print("="*60 + "\n")
    
    # 监控进程
    monitor_processes(backend_process, frontend_process)

if __name__ == '__main__':
    main()
