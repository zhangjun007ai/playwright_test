import asyncio
import json
import os
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.requests import Request
from pydantic import BaseModel
import uvicorn

from loguru import logger
from config.settings import settings
from core.windows_recorder import windows_recorder
from core.ai_generator import ai_generator
from core.models import TestSession, TestCase, SessionSummary, ExportConfig
from utils.file_manager import FileManager
# from utils.export_handler import ExportHandler  # 临时注释掉


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于Playwright的测试用例自动录制和生成系统"
)

# 静态文件和模板
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))

# 文件管理器和导出处理器
file_manager = FileManager()
# export_handler = ExportHandler()

# 全局变量存储WebSocket连接
active_websockets = []

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        active_websockets.append(websocket)  # 添加到全局列表

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in active_websockets:
            active_websockets.remove(websocket)

    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(message, ensure_ascii=False, default=str))

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, ensure_ascii=False, default=str))
            except:
                # 连接已断开，移除
                self.active_connections.remove(connection)

manager = ConnectionManager()

# 线程安全的消息队列
import queue
message_queue = queue.Queue()

# 后台任务处理消息队列
async def process_message_queue():
    """处理消息队列中的WebSocket消息"""
    while True:
        try:
            if not message_queue.empty():
                message = message_queue.get_nowait()
                # 广播到所有活跃的WebSocket连接
                for websocket in active_websockets.copy():
                    try:
                        await manager.send_message(message, websocket)
                        logger.info(f"WebSocket消息已发送: {message.get('type', 'unknown')}")
                    except Exception as e:
                        logger.error(f"WebSocket发送失败: {e}")
                        # 移除失效的连接
                        if websocket in active_websockets:
                            active_websockets.remove(websocket)
            
            await asyncio.sleep(0.1)  # 避免CPU占用过高
            
        except Exception as e:
            logger.error(f"处理消息队列失败: {e}")
            await asyncio.sleep(1)


# 请求模型
class StartRecordingRequest(BaseModel):
    test_name: str
    description: Optional[str] = ""
    target_url: Optional[str] = ""


class NavigateRequest(BaseModel):
    url: str


class ExportRequest(BaseModel):
    session_id: str
    format: str  # excel, word, json
    include_screenshots: bool = True
    author: str = "测试工程师"
    version: str = "1.0"


# API路由

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """主页"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return {
        "recording": windows_recorder.is_recording,
        "session_id": windows_recorder.session.id if windows_recorder.session else None,
        "browser_initialized": True,  # Windows录制器总是可用
        "action_count": len(windows_recorder.session.actions) if windows_recorder.session else 0
    }


@app.post("/api/recording/start")
async def start_recording(request: dict):
    """开始录制测试用例"""
    try:
        test_name = request.get("test_name", "")
        description = request.get("description", "")
        
        if not test_name:
            raise HTTPException(status_code=400, detail="测试名称不能为空")
        
        # 使用Windows录制器
        session_id = windows_recorder.start_recording(test_name, description)
        
        return {
            "success": True,
            "session_id": session_id,
            "message": f"开始录制测试用例: {test_name}"
        }
        
    except Exception as e:
        logger.error(f"开始录制失败: {e}")
        raise HTTPException(status_code=500, detail=f"开始录制失败: {str(e)}")


@app.post("/api/recording/stop")
async def stop_recording():
    """停止录制测试用例"""
    try:
        if not windows_recorder.is_recording:
            raise HTTPException(status_code=400, detail="当前没有正在进行的录制")
        
        session = windows_recorder.stop_recording()
        
        return {
            "success": True,
            "session": session.dict(),
            "message": f"录制完成: {session.name}"
        }
        
    except Exception as e:
        logger.error(f"停止录制失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止录制失败: {str(e)}")


@app.post("/api/recording/navigate")
async def navigate_to_url(request: dict):
    """导航到指定URL"""
    try:
        url = request.get("url", "")
        if not url:
            raise HTTPException(status_code=400, detail="URL不能为空")
        
        windows_recorder.navigate_to(url)
        
        return {
            "success": True,
            "message": f"导航到: {url}"
        }
        
    except Exception as e:
        logger.error(f"导航失败: {e}")
        raise HTTPException(status_code=500, detail=f"导航失败: {str(e)}")


@app.get("/api/sessions")
async def get_sessions():
    """获取所有录制会话"""
    try:
        sessions = await file_manager.get_all_sessions()
        summaries = [
            SessionSummary(
                session_id=session.id,
                name=session.name,
                start_time=session.start_time,
                end_time=session.end_time,
                action_count=session.action_count,
                duration=session.duration,
                status=session.status,
                browser_type=session.browser_type
            )
            for session in sessions
        ]
        
        return {"sessions": [summary.dict() for summary in summaries]}
        
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """获取指定会话详情"""
    try:
        session = await file_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {"session": session.dict()}
        
    except Exception as e:
        logger.error(f"获取会话详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除指定会话"""
    try:
        success = await file_manager.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-testcase/{session_id}")
