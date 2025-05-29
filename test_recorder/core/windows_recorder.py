#!/usr/bin/env python3
import json
import time
import threading
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import uuid
import tempfile
import os

from loguru import logger

from config.settings import settings
from core.models import TestSession, ActionRecord


class WindowsTestRecorder:
    """Windows兼容的测试录制器 - 使用同步方式避免事件循环问题"""
    
    def __init__(self):
        self.session: Optional[TestSession] = None
        self.is_recording = False
        self.action_count = 0
        
        # 事件监听器存储
        self._listeners: List[Callable] = []
        
        # 浏览器进程
        self.browser_process: Optional[subprocess.Popen] = None
        self.recording_thread: Optional[threading.Thread] = None
        
        # 临时文件用于通信
        self.temp_dir = Path(tempfile.mkdtemp(prefix="windows_recorder_"))
        self.actions_file = self.temp_dir / "actions.json"
        self.status_file = self.temp_dir / "status.json"
        
    def initialize(self):
        """初始化录制器"""
        try:
            logger.info("正在启动Windows录制器...")
            
            # 创建临时文件
            self.actions_file.touch()
            self.status_file.touch()
            
            # 初始化状态
            self._update_status("initialized")
            
            logger.info("Windows录制器初始化完成")
            
        except Exception as e:
            logger.error(f"Windows录制器初始化失败: {e}")
            raise
    
    def _update_status(self, status: str, message: str = ""):
        """更新状态文件"""
        status_data = {
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"更新状态失败: {e}")
    
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
            
            # 启动浏览器进程
            self._start_browser_process()
            
            self.is_recording = True
            self.action_count = 0
            
            # 启动录制监控线程
            self.recording_thread = threading.Thread(
                target=self._recording_monitor,
                daemon=True
            )
            self.recording_thread.start()
            
            self._update_status("recording", f"Recording: {test_name}")
            
            logger.info(f"开始录制测试用例: {test_name} (ID: {session_id})")
            
            return session_id
            
        except Exception as e:
            logger.error(f"开始录制失败: {e}")
            raise Exception(f"开始录制失败: {str(e)}")
    
    def _start_browser_process(self):
        """启动浏览器进程"""
        try:
            # 使用playwright codegen来启动浏览器并录制
            cmd = [
                sys.executable, "-m", "playwright", "codegen",
                "--target", "python-async",
                "--output", str(self.temp_dir / "generated_code.py"),
                "about:blank"
            ]
            
            logger.info(f"启动浏览器命令: {' '.join(cmd)}")
            
            self.browser_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.temp_dir)
            )
            
            logger.info("浏览器进程启动成功")
            
        except Exception as e:
            logger.error(f"启动浏览器进程失败: {e}")
            raise
    
    def _recording_monitor(self):
        """录制监控线程"""
        logger.info("录制监控线程启动")
        
        last_check_time = time.time()
        action_counter = 0
        last_code_content = ""
        
        while self.is_recording:
            try:
                # 检查生成的代码文件
                code_file = self.temp_dir / "generated_code.py"
                if code_file.exists():
                    # 读取生成的代码
                    with open(code_file, 'r', encoding='utf-8') as f:
                        code_content = f.read()
                    
                    # 只有当代码内容发生变化时才解析
                    if code_content != last_code_content:
                        last_code_content = code_content
                        
                        # 解析代码中的操作
                        actions = self._parse_generated_code(code_content)
                        
                        # 添加新的操作
                        current_action_count = len(self.session.actions)
                        for i, action in enumerate(actions):
                            if i >= current_action_count:  # 只处理新的操作
                                action_counter += 1
                                action_record = ActionRecord(
                                    id=str(uuid.uuid4()),
                                    session_id=self.session.id,
                                    action_type=action.get('type', 'unknown'),
                                    timestamp=datetime.now(),
                                    page_url=action.get('url', ''),
                                    page_title=action.get('title', ''),
                                    element_info=action.get('element', {}),
                                    description=action.get('description', ''),
                                    additional_data=json.dumps(action.get('data', {}))
                                )
                                
                                self.session.actions.append(action_record)
                                
                                # 通知监听器
                                logger.info(f"新操作记录: {action.get('type', 'unknown')}")
                                self._notify_listeners('action_recorded', action_record)
                
                time.sleep(0.5)  # 每500ms检查一次
                
            except Exception as e:
                logger.error(f"录制监控错误: {e}")
                time.sleep(1)
        
        logger.info("录制监控线程结束")
    
    def _parse_generated_code(self, code_content: str) -> List[Dict]:
        """解析Playwright生成的代码"""
        actions = []
        
        try:
            lines = code_content.split('\n')
            current_url = "about:blank"
            
            for line_num, line in enumerate(lines):
                line = line.strip()
                
                # 解析不同类型的操作
                if 'page.goto(' in line:
                    url = self._extract_string_from_line(line)
                    current_url = url
                    actions.append({
                        'type': 'goto',
                        'url': url,
                        'title': f'导航到: {url}',
                        'description': f'打开网页: {url}',
                        'element': {'type': 'navigation', 'url': url},
                        'data': {'url': url, 'action': 'navigate'}
                    })
                
                elif 'page.click(' in line:
                    selector = self._extract_string_from_line(line)
                    # 尝试提取更友好的元素描述
                    element_desc = self._get_element_description(selector)
                    actions.append({
                        'type': 'click',
                        'url': current_url,
                        'title': f'点击: {element_desc}',
                        'description': f'点击元素: {selector}',
                        'element': {'selector': selector, 'type': 'click', 'description': element_desc},
                        'data': {'selector': selector, 'action': 'click', 'element_type': 'button/link'}
                    })
                
                elif 'page.fill(' in line:
                    parts = line.split(',', 1)
                    if len(parts) >= 2:
                        selector = self._extract_string_from_line(parts[0])
                        value = self._extract_string_from_line(parts[1])
                        element_desc = self._get_element_description(selector)
                        actions.append({
                            'type': 'fill',
                            'url': current_url,
                            'title': f'输入文本: {value[:20]}{"..." if len(value) > 20 else ""}',
                            'description': f'在 {element_desc} 中输入: {value}',
                            'element': {'selector': selector, 'type': 'input', 'description': element_desc},
                            'data': {'selector': selector, 'value': value, 'action': 'input'}
                        })
                
                elif 'page.press(' in line:
                    parts = line.split(',', 1)
                    if len(parts) >= 2:
                        selector = self._extract_string_from_line(parts[0])
                        key = self._extract_string_from_line(parts[1])
                        element_desc = self._get_element_description(selector)
                        actions.append({
                            'type': 'press',
                            'url': current_url,
                            'title': f'按键: {key}',
                            'description': f'在 {element_desc} 中按下 {key} 键',
                            'element': {'selector': selector, 'type': 'keypress', 'description': element_desc},
                            'data': {'selector': selector, 'key': key, 'action': 'keypress'}
                        })
                
                elif 'page.select_option(' in line:
                    parts = line.split(',', 1)
                    if len(parts) >= 2:
                        selector = self._extract_string_from_line(parts[0])
                        value = self._extract_string_from_line(parts[1])
                        element_desc = self._get_element_description(selector)
                        actions.append({
                            'type': 'select',
                            'url': current_url,
                            'title': f'选择选项: {value}',
                            'description': f'在 {element_desc} 中选择: {value}',
                            'element': {'selector': selector, 'type': 'select', 'description': element_desc},
                            'data': {'selector': selector, 'value': value, 'action': 'select'}
                        })
                
                elif 'page.check(' in line:
                    selector = self._extract_string_from_line(line)
                    element_desc = self._get_element_description(selector)
                    actions.append({
                        'type': 'check',
                        'url': current_url,
                        'title': f'勾选: {element_desc}',
                        'description': f'勾选复选框: {selector}',
                        'element': {'selector': selector, 'type': 'checkbox', 'description': element_desc},
                        'data': {'selector': selector, 'action': 'check'}
                    })
                
                elif 'page.uncheck(' in line:
                    selector = self._extract_string_from_line(line)
                    element_desc = self._get_element_description(selector)
                    actions.append({
                        'type': 'uncheck',
                        'url': current_url,
                        'title': f'取消勾选: {element_desc}',
                        'description': f'取消勾选复选框: {selector}',
                        'element': {'selector': selector, 'type': 'checkbox', 'description': element_desc},
                        'data': {'selector': selector, 'action': 'uncheck'}
                    })
                
                elif 'page.hover(' in line:
                    selector = self._extract_string_from_line(line)
                    element_desc = self._get_element_description(selector)
                    actions.append({
                        'type': 'hover',
                        'url': current_url,
                        'title': f'悬停: {element_desc}',
                        'description': f'鼠标悬停在: {selector}',
                        'element': {'selector': selector, 'type': 'hover', 'description': element_desc},
                        'data': {'selector': selector, 'action': 'hover'}
                    })
                
                elif 'page.wait_for_selector(' in line:
                    selector = self._extract_string_from_line(line)
                    element_desc = self._get_element_description(selector)
                    actions.append({
                        'type': 'wait',
                        'url': current_url,
                        'title': f'等待元素: {element_desc}',
                        'description': f'等待元素出现: {selector}',
                        'element': {'selector': selector, 'type': 'wait', 'description': element_desc},
                        'data': {'selector': selector, 'action': 'wait'}
                    })
        
        except Exception as e:
            logger.error(f"解析代码失败: {e}")
        
        return actions
    
    def _get_element_description(self, selector: str) -> str:
        """根据选择器生成友好的元素描述"""
        try:
            if not selector:
                return "未知元素"
            
            # 处理常见的选择器类型
            if selector.startswith('#'):
                return f"ID为'{selector[1:]}'"
            elif selector.startswith('.'):
                return f"类名为'{selector[1:]}'"
            elif 'text=' in selector:
                text = selector.split('text=')[1].strip('"\'')
                return f"文本为'{text}'"
            elif 'placeholder=' in selector:
                placeholder = selector.split('placeholder=')[1].strip('"\'')
                return f"占位符为'{placeholder}'"
            elif selector.startswith('input'):
                return "输入框"
            elif selector.startswith('button'):
                return "按钮"
            elif selector.startswith('a'):
                return "链接"
            elif selector.startswith('select'):
                return "下拉选择框"
            elif 'role=' in selector:
                role = selector.split('role=')[1].split(']')[0].strip('"\'')
                return f"角色为'{role}'"
            else:
                # 截取选择器的前30个字符作为描述
                return selector[:30] + ("..." if len(selector) > 30 else "")
                
        except Exception:
            return selector[:30] + ("..." if len(selector) > 30 else "")
    
    def _extract_string_from_line(self, line: str) -> str:
        """从代码行中提取字符串"""
        try:
            # 查找引号内的内容，支持单引号和双引号
            import re
            # 优先匹配双引号
            match = re.search(r'"([^"]*)"', line)
            if match:
                return match.group(1)
            # 然后匹配单引号
            match = re.search(r"'([^']*)'", line)
            if match:
                return match.group(1)
        except:
            pass
        return ""
    
    def stop_recording(self) -> TestSession:
        """停止录制并保存结果"""
        try:
            if not self.is_recording or not self.session:
                raise ValueError("当前没有正在进行的录制")
            
            logger.info("正在停止录制...")
            
            self.is_recording = False
            
            # 先关闭浏览器进程
            if self.browser_process:
                try:
                    logger.info("正在关闭浏览器进程...")
                    # 发送CTRL+C信号
                    import signal
                    if hasattr(signal, 'CTRL_C_EVENT'):
                        self.browser_process.send_signal(signal.CTRL_C_EVENT)
                    else:
                        self.browser_process.terminate()
                    
                    # 等待进程结束
                    try:
                        self.browser_process.wait(timeout=3)
                        logger.info("浏览器进程已正常关闭")
                    except subprocess.TimeoutExpired:
                        logger.warning("浏览器进程未响应，强制终止")
                        self.browser_process.kill()
                        self.browser_process.wait(timeout=2)
                        
                except Exception as e:
                    logger.error(f"关闭浏览器进程失败: {e}")
                    try:
                        self.browser_process.kill()
                    except:
                        pass
                finally:
                    self.browser_process = None
            
            # 等待录制线程结束
            if self.recording_thread and self.recording_thread.is_alive():
                logger.info("等待录制监控线程结束...")
                self.recording_thread.join(timeout=5)
            
            # 更新会话状态
            self.session.end_time = datetime.now()
            self.session.status = "completed"
            
            # 保存会话数据
            self._save_session()
            
            self._update_status("stopped")
            
            logger.info(f"录制完成: {self.session.name} (总操作数: {len(self.session.actions)})")
            
            return self.session
            
        except Exception as e:
            logger.error(f"停止录制失败: {e}")
            raise Exception(f"停止录制失败: {str(e)}")
    
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
    
    def navigate_to(self, url: str):
        """导航到指定URL（通过模拟操作）"""
        try:
            # 记录导航操作
            if self.is_recording and self.session:
                action_record = ActionRecord(
                    id=str(uuid.uuid4()),
                    session_id=self.session.id,
                    action_type="goto",
                    timestamp=datetime.now(),
                    page_url=url,
                    page_title="",
                    additional_data=f"导航到: {url}"
                )
                
                self.session.actions.append(action_record)
                self._notify_listeners('action_recorded', action_record)
            
            logger.info(f"记录导航操作: {url}")
            
        except Exception as e:
            logger.error(f"导航操作失败: {e}")
            raise
    
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
            
            # 确保浏览器进程已关闭
            if self.browser_process:
                try:
                    self.browser_process.kill()
                    self.browser_process.wait(timeout=2)
                except:
                    pass
                self.browser_process = None
            
            # 清理临时文件
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            
            logger.info("Windows录制器资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")


# 全局Windows录制器实例
windows_recorder = WindowsTestRecorder() 