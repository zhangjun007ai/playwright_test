#!/usr/bin/env python3
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from loguru import logger

from config.settings import settings
from core.models import TestSession, ActionRecord, TestCase
# 使用新的实时录制器
from core.realtime_recorder import realtime_recorder
# 新增：导入Inspector录制器
from core.inspector_recorder import inspector_recorder
from core.ai_generator import ai_generator
from utils.file_manager import FileManager
from utils.export_handler import export_handler

# 创建文件管理器实例
file_manager = FileManager()

# 创建FastAPI应用
app = FastAPI(title="测试用例录制系统（跨窗口增强版）", version="2.0.0")

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.message_processor_task = None
        self.is_processing = False
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket连接已建立，当前连接数: {len(self.active_connections)}")
        
        # 启动消息处理器（如果还没有启动）
        if self.message_processor_task is None or self.message_processor_task.done():
            logger.info("启动WebSocket消息处理器")
            self.message_processor_task = asyncio.create_task(self.process_message_queue())
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket连接已断开，当前连接数: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
            logger.debug(f"发送个人消息成功: {message[:100]}...")
        except Exception as e:
            logger.error(f"发送个人消息失败: {e}")
    
    async def broadcast(self, message: str):
        """广播消息到所有连接"""
        if not self.active_connections:
            logger.debug("没有活动的WebSocket连接，跳过广播")
            return
            
        logger.debug(f"广播消息到 {len(self.active_connections)} 个连接: {message[:100]}...")
        disconnected = []
        success_count = 0
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
                success_count += 1
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                disconnected.append(connection)
        
        # 移除断开的连接
        for connection in disconnected:
            self.disconnect(connection)
        
        logger.debug(f"广播完成，成功: {success_count}，失败: {len(disconnected)}")
    
    async def process_message_queue(self):
        """处理录制器的消息队列"""
        logger.info("WebSocket消息队列处理器已启动")
        self.is_processing = True
        message_count = 0
        
        while True:
            try:
                # 处理实时录制器的消息队列
                realtime_queue = realtime_recorder.get_message_queue()
                inspector_queue = inspector_recorder.get_message_queue()
                
                # 检查实时录制器队列
                realtime_queue_size = realtime_queue.qsize()
                inspector_queue_size = inspector_queue.qsize()
                
                if realtime_queue_size > 0:
                    logger.debug(f"实时录制器队列中有 {realtime_queue_size} 条消息待处理")
                
                if inspector_queue_size > 0:
                    logger.debug(f"Inspector录制器队列中有 {inspector_queue_size} 条消息待处理")
                
                # 处理实时录制器消息
                while not realtime_queue.empty():
                    try:
                        event_type, data = realtime_queue.get_nowait()
                        message_count += 1
                        logger.info(f"处理实时录制器消息 #{message_count}: {event_type}")
                        await self._process_recorder_message(event_type, data, "realtime")
                    except Exception as e:
                        logger.error(f"处理实时录制器消息失败: {e}")
                
                # 处理Inspector录制器消息
                while not inspector_queue.empty():
                    try:
                        event_type, data = inspector_queue.get_nowait()
                        message_count += 1
                        logger.info(f"处理Inspector录制器消息 #{message_count}: {event_type}")
                        await self._process_recorder_message(event_type, data, "inspector")
                    except Exception as e:
                        logger.error(f"处理Inspector录制器消息失败: {e}")
                
                # 短暂休眠避免CPU占用过高
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"消息队列处理器异常: {e}")
                import traceback
                logger.error(f"异常详情: {traceback.format_exc()}")
                await asyncio.sleep(1)
    
    async def _process_recorder_message(self, event_type: str, data: any, recorder_type: str):
        """处理录制器消息的统一方法（增强跨窗口支持）"""
        try:
            if event_type == 'recording_started':
                # 录制开始消息（增强版）
                message = {
                    "type": "recording_started",
                    "recorder_type": recorder_type,
                    "data": data,
                    "cross_window_support": True,
                    "features": data.get('features', [])
                }
                message_json = json.dumps(message)
                await self.broadcast(message_json)
                logger.info(f"{recorder_type}录制器已开始录制（跨窗口增强版）")
                
            elif event_type == 'recording_stopped':
                # 录制停止消息（增强版）
                enhanced_data = data.copy() if isinstance(data, dict) else {}
                
                # 添加跨窗口统计信息
                if recorder_type == "realtime" and hasattr(realtime_recorder, 'get_cross_window_stats'):
                    enhanced_data['cross_window_stats'] = realtime_recorder.get_cross_window_stats()
                elif recorder_type == "inspector" and hasattr(inspector_recorder, 'get_cross_window_statistics'):
                    enhanced_data['cross_window_stats'] = inspector_recorder.get_cross_window_statistics()
                
                message = {
                    "type": "recording_stopped", 
                    "recorder_type": recorder_type,
                    "data": enhanced_data,
                    "cross_window_support": True
                }
                message_json = json.dumps(message)
                await self.broadcast(message_json)
                logger.info(f"{recorder_type}录制器已停止录制（跨窗口增强版）")
                
            elif event_type == 'action_recorded':
                # 处理新的消息格式，包含跨窗口信息
                if isinstance(data, dict) and 'action_record' in data:
                    # 新格式：包含action_record, playwright_code, analyzed_element
                    action_record = data['action_record']
                    playwright_code = data.get('playwright_code', '')
                    analyzed_element = data.get('analyzed_element', {})
                    
                    # 提取跨窗口信息
                    window_info = data.get('window_info', {})
                    cross_window_stats = data.get('cross_window_stats', {})
                    is_cross_window = data.get('is_cross_window', False)
                    
                    logger.debug(f"处理{recorder_type}录制器新格式消息: {action_record.action_type}, 跨窗口: {is_cross_window}")
                    
                    message = {
                        "type": "action_recorded",
                        "recorder_type": recorder_type,
                        "action": {
                            "id": action_record.id,
                            "action_type": action_record.action_type,
                            "timestamp": action_record.timestamp.isoformat(),
                            "page_url": action_record.page_url,
                            "page_title": action_record.page_title,
                            "title": action_record.page_title,  # 兼容前端
                            "description": action_record.description,
                            "element_info": action_record.element_info,
                            "screenshot_path": action_record.screenshot_path,
                            "additional_data": action_record.additional_data,
                            # 新增Playwright相关信息
                            "playwright_code": playwright_code,
                            "analyzed_element": analyzed_element,
                            # 跨窗口增强信息
                            "window_info": window_info,
                            "cross_window_stats": cross_window_stats,
                            "is_cross_window": is_cross_window
                        }
                    }
                else:
                    # 兼容旧格式
                    action_record = data
                    logger.debug(f"处理{recorder_type}录制器旧格式消息: {action_record.action_type}")
                    
                    message = {
                        "type": "action_recorded",
                        "recorder_type": recorder_type,
                        "action": {
                            "id": action_record.id,
                            "action_type": action_record.action_type,
                            "timestamp": action_record.timestamp.isoformat(),
                            "page_url": action_record.page_url,
                            "page_title": action_record.page_title,
                            "title": action_record.page_title,  # 兼容前端
                            "description": action_record.description,
                            "element_info": action_record.element_info,
                            "screenshot_path": action_record.screenshot_path,
                            "additional_data": action_record.additional_data,
                            # 默认跨窗口信息
                            "window_info": {},
                            "cross_window_stats": {},
                            "is_cross_window": False
                        }
                    }
                
                message_json = json.dumps(message, default=str)
                await self.broadcast(message_json)
                logger.debug(f"广播{recorder_type}录制器动作: {message['action']['action_type']}")
                
            else:
                # 其他类型的消息
                message = {
                    "type": event_type,
                    "recorder_type": recorder_type,
                    "data": data
                }
                message_json = json.dumps(message, default=str)
                await self.broadcast(message_json)
                logger.debug(f"广播{recorder_type}录制器消息: {event_type}")
                
        except Exception as e:
            logger.error(f"处理{recorder_type}录制器消息失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")

