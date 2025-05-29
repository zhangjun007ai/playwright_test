import asyncio
import json
import time
import platform
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import uuid
import traceback

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from loguru import logger

from config.settings import settings
from core.models import TestSession, ActionRecord

# Windows环境下设置事件循环策略
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

class EnhancedTestRecorder:
    """增强版测试录制器 - 解决Windows兼容性问题"""
    
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
            logger.info("正在启动增强录制器...")
            
            # 创建新的事件循环（如果需要）
            try:
                loop = asyncio.get_running_loop()
                logger.info(f"使用现有事件循环: {type(loop).__name__}")
            except RuntimeError:
                logger.info("创建新的事件循环")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # 启动Playwright
            logger.info("正在启动Playwright...")
            self.playwright = await async_playwright().start()
            logger.info("Playwright启动成功")
            
            # 启动浏览器
            logger.info("正在启动浏览器...")
            self.browser = await self.playwright.chromium.launch(
                headless=False,
                slow_mo=100,
                args=['--no-sandbox', '--disable-dev-shm-usage']  # 增加稳定性
            )
            logger.info("浏览器启动成功")
            
            # 创建上下文
            logger.info("正在创建浏览器上下文...")
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            logger.info("浏览器上下文创建成功")
            
            # 创建页面
            logger.info("正在创建页面...")
            self.page = await self.context.new_page()
            logger.info("页面创建成功")
            
            logger.info("增强录制器初始化完成")
            
        except Exception as e:
            logger.error(f"增强录制器初始化失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.error(f"错误详情: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            await self._cleanup_resources()
            raise Exception(f"增强录制器初始化失败: {type(e).__name__}: {str(e)}")
    
    async def start_recording(self, test_name: str, description: str = "") -> str:
        """开始录制测试用例"""
        try:
            if self.is_recording:
                raise ValueError("录制已在进行中")
            
            logger.info(f"准备开始录制: {test_name}")
            
            if not self.page:
                logger.info("页面未初始化，正在初始化...")
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
            logger.info("设置页面事件监听...")
            await self._setup_page_listeners()
            
            logger.info(f"开始录制测试用例: {test_name} (ID: {session_id})")
            
            return session_id
            
        except Exception as e:
            logger.error(f"开始录制失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.error(f"错误详情: {str(e)}")
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise Exception(f"开始录制失败: {type(e).__name__}: {str(e)}")
    
    async def _setup_page_listeners(self):
        """设置页面事件监听器"""
        if not self.page:
            return
        
        # 监听页面导航
        async def on_response(response):
            if response.request.resource_type == "document":
                await self._record_action("navigation", {
                    "url": response.url,
                    "status": response.status,
                    "method": response.request.method
                })
        
        # 监听控制台消息
        async def on_console(message):
            if message.text.startswith('PLAYWRIGHT_ACTION:'):
                try:
                    action_json = message.text.replace('PLAYWRIGHT_ACTION:', '')
                    action_data = json.loads(action_json)
                    await self._record_page_action(action_data)
                except Exception as e:
                    logger.debug(f"处理页面消息失败: {e}")
        
        # 注册监听器
        self.page.on("response", on_response)
        self.page.on("console", on_console)
        
        # 注入JavaScript监听用户交互
        await self._inject_interaction_listeners()
    
    async def _inject_interaction_listeners(self):
        """注入JavaScript代码监听用户交互"""
        js_code = """
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
                if (id) selector = '#' + id;
                else if (className) selector = '.' + className.split(' ')[0];
                else if (name) selector = '[name="' + name + '"]';
                else if (placeholder) selector = '[placeholder="' + placeholder + '"]';
                
                return {
                    tagName: tagName,
                    id: id,
                    className: className,
                    text: text,
                    value: value,
                    placeholder: placeholder,
                    name: name,
                    type: type,
                    selector: selector,
                    position: { x: rect.left, y: rect.top },
                    size: { width: rect.width, height: rect.height }
                };
            }
            
            function recordAction(action, element, additionalData) {
                actionCount++;
                const elementInfo = getElementInfo(element);
                const actionData = {
                    action: action,
                    timestamp: Date.now(),
                    actionCount: actionCount,
                    element: elementInfo,
                    url: window.location.href,
                    title: document.title
                };
                
                if (additionalData) {
                    Object.assign(actionData, additionalData);
                }
                
                // 发送到Python后端
                console.log('PLAYWRIGHT_ACTION:' + JSON.stringify(actionData));
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
        """
        
        await self.page.add_init_script(js_code)
    
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
                additional_data=action_data.get('value', '') or json.dumps({
                    k: v for k, v in action_data.items() 
                    if k not in ['action', 'timestamp', 'element', 'url', 'title']
                })
            )
            
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
                page_title=await self.page.title() if self.page else '',
                additional_data=json.dumps(data)
            )
            
            self.session.actions.append(action_record)
            await self._notify_listeners('action_recorded', action_record)
            
        except Exception as e:
            logger.error(f"记录系统操作失败: {e}")
    
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
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.is_recording:
                await self.stop_recording()
            
            await self._cleanup_resources()
            
            logger.info("增强录制器资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")


# 全局增强录制器实例
enhanced_recorder = EnhancedTestRecorder() 