async def generate_test_case(session_id: str):
    """生成测试用例"""
    try:
        session = await file_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 生成测试用例
        test_case = ai_generator.generate_test_case(session)
        
        # 保存测试用例
        await file_manager.save_test_case(test_case)
        
        return {"success": True, "test_case": test_case.dict()}
        
    except Exception as e:
        logger.error(f"生成测试用例失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/export")
async def export_test_case(request: ExportRequest, background_tasks: BackgroundTasks):
    """导出测试用例"""
    try:
        # 获取会话数据
        session = await file_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 生成测试用例
        test_case = ai_generator.generate_test_case(session)
        
        # 临时返回JSON格式的测试用例
        import json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{test_case.name}_{timestamp}.json"
        output_path = settings.EXPORTS_DIR / filename
        
        export_data = {
            "export_info": {
                "export_time": datetime.now().isoformat(),
                "format": "JSON",
                "author": request.author,
                "version": request.version
            },
            "test_case": test_case.dict()
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)

        return {"success": True, "download_url": f"/api/download/{filename}"}
        
    except Exception as e:
        logger.error(f"导出测试用例失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """下载文件"""
    try:
        file_path = settings.EXPORTS_DIR / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/screenshot/{filename}")
async def get_screenshot(filename: str):
    """获取截图"""
    try:
        # 从filename中提取实际的文件名
        file_path = None
        
        # 查找截图文件
        for screenshot_file in settings.SCREENSHOTS_DIR.glob("*.png"):
            if filename in screenshot_file.name:
                file_path = screenshot_file
                break
        
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="截图不存在")
        
        return FileResponse(
            path=str(file_path),
            media_type='image/png'
        )
        
    except Exception as e:
        logger.error(f"获取截图失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接"""
    await manager.connect(websocket)
    logger.info("WebSocket连接已建立")
    
    # 添加Windows录制器监听器
    def on_action_recorded(event_type: str, data):
        if event_type == "action_recorded":
            logger.info(f"收到录制事件: {data.action_type}")
            
            # 将消息放入队列，由主线程处理
            try:
                message = {
                    "type": "action_recorded",
                    "action": data.dict()
                }
                message_queue.put(message)
                logger.debug("消息已放入队列")
            except Exception as e:
                logger.error(f"放入消息队列失败: {e}")
    
    windows_recorder.add_listener(on_action_recorded)
    logger.info("WebSocket监听器已添加")
    
    try:
        while True:
            # 保持连接活跃
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 处理客户端消息
            if message.get("type") == "ping":
                await manager.send_message({"type": "pong"}, websocket)
                logger.debug("收到ping，发送pong")
            
    except WebSocketDisconnect:
        logger.info("WebSocket连接已断开")
        manager.disconnect(websocket)
        windows_recorder.remove_listener(on_action_recorded)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # 初始化文件管理器
    await file_manager.initialize()
    
    # 初始化Windows录制器
    windows_recorder.initialize()
    
    # 启动消息队列处理任务
    asyncio.create_task(process_message_queue())
    logger.info("消息队列处理任务已启动")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("关闭应用...")
    
    # 清理Windows录制器资源
    try:
        windows_recorder.cleanup()
    except Exception as e:
        logger.error(f"清理Windows录制器失败: {e}")


# 错误处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "内部服务器错误"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "web.api:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 