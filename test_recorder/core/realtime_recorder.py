#!/usr/bin/env python3
import json
import time
import threading
import asyncio
import queue
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import uuid
import tempfile
import os

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger

from config.settings import settings
from core.models import TestSession, ActionRecord
from core.playwright_analyzer import playwright_analyzer
from core.code_generator import code_generator


class RealtimeTestRecorder:
    """实时测试录制器 - 基础版本，专注于单窗口稳定录制"""
    
    def __init__(self):
        self.session: Optional[TestSession] = None
        self.is_recording = False
        self.action_count = 0
        
        # 事件监听器存储
        self._listeners: List[Callable] = []
        
        # Playwright相关
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # 异步事件循环
        self.loop = None
        self.recording_thread: Optional[threading.Thread] = None
        
        # 消息队列用于线程间通信
        self.message_queue = queue.Queue()
        
        # 临时目录
        self.temp_dir = Path(tempfile.mkdtemp(prefix="realtime_recorder_"))
        
    def initialize(self):
        """初始化录制器"""
        try:
            logger.info("正在启动实时录制器...")
            
            # 创建临时目录
            self.temp_dir.mkdir(exist_ok=True)
            
            logger.info("实时录制器初始化完成")
            
        except Exception as e:
            logger.error(f"实时录制器初始化失败: {e}")
            raise
    
    def start_recording(self, test_name: str, description: str = "") -> str:
        """开始录制测试用例"""
        try:
            if self.is_recording:
                raise ValueError("录制已在进行中")
            
            logger.info(f"准备开始录制: {test_name}")
            
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
            
            # 启动录制线程
            self.recording_thread = threading.Thread(
                target=self._run_recording_loop,
                daemon=True
            )
            self.recording_thread.start()
            
            logger.info(f"开始录制测试用例: {test_name} (ID: {session_id})")
            
            return session_id
            
        except Exception as e:
            logger.error(f"开始录制失败: {e}")
            raise Exception(f"开始录制失败: {str(e)}")
    
    def _run_recording_loop(self):
        """在独立线程中运行异步录制循环"""
        try:
            # 设置Windows事件循环策略
            if os.name == 'nt':
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
            # 创建新的事件循环
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # 运行录制
            self.loop.run_until_complete(self._async_recording())
            
        except Exception as e:
            logger.error(f"录制循环异常: {e}")
        finally:
            if self.loop:
                self.loop.close()
    
    async def _async_recording(self):
        """异步录制主逻辑"""
        try:
            logger.info("启动异步录制...")
            
            # 启动Playwright
            self.playwright = await async_playwright().start()
            
            # 启动浏览器
            self.browser = await self.playwright.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )
            
            # 创建上下文
            self.context = await self.browser.new_context(
                viewport=None,  # 使用全屏
                record_video_dir=str(self.temp_dir / "videos"),
                record_video_size={"width": 1280, "height": 720}
            )
            
            # 开始trace
            await self.context.tracing.start(
                screenshots=True,
                snapshots=True,
                sources=True
            )
            
            # 创建页面
            self.page = await self.context.new_page()
            
            # 设置基础事件监听器
            await self._setup_basic_event_listeners()
            
            # 导航到起始页面
            await self.page.goto("about:blank")
            
            # 记录初始导航
            await self._record_action(
                action_type="goto",
                url="about:blank",
                title="浏览器已启动",
                description="录制开始，浏览器已准备就绪",
                element_info={"type": "navigation", "url": "about:blank"}
            )
            
            logger.info("浏览器已启动，基础录制功能已激活，等待用户操作...")
            
            # 保持录制状态直到停止
            while self.is_recording:
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"异步录制失败: {e}")
            raise
    
    async def _setup_basic_event_listeners(self):
        """设置基础事件监听器"""
        try:
            # 监听页面导航
            self.page.on("framenavigated", self._on_navigation)
            
            # 监听页面加载
            self.page.on("load", self._on_page_load)
            
            # 监听控制台消息
            self.page.on("console", self._on_console)
            
            # 注入基础事件监听脚本
            await self._inject_basic_event_script()
            
            logger.info("基础事件监听器设置完成")
            
        except Exception as e:
            logger.error(f"设置事件监听器失败: {e}")
    
    async def _inject_basic_event_script(self):
        """注入基础的事件监听脚本"""
        script = """
        (function() {
            if (window.playwrightRecorderInjected) {
                return 'already_injected';
            }
            
            window.playwrightRecorderInjected = true;
            
            console.log('RECORDER_DEBUG: 注入基础事件监听器');
            
            // 输入防抖处理
            const inputTimers = new Map();
            const INPUT_DELAY = 1000; // 1秒防抖延迟
            
            // 基础事件记录函数
            function recordEvent(eventType, element, eventData = {}) {
                try {
                    const elementInfo = {
                        tag: element ? element.tagName.toLowerCase() : '',
                        id: element ? element.id || '' : '',
                        class: element ? element.className || '' : '',
                        text: element ? (element.innerText || element.textContent || '').substring(0, 50) : '',
                        type: element ? element.type || '' : '',
                        name: element ? element.name || '' : '',
                        value: element ? element.value || '' : ''
                    };
                    
                    const pageInfo = {
                        url: window.location.href,
                        title: document.title
                    };
                    
                    const eventPayload = {
                        eventType: eventType,
                        element: elementInfo,
                        page: pageInfo,
                        eventData: eventData,
                        timestamp: Date.now()
                    };
                    
                    console.log('RECORDER_EVENT:' + eventType + ':' + JSON.stringify(eventPayload));
                    
                } catch (error) {
                    console.error('RECORDER_DEBUG: 事件记录失败:', error);
                }
            }
            
            // 防抖输入记录函数
            function recordInputWithDebounce(element) {
                const elementKey = element.id || element.name || element.tagName + '_' + element.type;
                
                // 清除之前的定时器
                if (inputTimers.has(elementKey)) {
                    clearTimeout(inputTimers.get(elementKey));
                }
                
                // 设置新的定时器
                const timer = setTimeout(() => {
                    const isPassword = element.type === 'password';
                    recordEvent('input', element, {
                        value: isPassword ? '***' : element.value,
                        finalInput: true
                    });
                    inputTimers.delete(elementKey);
                }, INPUT_DELAY);
                
                inputTimers.set(elementKey, timer);
            }
            
            // 点击事件
            document.addEventListener('click', function(event) {
                recordEvent('click', event.target, {
                    clientX: event.clientX,
                    clientY: event.clientY,
                    button: event.button
                });
            }, true);
            
            // 输入事件（使用防抖）
            document.addEventListener('input', function(event) {
                recordInputWithDebounce(event.target);
            }, true);
            
            // 失焦事件（确保记录最终输入）
            document.addEventListener('blur', function(event) {
                const element = event.target;
                if (element.tagName && ['INPUT', 'TEXTAREA'].includes(element.tagName.toLowerCase())) {
                    const elementKey = element.id || element.name || element.tagName + '_' + element.type;
                    
                    // 清除防抖定时器并立即记录
                    if (inputTimers.has(elementKey)) {
                        clearTimeout(inputTimers.get(elementKey));
                        inputTimers.delete(elementKey);
                    }
                    
                    // 立即记录最终值
                    const isPassword = element.type === 'password';
                    if (element.value) {  // 只有非空值才记录
                        recordEvent('input', element, {
                            value: isPassword ? '***' : element.value,
                            finalInput: true,
                            trigger: 'blur'
                        });
                    }
                }
            }, true);
            
            // 键盘事件
            document.addEventListener('keydown', function(event) {
                if (['Enter', 'Tab', 'Escape'].includes(event.key)) {
                    recordEvent('keydown', event.target, {
                        key: event.key
                    });
                    
                    // 如果是Enter键在输入框中，立即记录输入值
                    if (event.key === 'Enter') {
                        const element = event.target;
                        if (element.tagName && ['INPUT', 'TEXTAREA'].includes(element.tagName.toLowerCase())) {
                            const elementKey = element.id || element.name || element.tagName + '_' + element.type;
                            
                            // 清除防抖定时器
                            if (inputTimers.has(elementKey)) {
                                clearTimeout(inputTimers.get(elementKey));
                                inputTimers.delete(elementKey);
                            }
                            
                            // 立即记录
                            const isPassword = element.type === 'password';
                            if (element.value) {
                                recordEvent('input', element, {
                                    value: isPassword ? '***' : element.value,
                                    finalInput: true,
                                    trigger: 'enter'
                                });
                            }
                        }
                    }
                }
            }, true);
            
            // 表单提交
            document.addEventListener('submit', function(event) {
                recordEvent('submit', event.target, {
                    action: event.target.action || ''
                });
            }, true);
            
            // 选择改变
            document.addEventListener('change', function(event) {
                let changeData = { value: event.target.value || '' };
                
                if (event.target.tagName.toLowerCase() === 'select') {
                    const selectedOption = event.target.options[event.target.selectedIndex];
                    changeData.selectedText = selectedOption ? selectedOption.text : '';
                }
                
                recordEvent('change', event.target, changeData);
            }, true);
            
            console.log('RECORDER_DEBUG: 基础事件监听器注入完成（支持输入防抖）');
            
        })();
        """
        
        try:
            await self.page.add_init_script(script)
            await self.page.evaluate(script)
            logger.debug("基础事件监听脚本注入成功（支持输入防抖）")
        except Exception as e:
            logger.error(f"注入事件监听脚本失败: {e}")
    
    def _on_navigation(self, frame):
        """处理页面导航事件"""
        try:
            if frame == self.page.main_frame:
                url = frame.url
                logger.info(f"页面导航到: {url}")
                
                # 重新注入事件监听器
                asyncio.create_task(self._inject_basic_event_script())
                
                asyncio.create_task(self._record_action(
                    action_type="goto",
                    url=url,
                    title=f"导航到: {url}",
                    description=f"页面导航到: {url}",
                    element_info={"type": "navigation", "url": url}
                ))
        except Exception as e:
            logger.error(f"处理导航事件失败: {e}")
    
    def _on_page_load(self, page):
        """处理页面加载事件"""
        try:
            url = page.url
            logger.info(f"页面加载完成: {url}")
            
            # 重新注入事件监听器
            asyncio.create_task(self._inject_basic_event_script())
            
        except Exception as e:
            logger.error(f"处理页面加载事件失败: {e}")
    
    def _on_console(self, msg):
        """处理控制台消息"""
        try:
            text = msg.text
            
            # 处理录制器事件
            if text.startswith('RECORDER_EVENT:'):
                try:
                    parts = text.split(':', 2)
                    if len(parts) >= 3:
                        event_type = parts[1]
                        event_data_str = parts[2]
                        event_data = json.loads(event_data_str)
                        
                        # 异步处理事件
                        if self.loop:
                            asyncio.run_coroutine_threadsafe(
                                self._record_browser_action(event_type, event_data),
                                self.loop
                            )
                        
                except json.JSONDecodeError as e:
                    logger.error(f"解析事件数据失败: {e}")
                except Exception as e:
                    logger.error(f"处理录制器事件失败: {e}")
            
            # 处理调试信息
            elif text.startswith('RECORDER_DEBUG:'):
                logger.debug(f"录制器调试: {text}")
                
        except Exception as e:
            logger.error(f"处理控制台消息失败: {e}")
    
    async def _record_browser_action(self, event_type: str, event_data: Dict):
        """记录浏览器操作事件"""
        try:
            element_info = event_data.get('element', {})
            page_info = event_data.get('page', {})
            additional_data = event_data.get('eventData', {})
            
            # 使用Playwright分析器分析元素
            analyzed_element = playwright_analyzer.analyze_element(element_info)
            
            # 生成友好的描述
            element_desc = self._get_element_description(analyzed_element, element_info)
            
            if event_type == 'click':
                title = f"点击: {element_desc}"
                description = f"点击了 {element_desc}"
            elif event_type == 'input':
                value = additional_data.get('value', '')
                title = f"输入文本: {value[:20]}{'...' if len(value) > 20 else ''}"
                description = f"在 {element_desc} 中输入: {value}"
            elif event_type == 'keydown':
                key = additional_data.get('key', '')
                title = f"按键: {key}"
                description = f"在 {element_desc} 中按下 {key} 键"
            elif event_type == 'change':
                selected_text = additional_data.get('selectedText', '')
                if selected_text:
                    title = f"选择选项: {selected_text}"
                    description = f"在下拉框中选择: {selected_text}"
                else:
                    title = f"修改值: {additional_data.get('value', '')}"
                    description = f"修改 {element_desc} 的值"
            elif event_type == 'submit':
                title = "提交表单"
                description = "提交表单"
            else:
                title = f"执行操作: {event_type}"
                description = f"执行了 {event_type} 操作"
            
            await self._record_action(
                action_type=event_type,
                url=page_info.get('url', ''),
                title=title,
                description=description,
                element_info=element_info,
                additional_data=event_data,
                analyzed_element=analyzed_element
            )
            
        except Exception as e:
            logger.error(f"记录浏览器操作失败: {e}")
    
    def _get_element_description(self, analyzed_element: Dict, element_info: Dict) -> str:
        """生成元素描述"""
        try:
            # 优先使用分析结果
            if analyzed_element and analyzed_element.get('text'):
                text = analyzed_element['text'].strip()
                if text:
                    return f"'{text[:30]}...'" if len(text) > 30 else f"'{text}'"
            
            # 使用基本信息
            element_id = element_info.get('id', '')
            if element_id:
                return f"ID为'{element_id}'的元素"
            
            element_class = element_info.get('class', '')
            if element_class:
                main_class = element_class.split(' ')[0]
                return f"类名为'{main_class}'的元素"
            
            element_text = element_info.get('text', '')
            if element_text:
                return f"'{element_text[:20]}...'" if len(element_text) > 20 else f"'{element_text}'"
            
            # 对于输入框，使用更友好的描述
            tag_name = element_info.get('tag', '').lower()
            element_type = element_info.get('type', '').lower()
            element_name = element_info.get('name', '')
            
            if tag_name == 'input':
                if element_type == 'password':
                    return '密码输入框'
                elif element_type == 'email':
                    return '邮箱输入框'
                elif element_type == 'text' or element_type == '':
                    return '文本输入框'
                elif element_type == 'search':
                    return '搜索框'
                elif element_type == 'tel':
                    return '电话输入框'
                else:
                    return f'{element_type}输入框'
            elif tag_name == 'textarea':
                return '文本区域'
            elif tag_name == 'select':
                return '下拉选择框'
            elif tag_name == 'button':
                return '按钮'
            elif tag_name == 'a':
                return '链接'
            
            # 如果有name属性，使用name
            if element_name:
                return f"名为'{element_name}'的{tag_name}元素"
            
            # 最后的备选方案
            if tag_name:
                return f'{tag_name.upper()}元素'
            
            return "未知元素"
            
        except Exception:
            return "未知元素"
    
    async def _record_action(self, action_type: str, url: str = "", title: str = "", 
                           description: str = "", element_info: Dict = None, 
                           additional_data: Dict = None, analyzed_element: Dict = None):
        """记录操作"""
        try:
            if not self.session:
                return
            
            # 截图
            screenshot_path = ""
            try:
                screenshot_filename = f"screenshot_{len(self.session.actions) + 1}_{int(time.time())}.png"
                screenshot_path = str(settings.SCREENSHOTS_DIR / screenshot_filename)
                await self.page.screenshot(path=screenshot_path, full_page=True)
            except Exception as e:
                logger.warning(f"截图失败: {e}")
            
            # 创建操作记录
            action_record = ActionRecord(
                id=str(uuid.uuid4()),
                session_id=self.session.id,
                action_type=action_type,
                timestamp=datetime.now(),
                page_url=url,
                page_title=title,
                element_info=element_info or {},
                description=description,
                screenshot_path=screenshot_path,
                additional_data=json.dumps(additional_data or {})
            )
            
            self.session.actions.append(action_record)
            self.action_count += 1
            
            # 生成Playwright代码
            playwright_code = code_generator.generate_action_code(action_record)
            
            # 添加到消息队列
            self.message_queue.put(('action_recorded', {
                'action_record': action_record,
                'playwright_code': playwright_code,
                'analyzed_element': analyzed_element
            }))
            
            logger.info(f"记录操作: {action_type} - {title}")
            logger.info(f"Playwright代码: {playwright_code}")
            
        except Exception as e:
            logger.error(f"记录操作失败: {e}")
    
    def stop_recording(self) -> TestSession:
        """停止录制并保存结果"""
        try:
            if not self.is_recording or not self.session:
                raise ValueError("当前没有正在进行的录制")
            
            logger.info("正在停止录制...")
            
            self.is_recording = False
            
            # 等待录制线程结束
            if self.recording_thread and self.recording_thread.is_alive():
                logger.info("等待录制线程结束...")
                self.recording_thread.join(timeout=10)
            
            # 在异步上下文中清理资源
            if self.loop and not self.loop.is_closed():
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        self._cleanup_async_resources(), 
                        self.loop
                    )
                    future.result(timeout=10)
                    logger.info("异步资源清理完成")
                except Exception as e:
                    logger.error(f"清理异步资源失败: {e}")
                finally:
                    if not self.loop.is_closed():
                        self.loop.call_soon_threadsafe(self.loop.stop)
                        time.sleep(1)
            
            # 更新会话状态
            self.session.end_time = datetime.now()
            self.session.status = "completed"
            
            # 保存会话数据
            self._save_session()
            
            # 生成完整的Playwright代码
            self._generate_full_playwright_code()
            
            # 通知监听器
            self._notify_listeners("recording_stopped", self.session)
            
            logger.info(f"录制完成: {self.session.name} (总操作数: {len(self.session.actions)})")
            
            return self.session
            
        except Exception as e:
            logger.error(f"停止录制失败: {e}")
            raise Exception(f"停止录制失败: {str(e)}")
    
    def _generate_full_playwright_code(self):
        """生成完整的Playwright代码文件"""
        try:
            if not self.session or not self.session.actions:
                return
            
            # 生成完整代码
            full_code = code_generator.generate_test_code(
                self.session.actions, 
                self.session.name
            )
            
            # 保存代码文件
            code_filename = f"{self.session.id}_playwright_code.py"
            code_path = settings.RECORDINGS_DIR / code_filename
            
            with open(code_path, 'w', encoding='utf-8') as f:
                f.write(full_code)
            
            logger.info(f"Playwright代码已保存: {code_path}")
            
        except Exception as e:
            logger.error(f"生成Playwright代码失败: {e}")
    
    async def _cleanup_async_resources(self):
        """清理异步资源"""
        try:
            if self.context:
                try:
                    # 停止trace
                    trace_path = self.temp_dir / "trace.zip"
                    await self.context.tracing.stop(path=str(trace_path))
                except Exception as e:
                    logger.error(f"停止trace失败: {e}")
                
                try:
                    # 关闭上下文
                    await self.context.close()
                except Exception as e:
                    logger.error(f"关闭上下文失败: {e}")
                finally:
                    self.context = None
            
            if self.browser:
                try:
                    await self.browser.close()
                except Exception as e:
                    logger.error(f"关闭浏览器失败: {e}")
                finally:
                    self.browser = None
            
            if self.playwright:
                try:
                    await self.playwright.stop()
                except Exception as e:
                    logger.error(f"停止Playwright失败: {e}")
                finally:
                    self.playwright = None
                    
            logger.info("异步资源清理完成")
            
        except Exception as e:
            logger.error(f"清理异步资源失败: {e}")
            raise
    
    def _save_session(self):
        """保存会话数据到文件"""
        try:
            session_file = settings.RECORDINGS_DIR / f"{self.session.id}_session.json"
            session_data = self.session.dict()
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"会话数据已保存: {session_file}")
            
        except Exception as e:
            logger.error(f"保存会话数据失败: {e}")
    
    def get_message_queue(self) -> queue.Queue:
        """获取消息队列"""
        return self.message_queue
    
    def add_listener(self, listener: Callable):
        """添加事件监听器"""
        self._listeners.append(listener)
    
    def remove_listener(self, listener: Callable):
        """移除事件监听器"""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    def _notify_listeners(self, event_type: str, data: Any):
        """通知事件监听器"""
        logger.debug(f"通知监听器: {event_type}")
        for listener in self._listeners:
            try:
                listener(event_type, data)
            except Exception as e:
                logger.error(f"监听器回调失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.is_recording:
                self.stop_recording()
            
            # 清理临时文件
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            
            logger.info("实时录制器资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")


# 全局实时录制器实例
realtime_recorder = RealtimeTestRecorder() 