#!/usr/bin/env python3
import json
import time
import threading
import asyncio
import queue
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Tuple
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
    """实时测试录制器 - 支持多窗口录制"""
    
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
        
        # 多窗口管理
        self.pages: Dict[str, Page] = {}  # 存储所有活跃的页面，key为页面ID
        self.page_counter = 0  # 页面计数器，用于生成唯一标识
        
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
            self.pages["main"] = self.page
            self.page_counter += 1
            
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
            self.page.on("framenavigated", lambda frame: self._on_navigation(frame))
            
            # 监听页面加载
            self.page.on("load", lambda page: self._on_page_load(page))
            
            # 监听控制台消息
            self.page.on("console", self._on_console)
            
            # 监听上下文级别的新页面事件（包括弹窗）
            self.context.on("page", self._on_context_page)
            
            # 注入基础事件监听脚本
            await self._inject_basic_event_script()
            
            logger.info("基础事件监听器设置完成，已启用多窗口录制支持")
            
        except Exception as e:
            logger.error(f"设置事件监听器失败: {e}")

    def _on_context_page(self, new_page):
        """处理上下文级别的新页面事件（包括弹窗和新标签页）"""
        try:
            logger.info(f"检测到新页面: {new_page.url}")
            asyncio.create_task(self._setup_popup_listeners(new_page))
        except Exception as e:
            logger.error(f"处理新页面事件失败: {e}")

    async def _setup_popup_listeners(self, popup_page):
        """为新窗口设置事件监听器"""
        try:
            page_id = f"page_{self.page_counter}"
            self.page_counter += 1
            self.pages[page_id] = popup_page
            
            # 监听页面导航
            popup_page.on("framenavigated", lambda frame: self._on_navigation(frame))
            
            # 监听页面加载
            popup_page.on("load", lambda page: self._on_page_load(page))
            
            # 监听控制台消息
            popup_page.on("console", self._on_console)
            
            # 监听页面关闭
            popup_page.on("close", lambda: self._on_page_close(page_id))
            
            # 注入基础事件监听脚本
            await self._inject_basic_event_script_to_page(popup_page)
            
            logger.info(f"为新页面 {page_id} 设置了事件监听器")
        except Exception as e:
            logger.error(f"为新页面设置事件监听器失败: {e}")

    def _on_page_close(self, page_id):
        """处理页面关闭事件"""
        try:
            logger.info(f"页面 {page_id} 已关闭")
            if page_id in self.pages:
                del self.pages[page_id]
        except Exception as e:
            logger.error(f"处理页面关闭事件失败: {e}")

    async def _inject_basic_event_script_to_page(self, page):
        """向指定页面注入基础的事件监听脚本"""
        script = r"""
        (function() {
            if (window.playwrightRecorderInjected) {
                return 'already_injected';
            }
            
            window.playwrightRecorderInjected = true;
            
            console.log('RECORDER_DEBUG: 注入基础事件监听器');
            
            // 输入防抖处理
            const inputTimers = new Map();
            const INPUT_DELAY = 1000; // 1秒防抖延迟
            
            // 清理标签文本
            function cleanLabelText(text) {
                if (!text) return '';
                
                // 移除前后空格
                text = text.trim();
                
                // 移除前面的星号（支持各种星号字符）
                text = text.replace(/^[*＊※●⚫︎⬤⏺⭐️★☆✱✲✳✴✵✶✷✸✹✺✻✼✽✾✿❀❁❂❃❄❅❆❇❈❉❊❋⁎⁑⁂⁕﹡]\s*/g, '');
                
                // 移除前面的数字序号（如：1.、1、等）
                text = text.replace(/^[\d一二三四五六七八九十]+[.、．。:：]\s*/g, '');
                
                // 移除末尾的冒号和空格
                text = text.replace(/[：:]*\s*$/g, '');
                
                // 如果文本被括号包围，移除括号
                text = text.replace(/^[([{（【［｛](.+?)[)\]}）】］｝]$/g, '$1');
                
                // 移除常见的表单前缀词
                const prefixes = ['请输入', '请选择', '输入', '选择', '填写'];
                for (let prefix of prefixes) {
                    if (text.startsWith(prefix)) {
                        text = text.substring(prefix.length);
                    }
                }
                
                return text.trim();
            }
            
            // 获取输入框关联的标签文本
            function getInputLabel(element) {
                let labelText = '';
                let labels = [];
                
                // 特殊处理图标元素
                if (element.classList && Array.from(element.classList).some(cls => cls.includes('glyphicon'))) {
                    // 方法1: 检查title属性
                    if (element.title) {
                        labels.push(element.title);
                    }
                    
                    // 方法2: 检查aria-label属性
                    if (element.getAttribute('aria-label')) {
                        labels.push(element.getAttribute('aria-label'));
                    }
                    
                    // 方法3: 检查父元素的文本内容
                    let parent = element.parentElement;
                    if (parent) {
                        // 克隆父元素以防止修改原始DOM
                        const parentClone = parent.cloneNode(true);
                        // 移除所有图标元素
                        parentClone.querySelectorAll('.glyphicon').forEach(icon => icon.remove());
                        const parentText = parentClone.innerText || parentClone.textContent;
                        if (parentText.trim()) {
                            labels.push(parentText.trim());
                        }
                    }
                    
                    // 方法4: 使用图标类名映射
                    const iconClassMap = {
                        'glyphicon-refresh': '刷新',
                        'glyphicon-search': '搜索',
                        'glyphicon-plus': '添加',
                        'glyphicon-minus': '删除',
                        'glyphicon-edit': '编辑',
                        'glyphicon-trash': '删除',
                        'glyphicon-ok': '确定',
                        'glyphicon-remove': '取消',
                        'glyphicon-save': '保存',
                        'glyphicon-print': '打印',
                        'glyphicon-download': '下载',
                        'glyphicon-upload': '上传',
                        'glyphicon-export': '导出',
                        'glyphicon-import': '导入'
                    };
                    
                    for (const className of element.classList) {
                        if (iconClassMap[className]) {
                            labels.push(iconClassMap[className]);
                            break;
                        }
                    }
                }
                
                // 原有的标签文本查找逻辑
                // 方法1: 查找前面的所有文本节点和元素
                function findPrecedingText(element) {
                    const textsFound = [];
                    
                    // 获取所有前面的兄弟节点
                    let previousNode = element.previousSibling;
                    while (previousNode) {
                        // 如果是文本节点
                        if (previousNode.nodeType === 3) {
                            const text = previousNode.textContent.trim();
                            if (text) textsFound.unshift(text);
                        }
                        // 如果是元素节点
                        else if (previousNode.nodeType === 1) {
                            const nodeName = previousNode.nodeName.toLowerCase();
                            // 如果是label或常见的文本容器元素
                            if (['label', 'span', 'div', 'p', 'td', 'th'].includes(nodeName)) {
                                const text = previousNode.innerText || previousNode.textContent;
                                if (text.trim()) textsFound.unshift(text.trim());
                            }
                        }
                        previousNode = previousNode.previousSibling;
                    }
                    
                    // 如果在兄弟节点中没找到，尝试查找父元素的前面的文本
                    if (textsFound.length === 0 && element.parentElement) {
                        let parent = element.parentElement;
                        let foundInParent = false;
                        
                        // 检查父元素的前面的兄弟节点
                        previousNode = parent.previousSibling;
                        while (previousNode && !foundInParent) {
                            if (previousNode.nodeType === 3) {
                                const text = previousNode.textContent.trim();
                                if (text) {
                                    textsFound.unshift(text);
                                    foundInParent = true;
                                }
                            } else if (previousNode.nodeType === 1) {
                                const text = previousNode.innerText || previousNode.textContent;
                                if (text.trim()) {
                                    textsFound.unshift(text.trim());
                                    foundInParent = true;
                                }
                            }
                            previousNode = previousNode.previousSibling;
                        }
                        
                        // 如果还没找到，检查父元素本身是否包含文本
                        if (!foundInParent) {
                            // 克隆父元素以防止修改原始DOM
                            const parentClone = parent.cloneNode(true);
                            // 移除目标输入框及其后面的所有元素
                            let found = false;
                            Array.from(parentClone.children).forEach(child => {
                                if (found || child.isEqualNode(element)) {
                                    child.remove();
                                    found = true;
                                }
                            });
                            const text = parentClone.innerText || parentClone.textContent;
                            if (text.trim()) textsFound.unshift(text.trim());
                        }
                    }
                    
                    return textsFound;
                }
                
                // 首先尝试查找前面的文本
                const precedingTexts = findPrecedingText(element);
                if (precedingTexts.length > 0) {
                    labels.push(...precedingTexts);
                }
                
                // 方法2: 通过for属性关联的label
                if (element.id) {
                    const label = document.querySelector(`label[for="${element.id}"]`);
                    if (label) {
                        labels.push(label.innerText || label.textContent || '');
                    }
                }
                
                // 方法3: 父级label元素
                const parentLabel = element.closest('label');
                if (parentLabel) {
                    const clone = parentLabel.cloneNode(true);
                    const inputs = clone.querySelectorAll('input');
                    inputs.forEach(input => input.remove());
                    labels.push(clone.innerText || clone.textContent || '');
                }
                
                // 方法4: 通过aria-label
                if (element.getAttribute('aria-label')) {
                    labels.push(element.getAttribute('aria-label'));
                }
                
                // 方法5: 通过aria-labelledby
                if (element.getAttribute('aria-labelledby')) {
                    const labelId = element.getAttribute('aria-labelledby');
                    const labelElement = document.getElementById(labelId);
                    if (labelElement) {
                        labels.push(labelElement.innerText || labelElement.textContent || '');
                    }
                }
                
                // 方法6: 查找表格中的表头
                const td = element.closest('td');
                if (td) {
                    const tr = td.closest('tr');
                    const table = td.closest('table');
                    if (tr && table) {
                        const cellIndex = Array.from(tr.children).indexOf(td);
                        const headerRow = table.querySelector('tr:first-child, thead tr');
                        if (headerRow && headerRow.children[cellIndex]) {
                            labels.push(headerRow.children[cellIndex].innerText || headerRow.children[cellIndex].textContent || '');
                        }
                    }
                }
                
                // 方法7: 通过placeholder作为备选
                if (element.placeholder) {
                    labels.push(element.placeholder);
                }
                
                // 方法8: 通过name属性作为最后备选
                if (element.name) {
                    labels.push(element.name);
                }
                
                // 处理所有找到的标签文本
                for (let text of labels) {
                    text = cleanLabelText(text);
                    // 特别处理：如果清理后的文本是中文，优先使用它
                    if (text && /[\u4e00-\u9fa5]/.test(text)) {
                        labelText = text;
                        break;
                    }
                    // 否则继续查找
                    if (text && !labelText) {
                        labelText = text;
                    }
                }
                
                // 如果没有找到任何标签文本，使用ID或name作为最后的备选
                if (!labelText) {
                    if (element.id && !/^\d+$/.test(element.id)) {
                        labelText = element.id;
                    } else if (element.name && !/^\d+$/.test(element.name)) {
                        labelText = element.name;
                    }
                }
                
                return labelText;
            }
            
            // 获取选择框的选项文本
            function getSelectOptionText(selectElement, value) {
                if (selectElement.tagName.toLowerCase() === 'select') {
                    const options = selectElement.querySelectorAll('option');
                    for (let option of options) {
                        if (option.value === value) {
                            return option.innerText || option.textContent || value;
                        }
                    }
                }
                return value;
            }
            
            // 基础事件记录函数
            function recordEvent(eventType, element, eventData = {}) {
                try {
                    const labelText = getInputLabel(element);
                    
                    const elementInfo = {
                        tag: element ? element.tagName.toLowerCase() : '',
                        id: element ? element.id || '' : '',
                        class: element ? element.className || '' : '',
                        text: element ? (element.innerText || element.textContent || '').substring(0, 50) : '',
                        type: element ? element.type || '' : '',
                        name: element ? element.name || '' : '',
                        value: element ? element.value || '' : '',
                        label: labelText,
                        placeholder: element ? element.placeholder || '' : ''
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
                // 处理 iCheck 相关元素
                if (event.target.classList.contains('iCheck-helper')) {
                    // 获取关联的 input 元素
                    const input = event.target.previousElementSibling;
                    if (input && (input.type === 'radio' || input.type === 'checkbox')) {
                        // 使用关联的 input 元素记录事件
                        recordEvent('change', input, {
                            checked: !input.checked,
                            value: input.value,
                            type: input.type
                        });
                        return;
                    }
                }
                
                // 如果是select元素或其子元素，不记录点击事件
                if (event.target.tagName.toLowerCase() === 'select' ||
                    event.target.closest('select') ||
                    event.target.tagName.toLowerCase() === 'option') {
                    return;
                }
                
                recordEvent('click', event.target, {
                    clientX: event.clientX,
                    clientY: event.clientY,
                    button: event.button
                });
            }, true);
            
            // 输入事件（使用防抖）
            document.addEventListener('input', function(event) {
                // 如果是select、radio或checkbox元素，不记录input事件
                if (event.target.tagName.toLowerCase() === 'select' ||
                    event.target.type === 'radio' ||
                    event.target.type === 'checkbox') {
                    return;
                }
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
                const target = event.target;
                if (target.tagName.toLowerCase() === 'select') {
                    const selectedOption = target.options[target.selectedIndex];
                    const selectedText = selectedOption ? (selectedOption.text || '').trim() : '';
                    const selectedValue = target.value || '';
                    
                    // 只记录一次change事件，使用显示文本
                    recordEvent('change', target, {
                        value: selectedText, // 只使用显示文本
                        selectedText: selectedText,
                        actualValue: selectedValue // 保留实际值作为备用
                    });
                } else if (target.type === 'radio' || target.type === 'checkbox') {
                    // 获取关联的标签文本
                    let labelText = '';
                    
                    // 1. 检查for属性关联的label
                    if (target.id) {
                        const label = document.querySelector(`label[for="${target.id}"]`);
                        if (label) {
                            labelText = label.textContent.trim();
                        }
                    }
                    
                    // 2. 检查父级label
                    if (!labelText) {
                        const parentLabel = target.closest('label');
                        if (parentLabel) {
                            const clone = parentLabel.cloneNode(true);
                            const inputs = clone.querySelectorAll('input');
                            inputs.forEach(input => input.remove());
                            labelText = clone.textContent.trim();
                        }
                    }
                    
                    // 3. 如果还没找到，尝试使用相邻文本
                    if (!labelText) {
                        let sibling = target.nextSibling;
                        while (sibling && !labelText) {
                            if (sibling.nodeType === 3) { // 文本节点
                                labelText = sibling.textContent.trim();
                            }
                            sibling = sibling.nextSibling;
                        }
                    }
                    
                    recordEvent('change', target, {
                        type: target.type,
                        checked: target.checked,
                        value: labelText || target.value || (target.checked ? '选中' : '取消选中'),
                        labelText: labelText
                    });
                } else {
                    // 其他元素的change事件处理
                    recordEvent('change', target, {
                        value: target.value || ''
                    });
                }
            }, true);
            
            console.log('RECORDER_DEBUG: 基础事件监听器注入完成（支持输入防抖和增强的标签识别）');
            
        })();
        """
        
        try:
            await page.add_init_script(script)
            await page.evaluate(script)
            logger.debug("基础事件监听脚本注入成功（支持输入防抖和增强的标签识别）")
        except Exception as e:
            logger.error(f"注入事件监听脚本失败: {e}")
    
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
            
            // 清理标签文本
            function cleanLabelText(text) {
                if (!text) return '';
                
                // 移除前后空格
                text = text.trim();
                
                // 移除前面的星号（支持各种星号字符）
                text = text.replace(/^[*＊※●⚫︎⬤⏺⭐️★☆✱✲✳✴✵✶✷✸✹✺✻✼✽✾✿❀❁❂❃❄❅❆❇❈❉❊❋⁎⁑⁂⁕﹡]\s*/g, '');
                
                // 移除前面的数字序号（如：1.、1、等）
                text = text.replace(/^[\d一二三四五六七八九十]+[.、．。:：]\s*/g, '');
                
                // 移除末尾的冒号和空格
                text = text.replace(/[：:]*\s*$/g, '');
                
                // 如果文本被括号包围，移除括号
                text = text.replace(/^[([{（【［｛](.+?)[)\]}）】］｝]$/g, '$1');
                
                // 移除常见的表单前缀词
                const prefixes = ['请输入', '请选择', '输入', '选择', '填写'];
                for (let prefix of prefixes) {
                    if (text.startsWith(prefix)) {
                        text = text.substring(prefix.length);
                    }
                }
                
                return text.trim();
            }
            
            // 获取输入框关联的标签文本
            function getInputLabel(element) {
                let labelText = '';
                let labels = [];
                
                // 特殊处理图标元素
                if (element.classList && Array.from(element.classList).some(cls => cls.includes('glyphicon'))) {
                    // 方法1: 检查title属性
                    if (element.title) {
                        labels.push(element.title);
                    }
                    
                    // 方法2: 检查aria-label属性
                    if (element.getAttribute('aria-label')) {
                        labels.push(element.getAttribute('aria-label'));
                    }
                    
                    // 方法3: 检查父元素的文本内容
                    let parent = element.parentElement;
                    if (parent) {
                        // 克隆父元素以防止修改原始DOM
                        const parentClone = parent.cloneNode(true);
                        // 移除所有图标元素
                        parentClone.querySelectorAll('.glyphicon').forEach(icon => icon.remove());
                        const parentText = parentClone.innerText || parentClone.textContent;
                        if (parentText.trim()) {
                            labels.push(parentText.trim());
                        }
                    }
                    
                    // 方法4: 使用图标类名映射
                    const iconClassMap = {
                        'glyphicon-refresh': '刷新',
                        'glyphicon-search': '搜索',
                        'glyphicon-plus': '添加',
                        'glyphicon-minus': '删除',
                        'glyphicon-edit': '编辑',
                        'glyphicon-trash': '删除',
                        'glyphicon-ok': '确定',
                        'glyphicon-remove': '取消',
                        'glyphicon-save': '保存',
                        'glyphicon-print': '打印',
                        'glyphicon-download': '下载',
                        'glyphicon-upload': '上传',
                        'glyphicon-export': '导出',
                        'glyphicon-import': '导入'
                    };
                    
                    for (const className of element.classList) {
                        if (iconClassMap[className]) {
                            labels.push(iconClassMap[className]);
                            break;
                        }
                    }
                }
                
                // 原有的标签文本查找逻辑
                // 方法1: 查找前面的所有文本节点和元素
                function findPrecedingText(element) {
                    const textsFound = [];
                    
                    // 获取所有前面的兄弟节点
                    let previousNode = element.previousSibling;
                    while (previousNode) {
                        // 如果是文本节点
                        if (previousNode.nodeType === 3) {
                            const text = previousNode.textContent.trim();
                            if (text) textsFound.unshift(text);
                        }
                        // 如果是元素节点
                        else if (previousNode.nodeType === 1) {
                            const nodeName = previousNode.nodeName.toLowerCase();
                            // 如果是label或常见的文本容器元素
                            if (['label', 'span', 'div', 'p', 'td', 'th'].includes(nodeName)) {
                                const text = previousNode.innerText || previousNode.textContent;
                                if (text.trim()) textsFound.unshift(text.trim());
                            }
                        }
                        previousNode = previousNode.previousSibling;
                    }
                    
                    // 如果在兄弟节点中没找到，尝试查找父元素的前面的文本
                    if (textsFound.length === 0 && element.parentElement) {
                        let parent = element.parentElement;
                        let foundInParent = false;
                        
                        // 检查父元素的前面的兄弟节点
                        previousNode = parent.previousSibling;
                        while (previousNode && !foundInParent) {
                            if (previousNode.nodeType === 3) {
                                const text = previousNode.textContent.trim();
                                if (text) {
                                    textsFound.unshift(text);
                                    foundInParent = true;
                                }
                            } else if (previousNode.nodeType === 1) {
                                const text = previousNode.innerText || previousNode.textContent;
                                if (text.trim()) {
                                    textsFound.unshift(text.trim());
                                    foundInParent = true;
                                }
                            }
                            previousNode = previousNode.previousSibling;
                        }
                        
                        // 如果还没找到，检查父元素本身是否包含文本
                        if (!foundInParent) {
                            // 克隆父元素以防止修改原始DOM
                            const parentClone = parent.cloneNode(true);
                            // 移除目标输入框及其后面的所有元素
                            let found = false;
                            Array.from(parentClone.children).forEach(child => {
                                if (found || child.isEqualNode(element)) {
                                    child.remove();
                                    found = true;
                                }
                            });
                            const text = parentClone.innerText || parentClone.textContent;
                            if (text.trim()) textsFound.unshift(text.trim());
                        }
                    }
                    
                    return textsFound;
                }
                
                // 首先尝试查找前面的文本
                const precedingTexts = findPrecedingText(element);
                if (precedingTexts.length > 0) {
                    labels.push(...precedingTexts);
                }
                
                // 方法2: 通过for属性关联的label
                if (element.id) {
                    const label = document.querySelector(`label[for="${element.id}"]`);
                    if (label) {
                        labels.push(label.innerText || label.textContent || '');
                    }
                }
                
                // 方法3: 父级label元素
                const parentLabel = element.closest('label');
                if (parentLabel) {
                    const clone = parentLabel.cloneNode(true);
                    const inputs = clone.querySelectorAll('input');
                    inputs.forEach(input => input.remove());
                    labels.push(clone.innerText || clone.textContent || '');
                }
                
                // 方法4: 通过aria-label
                if (element.getAttribute('aria-label')) {
                    labels.push(element.getAttribute('aria-label'));
                }
                
                // 方法5: 通过aria-labelledby
                if (element.getAttribute('aria-labelledby')) {
                    const labelId = element.getAttribute('aria-labelledby');
                    const labelElement = document.getElementById(labelId);
                    if (labelElement) {
                        labels.push(labelElement.innerText || labelElement.textContent || '');
                    }
                }
                
                // 方法6: 查找表格中的表头
                const td = element.closest('td');
                if (td) {
                    const tr = td.closest('tr');
                    const table = td.closest('table');
                    if (tr && table) {
                        const cellIndex = Array.from(tr.children).indexOf(td);
                        const headerRow = table.querySelector('tr:first-child, thead tr');
                        if (headerRow && headerRow.children[cellIndex]) {
                            labels.push(headerRow.children[cellIndex].innerText || headerRow.children[cellIndex].textContent || '');
                        }
                    }
                }
                
                // 方法7: 通过placeholder作为备选
                if (element.placeholder) {
                    labels.push(element.placeholder);
                }
                
                // 方法8: 通过name属性作为最后备选
                if (element.name) {
                    labels.push(element.name);
                }
                
                // 处理所有找到的标签文本
                for (let text of labels) {
                    text = cleanLabelText(text);
                    // 特别处理：如果清理后的文本是中文，优先使用它
                    if (text && /[\u4e00-\u9fa5]/.test(text)) {
                        labelText = text;
                        break;
                    }
                    // 否则继续查找
                    if (text && !labelText) {
                        labelText = text;
                    }
                }
                
                // 如果没有找到任何标签文本，使用ID或name作为最后的备选
                if (!labelText) {
                    if (element.id && !/^\d+$/.test(element.id)) {
                        labelText = element.id;
                    } else if (element.name && !/^\d+$/.test(element.name)) {
                        labelText = element.name;
                    }
                }
                
                return labelText;
            }
            
            // 获取选择框的选项文本
            function getSelectOptionText(selectElement, value) {
                if (selectElement.tagName.toLowerCase() === 'select') {
                    const options = selectElement.querySelectorAll('option');
                    for (let option of options) {
                        if (option.value === value) {
                            return option.innerText || option.textContent || value;
                        }
                    }
                }
                return value;
            }
            
            // 基础事件记录函数
            function recordEvent(eventType, element, eventData = {}) {
                try {
                    const labelText = getInputLabel(element);
                    
                    const elementInfo = {
                        tag: element ? element.tagName.toLowerCase() : '',
                        id: element ? element.id || '' : '',
                        class: element ? element.className || '' : '',
                        text: element ? (element.innerText || element.textContent || '').substring(0, 50) : '',
                        type: element ? element.type || '' : '',
                        name: element ? element.name || '' : '',
                        value: element ? element.value || '' : '',
                        label: labelText,
                        placeholder: element ? element.placeholder || '' : ''
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
                // 处理 iCheck 相关元素
                if (event.target.classList.contains('iCheck-helper')) {
                    // 获取关联的 input 元素
                    const input = event.target.previousElementSibling;
                    if (input && (input.type === 'radio' || input.type === 'checkbox')) {
                        // 使用关联的 input 元素记录事件
                        recordEvent('change', input, {
                            checked: !input.checked,
                            value: input.value,
                            type: input.type
                        });
                        return;
                    }
                }
                
                // 如果是select元素或其子元素，不记录点击事件
                if (event.target.tagName.toLowerCase() === 'select' ||
                    event.target.closest('select') ||
                    event.target.tagName.toLowerCase() === 'option') {
                    return;
                }
                
                recordEvent('click', event.target, {
                    clientX: event.clientX,
                    clientY: event.clientY,
                    button: event.button
                });
            }, true);
            
            // 输入事件（使用防抖）
            document.addEventListener('input', function(event) {
                // 如果是select、radio或checkbox元素，不记录input事件
                if (event.target.tagName.toLowerCase() === 'select' ||
                    event.target.type === 'radio' ||
                    event.target.type === 'checkbox') {
                    return;
                }
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
                const target = event.target;
                if (target.tagName.toLowerCase() === 'select') {
                    const selectedOption = target.options[target.selectedIndex];
                    const selectedText = selectedOption ? (selectedOption.text || '').trim() : '';
                    const selectedValue = target.value || '';
                    
                    // 只记录一次change事件，使用显示文本
                    recordEvent('change', target, {
                        value: selectedText, // 只使用显示文本
                        selectedText: selectedText,
                        actualValue: selectedValue // 保留实际值作为备用
                    });
                } else if (target.type === 'radio' || target.type === 'checkbox') {
                    // 获取关联的标签文本
                    let labelText = '';
                    
                    // 1. 检查for属性关联的label
                    if (target.id) {
                        const label = document.querySelector(`label[for="${target.id}"]`);
                        if (label) {
                            labelText = label.textContent.trim();
                        }
                    }
                    
                    // 2. 检查父级label
                    if (!labelText) {
                        const parentLabel = target.closest('label');
                        if (parentLabel) {
                            const clone = parentLabel.cloneNode(true);
                            const inputs = clone.querySelectorAll('input');
                            inputs.forEach(input => input.remove());
                            labelText = clone.textContent.trim();
                        }
                    }
                    
                    // 3. 如果还没找到，尝试使用相邻文本
                    if (!labelText) {
                        let sibling = target.nextSibling;
                        while (sibling && !labelText) {
                            if (sibling.nodeType === 3) { // 文本节点
                                labelText = sibling.textContent.trim();
                            }
                            sibling = sibling.nextSibling;
                        }
                    }
                    
                    recordEvent('change', target, {
                        type: target.type,
                        checked: target.checked,
                        value: labelText || target.value || (target.checked ? '选中' : '取消选中'),
                        labelText: labelText
                    });
                } else {
                    // 其他元素的change事件处理
                    recordEvent('change', target, {
                        value: target.value || ''
                    });
                }
            }, true);
            
            console.log('RECORDER_DEBUG: 基础事件监听器注入完成（支持输入防抖和增强的标签识别）');
            
        })();
        """
        
        try:
            await self.page.add_init_script(script)
            await self.page.evaluate(script)
            logger.debug("基础事件监听脚本注入成功（支持输入防抖和增强的标签识别）")
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
            
            # 分离主要描述和技术细节
            main_desc, tech_details = self._split_element_description(element_desc)
            
            # 生成标题（只使用主要描述）
            if event_type == 'click':
                title = f"点击{main_desc}"
                description = f"点击 {element_desc}"
            elif event_type == 'input':
                value = additional_data.get('value', '')
                if '输入框' in tech_details or '文本区域' in tech_details:
                    title = f"在{main_desc}中输入：{value[:20]}{'...' if len(value) > 20 else ''}"
                else:
                    title = f"输入文本：{value[:20]}{'...' if len(value) > 20 else ''}"
                description = f"在 {element_desc} 中输入：{value}"
            elif event_type == 'keydown':
                key = additional_data.get('key', '')
                if key == 'Enter':
                    title = f"在{main_desc}中按下回车键"
                elif key == 'Tab':
                    title = f"按下Tab键切换到下一个元素"
                elif key == 'Escape':
                    title = f"按下Escape键"
                else:
                    title = f"按键：{key}"
                description = f"在 {element_desc} 中按下 {key} 键"
            elif event_type == 'change':
                # 特别处理下拉框的change事件
                if element_info.get('tag', '').lower() == 'select':
                    selected_text = additional_data.get('selectedText', '')
                    if selected_text:
                        title = f"在{main_desc}中选择：{selected_text}"
                        description = f"在 {element_desc} 中选择：{selected_text}"
                    else:
                        # 如果没有selectedText，尝试使用value
                        value = additional_data.get('value', '')
                        title = f"在{main_desc}中选择：{value}"
                        description = f"在 {element_desc} 中选择：{value}"
                # 特别处理单选框和复选框
                elif element_info.get('type', '') in ['radio', 'checkbox']:
                    is_checked = additional_data.get('checked', False)
                    label_text = additional_data.get('labelText', '')
                    value = additional_data.get('value', '')
                    display_text = label_text or value
                    
                    if element_info['type'] == 'radio':
                        title = f"选择{main_desc}：{display_text}"
                        description = f"选择 {element_desc}：{display_text}"
                    else:  # checkbox
                        action = "选中" if is_checked else "取消选中"
                        title = f"{action}{main_desc}：{display_text}"
                        description = f"{action} {element_desc}：{display_text}"
                else:
                    value = additional_data.get('value', '')
                    title = f"修改{main_desc}的值"
                    description = f"修改 {element_desc} 的值为：{value}"
            elif event_type == 'submit':
                if '表单' in tech_details:
                    title = f"提交{main_desc}"
                else:
                    title = "提交表单"
                description = f"提交 {element_desc}"
            else:
                title = f"对{main_desc}执行{event_type}操作"
                description = f"对 {element_desc} 执行了 {event_type} 操作"
            
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
    
    def _split_element_description(self, element_desc: str) -> Tuple[str, str]:
        """分离元素描述中的主要描述和技术细节"""
        try:
            # 如果描述中包含方括号，提取其中的内容作为主要描述
            if '【' in element_desc and '】' in element_desc:
                main_content = element_desc[element_desc.find('【'):element_desc.find('】')+1]
                tech_details = element_desc[element_desc.find('】')+1:].strip()
                
                # 对于统一格式的描述，保留类型信息
                if tech_details in ['按钮', '图标']:
                    main_content = f"{main_content}{tech_details}"
                elif any(ui_type in tech_details for ui_type in ['输入框', '文本区域', '下拉选择框', '复选框', '单选框', '密码输入框', '邮箱输入框', '搜索框', '电话输入框', '数字输入框', '网址输入框', '日期选择器', '时间选择器', '文件上传框']):
                    # 对于表单元素，保留完整的类型描述
                    main_content = f"{main_content}{tech_details}"
                
                return main_content, tech_details
            
            # 如果没有方括号，尝试分离类型信息
            parts = element_desc.split(' ')
            if len(parts) > 1:
                # 假设最后一个部分是技术细节
                return ' '.join(parts[:-1]), parts[-1]
            
            # 如果无法分离，返回原始描述作为主要描述，技术细节为空
            return element_desc, ""
            
        except Exception as e:
            logger.error(f"分离元素描述失败: {e}")
            return element_desc, ""
    
    def _get_element_description(self, analyzed_element: Dict, element_info: Dict) -> str:
        """生成元素描述"""
        try:
            # 获取标签文本
            label_text = element_info.get('label', '').strip()
            element_text = element_info.get('text', '').strip()
            tag_name = element_info.get('tag', '').lower()
            element_type = element_info.get('type', '').lower()
            element_id = element_info.get('id', '')
            element_class = element_info.get('class', '')
            element_name = element_info.get('name', '')
            element_placeholder = element_info.get('placeholder', '')
            
            # 处理 iCheck 相关元素
            if element_class and 'iCheck-helper' in element_class:
                if element_type == 'radio':
                    return f"【{label_text or element_text or '未知选项'}】单选框"
                elif element_type == 'checkbox':
                    return f"【{label_text or element_text or '未知选项'}】复选框"
            
            # 特殊处理图标元素
            if element_class and 'glyphicon' in element_class:
                # 如果有标签文本（来自getInputLabel的增强处理），直接使用
                if label_text:
                    return f"【{label_text}】图标"
                
                # 尝试从类名中提取图标类型
                classes = element_class.split()
                for cls in classes:
                    if cls.startswith('glyphicon-'):
                        icon_type = cls.replace('glyphicon-', '')
                        # 图标类型映射
                        icon_map = {
                            'refresh': '刷新',
                            'search': '搜索',
                            'plus': '添加',
                            'minus': '删除',
                            'edit': '编辑',
                            'trash': '删除',
                            'ok': '确定',
                            'remove': '取消',
                            'save': '保存',
                            'print': '打印',
                            'download': '下载',
                            'upload': '上传',
                            'export': '导出',
                            'import': '导入'
                        }
                        if icon_type in icon_map:
                            return f"【{icon_map[icon_type]}】图标"
                        return f"【{icon_type}】图标"
            
            # 对于表单元素，保持原有的特殊处理逻辑
            if tag_name == 'input':
                input_type_desc = ''
                if element_type == 'password':
                    input_type_desc = '密码输入框'
                elif element_type == 'email':
                    input_type_desc = '邮箱输入框'
                elif element_type == 'text' or element_type == '':
                    input_type_desc = '文本输入框'
                elif element_type == 'search':
                    input_type_desc = '搜索框'
                elif element_type == 'tel':
                    input_type_desc = '电话输入框'
                elif element_type == 'number':
                    input_type_desc = '数字输入框'
                elif element_type == 'url':
                    input_type_desc = '网址输入框'
                elif element_type == 'date':
                    input_type_desc = '日期选择器'
                elif element_type == 'time':
                    input_type_desc = '时间选择器'
                elif element_type == 'file':
                    input_type_desc = '文件上传框'
                elif element_type == 'checkbox':
                    input_type_desc = '复选框'
                elif element_type == 'radio':
                    input_type_desc = '单选框'
                elif element_type == 'button' or element_type == 'submit':
                    # 对于真正的按钮类型，使用按钮描述
                    if label_text:
                        return f"【{label_text}】按钮"
                    if element_text:
                        return f"【{element_text[:15]}】按钮"
                    if element_id:
                        return f"ID为【{element_id}】的按钮"
                    return '按钮'
                else:
                    input_type_desc = f'{element_type}输入框'
                
                # 对于非按钮类型的input元素，使用输入框描述
                if element_type not in ['button', 'submit']:
                    # 如果有标签文本，使用【标签】格式
                    if label_text:
                        return f"【{label_text}】{input_type_desc}"
                    
                    # 如果有placeholder，使用作为备选标签
                    if element_placeholder:
                        return f"【{element_placeholder}】{input_type_desc}"
                    
                    # 如果有元素文本，使用元素文本
                    if element_text:
                        return f"【{element_text[:15]}】{input_type_desc}"
                    
                    # 如果有ID，使用ID
                    if element_id:
                        return f"ID为【{element_id}】的{input_type_desc}"
                    
                    # 如果有name，使用name
                    if element_name:
                        return f"名为【{element_name}】的{input_type_desc}"
                    
                    return input_type_desc
            
            elif tag_name == 'textarea':
                # 文本区域处理
                if label_text:
                    return f"【{label_text}】文本区域"
                if element_placeholder:
                    return f"【{element_placeholder}】文本区域"
                if element_text:
                    return f"【{element_text[:15]}】文本区域"
                return '文本区域'
            
            elif tag_name == 'select':
                # 下拉选择框处理
                if label_text:
                    return f"【{label_text}】下拉选择框"
                if element_text:
                    return f"【{element_text[:15]}】下拉选择框"
                if element_name:
                    return f"名为【{element_name}】的下拉选择框"
                return '下拉选择框'
            
            # 对于其他可点击元素（如菜单项、链接、span等），统一使用"按钮"描述
            # 获取显示文本
            display_text = ""
            if element_text:
                display_text = element_text
            elif label_text:
                display_text = label_text
            elif element_placeholder:
                display_text = element_placeholder
            elif element_id:
                display_text = element_id
            elif element_name:
                display_text = element_name
            
            # 如果有显示文本，使用统一的按钮格式
            if display_text:
                return f"【{display_text[:15]}】按钮"
            
            # 最后的备选方案 - 使用统一的按钮格式
            if element_class:
                main_class = element_class.split(' ')[0]
                return f"类名为【{main_class}】的按钮"
            
            if tag_name:
                return f'{tag_name.upper()}按钮'
            
            return "未知按钮"
            
        except Exception as e:
            logger.error(f"生成元素描述失败: {e}")
            return "未知按钮"
    
    async def _record_action(self, action_type: str, url: str = "", title: str = "", 
                           description: str = "", element_info: Dict = None, 
                           additional_data: Dict = None, analyzed_element: Dict = None):
        """记录操作"""
        try:
            if not self.session:
                return
            
            # 截图
            screenshot_path = ""
            # try:
            #     screenshot_filename = f"screenshot_{len(self.session.actions) + 1}_{int(time.time())}.png"
            #     screenshot_path = str(settings.SCREENSHOTS_DIR / screenshot_filename)
            #     await self.page.screenshot(path=screenshot_path, full_page=True)
            # except Exception as e:
            #     logger.warning(f"截图失败: {e}")
            
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