# 创建连接管理器实例
manager = ConnectionManager()

# 数据模型定义
class StartRecordingRequest(BaseModel):
    test_name: str
    description: str = ""
    target_url: str = ""
    # 增强：录制器类型选择
    recorder_type: str = "realtime"  # "realtime" 或 "inspector"
    # 新增：跨窗口选项
    cross_window_enabled: bool = True  # 是否启用跨窗口录制

class NavigateRequest(BaseModel):
    url: str

class ExportRequest(BaseModel):
    session_id: str
    format: str = "excel"
    include_screenshots: bool = True
    author: str = ""
    version: str = "1.0"
    remarks: str = ""
    # 新增：包含跨窗口信息
    include_cross_window_info: bool = True

# 路由定义
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """主页"""
    try:
        template_path = settings.TEMPLATES_DIR / "index.html"
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"读取模板失败: {e}")
        return HTMLResponse("<h1>模板加载失败</h1>", status_code=500)

@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """停止按钮测试页面"""
    try:
        test_template_path = settings.STATIC_DIR / "test_stop_button.html"
        with open(test_template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"读取测试模板失败: {e}")
        return HTMLResponse("<h1>测试页面加载失败</h1>", status_code=500)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接端点"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong"}), 
                    websocket
                )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        manager.disconnect(websocket)

