from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ActionType(str, Enum):
    """操作类型枚举"""
    CLICK = "click"
    FILL = "fill"
    SELECT = "select"
    CHECK = "check"
    UNCHECK = "uncheck"
    HOVER = "hover"
    PRESS = "press"
    GOTO = "goto"
    NAVIGATION = "navigation"
    SCREENSHOT = "screenshot"
    SCROLL = "scroll"
    WAIT = "wait"


class ElementInfo(BaseModel):
    """元素信息模型"""
    tag_name: str = Field(description="HTML标签名")
    id: Optional[str] = Field(default="", description="元素ID")
    class_name: Optional[str] = Field(default="", description="CSS类名")
    text: Optional[str] = Field(default="", description="元素文本内容")
    value: Optional[str] = Field(default="", description="元素值")
    placeholder: Optional[str] = Field(default="", description="占位符文本")
    name: Optional[str] = Field(default="", description="元素name属性")
    type: Optional[str] = Field(default="", description="元素类型")
    selector: Optional[str] = Field(default="", description="CSS选择器")
    position: Optional[Dict[str, float]] = Field(default_factory=dict, description="元素位置")
    size: Optional[Dict[str, float]] = Field(default_factory=dict, description="元素尺寸")


class ActionRecord(BaseModel):
    """操作记录模型"""
    id: str = Field(description="操作记录唯一ID")
    session_id: str = Field(description="会话ID")
    action_type: str = Field(description="操作类型")
    timestamp: datetime = Field(description="操作时间戳")
    
    # 元素相关信息
    element_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元素信息")
    
    # 页面相关信息
    page_url: str = Field(default="", description="页面URL")
    page_title: str = Field(default="", description="页面标题")
    page_text: Optional[str] = Field(default="", description="页面文本内容")
    
    # 操作相关数据
    additional_data: Optional[str] = Field(default="", description="附加数据")
    screenshot_path: Optional[str] = Field(default="", description="截图路径")
    
    # 生成的描述
    description: Optional[str] = Field(default="", description="操作描述")
    expected_result: Optional[str] = Field(default="", description="预期结果")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TestStep(BaseModel):
    """测试步骤模型"""
    step_number: int = Field(description="步骤编号")
    action: str = Field(description="操作动作")
    description: str = Field(description="步骤描述")
    expected_result: str = Field(description="预期结果")
    actual_result: Optional[str] = Field(default="", description="实际结果")
    screenshot_path: Optional[str] = Field(default="", description="相关截图路径")
    status: str = Field(default="", description="执行状态")


class TestSession(BaseModel):
    """测试会话模型"""
    id: str = Field(description="会话唯一ID")
    name: str = Field(description="测试用例名称")
    description: Optional[str] = Field(default="", description="测试用例描述")
    
    # 时间信息
    start_time: datetime = Field(description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    
    # 操作记录
    actions: List[ActionRecord] = Field(default_factory=list, description="操作记录列表")
    
    # 生成的测试步骤
    test_steps: List[TestStep] = Field(default_factory=list, description="生成的测试步骤")
    
    # 文件路径
    trace_file: Optional[str] = Field(default="", description="追踪文件路径")
    video_file: Optional[str] = Field(default="", description="视频文件路径")
    
    # 元数据
    browser_type: str = Field(default="chromium", description="浏览器类型")
    status: str = Field(default="recording", description="会话状态")
    tags: List[str] = Field(default_factory=list, description="标签")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @property
    def duration(self) -> Optional[float]:
        """计算会话持续时间（秒）"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def action_count(self) -> int:
        """获取操作数量"""
        return len(self.actions)


class TestCase(BaseModel):
    """完整的测试用例模型"""
    id: str = Field(description="测试用例ID")
    name: str = Field(description="测试用例名称")
    description: str = Field(description="测试用例描述")
    
    # 基本信息
    priority: str = Field(default="中", description="优先级")
    category: str = Field(default="功能测试", description="测试类别")
    module: str = Field(default="", description="所属模块")
    
    # 前置条件
    preconditions: List[str] = Field(default_factory=list, description="前置条件")
    
    # 测试步骤
    test_steps: List[TestStep] = Field(default_factory=list, description="测试步骤")
    
    # 期望结果
    expected_results: List[str] = Field(default_factory=list, description="期望结果")
    
    # 关联文件
    screenshots: List[str] = Field(default_factory=list, description="截图文件列表")
    trace_file: Optional[str] = Field(default="", description="追踪文件")
    
    # 元数据
    created_time: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_time: Optional[datetime] = Field(default=None, description="更新时间")
    created_by: str = Field(default="AI自动生成", description="创建者")
    
    # 执行信息
    execution_time: Optional[float] = Field(default=None, description="执行时长")
    execution_status: str = Field(default="未执行", description="执行状态")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionSummary(BaseModel):
    """会话摘要模型"""
    session_id: str
    name: str
    start_time: datetime
    end_time: Optional[datetime]
    action_count: int
    duration: Optional[float]
    status: str
    browser_type: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ExportConfig(BaseModel):
    """导出配置模型"""
    format: str = Field(description="导出格式: excel, word, json")
    include_screenshots: bool = Field(default=True, description="是否包含截图")
    include_trace: bool = Field(default=False, description="是否包含追踪文件")
    template_path: Optional[str] = Field(default="", description="模板文件路径")
    output_path: str = Field(description="输出文件路径")
    
    # 自定义字段
    author: str = Field(default="测试工程师", description="作者")
    version: str = Field(default="1.0", description="版本号")
    remarks: Optional[str] = Field(default="", description="备注") 