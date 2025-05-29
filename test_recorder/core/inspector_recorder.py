#!/usr/bin/env python3
"""
基于Playwright Inspector的录制器
直接使用playwright codegen命令进行录制，实时解析生成的代码
简化版本，专注于稳定性和基础功能
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import time
import threading
import queue
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import uuid
import tempfile
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from loguru import logger

from config.settings import settings
from core.models import TestSession, ActionRecord


class CodeFileWatcher(FileSystemEventHandler):
    """代码文件监控器"""
    
    def __init__(self, code_file_path: Path, callback: Callable):
        self.code_file_path = code_file_path
        self.callback = callback
        self.last_modified = 0
        
    def on_modified(self, event):
        """文件修改事件处理"""
        if event.is_directory:
            return
            
        if Path(event.src_path) == self.code_file_path:
            # 防止重复触发
            current_time = time.time()
            if current_time - self.last_modified < 0.1:  # 100ms内的重复事件忽略
                return
            self.last_modified = current_time
            
            try:
                if self.callback:
                    self.callback()
            except Exception as e:
                logger.error(f"代码文件变化回调失败: {e}")


class InspectorTestRecorder:
    """简化的Inspector测试录制器"""
    
    def __init__(self):
        self.session: Optional[TestSession] = None
        self.is_recording = False
        self.action_count = 0
        
        # Inspector进程
        self.inspector_process: Optional[subprocess.Popen] = None
        
        # 文件监控
        self.code_file_path: Optional[Path] = None
        self.file_observer: Optional[Observer] = None
        self.file_watcher: Optional[CodeFileWatcher] = None
        
        # 代码内容跟踪
        self.last_code_content = ""
        self.generated_actions: List[Dict] = []
        
        # 消息队列和监听器
        self.message_queue = queue.Queue()
        self._listeners: List[Callable] = []
        
        # 临时目录
        self.temp_dir = Path(tempfile.mkdtemp(prefix="inspector_recorder_"))
        
        # 统计信息
        self.stats = {
            "total_actions": 0,
            "code_lines": 0,
            "start_time": None,
            "inspector_launches": 0
        }
        
    def initialize(self):
        """初始化录制器"""
        try:
            logger.info("正在启动Inspector录制器...")
            
            # 创建临时目录
            self.temp_dir.mkdir(exist_ok=True)
            
            logger.info("Inspector录制器初始化完成")
            
        except Exception as e:
            logger.error(f"Inspector录制器初始化失败: {e}")
            raise
    
    def start_recording(self, test_name: str, description: str = "") -> str:
        """开始录制测试用例"""
        try:
            if self.is_recording:
                raise ValueError("录制已在进行中")
            
            logger.info(f"准备开始Inspector录制: {test_name}")
            
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
            self.last_code_content = ""
            self.generated_actions.clear()
            
            # 重置统计
            self.stats = {
                "total_actions": 0,
                "code_lines": 0,
                "start_time": datetime.now(),
                "inspector_launches": 0
            }
            
            # 设置代码文件路径
            code_filename = f"test_{session_id}.py"
            self.code_file_path = self.temp_dir / code_filename
            
            # 启动Inspector进程
            self._start_inspector_process()
            
            # 启动文件监控
            self._start_file_monitoring()
            
            logger.info(f"Inspector录制已启动: {test_name} (ID: {session_id})")
            logger.info(f"代码文件: {self.code_file_path}")
            
            return session_id
            
        except Exception as e:
            logger.error(f"开始Inspector录制失败: {e}")
            raise Exception(f"开始Inspector录制失败: {str(e)}")
    
    def _start_inspector_process(self):
        """启动Inspector进程"""
        try:
            # 准备codegen命令
            cmd = [
                sys.executable, "-m", "playwright", "codegen",
                "--target", "python-async",
                "--output", str(self.code_file_path),
                "about:blank"
            ]
            
            logger.info(f"启动Inspector进程: {' '.join(cmd)}")
            
            # 启动进程
            self.inspector_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            self.stats["inspector_launches"] += 1
            
            logger.info(f"Inspector进程已启动，PID: {self.inspector_process.pid}")
            
            # 等待一下让Inspector启动完成
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"启动Inspector进程失败: {e}")
            raise
    
    def _start_file_monitoring(self):
        """启动文件监控"""
        try:
            # 创建文件监控器
            self.file_watcher = CodeFileWatcher(
                self.code_file_path,
                self._on_code_file_changed
            )
            
            # 创建观察者
            self.file_observer = Observer()
            self.file_observer.schedule(
                self.file_watcher,
                str(self.code_file_path.parent),
                recursive=False
            )
            
            # 启动观察者
            self.file_observer.start()
            
            logger.info("代码文件监控已启动")
            
        except Exception as e:
            logger.error(f"启动文件监控失败: {e}")
            raise
    
    def _on_code_file_changed(self):
        """代码文件变化处理"""
        try:
            if not self.code_file_path.exists():
                return
            
            # 读取当前内容
            with open(self.code_file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            # 检查是否有实际变化
            if current_content == self.last_code_content:
                return
            
            logger.debug(f"检测到代码文件变化: {self.code_file_path}")
            
            # 解析新增的代码行
            new_actions = self._parse_code_changes(self.last_code_content, current_content)
            
            # 处理新动作
            for action in new_actions:
                self._process_inspector_action(action)
            
            # 更新内容
            self.last_code_content = current_content
            self.stats["code_lines"] = len(current_content.splitlines())
            
        except Exception as e:
            logger.error(f"处理代码文件变化失败: {e}")
    
    def _parse_code_changes(self, old_content: str, new_content: str) -> List[Dict]:
        """解析代码变化，提取新的动作"""
        try:
            old_lines = old_content.splitlines() if old_content else []
            new_lines = new_content.splitlines()
            
            # 找出新增的行
            if len(new_lines) <= len(old_lines):
                return []
            
            new_actions = []
            added_lines = new_lines[len(old_lines):]
            
            for line in added_lines:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('import'):
                    continue
                
                # 解析动作类型
                action = self._parse_code_line(line)
                if action:
                    new_actions.append(action)
            
            return new_actions
            
        except Exception as e:
            logger.error(f"解析代码变化失败: {e}")
            return []
    
    def _parse_code_line(self, code_line: str) -> Optional[Dict]:
        """解析单行代码，提取动作信息"""
        try:
            action = {
                'code_line': code_line,
                'action_type': 'unknown',
                'element_info': {},
                'description': code_line,
                'timestamp': datetime.now()
            }
            
            # 点击操作
            if '.click(' in code_line:
                action['action_type'] = 'click'
                selector = self._extract_selector(code_line)
                if selector:
                    action['element_info'] = {'selector': selector}
                    action['description'] = f"点击元素: {selector}"
            
            # 填入操作
            elif '.fill(' in code_line:
                action['action_type'] = 'fill'
                selector = self._extract_selector(code_line)
                value = self._extract_fill_value(code_line)
                if selector:
                    action['element_info'] = {'selector': selector}
                    action['description'] = f"在 {selector} 中输入: {value}"
            
            # 导航操作
            elif '.goto(' in code_line:
                action['action_type'] = 'goto'
                url = self._extract_goto_url(code_line)
                if url:
                    action['element_info'] = {'url': url}
                    action['description'] = f"导航到: {url}"
            
            # 按键操作
            elif '.press(' in code_line:
                action['action_type'] = 'press'
                key = self._extract_press_key(code_line)
                if key:
                    action['element_info'] = {'key': key}
                    action['description'] = f"按键: {key}"
            
            # 选择操作
            elif '.select_option(' in code_line:
                action['action_type'] = 'select'
                selector = self._extract_selector(code_line)
                option = self._extract_select_option(code_line)
                if selector:
                    action['element_info'] = {'selector': selector, 'option': option}
                    action['description'] = f"在 {selector} 中选择: {option}"
            
            # 等待操作
            elif '.wait_for_' in code_line:
                action['action_type'] = 'wait'
                action['description'] = f"等待操作: {code_line}"
            
            else:
                action['description'] = f"执行操作: {code_line}"
            
            return action
            
        except Exception as e:
            logger.error(f"解析代码行失败: {e}")
            return None
    
    def _extract_selector(self, code_line: str) -> Optional[str]:
        """从代码行中提取选择器"""
        # 匹配各种选择器格式
        patterns = [
            r'\.click\(["\']([^"\']+)["\']',
            r'\.fill\(["\']([^"\']+)["\']',
            r'\.select_option\(["\']([^"\']+)["\']',
            r'\.press\(["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, code_line)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_fill_value(self, code_line: str) -> str:
        """提取填入的值"""
        match = re.search(r'\.fill\([^,]+,\s*["\']([^"\']*)["\']', code_line)
        return match.group(1) if match else ""
    
    def _extract_goto_url(self, code_line: str) -> Optional[str]:
        """提取导航URL"""
        match = re.search(r'\.goto\(["\']([^"\']+)["\']', code_line)
        return match.group(1) if match else None
    
    def _extract_press_key(self, code_line: str) -> Optional[str]:
        """提取按键"""
        match = re.search(r'\.press\(["\']([^"\']+)["\']', code_line)
        return match.group(1) if match else None
    
    def _extract_select_option(self, code_line: str) -> str:
        """提取选择的选项"""
        match = re.search(r'\.select_option\([^,]+,\s*["\']([^"\']*)["\']', code_line)
        return match.group(1) if match else ""
    
    def _process_inspector_action(self, action_data: Dict):
        """处理Inspector动作"""
        try:
            # 创建ActionRecord
            action_record = ActionRecord(
                id=str(uuid.uuid4()),
                session_id=self.session.id,
                action_type=action_data['action_type'],
                timestamp=action_data['timestamp'],
                page_url="",  # Inspector模式下无法直接获取URL
                page_title=action_data['description'],
                element_info=action_data['element_info'],
                description=action_data['description'],
                screenshot_path="",  # Inspector模式下无截图
                additional_data=json.dumps({
                    'code_line': action_data['code_line'],
                    'source': 'inspector'
                })
            )
            
            # 添加到会话
            self.session.actions.append(action_record)
            self.action_count += 1
            self.stats["total_actions"] += 1
            
            # 生成Playwright代码
            playwright_code = action_data['code_line']
            
            # 添加到消息队列
            self.message_queue.put(('action_recorded', {
                'action_record': action_record,
                'playwright_code': playwright_code,
                'source': 'inspector'
            }))
            
            # 通知监听器
            self._notify_listeners("action_recorded", action_record)
            
            logger.info(f"Inspector动作已记录: {action_data['action_type']} - {action_data['description']}")
            
        except Exception as e:
            logger.error(f"处理Inspector动作失败: {e}")
    
    def stop_recording(self) -> TestSession:
        """停止录制并保存结果"""
        try:
            if not self.is_recording or not self.session:
                raise ValueError("当前没有正在进行的录制")
            
            logger.info("正在停止Inspector录制...")
            
            self.is_recording = False
            
            # 停止文件监控
            if self.file_observer:
                self.file_observer.stop()
                self.file_observer.join(timeout=5)
                self.file_observer = None
            
            # 停止Inspector进程
            if self.inspector_process:
                try:
                    if os.name == 'nt':
                        # Windows下使用CTRL_BREAK_EVENT
                        self.inspector_process.send_signal(subprocess.signal.CTRL_BREAK_EVENT)
                    else:
                        self.inspector_process.terminate()
                    
                    # 等待进程结束
                    try:
                        self.inspector_process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        self.inspector_process.kill()
                        self.inspector_process.wait(timeout=5)
                    
                    logger.info("Inspector进程已停止")
                except Exception as e:
                    logger.error(f"停止Inspector进程失败: {e}")
                finally:
                    self.inspector_process = None
            
            # 更新会话状态
            self.session.end_time = datetime.now()
            self.session.status = "completed"
            
            # 保存会话数据
            self._save_session()
            
            # 保存生成的代码
            self._save_generated_code()
            
            # 通知监听器
            self._notify_listeners("recording_stopped", self.session)
            
            logger.info(f"Inspector录制完成: {self.session.name} (总动作数: {len(self.session.actions)})")
            
            return self.session
            
        except Exception as e:
            logger.error(f"停止Inspector录制失败: {e}")
            raise Exception(f"停止Inspector录制失败: {str(e)}")
    
    def _save_session(self):
        """保存会话数据到文件"""
        try:
            session_file = settings.RECORDINGS_DIR / f"{self.session.id}_inspector_session.json"
            
            # 准备会话数据
            session_data = self.session.dict()
            session_data['stats'] = self.stats
            session_data['recording_method'] = 'inspector'
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Inspector会话数据已保存: {session_file}")
            
        except Exception as e:
            logger.error(f"保存Inspector会话数据失败: {e}")
    
    def _save_generated_code(self):
        """保存生成的代码文件"""
        try:
            if not self.code_file_path or not self.code_file_path.exists():
                return
            
            # 目标文件路径
            code_filename = f"{self.session.id}_inspector_code.py"
            target_path = settings.RECORDINGS_DIR / code_filename
            
            # 读取并保存代码
            with open(self.code_file_path, 'r', encoding='utf-8') as src:
                content = src.read()
            
            with open(target_path, 'w', encoding='utf-8') as dst:
                dst.write(content)
            
            logger.info(f"Inspector生成的代码已保存: {target_path}")
            
        except Exception as e:
            logger.error(f"保存Inspector生成的代码失败: {e}")
    
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
            
            logger.info("Inspector录制器资源清理完成")
            
        except Exception as e:
            logger.error(f"清理Inspector录制器资源失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()


# 全局Inspector录制器实例
inspector_recorder = InspectorTestRecorder() 