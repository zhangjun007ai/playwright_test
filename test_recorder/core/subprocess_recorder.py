import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import uuid
import tempfile
import os

from loguru import logger

from config.settings import settings
from core.models import TestSession, ActionRecord


class SubprocessTestRecorder:
    """基于子进程的测试录制器 - 解决Windows事件循环问题"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.session: Optional[TestSession] = None
        self.is_recording = False
        self.action_count = 0
        
        # 事件监听器存储
        self._listeners: List[Callable] = []
        
        # 临时文件用于进程间通信
        self.temp_dir = Path(tempfile.mkdtemp(prefix="playwright_recorder_"))
        self.command_file = self.temp_dir / "commands.json"
        self.status_file = self.temp_dir / "status.json"
        self.session_file = self.temp_dir / "session.json"
        
    async def initialize(self):
        """初始化子进程录制器"""
        try:
            logger.info("正在启动子进程录制器...")
            
            # 创建Playwright子进程脚本
            script_content = self._create_playwright_script()
            script_file = self.temp_dir / "playwright_worker.py"
            
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # 启动子进程
            self.process = subprocess.Popen(
                [sys.executable, str(script_file)],
                cwd=str(self.temp_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待子进程初始化
            await self._wait_for_status("initialized", timeout=30)
            
            logger.info("子进程录制器初始化完成")
            
        except Exception as e:
            logger.error(f"子进程录制器初始化失败: {e}")
            await self._cleanup_resources()
            raise
    
    def _create_playwright_script(self) -> str:
        """创建Playwright工作脚本"""
        return f'''
import asyncio
import json
import sys
import platform
from datetime import datetime
from pathlib import Path
import uuid

# Windows环境下设置事件循环策略
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.async_api import async_playwright

class PlaywrightWorker:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.is_recording = False
        self.session_data = None
        
        self.temp_dir = Path.cwd()
        self.command_file = self.temp_dir / "commands.json"
        self.status_file = self.temp_dir / "status.json"
        self.session_file = self.temp_dir / "session.json"
        self.events_file = self.temp_dir / "events.json"
        
    async def initialize(self):
        """初始化Playwright"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=False,
                slow_mo=100
            )
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            
            await self._update_status("initialized")
            print("Playwright worker initialized successfully")
            
        except Exception as e:
            await self._update_status("error", str(e))
            raise
    
    async def _update_status(self, status, message=""):
        """更新状态文件"""
        status_data = {{
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }}
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
    
    async def _notify_event(self, event_type, data):
        """通知事件到主进程"""
        event_data = {{
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }}
        
        # 追加到事件文件
        events = []
        if self.events_file.exists():
            try:
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    events = json.load(f)
            except:
                events = []
        
        events.append(event_data)
        
        # 只保留最近100个事件
        if len(events) > 100:
            events = events[-100:]
        
        with open(self.events_file, 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
    
    async def start_recording(self, test_name, description=""):
        """开始录制"""
        try:
            session_id = str(uuid.uuid4())
            self.session_data = {{
                "id": session_id,
                "name": test_name,
                "description": description,
                "start_time": datetime.now().isoformat(),
                "actions": [],
                "test_steps": [],
                "trace_file": "",
                "video_file": "",
                "browser_type": "chromium",
                "status": "recording",
                "tags": []
            }}
            self.is_recording = True
            
            # 设置页面事件监听
            await self._setup_page_listeners()
            
            await self._update_status("recording", f"Recording: {{test_name}}")
            await self._save_session()
            
            return session_id
            
        except Exception as e:
            await self._update_status("error", str(e))
            raise
    
    async def _setup_page_listeners(self):
        """设置页面事件监听器"""
        if not self.page:
            return
        
        # 监听页面导航
        async def on_response(response):
            if response.request.resource_type == "document":
                action_data = {{
                    "id": str(uuid.uuid4()),
                    "session_id": self.session_data["id"],
                    "action_type": "navigation",
                    "timestamp": datetime.now().isoformat(),
                    "page_url": response.url,
                    "page_title": await self.page.title() if self.page else "",
                    "additional_data": f"页面导航: {{response.url}}"
                }}
                
                if self.is_recording and self.session_data:
                    self.session_data["actions"].append(action_data)
                    await self._save_session()
                    await self._notify_event("action_recorded", action_data)
        
        # 注册监听器
        self.page.on("response", on_response)
        
        # 注入JavaScript监听用户交互
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
                console.log('PLAYWRIGHT_ACTION:', JSON.stringify(actionData));
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
        
        # 监听控制台消息来捕获用户操作
        async def handle_console_message(message):
            if message.text.startswith('PLAYWRIGHT_ACTION:'):
                try:
                    action_json = message.text.replace('PLAYWRIGHT_ACTION:', '')
                    action_data = json.loads(action_json)
                    await self._record_page_action(action_data)
                except Exception as e:
                    print(f"处理页面操作失败: {e}")
        
        self.page.on("console", handle_console_message)
    
    async def _record_page_action(self, action_data):
        """记录来自页面的用户操作"""
        try:
            # 创建操作记录
            action_record = {
                "id": str(uuid.uuid4()),
                "session_id": self.session_data["id"],
                "action_type": action_data['action'],
                "timestamp": datetime.fromtimestamp(action_data['timestamp'] / 1000).isoformat(),
                "element_info": action_data['element'],
                "page_url": action_data['url'],
                "page_title": action_data['title'],
                "additional_data": action_data.get('value', '') or json.dumps(action_data.get('additionalData', {}))
            }
            
            if self.is_recording and self.session_data:
                self.session_data["actions"].append(action_record)
                await self._save_session()
                await self._notify_event("action_recorded", action_record)
                print(f"记录操作: {action_data['action']} on {action_data['element']['tagName']}")
            
        except Exception as e:
            print(f"记录操作失败: {e}")
    
    async def stop_recording(self):
        """停止录制"""
        try:
            if self.session_data:
                self.session_data["end_time"] = datetime.now().isoformat()
                self.session_data["status"] = "completed"
            self.is_recording = False
            
            await self._update_status("stopped")
            await self._save_session()
            
        except Exception as e:
            await self._update_status("error", str(e))
            raise
    
    async def navigate_to(self, url):
        """导航到URL"""
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # 记录导航操作
            if self.is_recording and self.session_data:
                action = {{
                    "id": str(uuid.uuid4()),
                    "session_id": self.session_data["id"],
                    "action_type": "goto",
                    "timestamp": datetime.now().isoformat(),
                    "page_url": url,
                    "page_title": await self.page.title(),
                    "additional_data": f"导航到: {{url}}"
                }}
                self.session_data["actions"].append(action)
                await self._save_session()
                await self._notify_event("action_recorded", action)
            
            await self._update_status("navigated", f"Navigated to: {{url}}")
            
        except Exception as e:
            await self._update_status("error", str(e))
            raise
    
    async def _save_session(self):
        """保存会话数据"""
        if self.session_data:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, ensure_ascii=False, indent=2)
    
    async def process_commands(self):
        """处理命令"""
        while True:
            try:
                if self.command_file.exists():
                    with open(self.command_file, 'r', encoding='utf-8') as f:
                        command = json.load(f)
                    
                    # 删除命令文件
                    self.command_file.unlink()
                    
                    # 处理命令
                    if command["action"] == "start_recording":
                        await self.start_recording(
                            command["test_name"], 
                            command.get("description", "")
                        )
                    elif command["action"] == "stop_recording":
                        await self.stop_recording()
                    elif command["action"] == "navigate":
                        await self.navigate_to(command["url"])
                    elif command["action"] == "shutdown":
                        break
                
                await asyncio.sleep(0.1)  # 避免CPU占用过高
                
            except Exception as e:
                await self._update_status("error", str(e))
                await asyncio.sleep(1)
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Cleanup error: {{e}}")

