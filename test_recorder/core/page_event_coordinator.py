#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
页面事件协调器
协调多个页面的事件流，维护事件时序和上下文关系
处理事件去重、合并和排序

作者: AI Assistant
版本: 1.0.0
"""

import asyncio
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from collections import deque
from loguru import logger


@dataclass
class CrossWindowEvent:
    """跨窗口事件数据结构"""
    event_id: str
    window_id: str
    event_type: str
    timestamp: float
    url: str
    title: str
    element_info: Dict[str, Any]
    additional_data: Dict[str, Any]
    parent_window_id: Optional[str] = None
    is_cross_window: bool = False
    sequence_number: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CrossWindowEvent':
        """从字典创建事件对象"""
        return cls(**data)


class EventBuffer:
    """事件缓冲器 - 处理事件的暂存和排序"""
    
    def __init__(self, buffer_size: int = 100, flush_interval: float = 0.5):
        self.buffer: deque = deque(maxlen=buffer_size)
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.last_flush_time = time.time()
        
    def add_event(self, event: CrossWindowEvent):
        """添加事件到缓冲区"""
        self.buffer.append(event)
    
    def should_flush(self) -> bool:
        """判断是否应该刷新缓冲区"""
        current_time = time.time()
        return (
            len(self.buffer) >= self.buffer_size or
            (current_time - self.last_flush_time) >= self.flush_interval
        )
    
    def flush(self) -> List[CrossWindowEvent]:
        """刷新缓冲区，返回排序后的事件列表"""
        if not self.buffer:
            return []
        
        # 按时间戳排序
        sorted_events = sorted(self.buffer, key=lambda e: e.timestamp)
        self.buffer.clear()
        self.last_flush_time = time.time()
        
        return sorted_events
    
    def get_pending_count(self) -> int:
        """获取待处理事件数量"""
        return len(self.buffer)


class PageEventCoordinator:
    """页面事件协调器 - 协调多个页面的事件流"""
    
    def __init__(self, buffer_size: int = 100, flush_interval: float = 0.5):
        self.event_buffer = EventBuffer(buffer_size, flush_interval)
        self.is_active = False
        self.sequence_counter = 0
        
        # 事件处理回调
        self._event_processed_callbacks: List[Callable] = []
        self._batch_processed_callbacks: List[Callable] = []
        
        # 窗口状态跟踪
        self.window_states: Dict[str, Dict[str, Any]] = {}
        
        # 事件去重
        self.recent_events: deque = deque(maxlen=50)  # 保留最近50个事件的指纹
        
        # 异步任务
        self._flush_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """启动事件协调器"""
        try:
            if self.is_active:
                logger.warning("事件协调器已在运行")
                return
            
            self.is_active = True
            self.sequence_counter = 0
            
            # 启动定期刷新任务
            self._flush_task = asyncio.create_task(self._periodic_flush())
            
            logger.info("页面事件协调器已启动")
            
        except Exception as e:
            logger.error(f"启动事件协调器失败: {e}")
            raise
    
    async def stop(self):
        """停止事件协调器"""
        try:
            if not self.is_active:
                return
            
            self.is_active = False
            
            # 停止刷新任务
            if self._flush_task and not self._flush_task.done():
                self._flush_task.cancel()
                try:
                    await self._flush_task
                except asyncio.CancelledError:
                    pass
            
            # 处理剩余事件
            await self._flush_events()
            
            logger.info("页面事件协调器已停止")
            
        except Exception as e:
            logger.error(f"停止事件协调器失败: {e}")
    
    async def add_event(self, window_id: str, event_type: str, url: str, title: str,
                       element_info: Dict[str, Any], additional_data: Dict[str, Any] = None,
                       parent_window_id: str = None) -> str:
        """添加事件到协调器"""
        try:
            if not self.is_active:
                logger.warning("事件协调器未启动，忽略事件")
                return ""
            
            # 生成事件ID和时间戳
            event_id = f"{window_id}_{int(time.time() * 1000)}_{self.sequence_counter}"
            timestamp = time.time()
            
            # 创建事件对象
            event = CrossWindowEvent(
                event_id=event_id,
                window_id=window_id,
                event_type=event_type,
                timestamp=timestamp,
                url=url,
                title=title,
                element_info=element_info or {},
                additional_data=additional_data or {},
                parent_window_id=parent_window_id,
                is_cross_window=parent_window_id is not None,
                sequence_number=self.sequence_counter
            )
            
            self.sequence_counter += 1
            
            # 事件去重检查
            if self._is_duplicate_event(event):
                logger.debug(f"检测到重复事件，跳过: {event_id}")
                return event_id
            
            # 添加到缓冲区
            self.event_buffer.add_event(event)
            
            # 更新窗口状态
            self._update_window_state(window_id, event)
            
            # 记录事件指纹用于去重
            self._record_event_fingerprint(event)
            
            logger.debug(f"事件已添加到协调器: {event_type} - {window_id}")
            
            # 检查是否需要立即刷新
            if self.event_buffer.should_flush():
                await self._flush_events()
            
            return event_id
            
        except Exception as e:
            logger.error(f"添加事件失败: {e}")
            return ""
    
    def _is_duplicate_event(self, event: CrossWindowEvent) -> bool:
        """检查是否为重复事件"""
        try:
            # 生成事件指纹（基于事件类型、窗口ID、元素信息等）
            fingerprint = self._generate_event_fingerprint(event)
            
            # 检查最近事件中是否有相同指纹
            return fingerprint in self.recent_events
            
        except Exception as e:
            logger.error(f"检查重复事件失败: {e}")
            return False
    
    def _generate_event_fingerprint(self, event: CrossWindowEvent) -> str:
        """生成事件指纹用于去重"""
        try:
            # 基于事件关键信息生成指纹
            element_key = ""
            if event.element_info:
                # 使用元素的关键属性生成指纹
                element_key = f"{event.element_info.get('tag', '')}{event.element_info.get('id', '')}{event.element_info.get('class', '')}"
            
            fingerprint_data = f"{event.window_id}:{event.event_type}:{element_key}:{event.url}"
            return fingerprint_data
            
        except Exception as e:
            logger.error(f"生成事件指纹失败: {e}")
            return f"{event.window_id}:{event.event_type}:{time.time()}"
    
    def _record_event_fingerprint(self, event: CrossWindowEvent):
        """记录事件指纹"""
        try:
            fingerprint = self._generate_event_fingerprint(event)
            self.recent_events.append(fingerprint)
        except Exception as e:
            logger.error(f"记录事件指纹失败: {e}")
    
    def _update_window_state(self, window_id: str, event: CrossWindowEvent):
        """更新窗口状态"""
        try:
            if window_id not in self.window_states:
                self.window_states[window_id] = {}
            
            window_state = self.window_states[window_id]
            window_state['last_event_time'] = event.timestamp
            window_state['last_event_type'] = event.event_type
            window_state['last_url'] = event.url
            window_state['event_count'] = window_state.get('event_count', 0) + 1
            
        except Exception as e:
            logger.error(f"更新窗口状态失败: {e}")
    
    async def _periodic_flush(self):
        """定期刷新事件缓冲区"""
        try:
            while self.is_active:
                await asyncio.sleep(self.event_buffer.flush_interval)
                
                if self.event_buffer.should_flush():
                    await self._flush_events()
                    
        except asyncio.CancelledError:
            logger.debug("定期刷新任务已取消")
        except Exception as e:
            logger.error(f"定期刷新失败: {e}")
    
    async def _flush_events(self):
        """刷新事件缓冲区"""
        try:
            events = self.event_buffer.flush()
            if not events:
                return
            
            logger.debug(f"刷新 {len(events)} 个事件")
            
            # 按窗口分组处理事件
            window_groups = self._group_events_by_window(events)
            
            # 分析跨窗口关系
            self._analyze_cross_window_relationships(events)
            
            # 触发事件处理回调
            for event in events:
                await self._notify_event_processed(event)
            
            # 触发批处理回调
            await self._notify_batch_processed(events)
            
        except Exception as e:
            logger.error(f"刷新事件失败: {e}")
    
    def _group_events_by_window(self, events: List[CrossWindowEvent]) -> Dict[str, List[CrossWindowEvent]]:
        """按窗口分组事件"""
        window_groups = {}
        for event in events:
            window_id = event.window_id
            if window_id not in window_groups:
                window_groups[window_id] = []
            window_groups[window_id].append(event)
        return window_groups
    
    def _analyze_cross_window_relationships(self, events: List[CrossWindowEvent]):
        """分析跨窗口关系"""
        try:
            # 检测跨窗口操作模式
            for i, event in enumerate(events):
                if i > 0:
                    prev_event = events[i-1]
                    
                    # 检测窗口切换
                    if (event.window_id != prev_event.window_id and 
                        abs(event.timestamp - prev_event.timestamp) < 2.0):  # 2秒内的窗口切换
                        event.is_cross_window = True
                        
                        # 如果前一个事件可能触发了新窗口创建
                        if (prev_event.event_type in ['click', 'submit'] and 
                            'target' in prev_event.element_info and 
                            prev_event.element_info.get('target') == '_blank'):
                            event.parent_window_id = prev_event.window_id
            
        except Exception as e:
            logger.error(f"分析跨窗口关系失败: {e}")
    
    def get_window_state(self, window_id: str) -> Optional[Dict[str, Any]]:
        """获取窗口状态"""
        return self.window_states.get(window_id)
    
    def get_all_window_states(self) -> Dict[str, Dict[str, Any]]:
        """获取所有窗口状态"""
        return self.window_states.copy()
    
    def get_pending_events_count(self) -> int:
        """获取待处理事件数量"""
        return self.event_buffer.get_pending_count()
    
    def clear_window_state(self, window_id: str):
        """清理窗口状态"""
        try:
            if window_id in self.window_states:
                del self.window_states[window_id]
                logger.debug(f"已清理窗口状态: {window_id}")
        except Exception as e:
            logger.error(f"清理窗口状态失败: {e}")
    
    # 事件回调管理
    def on_event_processed(self, callback: Callable[[CrossWindowEvent], None]):
        """注册事件处理回调"""
        self._event_processed_callbacks.append(callback)
    
    def on_batch_processed(self, callback: Callable[[List[CrossWindowEvent]], None]):
        """注册批处理回调"""
        self._batch_processed_callbacks.append(callback)
    
    async def _notify_event_processed(self, event: CrossWindowEvent):
        """通知事件处理完成"""
        for callback in self._event_processed_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"事件处理回调执行失败: {e}")
    
    async def _notify_batch_processed(self, events: List[CrossWindowEvent]):
        """通知批处理完成"""
        for callback in self._batch_processed_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(events)
                else:
                    callback(events)
            except Exception as e:
                logger.error(f"批处理回调执行失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取协调器状态"""
        return {
            "is_active": self.is_active,
            "sequence_counter": self.sequence_counter,
            "pending_events": self.get_pending_events_count(),
            "window_count": len(self.window_states),
            "buffer_size": self.event_buffer.buffer_size,
            "flush_interval": self.event_buffer.flush_interval,
            "recent_events_count": len(self.recent_events)
        }
    
    async def force_flush(self):
        """强制刷新事件缓冲区"""
        await self._flush_events() 