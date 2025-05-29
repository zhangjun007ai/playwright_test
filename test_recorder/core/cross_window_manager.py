#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨窗口管理器
整合窗口检测器和事件协调器，提供统一的跨窗口录制管理接口

作者: AI Assistant  
版本: 1.0.0
"""

import asyncio
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from playwright.async_api import Page, BrowserContext, Browser
import time

from loguru import logger

# 导入自定义模块
from .window_detector import WindowDetector, WindowInfo
from .page_event_coordinator import PageEventCoordinator, CrossWindowEvent


class CrossWindowManager:
    """跨窗口管理器 - 统一管理多窗口录制功能"""
    
    def __init__(self, event_buffer_size: int = 100, flush_interval: float = 0.5):
        # 核心组件
        self.window_detector = WindowDetector()
        self.event_coordinator = PageEventCoordinator(event_buffer_size, flush_interval)
        
        # 状态管理
        self.is_active = False
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.main_page: Optional[Page] = None
        
        # 事件监听脚本缓存
        self._event_script_cache: Optional[str] = None
        
        # 外部回调
        self._action_recorded_callbacks: List[Callable] = []
        self._window_event_callbacks: List[Callable] = []
        
        # 录制统计
        self.recording_stats = {
            "total_events": 0,
            "windows_created": 0,
            "cross_window_events": 0,
            "start_time": None
        }
        
    async def initialize(self, browser: Browser, context: BrowserContext, main_page: Page):
        """初始化跨窗口管理器"""
        try:
            if self.is_active:
                logger.warning("跨窗口管理器已初始化")
                return
            
            self.browser = browser
            self.context = context
            self.main_page = main_page
            
            logger.info("初始化跨窗口管理器...")
            
            # 设置组件间的事件绑定
            await self._setup_component_bindings()
            
            # 启动核心组件
            await self.window_detector.start_monitoring(context, main_page)
            await self.event_coordinator.start()
            
            # 为主页面注入事件监听器
            await self._inject_event_listeners(main_page, self.window_detector.main_window_id)
            
            self.is_active = True
            self.recording_stats["start_time"] = datetime.now()
            
            logger.info("跨窗口管理器初始化完成")
            
        except Exception as e:
            logger.error(f"初始化跨窗口管理器失败: {e}")
            raise
    
    async def cleanup(self):
        """清理跨窗口管理器"""
        try:
            if not self.is_active:
                return
            
            logger.info("清理跨窗口管理器...")
            
            self.is_active = False
            
            # 停止核心组件
            await self.window_detector.stop_monitoring()
            await self.event_coordinator.stop()
            
            # 清理引用
            self.browser = None
            self.context = None
            self.main_page = None
            
            logger.info("跨窗口管理器清理完成")
            
        except Exception as e:
            logger.error(f"清理跨窗口管理器失败: {e}")
    
    async def _setup_component_bindings(self):
        """设置组件间的事件绑定"""
        try:
            # 绑定窗口检测器事件
            self.window_detector.on_window_created(self._on_window_created)
            self.window_detector.on_window_closed(self._on_window_closed)
            self.window_detector.on_window_navigation(self._on_window_navigation)
            
            # 绑定事件协调器事件
            self.event_coordinator.on_event_processed(self._on_event_processed)
            self.event_coordinator.on_batch_processed(self._on_batch_processed)
            
            logger.debug("组件间事件绑定完成")
            
        except Exception as e:
            logger.error(f"设置组件绑定失败: {e}")
            raise
    
    async def _on_window_created(self, window_info: WindowInfo):
        """处理新窗口创建事件"""
        try:
            logger.info(f"处理新窗口创建: {window_info.window_id}, URL: {window_info.url}")
            
            # 为新窗口注入事件监听器
            await self._inject_event_listeners(window_info.page, window_info.window_id)
            
            # 更新统计
            self.recording_stats["windows_created"] += 1
            
            # 通知外部回调
            await self._notify_window_event("window_created", window_info)
            
        except Exception as e:
            logger.error(f"处理窗口创建失败: {e}")
    
    async def _on_window_closed(self, window_info: WindowInfo):
        """处理窗口关闭事件"""
        try:
            logger.info(f"处理窗口关闭: {window_info.window_id}")
            
            # 清理事件协调器中的窗口状态
            self.event_coordinator.clear_window_state(window_info.window_id)
            
            # 通知外部回调
            await self._notify_window_event("window_closed", window_info)
            
        except Exception as e:
            logger.error(f"处理窗口关闭失败: {e}")
    
    async def _on_window_navigation(self, window_info: WindowInfo, old_url: str, new_url: str):
        """处理窗口导航事件"""
        try:
            logger.info(f"处理窗口导航: {window_info.window_id}, {old_url} -> {new_url}")
            
            # 重新注入事件监听器（防止页面刷新后丢失）
            await self._inject_event_listeners(window_info.page, window_info.window_id)
            
            # 通知外部回调
            await self._notify_window_event("window_navigation", window_info, {
                "old_url": old_url,
                "new_url": new_url
            })
            
        except Exception as e:
            logger.error(f"处理窗口导航失败: {e}")
    
    async def _inject_event_listeners(self, page: Page, window_id: str):
        """为页面注入事件监听器"""
        try:
            # 获取事件监听脚本
            script = self._get_enhanced_event_listener_script(window_id)
            
            # 注入初始化脚本
            await page.add_init_script(script)
            
            # 如果页面已经加载，直接执行脚本
            try:
                await page.evaluate(script)
                logger.debug(f"已为窗口 {window_id} 注入事件监听器")
            except Exception as e:
                logger.debug(f"页面可能还未完全加载，注入初始化脚本: {e}")
            
        except Exception as e:
            logger.error(f"注入事件监听器失败: {e}")
    
    def _get_enhanced_event_listener_script(self, window_id: str) -> str:
        """获取简化版事件监听器脚本（记录关键元素信息）"""
        if self._event_script_cache:
            return self._event_script_cache.replace("WINDOW_ID_PLACEHOLDER", window_id)
        
        script = f"""
        (function() {{
            const windowId = '{window_id}';
            
            if (window.playwrightWindowId === windowId) {{
                return 'already_injected_for_window';
            }}
            
            window.playwrightWindowId = windowId;
            
            console.log('RECORDER_DEBUG: 注入简化版事件监听器，窗口ID:', windowId);
            
            // 获取元素的关键信息（简化版）
            function getElementInfo(element) {{
                if (!element) return {{}};
                
                const rect = element.getBoundingClientRect();
                
                return {{
                    // 基本信息
                    tag: element.tagName.toLowerCase(),
                    id: element.id || '',
                    class: element.className || '',
                    name: element.name || '',
                    type: element.type || '',
                    value: element.value || '',
                    text: (element.innerText || element.textContent || '').substring(0, 100),
                    
                    // 链接和基本属性
                    href: element.href || '',
                    src: element.src || '',
                    placeholder: element.placeholder || '',
                    
                    // 位置信息
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    
                    // DOM路径（简化）
                    cssSelector: getCSSSelector(element),
                    xpath: getSimpleXPath(element),
                    
                    // 父元素信息（基本）
                    parentTag: element.parentElement ? element.parentElement.tagName.toLowerCase() : '',
                    parentId: element.parentElement ? element.parentElement.id : '',
                    parentClass: element.parentElement ? element.parentElement.className.split(' ')[0] : ''
                }};
            }}
            
            // 获取CSS选择器（简化版）
            function getCSSSelector(element) {{
                if (!element) return '';
                
                if (element.id) {{
                    return '#' + element.id;
                }}
                
                if (element.className) {{
                    const classes = element.className.split(' ').filter(c => c.trim());
                    if (classes.length > 0) {{
                        return element.tagName.toLowerCase() + '.' + classes[0];
                    }}
                }}
                
                return element.tagName.toLowerCase();
            }}
            
            // 获取简化XPath
            function getSimpleXPath(element) {{
                if (!element) return '';
                
                if (element.id) {{
                    return `//*[@id="${{element.id}}"]`;
                }}
                
                let path = element.tagName.toLowerCase();
                let current = element;
                let level = 0;
                
                while (current.parentElement && level < 3) {{
                    const parent = current.parentElement;
                    let parentPath = parent.tagName.toLowerCase();
                    
                    if (parent.id) {{
                        return `//*[@id="${{parent.id}}"]/${{{path}}}`;
                    }}
                    
                    if (parent.className) {{
                        const firstClass = parent.className.split(' ')[0];
                        if (firstClass) {{
                            parentPath += `[@class="${{firstClass}}"]`;
                        }}
                    }}
                    
                    path = parentPath + '/' + path;
                    current = parent;
                    level++;
                }}
                
                return '//' + path;
            }}
            
            // 核心事件记录函数（简化版）
            function recordEvent(eventType, element, eventData = {{}}) {{
                try {{
                    const elementInfo = getElementInfo(element);
                    
                    const eventPayload = {{
                        windowId: windowId,
                        eventType: eventType,
                        element: elementInfo,
                        page: {{
                            url: window.location.href,
                            title: document.title,
                            timestamp: Date.now()
                        }},
                        eventData: eventData,
                        timestamp: Date.now()
                    }};
                    
                    // 发送到控制台供Playwright捕获
                    console.log('RECORDER_EVENT:' + eventType + ':' + JSON.stringify(eventPayload));
                    
                    // 简化调试信息
                    console.log('RECORDER_DEBUG: 事件记录', {{
                        窗口: windowId,
                        类型: eventType,
                        元素: elementInfo.tag + (elementInfo.id ? '#' + elementInfo.id : '') + (elementInfo.class ? '.' + elementInfo.class.split(' ')[0] : ''),
                        文本: elementInfo.text.substring(0, 30)
                    }});
                    
                }} catch (error) {{
                    console.error('RECORDER_DEBUG: 事件记录失败:', error);
                }}
            }}
            
            // 点击事件监听
            document.addEventListener('click', function(event) {{
                recordEvent('click', event.target, {{
                    button: event.button,
                    ctrlKey: event.ctrlKey,
                    shiftKey: event.shiftKey,
                    altKey: event.altKey,
                    clientX: event.clientX,
                    clientY: event.clientY
                }});
            }}, true);
            
            // 输入事件监听
            document.addEventListener('input', function(event) {{
                const isPassword = event.target.type === 'password';
                recordEvent('input', event.target, {{
                    value: isPassword ? '***' : event.target.value,
                    inputType: event.inputType || ''
                }});
            }}, true);
            
            // 键盘事件监听（仅记录特殊按键）
            document.addEventListener('keydown', function(event) {{
                if (['Enter', 'Tab', 'Escape', 'Backspace', 'Delete'].includes(event.key)) {{
                    recordEvent('keydown', event.target, {{
                        key: event.key,
                        ctrlKey: event.ctrlKey,
                        shiftKey: event.shiftKey,
                        altKey: event.altKey
                    }});
                }}
            }}, true);
            
            // 表单事件监听
            document.addEventListener('submit', function(event) {{
                recordEvent('submit', event.target, {{
                    action: event.target.action || '',
                    method: event.target.method || 'get'
                }});
            }}, true);
            
            // 选择和改变事件
            document.addEventListener('change', function(event) {{
                let changeData = {{
                    value: event.target.value || ''
                }};
                
                if (event.target.tagName.toLowerCase() === 'select') {{
                    const selectedOption = event.target.options[event.target.selectedIndex];
                    changeData.selectedText = selectedOption ? selectedOption.text : '';
                }} else if (event.target.type === 'checkbox' || event.target.type === 'radio') {{
                    changeData.checked = event.target.checked;
                }}
                
                recordEvent('change', event.target, changeData);
            }}, true);
            
            // 监听链接点击（特别是target="_blank"）
            document.addEventListener('click', function(event) {{
                const element = event.target.closest('a');
                if (element && element.href) {{
                    recordEvent('link_click', element, {{
                        href: element.href,
                        target: element.target || '_self'
                    }});
                }}
            }}, true);
            
            // 监听页面跳转（用于检测跨窗口操作）
            const originalOpen = window.open;
            window.open = function(url, target, features) {{
                recordEvent('window_open', null, {{
                    url: url,
                    target: target || '_blank'
                }});
                return originalOpen.call(this, url, target, features);
            }};
            
            console.log('RECORDER_DEBUG: 简化版事件监听器注入完成 - 窗口ID:', windowId);
            
            return 'simplified_injection_success';
            
        }})();
        """
        
        self._event_script_cache = script
        return script
    
    async def _on_event_processed(self, event: CrossWindowEvent):
        """处理单个事件"""
        try:
            # 更新统计
            self.recording_stats["total_events"] += 1
            if event.is_cross_window:
                self.recording_stats["cross_window_events"] += 1
            
            # 通知外部回调
            await self._notify_action_recorded(event)
            
        except Exception as e:
            logger.error(f"处理事件失败: {e}")
    
    async def _on_batch_processed(self, events: List[CrossWindowEvent]):
        """处理批量事件"""
        try:
            logger.debug(f"批量处理 {len(events)} 个事件")
            
            # 可以在这里添加批量处理逻辑
            # 比如生成测试代码、更新UI等
            
        except Exception as e:
            logger.error(f"批量处理事件失败: {e}")
    
    # 录制事件接口
    async def record_browser_action(self, window_id: str, event_type: str, event_data: Dict[str, Any]):
        """记录浏览器操作事件（从JavaScript事件监听器调用）- 简化版"""
        try:
            window_info = self.window_detector.get_window_info(window_id)
            if not window_info:
                logger.warning(f"未找到窗口信息: {window_id}")
                return
            
            # 处理事件数据
            element_info = event_data.get('element', {})
            page_context = event_data.get('page', {})
            original_event_data = event_data.get('eventData', {})
            
            # 获取页面信息
            url = page_context.get('url', '')
            title = page_context.get('title', '')
            
            logger.debug(f"记录跨窗口事件: {event_type}, 窗口: {window_id}, 元素: {element_info.get('tag', '')}#{element_info.get('id', '')} .{element_info.get('class', '')}")
            
            # 确定父窗口ID（用于跨窗口关系检测）
            parent_window_id = window_info.parent_id
            
            # 构建完整的附加数据
            complete_additional_data = {
                'original_event_data': original_event_data,
                'page_context': page_context,
                'window_id': window_id,
                'timestamp': event_data.get('timestamp', time.time() * 1000)
            }
            
            # 添加到事件协调器
            event_id = await self.event_coordinator.add_event(
                window_id=window_id,
                event_type=event_type,
                url=url,
                title=title,
                element_info=element_info,
                additional_data=complete_additional_data,
                parent_window_id=parent_window_id
            )
            
            logger.debug(f"跨窗口事件已记录: {event_type} - {window_id} - {event_id}")
            
        except Exception as e:
            logger.error(f"记录跨窗口浏览器事件失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
    
    # 状态查询接口
    def get_all_windows(self) -> List[WindowInfo]:
        """获取所有活动窗口"""
        return self.window_detector.get_all_windows()
    
    def get_main_window(self) -> Optional[WindowInfo]:
        """获取主窗口"""
        return self.window_detector.get_main_window()
    
    def get_popup_windows(self) -> List[WindowInfo]:
        """获取所有popup窗口"""
        return self.window_detector.get_popup_windows()
    
    def get_window_info(self, window_id: str) -> Optional[WindowInfo]:
        """获取指定窗口信息"""
        return self.window_detector.get_window_info(window_id)
    
    def get_recording_stats(self) -> Dict[str, Any]:
        """获取录制统计信息"""
        stats = self.recording_stats.copy()
        if stats["start_time"]:
            duration = datetime.now() - stats["start_time"]
            stats["duration_seconds"] = duration.total_seconds()
        
        # 添加组件状态
        stats.update({
            "window_detector": self.window_detector.get_status(),
            "event_coordinator": self.event_coordinator.get_status()
        })
        
        return stats
    
    async def force_flush_events(self):
        """强制刷新所有待处理事件"""
        await self.event_coordinator.force_flush()
    
    # 回调管理
    def on_action_recorded(self, callback: Callable[[CrossWindowEvent], None]):
        """注册动作录制回调"""
        self._action_recorded_callbacks.append(callback)
    
    def on_window_event(self, callback: Callable[[str, WindowInfo, Dict], None]):
        """注册窗口事件回调"""
        self._window_event_callbacks.append(callback)
    
    async def _notify_action_recorded(self, event: CrossWindowEvent):
        """通知动作录制"""
        for callback in self._action_recorded_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"动作录制回调执行失败: {e}")
    
    async def _notify_window_event(self, event_type: str, window_info: WindowInfo, data: Dict = None):
        """通知窗口事件"""
        for callback in self._window_event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, window_info, data or {})
                else:
                    callback(event_type, window_info, data or {})
            except Exception as e:
                logger.error(f"窗口事件回调执行失败: {e}")
    
    def is_recording_active(self) -> bool:
        """检查录制是否激活"""
        return self.is_active and self.event_coordinator.is_active 
        return self.is_active and self.event_coordinator.is_active 