async def main():
    worker = PlaywrightWorker()
    try:
        await worker.initialize()
        await worker.process_commands()
    finally:
        await worker.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    async def _wait_for_status(self, expected_status: str, timeout: int = 30):
        """等待特定状态"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.status_file.exists():
                try:
                    with open(self.status_file, 'r', encoding='utf-8') as f:
                        status_data = json.load(f)
                    
                    if status_data.get("status") == expected_status:
                        return True
                    elif status_data.get("status") == "error":
                        raise Exception(f"子进程错误: {status_data.get('message', 'Unknown error')}")
                        
                except json.JSONDecodeError:
                    pass
            
            await asyncio.sleep(0.1)
        
        raise TimeoutError(f"等待状态 '{expected_status}' 超时")
    
    async def _send_command(self, command: Dict):
        """发送命令到子进程"""
        with open(self.command_file, 'w', encoding='utf-8') as f:
            json.dump(command, f, ensure_ascii=False, indent=2)
    
    async def start_recording(self, test_name: str, description: str = "") -> str:
        """开始录制测试用例"""
        if self.is_recording:
            raise ValueError("录制已在进行中")
        
        if not self.process:
            await self.initialize()
        
        # 发送开始录制命令
        await self._send_command({
            "action": "start_recording",
            "test_name": test_name,
            "description": description
        })
        
        # 等待录制开始
        await self._wait_for_status("recording")
        
        # 读取会话数据
        if self.session_file.exists():
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            self.session = TestSession(**session_data)
            self.is_recording = True
            
            logger.info(f"开始录制测试用例: {test_name} (ID: {self.session.id})")
            return self.session.id
        
        raise Exception("无法获取会话数据")
    
    async def stop_recording(self) -> TestSession:
        """停止录制并保存结果"""
        if not self.is_recording or not self.session:
            raise ValueError("当前没有正在进行的录制")
        
        # 发送停止录制命令
        await self._send_command({"action": "stop_recording"})
        
        # 等待录制停止
        await self._wait_for_status("stopped")
        
        # 读取最终会话数据
        if self.session_file.exists():
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            self.session = TestSession(**session_data)
            self.is_recording = False
            
            # 保存到正式目录
            await self._save_session_to_recordings()
            
            logger.info(f"录制完成: {self.session.name} (总操作数: {len(self.session.actions)})")
            return self.session
        
        raise Exception("无法获取最终会话数据")
    
    async def _save_session_to_recordings(self):
        """保存会话数据到正式录制目录"""
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
        if not self.process:
            raise ValueError("子进程未初始化")
        
        # 发送导航命令
        await self._send_command({
            "action": "navigate",
            "url": url
        })
        
        # 等待导航完成
        await self._wait_for_status("navigated")
        
        logger.info(f"导航到: {url}")
    
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
            if self.process:
                # 发送关闭命令
                try:
                    await self._send_command({"action": "shutdown"})
                    # 等待进程结束
                    self.process.wait(timeout=5)
                except:
                    # 强制终止进程
                    self.process.terminate()
                    self.process.wait(timeout=5)
                    if self.process.poll() is None:
                        self.process.kill()
            
            # 清理临时文件
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                
        except Exception as e:
            logger.warning(f"清理资源时出错: {e}")
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.is_recording:
                await self.stop_recording()
            
            await self._cleanup_resources()
            
            logger.info("子进程录制器资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")


# 全局子进程录制器实例
subprocess_recorder = SubprocessTestRecorder() 