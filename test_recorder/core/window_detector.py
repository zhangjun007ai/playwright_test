#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
窗口检测器
自动检测新窗口创建和生命周期管理
用于支持跨窗口录制功能

作者: AI Assistant
版本: 1.0.0
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from playwright.async_api import Page, BrowserContext
from loguru import logger


class WindowInfo:
    """窗口信息类"""
    
    def __init__(self, page: Page, window_id: str = None, parent_id: str = None):
        self.page = page
        self.window_id = window_id or str(uuid.uuid4())
        self.parent_id = parent_id
        self.created_at = datetime.now()
        self.url = ""
        self.title = ""
        self.is_popup = parent_id is not None
        self.is_active = True
        
    async def update_info(self):
        """更新窗口信息"""
        try:
            self.url = self.page.url
            self.title = await self.page.title()
        except Exception as e:
            logger.warning(f"更新窗口信息失败: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "window_id": self.window_id,
            "parent_id": self.parent_id,
            "url": self.url,
            "title": self.title,
            "is_popup": self.is_popup,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat()
        }


class WindowDetector:
    """窗口检测器 - 自动检测和管理浏览器窗口"""
    
    def __init__(self):
        self.windows: Dict[str, WindowInfo] = {}
        self.context: Optional[BrowserContext] = None
        self.is_monitoring = False
        
        # 事件回调
        self._window_created_callbacks: List[Callable] = []
        self._window_closed_callbacks: List[Callable] = []
        self._window_navigation_callbacks: List[Callable] = []
        
        # 主窗口标识
        self.main_window_id: Optional[str] = None
        
    async def start_monitoring(self, context: BrowserContext, main_page: Page = None):
        """开始监控指定的browser context"""
        try:
            if self.is_monitoring:
                logger.warning("窗口检测器已在运行")
                return
                
            self.context = context
            self.is_monitoring = True
            
            logger.info("开始监控窗口创建和关闭事件")
            
            # 如果提供了主窗口，先注册它
            if main_page:
                await self._register_main_window(main_page)
            
            # 监听新页面创建事件
            context.on("page", self._on_page_created)
            
            # 检查是否已有页面存在
            existing_pages = context.pages
            for page in existing_pages:
                if not self._get_window_by_page(page):
                    await self._handle_new_page(page)
                    
            logger.info(f"窗口检测器启动完成，当前监控 {len(self.windows)} 个窗口")
            
        except Exception as e:
            logger.error(f"启动窗口监控失败: {e}")
            raise
    
    async def stop_monitoring(self):
        """停止监控"""
        try:
            if not self.is_monitoring:
                return
                
            self.is_monitoring = False
            
            if self.context:
                # 移除事件监听器
                self.context.remove_listener("page", self._on_page_created)
            
            # 清理所有窗口的监听器
            for window_info in self.windows.values():
                await self._remove_page_listeners(window_info.page)
            
            logger.info("窗口检测器已停止监控")
            
        except Exception as e:
            logger.error(f"停止窗口监控失败: {e}")
    
    async def _register_main_window(self, page: Page):
        """注册主窗口"""
        try:
            window_id = str(uuid.uuid4())
            window_info = WindowInfo(page, window_id)
            await window_info.update_info()
            
            self.windows[window_id] = window_info
            self.main_window_id = window_id
            
            # 为主窗口设置事件监听
            await self._setup_page_listeners(page, window_id)
            
            logger.info(f"主窗口已注册: {window_id}, URL: {window_info.url}")
            
            # 触发窗口创建回调
            await self._notify_window_created(window_info)
            
        except Exception as e:
            logger.error(f"注册主窗口失败: {e}")
            raise
    
    def _on_page_created(self, page: Page):
        """页面创建事件处理器"""
        try:
            logger.info(f"检测到新页面创建: {page.url}")
            asyncio.create_task(self._handle_new_page(page))
        except Exception as e:
            logger.error(f"处理新页面创建失败: {e}")
    
    async def _handle_new_page(self, page: Page):
        """处理新页面创建"""
        try:
            # 检查是否已经注册过
            if self._get_window_by_page(page):
                return
            
            window_id = str(uuid.uuid4())
            
            # 判断是否为popup窗口
            parent_id = None
            opener = None
            try:
                opener = await page.opener()
            except:
                pass
            
            if opener:
                parent_window = self._get_window_by_page(opener)
                if parent_window:
                    parent_id = parent_window.window_id
            
            # 创建窗口信息
            window_info = WindowInfo(page, window_id, parent_id)
            
            # 等待页面稳定后更新信息
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=3000)
                await window_info.update_info()
            except:
                # 如果无法等待加载完成，使用当前信息
                await window_info.update_info()
            
            self.windows[window_id] = window_info
            
            # 设置页面事件监听
            await self._setup_page_listeners(page, window_id)
            
            logger.info(f"新窗口已注册: {window_id}, URL: {window_info.url}, 父窗口: {parent_id}")
            
            # 触发窗口创建回调
            await self._notify_window_created(window_info)
            
        except Exception as e:
            logger.error(f"处理新页面失败: {e}")
    
    async def _setup_page_listeners(self, page: Page, window_id: str):
        """为页面设置事件监听器"""
        try:
            # 监听页面关闭事件
            page.on("close", lambda: asyncio.create_task(self._on_page_closed(window_id)))
            
            # 监听页面导航事件
            page.on("framenavigated", lambda frame: asyncio.create_task(
                self._on_page_navigated(window_id, frame.url) if frame == page.main_frame else None
            ))
            
            logger.debug(f"已为窗口 {window_id} 设置事件监听器")
            
        except Exception as e:
            logger.error(f"设置页面监听器失败: {e}")
    
    async def _remove_page_listeners(self, page: Page):
        """移除页面事件监听器"""
        try:
            # Playwright 的事件监听器会在页面关闭时自动清理
            # 这里主要用于显式清理
            pass
        except Exception as e:
            logger.error(f"移除页面监听器失败: {e}")
    
    async def _on_page_closed(self, window_id: str):
        """页面关闭事件处理"""
        try:
            window_info = self.windows.get(window_id)
            if not window_info:
                return
            
            window_info.is_active = False
            
            logger.info(f"窗口已关闭: {window_id}, URL: {window_info.url}")
            
            # 触发窗口关闭回调
            await self._notify_window_closed(window_info)
            
            # 从窗口列表中移除
            del self.windows[window_id]
            
        except Exception as e:
            logger.error(f"处理页面关闭失败: {e}")
    
    async def _on_page_navigated(self, window_id: str, url: str):
        """页面导航事件处理"""
        try:
            window_info = self.windows.get(window_id)
            if not window_info:
                return
            
            old_url = window_info.url
            await window_info.update_info()
            
            logger.info(f"窗口导航: {window_id}, {old_url} -> {url}")
            
            # 触发导航回调
            await self._notify_window_navigation(window_info, old_url, url)
            
        except Exception as e:
            logger.error(f"处理页面导航失败: {e}")
    
    def _get_window_by_page(self, page: Page) -> Optional[WindowInfo]:
        """根据page对象查找窗口信息"""
        for window_info in self.windows.values():
            if window_info.page == page:
                return window_info
        return None
    
    def get_window_info(self, window_id: str) -> Optional[WindowInfo]:
        """获取窗口信息"""
        return self.windows.get(window_id)
    
    def get_all_windows(self) -> List[WindowInfo]:
        """获取所有活动窗口"""
        return [window for window in self.windows.values() if window.is_active]
    
    def get_main_window(self) -> Optional[WindowInfo]:
        """获取主窗口"""
        if self.main_window_id:
            return self.windows.get(self.main_window_id)
        return None
    
    def get_popup_windows(self) -> List[WindowInfo]:
        """获取所有popup窗口"""
        return [window for window in self.windows.values() if window.is_popup and window.is_active]
    
    # 事件回调管理
    def on_window_created(self, callback: Callable[[WindowInfo], None]):
        """注册窗口创建回调"""
        self._window_created_callbacks.append(callback)
    
    def on_window_closed(self, callback: Callable[[WindowInfo], None]):
        """注册窗口关闭回调"""
        self._window_closed_callbacks.append(callback)
    
    def on_window_navigation(self, callback: Callable[[WindowInfo, str, str], None]):
        """注册窗口导航回调"""
        self._window_navigation_callbacks.append(callback)
    
    async def _notify_window_created(self, window_info: WindowInfo):
        """通知窗口创建"""
        for callback in self._window_created_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(window_info)
                else:
                    callback(window_info)
            except Exception as e:
                logger.error(f"窗口创建回调执行失败: {e}")
    
    async def _notify_window_closed(self, window_info: WindowInfo):
        """通知窗口关闭"""
        for callback in self._window_closed_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(window_info)
                else:
                    callback(window_info)
            except Exception as e:
                logger.error(f"窗口关闭回调执行失败: {e}")
    
    async def _notify_window_navigation(self, window_info: WindowInfo, old_url: str, new_url: str):
        """通知窗口导航"""
        for callback in self._window_navigation_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(window_info, old_url, new_url)
                else:
                    callback(window_info, old_url, new_url)
            except Exception as e:
                logger.error(f"窗口导航回调执行失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取检测器状态"""
        return {
            "is_monitoring": self.is_monitoring,
            "total_windows": len(self.windows),
            "active_windows": len(self.get_all_windows()),
            "popup_windows": len(self.get_popup_windows()),
            "main_window_id": self.main_window_id,
            "window_list": [window.to_dict() for window in self.get_all_windows()]
        } 