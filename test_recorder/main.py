#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用例自动录制生成系统
主应用入口文件

作者: AI Assistant
版本: 1.0.0
"""

import asyncio
import signal
import sys
import os
import platform
from pathlib import Path

# 在最开始就设置Windows事件循环策略
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import uvicorn
from loguru import logger

from config.settings import settings
from api import app
from core.realtime_recorder import realtime_recorder


def setup_logging():
    """配置日志系统"""
    # 移除默认的日志处理器
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # 添加文件输出
    logger.add(
        settings.LOG_FILE,
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )


def setup_signal_handlers():
    """设置信号处理器"""
    def signal_handler(signum, frame):
        logger.info(f"接收到信号 {signum}，正在关闭应用...")
        
        # 执行清理工作
        try:
            asyncio.create_task(cleanup())
        except Exception as e:
            logger.error(f"清理过程中出错: {e}")
        
        sys.exit(0)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def cleanup():
    """清理资源"""
    try:
        logger.info("正在清理应用资源...")
        
        # 清理录制器
        if realtime_recorder:
            await realtime_recorder.cleanup()
        
        logger.info("资源清理完成")
        
    except Exception as e:
        logger.error(f"清理资源时发生错误: {e}")


def check_dependencies():
    """检查系统依赖"""
    logger.info("检查系统依赖...")
    
    try:
        # 检查Playwright
        import playwright
        logger.info("Playwright已安装")
        
        # 检查其他关键依赖
        import fastapi
        logger.info(f"FastAPI版本: {fastapi.__version__}")
        
        import openpyxl
        logger.info(f"OpenPyXL版本: {openpyxl.__version__}")
        
        try:
            import docx
            logger.info("Python-docx已安装")
        except ImportError:
            logger.warning("Python-docx未安装")
        
        logger.info("所有依赖检查通过")
        return True
        
    except ImportError as e:
        logger.error(f"缺少必要的依赖: {e}")
        logger.error("请运行 'pip install -r requirements.txt' 安装依赖")
        return False


def check_playwright_browsers():
    """检查Playwright浏览器"""
    logger.info("检查Playwright浏览器...")
    
    try:
        import subprocess
        result = subprocess.run(
            ["playwright", "install", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            logger.info("Playwright CLI可用")
            
            # 提示安装浏览器
            logger.info("如果首次使用，请运行以下命令安装浏览器:")
            logger.info("playwright install chromium")
            logger.info("playwright install firefox")
            logger.info("playwright install webkit")
            
        return True
        
    except Exception as e:
        logger.warning(f"Playwright CLI检查失败: {e}")
        logger.warning("建议手动安装Playwright浏览器: playwright install")
        return True  # 不阻止启动


def print_banner():
    """打印启动横幅"""
    banner = f"""
╭─────────────────────────────────────────────────────────────╮
│                                                             │
│           测试用例自动录制生成系统 v{settings.APP_VERSION}                 │
│                                                             │
│  🎯 基于Playwright的自动化测试用例录制与生成                      │
│  🚀 实时录制UI操作，AI智能生成测试用例                          │
│  📊 支持Excel、Word、JSON多格式导出                           │
│                                                             │
│  服务地址: http://{settings.HOST}:{settings.PORT}                       │
│  WebSocket: ws://{settings.HOST}:{settings.PORT}/ws                    │
│                                                             │
╰─────────────────────────────────────────────────────────────╯
"""
    print(banner)


def main():
    """主函数"""
    # 设置日志
    setup_logging()
    
    # 打印启动横幅
    print_banner()
    
    logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"工作目录: {os.getcwd()}")
    logger.info(f"项目目录: {project_root}")
    
    # 检查依赖
    if not check_dependencies():
        logger.error("依赖检查失败，退出程序")
        sys.exit(1)
    
    # 检查Playwright浏览器
    check_playwright_browsers()
    
    # 设置信号处理器
    setup_signal_handlers()
    
    # 确保必要的目录存在
    settings.create_directories()
    logger.info("目录结构检查完成")
    
    # 启动应用
    logger.info(f"启动Web服务器: {settings.HOST}:{settings.PORT}")
    logger.info(f"调试模式: {settings.DEBUG}")
    
    try:
        uvicorn.run(
            "api:app",  # 使用导入字符串
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level=settings.LOG_LEVEL.lower(),
            access_log=True,
            server_header=False,
            date_header=False
        )
    except KeyboardInterrupt:
        logger.info("用户中断，正在退出...")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 