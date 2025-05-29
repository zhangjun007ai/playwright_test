import json
import asyncio
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from loguru import logger
from config.settings import settings
from core.models import TestSession, TestCase


class FileManager:
    """文件管理器类"""
    
    def __init__(self):
        self.sessions_cache = {}
        self.test_cases_cache = {}
    
    async def initialize(self):
        """初始化文件管理器"""
        logger.info("初始化文件管理器...")
        
        # 确保目录存在
        settings.create_directories()
        
        # 预加载现有会话
        await self._load_existing_sessions()
        
        logger.info("文件管理器初始化完成")
    
    async def _load_existing_sessions(self):
        """加载现有的会话文件"""
        try:
            session_files = list(settings.RECORDINGS_DIR.glob("*_session.json"))
            
            for session_file in session_files:
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    session = TestSession(**session_data)
                    self.sessions_cache[session.id] = session
                    
                except Exception as e:
                    logger.warning(f"加载会话文件失败: {session_file}, 错误: {e}")
            
            logger.info(f"加载了 {len(self.sessions_cache)} 个现有会话")
            
        except Exception as e:
            logger.error(f"加载现有会话失败: {e}")
    
    async def save_session(self, session: TestSession) -> bool:
        """保存会话数据"""
        try:
            session_file = settings.RECORDINGS_DIR / f"{session.id}_session.json"
            
            # 转换为字典并处理datetime序列化
            session_dict = session.dict()
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_dict, f, ensure_ascii=False, indent=2, default=str)
            
            # 更新缓存
            self.sessions_cache[session.id] = session
            
            logger.info(f"会话保存成功: {session.id}")
            return True
            
        except Exception as e:
            logger.error(f"保存会话失败: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[TestSession]:
        """获取指定会话"""
        try:
            # 先从缓存查找
            if session_id in self.sessions_cache:
                return self.sessions_cache[session_id]
            
            # 从文件加载
            session_file = settings.RECORDINGS_DIR / f"{session_id}_session.json"
            if not session_file.exists():
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            session = TestSession(**session_data)
            
            # 缓存结果
            self.sessions_cache[session_id] = session
            
            return session
            
        except Exception as e:
            logger.error(f"获取会话失败: {session_id}, 错误: {e}")
            return None
    
    async def get_all_sessions(self) -> List[TestSession]:
        """获取所有会话"""
        try:
            # 重新扫描文件以确保数据最新
            await self._load_existing_sessions()
            
            # 按创建时间倒序排列
            sessions = sorted(
                self.sessions_cache.values(),
                key=lambda x: x.start_time,
                reverse=True
            )
            
            return sessions
            
        except Exception as e:
            logger.error(f"获取所有会话失败: {e}")
            return []
    
    async def delete_session(self, session_id: str) -> bool:
        """删除指定会话及相关文件"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # 删除会话文件
            session_file = settings.RECORDINGS_DIR / f"{session_id}_session.json"
            if session_file.exists():
                session_file.unlink()
            
            # 删除追踪文件
            if session.trace_file and Path(session.trace_file).exists():
                Path(session.trace_file).unlink()
            
            # 删除视频文件
            if session.video_file and Path(session.video_file).exists():
                Path(session.video_file).unlink()
            
            # 删除相关截图
            await self._delete_session_screenshots(session)
            
            # 从缓存移除
            if session_id in self.sessions_cache:
                del self.sessions_cache[session_id]
            
            logger.info(f"会话删除成功: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除会话失败: {session_id}, 错误: {e}")
            return False
    
    async def _delete_session_screenshots(self, session: TestSession):
        """删除会话相关的截图文件"""
        try:
            for action in session.actions:
                if action.screenshot_path and Path(action.screenshot_path).exists():
                    Path(action.screenshot_path).unlink()
                    logger.debug(f"删除截图: {action.screenshot_path}")
        except Exception as e:
            logger.warning(f"删除截图失败: {e}")
    
    async def save_test_case(self, test_case: TestCase) -> bool:
        """保存测试用例"""
        try:
            test_case_file = settings.RECORDINGS_DIR / f"testcase_{test_case.id}.json"
            
            # 转换为字典
            test_case_dict = test_case.dict()
            
            with open(test_case_file, 'w', encoding='utf-8') as f:
                json.dump(test_case_dict, f, ensure_ascii=False, indent=2, default=str)
            
            # 更新缓存
            self.test_cases_cache[test_case.id] = test_case
            
            logger.info(f"测试用例保存成功: {test_case.id}")
            return True
            
        except Exception as e:
            logger.error(f"保存测试用例失败: {e}")
            return False 