@app.post("/api/recording/start")
async def start_recording(request: StartRecordingRequest):
    """开始录制测试用例（增强跨窗口支持）"""
    try:
        logger.info(f"收到录制开始请求: {request.test_name}, 录制器类型: {request.recorder_type}, 跨窗口: {request.cross_window_enabled}")
        
        # 根据录制器类型选择相应的录制器
        if request.recorder_type == "inspector":
            # 初始化Inspector录制器
            try:
                inspector_recorder.initialize()
                session_id = inspector_recorder.start_recording(
                    test_name=request.test_name,
                    description=request.description
                )
                
                return {
                    "success": True,
                    "message": f"Inspector录制开始成功: {request.test_name}",
                    "session_id": session_id,
                    "recorder_type": "inspector",
                    "cross_window_enabled": True,  # Inspector总是支持跨窗口
                    "features": [
                        "跨窗口检测",
                        "弹窗处理", 
                        "窗口关系分析",
                        "增强代码生成",
                        "高级代码分析",
                        "分析报告生成"
                    ],
                    "instructions": "请在新打开的Playwright Inspector浏览器窗口中进行操作。支持完整的跨窗口录制，包括弹窗和新标签页操作。每个操作都会被实时记录并生成相应的Playwright代码。",
                    "cross_window_info": {
                        "window_detection": True,
                        "popup_handling": True,
                        "window_relationships": True,
                        "enhanced_analysis": True
                    }
                }
                
            except Exception as e:
                logger.error(f"Inspector录制器启动失败: {e}")
                raise HTTPException(status_code=500, detail=f"Inspector录制器启动失败: {str(e)}")
        
        else:
            # 使用实时录制器（默认）
            try:
                realtime_recorder.initialize()
                session_id = realtime_recorder.start_recording(
                    test_name=request.test_name,
                    description=request.description
                )
                
                # 检查跨窗口功能是否可用
                cross_window_available = hasattr(realtime_recorder, 'is_cross_window_recording_active')
                
                return {
                    "success": True,
                    "message": f"实时录制开始成功: {request.test_name}",
                    "session_id": session_id,
                    "recorder_type": "realtime",
                    "cross_window_enabled": request.cross_window_enabled and cross_window_available,
                    "features": [
                        "实时事件监听",
                        "跨窗口检测",
                        "自动窗口管理",
                        "事件协调",
                        "实时统计"
                    ] if cross_window_available else [
                        "实时事件监听",
                        "基础录制功能"
                    ],
                    "instructions": f"实时录制已开始，请在打开的浏览器中进行操作。{'支持跨窗口操作录制，包括弹窗和新标签页。' if cross_window_available else '当前为基础录制模式。'}",
                    "cross_window_info": {
                        "window_detection": cross_window_available,
                        "popup_handling": cross_window_available,
                        "window_relationships": cross_window_available,
                        "real_time_coordination": cross_window_available
                    }
                }
                
            except Exception as e:
                logger.error(f"实时录制器启动失败: {e}")
                raise HTTPException(status_code=500, detail=f"实时录制器启动失败: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"开始录制失败: {e}")
        raise HTTPException(status_code=500, detail=f"开始录制失败: {str(e)}")

@app.post("/api/recording/stop")
async def stop_recording():
    """停止录制测试用例（增强跨窗口支持）"""
    try:
        result_sessions = []
        
        # 尝试停止实时录制器
        if realtime_recorder.is_recording:
            try:
                session = realtime_recorder.stop_recording()
                
                # 获取跨窗口统计信息
                cross_window_stats = {}
                if hasattr(realtime_recorder, 'get_cross_window_stats'):
                    cross_window_stats = realtime_recorder.get_cross_window_stats()
                
                result_sessions.append({
                    "recorder_type": "realtime",
                    "session": session,
                    "success": True,
                    "cross_window_stats": cross_window_stats
                })
                logger.info("实时录制器已停止")
            except Exception as e:
                logger.error(f"停止实时录制器失败: {e}")
                result_sessions.append({
                    "recorder_type": "realtime",
                    "success": False,
                    "error": str(e)
                })
        
        # 尝试停止Inspector录制器
        if inspector_recorder.is_recording:
            try:
                session = inspector_recorder.stop_recording()
                
                # 获取跨窗口统计信息
                cross_window_stats = {}
                if hasattr(inspector_recorder, 'get_cross_window_statistics'):
                    cross_window_stats = inspector_recorder.get_cross_window_statistics()
                
                result_sessions.append({
                    "recorder_type": "inspector",
                    "session": session,
                    "success": True,
                    "cross_window_stats": cross_window_stats
                })
                logger.info("Inspector录制器已停止")
            except Exception as e:
                logger.error(f"停止Inspector录制器失败: {e}")
                result_sessions.append({
                    "recorder_type": "inspector",
                    "success": False,
                    "error": str(e)
                })
        
        if not result_sessions:
            return {
                "success": False,
                "message": "没有正在进行的录制",
                "sessions": []
            }
        
        # 构建返回结果
        success_sessions = [s for s in result_sessions if s.get("success")]
        failed_sessions = [s for s in result_sessions if not s.get("success")]
        
        if success_sessions:
            # 取第一个成功的会话作为主要结果
            main_result = success_sessions[0]
            main_session = main_result["session"]
            main_cross_window_stats = main_result.get("cross_window_stats", {})
            
            # 计算跨窗口摘要信息
            cross_window_summary = {
                "total_windows": 0,
                "cross_window_actions": 0,
                "popup_windows": 0,
                "window_switches": 0,
                "has_cross_window_activity": False
            }
            
            if main_cross_window_stats:
                if main_result["recorder_type"] == "realtime":
                    # 实时录制器的统计格式
                    manager_stats = main_cross_window_stats.get("manager_stats", {})
                    cross_window_summary.update({
                        "total_windows": main_cross_window_stats.get("total_windows", 0),
                        "cross_window_actions": main_cross_window_stats.get("cross_window_actions", 0),
                        "popup_windows": main_cross_window_stats.get("popup_windows", 0),
                        "current_windows": manager_stats.get("window_detector", {}).get("total_windows", 0)
                    })
                elif main_result["recorder_type"] == "inspector":
                    # Inspector录制器的统计格式
                    inspector_stats = main_cross_window_stats.get("cross_window_stats", {})
                    cross_window_summary.update({
                        "total_windows": inspector_stats.get("total_windows_created", 0),
                        "cross_window_actions": inspector_stats.get("cross_window_operations", 0),
                        "popup_windows": inspector_stats.get("popup_windows", 0),
                        "window_switches": inspector_stats.get("window_switches", 0)
                    })
                
                cross_window_summary["has_cross_window_activity"] = (
                    cross_window_summary["total_windows"] > 1 or 
                    cross_window_summary["cross_window_actions"] > 0 or 
                    cross_window_summary["popup_windows"] > 0
                )
            
            return {
                "success": True,
                "message": f"录制停止成功，共记录 {len(main_session.actions)} 个操作" + 
                          (f"，包含 {cross_window_summary['cross_window_actions']} 个跨窗口操作" if cross_window_summary['has_cross_window_activity'] else ""),
                "session": {
                    "id": main_session.id,
                    "name": main_session.name,
                    "description": main_session.description,
                    "start_time": main_session.start_time.isoformat(),
                    "end_time": main_session.end_time.isoformat() if main_session.end_time else None,
                    "action_count": len(main_session.actions),
                    "status": main_session.status
                },
                "cross_window_summary": cross_window_summary,
                "cross_window_stats": main_cross_window_stats,
                "recorder_type": main_result["recorder_type"],
                "all_results": result_sessions,
                "additional_files": {
                    "enhanced_code": f"{main_session.id}_inspector_enhanced_code.py" if main_result["recorder_type"] == "inspector" else None,
                    "analysis_report": f"{main_session.id}_cross_window_analysis.md" if main_result["recorder_type"] == "inspector" else None,
                    "original_code": f"{main_session.id}_inspector_original_code.py" if main_result["recorder_type"] == "inspector" else None
                }
            }
        else:
            # 所有录制器都失败了
            error_messages = [s.get("error", "未知错误") for s in failed_sessions]
            raise HTTPException(status_code=500, detail=f"停止录制失败: {'; '.join(error_messages)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止录制失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止录制失败: {str(e)}")

@app.post("/api/navigate")
async def navigate(request: NavigateRequest):
    """导航到指定URL"""
    try:
        logger.info(f"收到导航请求: {request.url}")
        
        # 这里可以添加导航逻辑
        # 由于使用实时录制器，导航会自动被监听和记录
        
        return {
            "success": True,
            "message": f"导航请求已发送: {request.url}"
        }
        
    except Exception as e:
        logger.error(f"导航失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/status")
async def get_status():
    """获取录制状态"""
    try:
        return {
            "recording": realtime_recorder.is_recording,
            "action_count": realtime_recorder.action_count,
            "session_id": realtime_recorder.session.id if realtime_recorder.session else None
        }
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        return {
            "recording": False,
            "action_count": 0,
            "session_id": None
        }

@app.get("/api/sessions")
async def get_sessions():
    """获取所有录制会话"""
    try:
        # 从文件系统加载会话数据
        sessions_dir = settings.RECORDINGS_DIR
        session_files = list(sessions_dir.glob("*_session.json"))
        sessions = []
        
        for session_file in session_files:
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                    # 转换时间戳字符串为datetime对象
                    if 'start_time' in session_data:
                        session_data['start_time'] = datetime.fromisoformat(session_data['start_time'])
                    if 'end_time' in session_data:
                        session_data['end_time'] = datetime.fromisoformat(session_data['end_time'])
                    sessions.append(session_data)
            except Exception as e:
                logger.error(f"加载会话文件失败 {session_file}: {e}")
                continue
        
        # 按开始时间倒序排序
        sessions.sort(key=lambda x: x.get('start_time', datetime.min), reverse=True)
        
        return sessions
        
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """获取指定会话"""
    try:
        session = file_manager.get_session(session_id)
        if session:
            return {
                "success": True,
                "session": session
            }
        else:
            raise HTTPException(status_code=404, detail="会话未找到")
    except Exception as e:
        logger.error(f"获取会话失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除指定会话"""
    try:
        success = file_manager.delete_session(session_id)
        if success:
            return {
                "success": True,
                "message": "会话删除成功"
            }
        else:
            raise HTTPException(status_code=404, detail="会话未找到")
    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/generate-testcase/{session_id}")
async def generate_testcase(session_id: str):
    """生成测试用例"""
    try:
        logger.info(f"收到生成测试用例请求: {session_id}")
        
        # 获取会话数据
        session_data = file_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="会话未找到")
        
        # 生成测试用例
        test_case = ai_generator.generate_test_case(session_data)
        
        # 保存测试用例
        file_manager.save_test_case(session_id, test_case)
        
        return {
            "success": True,
            "test_case": test_case.dict(),
            "message": "测试用例生成成功"
        }
        
    except Exception as e:
        logger.error(f"生成测试用例失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/export")
async def export_testcase(request: ExportRequest):
    """导出测试用例（增强跨窗口支持）"""
    try:
        logger.info(f"收到导出请求: {request.session_id}, 格式: {request.format}, 包含跨窗口信息: {request.include_cross_window_info}")
        
        # 获取会话数据
        session_data = file_manager.get_session(request.session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="会话未找到")
        
        # 获取测试用例
        test_case = file_manager.get_test_case(request.session_id)
        if not test_case:
            # 如果没有测试用例，先生成一个
            test_case = ai_generator.generate_test_case(session_data)
            file_manager.save_test_case(request.session_id, test_case)
        
        # 准备跨窗口信息（如果需要）
        cross_window_info = {}
        if request.include_cross_window_info:
            # 尝试读取跨窗口分析报告
            analysis_report_path = settings.RECORDINGS_DIR / f"{request.session_id}_cross_window_analysis.md"
            if analysis_report_path.exists():
                with open(analysis_report_path, 'r', encoding='utf-8') as f:
                    cross_window_info["analysis_report"] = f.read()
            
            # 尝试读取增强代码
            enhanced_code_path = settings.RECORDINGS_DIR / f"{request.session_id}_inspector_enhanced_code.py"
            if enhanced_code_path.exists():
                with open(enhanced_code_path, 'r', encoding='utf-8') as f:
                    cross_window_info["enhanced_code"] = f.read()
            
            # 尝试从会话数据中获取跨窗口统计
            if hasattr(session_data, 'additional_data') and session_data.additional_data:
                try:
                    import json
                    additional_data = json.loads(session_data.additional_data) if isinstance(session_data.additional_data, str) else session_data.additional_data
                    if 'cross_window_stats' in additional_data:
                        cross_window_info["statistics"] = additional_data['cross_window_stats']
                except:
                    pass
        
        # 导出文件（传递跨窗口信息）
        export_path = export_handler.export_test_case(
            test_case=test_case,
            format=request.format,
            include_screenshots=request.include_screenshots,
            author=request.author,
            version=request.version,
            remarks=request.remarks,
            cross_window_info=cross_window_info if request.include_cross_window_info else None
        )
        
        return {
            "success": True,
            "download_url": f"/api/download/{export_path.name}",
            "file_path": str(export_path),
            "message": "导出成功" + ("（包含跨窗口信息）" if request.include_cross_window_info and cross_window_info else ""),
            "included_cross_window_info": bool(cross_window_info) if request.include_cross_window_info else False,
            "cross_window_components": list(cross_window_info.keys()) if cross_window_info else []
        }
        
    except Exception as e:
        logger.error(f"导出失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """下载文件"""
    try:
        file_path = settings.EXPORTS_DIR / filename
        if file_path.exists():
            return FileResponse(
                path=str(file_path),
                filename=filename,
                media_type='application/octet-stream'
            )
        else:
            raise HTTPException(status_code=404, detail="文件未找到")
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/screenshot/{filename}")
async def get_screenshot(filename: str):
    """获取截图"""
    try:
        # 处理文件名中的路径
        if '/' in filename or '\\' in filename:
            # 如果是完整路径，直接使用
            file_path = Path(filename)
        else:
            # 如果只是文件名，在screenshots目录中查找
            file_path = settings.SCREENSHOTS_DIR / filename
        
        if file_path.exists():
            return FileResponse(
                path=str(file_path),
                media_type='image/png'
            )
        else:
            raise HTTPException(status_code=404, detail="截图未找到")
    except Exception as e:
        logger.error(f"获取截图失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recording/status")
async def get_recording_status():
    """获取录制器状态（增强跨窗口支持）"""
    try:
        # 获取实时录制器状态
        realtime_status = {
            "is_recording": realtime_recorder.is_recording,
            "current_session": None,
            "cross_window_support": True,
            "cross_window_stats": {}
        }
        
        if realtime_recorder.is_recording and realtime_recorder.session:
            session = realtime_recorder.session
            realtime_status["current_session"] = {
                "id": session.id,
                "name": session.name,
                "start_time": session.start_time.isoformat(),
                "action_count": len(session.actions)
            }
            
            # 添加跨窗口统计信息
            if hasattr(realtime_recorder, 'get_cross_window_stats'):
                realtime_status["cross_window_stats"] = realtime_recorder.get_cross_window_stats()
            
            # 添加窗口列表
            if hasattr(realtime_recorder, 'get_window_list'):
                realtime_status["window_list"] = realtime_recorder.get_window_list()
        
        # 获取Inspector录制器状态
        inspector_status = {
            "is_recording": inspector_recorder.is_recording,
            "current_session": None,
            "cross_window_support": True,
            "cross_window_stats": {}
        }
        
        if inspector_recorder.is_recording and inspector_recorder.session:
            session = inspector_recorder.session
            inspector_status["current_session"] = {
                "id": session.id,
                "name": session.name,
                "start_time": session.start_time.isoformat(),
                "action_count": len(session.actions)
            }
            
            # 添加跨窗口统计信息
            if hasattr(inspector_recorder, 'get_cross_window_statistics'):
                inspector_status["cross_window_stats"] = inspector_recorder.get_cross_window_statistics()
        
        # 确定活跃的录制器
        active_recorder = None
        if realtime_status["is_recording"]:
            active_recorder = "realtime"
        elif inspector_status["is_recording"]:
            active_recorder = "inspector"
        
        return {
            "success": True,
            "active_recorder": active_recorder,
            "realtime_recorder": realtime_status,
            "inspector_recorder": inspector_status,
            "message": f"当前活跃录制器: {active_recorder or '无'}",
            "cross_window_features": {
                "window_detection": True,
                "popup_handling": True,
                "window_relationships": True,
                "enhanced_code_generation": True
            }
        }
        
    except Exception as e:
        logger.error(f"获取录制状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取录制状态失败: {str(e)}")

@app.get("/api/recording/cross-window-stats")
async def get_cross_window_stats():
    """获取跨窗口录制统计信息"""
    try:
        stats = {
            "realtime_recorder": {},
            "inspector_recorder": {},
            "active_recorder": None
        }
        
        # 获取实时录制器的跨窗口统计
        if realtime_recorder.is_recording:
            stats["active_recorder"] = "realtime"
            if hasattr(realtime_recorder, 'get_cross_window_stats'):
                stats["realtime_recorder"] = realtime_recorder.get_cross_window_stats()
            if hasattr(realtime_recorder, 'get_window_list'):
                stats["realtime_recorder"]["window_list"] = realtime_recorder.get_window_list()
            if hasattr(realtime_recorder, 'get_main_window_info'):
                stats["realtime_recorder"]["main_window"] = realtime_recorder.get_main_window_info()
        
        # 获取Inspector录制器的跨窗口统计
        if inspector_recorder.is_recording:
            stats["active_recorder"] = "inspector"
            if hasattr(inspector_recorder, 'get_cross_window_statistics'):
                stats["inspector_recorder"] = inspector_recorder.get_cross_window_statistics()
        
        return {
            "success": True,
            "cross_window_stats": stats,
            "message": "跨窗口统计信息获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取跨窗口统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取跨窗口统计失败: {str(e)}")

@app.get("/api/recording/windows")
async def get_recording_windows():
    """获取当前录制的所有窗口信息"""
    try:
        windows_info = {
            "windows": [],
            "main_window": None,
            "popup_windows": [],
            "total_count": 0,
            "active_recorder": None
        }
        
        if realtime_recorder.is_recording:
            windows_info["active_recorder"] = "realtime"
            
            # 获取窗口列表
            if hasattr(realtime_recorder, 'get_window_list'):
                windows_info["windows"] = realtime_recorder.get_window_list()
                windows_info["total_count"] = len(windows_info["windows"])
            
            # 获取主窗口信息
            if hasattr(realtime_recorder, 'get_main_window_info'):
                windows_info["main_window"] = realtime_recorder.get_main_window_info()
            
            # 筛选弹窗窗口
            windows_info["popup_windows"] = [
                window for window in windows_info["windows"] 
                if window.get("is_popup", False)
            ]
        
        elif inspector_recorder.is_recording:
            windows_info["active_recorder"] = "inspector"
            
            # Inspector录制器的窗口信息从统计中获取
            if hasattr(inspector_recorder, 'get_cross_window_statistics'):
                stats = inspector_recorder.get_cross_window_statistics()
                window_analyzer_stats = stats.get('window_analyzer_stats', {})
                
                # 转换为窗口信息格式
                window_variables = window_analyzer_stats.get('window_variables', {})
                for page_var, window_id in window_variables.items():
                    windows_info["windows"].append({
                        "window_id": window_id,
                        "page_variable": page_var,
                        "is_popup": page_var != "page",
                        "is_main": page_var == "page"
                    })
                
                windows_info["total_count"] = len(windows_info["windows"])
                windows_info["popup_windows"] = [
                    window for window in windows_info["windows"] 
                    if window.get("is_popup", False)
                ]
                
                # 设置主窗口
                main_windows = [
                    window for window in windows_info["windows"] 
                    if window.get("is_main", False)
                ]
                if main_windows:
                    windows_info["main_window"] = main_windows[0]
        
        return {
            "success": True,
            "windows_info": windows_info,
            "message": f"获取到 {windows_info['total_count']} 个窗口信息"
        }
        
    except Exception as e:
        logger.error(f"获取窗口信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取窗口信息失败: {str(e)}")

@app.post("/api/recording/flush-events")
async def flush_cross_window_events():
    """强制刷新跨窗口事件"""
    try:
        flushed = False
        
        if realtime_recorder.is_recording:
            if hasattr(realtime_recorder, 'force_flush_cross_window_events'):
                await realtime_recorder.force_flush_cross_window_events()
                flushed = True
        
        elif inspector_recorder.is_recording:
            # Inspector录制器通常不需要手动刷新，因为它基于文件监控
            flushed = True
        
        return {
            "success": True,
            "flushed": flushed,
            "message": "跨窗口事件刷新完成" if flushed else "当前没有活跃的录制器"
        }
        
    except Exception as e:
        logger.error(f"刷新跨窗口事件失败: {e}")
        raise HTTPException(status_code=500, detail=f"刷新跨窗口事件失败: {str(e)}")

@app.get("/api/recording/enhanced-code/{session_id}")
async def get_enhanced_code(session_id: str):
    """获取增强版生成的代码（支持跨窗口）"""
    try:
        enhanced_code = ""
        code_stats = {}
        
        # 如果是Inspector录制器的会话，获取增强代码
        if hasattr(inspector_recorder, 'get_enhanced_code') and inspector_recorder.session and inspector_recorder.session.id == session_id:
            enhanced_code = inspector_recorder.get_enhanced_code()
            if hasattr(inspector_recorder, 'get_cross_window_statistics'):
                stats = inspector_recorder.get_cross_window_statistics()
                code_stats = stats.get('code_generator_stats', {})
        
        # 也可以从保存的文件中读取
        if not enhanced_code:
            enhanced_code_file = settings.RECORDINGS_DIR / f"{session_id}_inspector_enhanced_code.py"
            if enhanced_code_file.exists():
                with open(enhanced_code_file, 'r', encoding='utf-8') as f:
                    enhanced_code = f.read()
        
        return {
            "success": True,
            "enhanced_code": enhanced_code,
            "code_stats": code_stats,
            "message": "增强代码获取成功" if enhanced_code else "未找到增强代码"
        }
        
    except Exception as e:
        logger.error(f"获取增强代码失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取增强代码失败: {str(e)}")

@app.get("/api/recording/analysis-report/{session_id}")
async def get_analysis_report(session_id: str):
    """获取跨窗口分析报告"""
    try:
        report_content = ""
        
        # 尝试从文件中读取分析报告
        report_file = settings.RECORDINGS_DIR / f"{session_id}_cross_window_analysis.md"
        if report_file.exists():
            with open(report_file, 'r', encoding='utf-8') as f:
                report_content = f.read()
        
        return {
            "success": True,
            "report_content": report_content,
            "report_file": str(report_file) if report_file.exists() else None,
            "message": "分析报告获取成功" if report_content else "未找到分析报告"
        }
        
    except Exception as e:
        logger.error(f"获取分析报告失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分析报告失败: {str(e)}")

# 应用启动和关闭事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("测试用例录制系统启动")
    
    # 确保目录存在
    settings.RECORDINGS_DIR.mkdir(exist_ok=True)
    settings.SCREENSHOTS_DIR.mkdir(exist_ok=True)
    settings.EXPORTS_DIR.mkdir(exist_ok=True)
    settings.LOGS_DIR.mkdir(exist_ok=True)

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("测试用例录制系统关闭")
    
    # 清理录制器资源
    try:
        realtime_recorder.cleanup()
    except Exception as e:
        logger.error(f"清理录制器资源失败: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 