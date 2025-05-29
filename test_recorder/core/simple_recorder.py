import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import uuid

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from loguru import logger

from config.settings import settings
from core.models import TestSession, ActionRecord


class SimpleTestRecorder:
    """简化版测试录制器 - 专门针对Windows环境优化"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
        self.session: Optional[TestSession] = None
        self.is_recording = False
        self.action_count = 0
        
        # 事件监听器存储
        self._listeners: List[Callable] = []
        
    async def initialize(self):
        """初始化Playwright和浏览器 - 简化版"""
        try:
            logger.info("正在启动Playwright...")
            
            # 使用简化的启动方式
            self.playwright = await async_playwright().start()
            logger.info("Playwright启动成功")
            
            # 启动浏览器 - 使用最简单的配置
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # 显示浏览器窗口便于调试
                slow_mo=100
            )
            logger.info("浏览器启动成功")
            
            # 创建上下文 - 最简配置
            self.context = await self.browser.new_context()
            logger.info("浏览器上下文创建成功")
            
            # 创建页面
            self.page = await self.context.new_page()
            logger.info("页面创建成功")
            
            logger.info("简化录制器初始化完成")
            
        except Exception as e:
            logger.error(f"简化录制器初始化失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.error(f"错误详情: {str(e)}")
            
            # 清理资源
            await self._cleanup_resources()
            raise
    
    async def _cleanup_resources(self):
        """清理资源"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.warning(f"清理资源时出错: {e}")
    
    async def start_recording(self, test_name: str, description: str = "") -> str:
        """开始录制测试用例"""
        if self.is_recording:
            raise ValueError("录制已在进行中")
        
        if not self.page:
            await self.initialize()
        
        # 创建新的测试会话
        session_id = str(uuid.uuid4())
        self.session = TestSession(
            id=session_id,
            name=test_name,
            description=description,
            start_time=datetime.now(),
            actions=[]
        )
        
        self.is_recording = True
        self.action_count = 0
        
        logger.info(f"开始录制测试用例: {test_name} (ID: {session_id})")
        
        return session_id
    
    async def stop_recording(self) -> TestSession:
        """停止录制并保存结果"""
        if not self.is_recording or not self.session:
            raise ValueError("当前没有正在进行的录制")
        
        self.is_recording = False
        self.session.end_time = datetime.now()
        
        # 保存会话数据
        await self._save_session()
        
        logger.info(f"录制完成: {self.session.name} (总操作数: {len(self.session.actions)})")
        
        return self.session
    
    async def _save_session(self):
        """保存会话数据到文件"""
        try:
            session_file = settings.RECORDINGS_DIR / f"{self.session.id}_session.json"
            session_data = self.session.dict()
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"会话数据已保存: {session_file}")
            
        except Exception as e:
            logger.error(f"保存会话数据失败: {e}")
    
    async def navigate_to(self, url: str):
        """导航到指定URL"""
        if not self.page:
            raise ValueError("页面未初始化")
        
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            logger.info(f"导航到: {url}")
            
            # 记录导航操作
            if self.is_recording and self.session:
                action_record = ActionRecord(
                    id=str(uuid.uuid4()),
                    session_id=self.session.id,
                    action_type="goto",
                    timestamp=datetime.now(),
                    page_url=url,
                    page_title=await self.page.title(),
                    additional_data=f"导航到: {url}"
                )
                self.session.actions.append(action_record)
                await self._notify_listeners('action_recorded', action_record)
                
        except Exception as e:
            logger.error(f"导航失败: {e}")
            raise
    
    def add_listener(self, listener: Callable):
        """添加事件监听器"""
        self._listeners.append(listener)
    
    def remove_listener(self, listener: Callable):
        """移除事件监听器"""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    async def _notify_listeners(self, event_type: str, data: Any):
        """通知事件监听器"""
        for listener in self._listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event_type, data)
                else:
                    listener(event_type, data)
            except Exception as e:
                logger.error(f"监听器回调失败: {e}")
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.is_recording:
                await self.stop_recording()
            
            await self._cleanup_resources()
            
            logger.info("简化录制器资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")


# 全局简化录制器实例
simple_recorder = SimpleTestRecorder() 