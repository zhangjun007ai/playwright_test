import asyncio
import json
import time
import sys
import platform
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import uuid

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from loguru import logger

from config.settings import settings, ACTION_TYPES, ELEMENT_TYPES
from core.models import TestSession, ActionRecord, TestStep


class TestRecorder:
    """测试录制器核心类"""
    
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
        """初始化Playwright和浏览器"""
        try:
            logger.info("正在启动Playwright...")
            self.playwright = await async_playwright().start()
            
            # 简化的浏览器启动配置
            launch_options = {
                "headless": settings.HEADLESS,
                "slow_mo": settings.SLOW_MO
            }
            
            # 根据配置选择浏览器类型
            if settings.BROWSER_TYPE == "firefox":
                self.browser = await self.playwright.firefox.launch(**launch_options)
            elif settings.BROWSER_TYPE == "webkit":
                self.browser = await self.playwright.webkit.launch(**launch_options)
            else:  # chromium (default)
                self.browser = await self.playwright.chromium.launch(**launch_options)
            
            logger.info(f"浏览器启动成功: {settings.BROWSER_TYPE}")
            
            # 简化的浏览器上下文配置
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "ignore_https_errors": True
            }
            
            self.context = await self.browser.new_context(**context_options)
            
            # 创建页面
            self.page = await self.context.new_page()
            
            logger.info(f"浏览器初始化完成: {settings.BROWSER_TYPE}")
            
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.error(f"错误详情: {str(e)}")
            
            # 尝试清理已创建的资源
            try:
                if self.context:
                    await self.context.close()
                if self.browser:
                    await self.browser.close()
                if self.playwright:
                    await self.playwright.stop()
            except:
                pass
            
            raise
    
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
        
        # 设置页面事件监听
        await self._setup_page_listeners()
        
        logger.info(f"开始录制测试用例: {test_name} (ID: {session_id})")
        
        return session_id
    
    async def stop_recording(self) -> TestSession:
        """停止录制并保存结果"""
        if not self.is_recording or not self.session:
            raise ValueError("当前没有正在进行的录制")
        
        self.is_recording = False
        self.session.end_time = datetime.now()
        
        # 移除页面事件监听
        await self._remove_page_listeners()
        
        # 停止追踪并保存
        if settings.ENABLE_TRACING:
            trace_path = settings.RECORDINGS_DIR / f"{self.session.id}_trace.zip"
            await self.context.tracing.stop(path=trace_path)
            self.session.trace_file = str(trace_path)
        
        # 保存会话数据
        await self._save_session()
        
        logger.info(f"录制完成: {self.session.name} (总操作数: {len(self.session.actions)})")
        
        return self.session
    
    async def _setup_page_listeners(self):
        """设置页面事件监听器"""
        if not self.page:
            return
        
        # 监听页面导航
        async def on_navigation(response):
            if response and response.url:
                await self._record_action("goto", {
                    "url": response.url,
                    "title": await self.page.title()
                })
        
        # 监听请求完成
        async def on_response(response):
            # 只记录主要的页面导航
            if response.request.resource_type == "document":
                await self._record_action("navigation", {
                    "url": response.url,
                    "status": response.status,
                    "method": response.request.method
                })
        
        # 监听控制台消息
        def on_console(message):
            logger.debug(f"Console: {message.text}")
        
        # 注册监听器
        self.page.on("response", on_response)
        self.page.on("console", on_console)
        
        # 添加JavaScript注入来监听用户交互
        await self._inject_interaction_listeners()
    
    async def _inject_interaction_listeners(self):
        """注入JavaScript代码监听用户交互"""
        js_code = '''
        (function() {
            let actionCount = 0;
            
            function getElementInfo(element) {
                const rect = element.getBoundingClientRect();
                const tagName = element.tagName.toLowerCase();
                const id = element.id || '';
                const className = element.className || '';
                const text = element.textContent ? element.textContent.trim().substring(0, 50) : '';
                const value = element.value || '';
                const placeholder = element.placeholder || '';
                const name = element.name || '';
                const type = element.type || '';
                
                // 生成选择器
                let selector = tagName;
                if (id) selector = `#${id}`;
                else if (className) selector = `.${className.split(' ')[0]}`;
                else if (name) selector = `[name="${name}"]`;
                else if (placeholder) selector = `[placeholder="${placeholder}"]`;
                
                return {
                    tagName,
                    id,
                    className,
                    text,
                    value,
                    placeholder,
                    name,
                    type,
                    selector,
                    position: { x: rect.left, y: rect.top },
                    size: { width: rect.width, height: rect.height }
                };
            }
            
            function recordAction(action, element, additionalData = {}) {
                actionCount++;
                const elementInfo = getElementInfo(element);
                const actionData = {
                    action,
                    timestamp: Date.now(),
                    actionCount,
                    element: elementInfo,
                    url: window.location.href,
                    title: document.title,
                    ...additionalData
                };
                
                // 发送到Python后端
                window.postMessage({
                    type: 'PLAYWRIGHT_ACTION',
                    data: actionData
                }, '*');
            }
            
            // 监听点击事件
            document.addEventListener('click', function(e) {
                recordAction('click', e.target);
            }, true);
            
            // 监听输入事件
            document.addEventListener('input', function(e) {
                if (e.target.value) {
                    recordAction('fill', e.target, { value: e.target.value });
                }
            }, true);
            
            // 监听选择变化
            document.addEventListener('change', function(e) {
                if (e.target.tagName.toLowerCase() === 'select') {
                    recordAction('select', e.target, { 
                        value: e.target.value,
                        selectedText: e.target.options[e.target.selectedIndex].text
                    });
                } else if (e.target.type === 'checkbox') {
                    recordAction(e.target.checked ? 'check' : 'uncheck', e.target);
                } else if (e.target.type === 'radio') {
                    recordAction('check', e.target, { value: e.target.value });
                }
            }, true);
            
            // 监听键盘事件
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && e.target.tagName.toLowerCase() === 'input') {
                    recordAction('press', e.target, { key: 'Enter' });
                }
            }, true);
            
            console.log('用户交互监听器已注入');
        })();
        '''
        
        await self.page.add_init_script(js_code)
        
        # 监听来自页面的消息
        async def handle_page_message(message):
            if isinstance(message.args, list) and len(message.args) > 0:
                try:
                    data = await message.args[0].json_value()
                    if data.get('type') == 'PLAYWRIGHT_ACTION':
                        await self._record_page_action(data['data'])
                except Exception as e:
                    logger.debug(f"处理页面消息失败: {e}")
        
        self.page.on("console", handle_page_message)
    
    async def _record_page_action(self, action_data: Dict):
        """记录来自页面的用户操作"""
        try:
            # 创建操作记录
            action_record = ActionRecord(
                id=str(uuid.uuid4()),
                session_id=self.session.id,
                action_type=action_data['action'],
                timestamp=datetime.fromtimestamp(action_data['timestamp'] / 1000),
                element_info=action_data['element'],
                page_url=action_data['url'],
                page_title=action_data['title'],
                additional_data=action_data.get('value', '')
            )
            
            # 自动截图
            if settings.ENABLE_SCREENSHOTS:
                screenshot_path = await self._take_screenshot(
                    f"step_{len(self.session.actions) + 1}_{action_data['action']}"
                )
                action_record.screenshot_path = screenshot_path
            
            # 提取页面文本
            if settings.ENABLE_TEXT_EXTRACTION:
                page_text = await self._extract_page_text()
                action_record.page_text = page_text
            
            self.session.actions.append(action_record)
            
            # 通知监听器
            await self._notify_listeners('action_recorded', action_record)
            
            logger.debug(f"记录操作: {action_data['action']} on {action_data['element']['tagName']}")
            
        except Exception as e:
            logger.error(f"记录操作失败: {e}")
    
    async def _record_action(self, action_type: str, data: Dict):
        """记录系统级操作（如导航）"""
        try:
            action_record = ActionRecord(
                id=str(uuid.uuid4()),
                session_id=self.session.id,
                action_type=action_type,
                timestamp=datetime.now(),
                page_url=data.get('url', ''),
                page_title=data.get('title', ''),
                additional_data=json.dumps(data)
            )
            
            self.session.actions.append(action_record)
            await self._notify_listeners('action_recorded', action_record)
            
        except Exception as e:
            logger.error(f"记录系统操作失败: {e}")
    
    async def _take_screenshot(self, name: str) -> str:
        """截取当前页面截图"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"{timestamp}_{name}.png"
            screenshot_path = settings.SCREENSHOTS_DIR / filename
            
            await self.page.screenshot(
                path=screenshot_path,
                quality=settings.SCREENSHOT_QUALITY,
                full_page=True
            )
            
            return str(screenshot_path)
            
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return ""
    
    async def _extract_page_text(self) -> str:
        """提取当前页面的文本内容"""
        try:
            # 提取主要文本内容，排除脚本和样式
            page_text = await self.page.evaluate('''
                () => {
                    // 移除script和style元素
                    const scripts = document.querySelectorAll('script, style');
                    scripts.forEach(el => el.remove());
                    
                    // 获取body文本，保留基本结构
                    const bodyText = document.body ? document.body.innerText : '';
                    return bodyText.trim();
                }
            ''')
            
            return page_text[:2000]  # 限制长度
            
        except Exception as e:
            logger.error(f"提取页面文本失败: {e}")
            return ""
    
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
    
    async def _remove_page_listeners(self):
        """移除页面事件监听器"""
        # Playwright会在页面关闭时自动清理监听器
        pass
    
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
    
    def add_listener(self, listener: Callable):
        """添加事件监听器"""
        self._listeners.append(listener)
    
    def remove_listener(self, listener: Callable):
        """移除事件监听器"""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    async def navigate_to(self, url: str):
        """导航到指定URL"""
        if not self.page:
            raise ValueError("页面未初始化")
        
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            logger.info(f"导航到: {url}")
        except Exception as e:
            logger.error(f"导航失败: {e}")
            raise
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.is_recording:
                await self.stop_recording()
            
            if self.context:
                await self.context.close()
            
            if self.browser:
                await self.browser.close()
            
            if self.playwright:
                await self.playwright.stop()
            
            logger.info("录制器资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")


# 全局录制器实例
recorder = TestRecorder() 