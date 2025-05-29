from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    APP_NAME: str = "测试用例自动录制生成系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # 存储路径配置
    BASE_DIR: Path = Path(__file__).parent.parent
    RECORDINGS_DIR: Path = BASE_DIR / "recordings"
    SCREENSHOTS_DIR: Path = BASE_DIR / "screenshots" 
    EXPORTS_DIR: Path = BASE_DIR / "exports"
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    STATIC_DIR: Path = BASE_DIR / "static"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    # 数据库配置
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/database.db"
    
    # AI配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # Playwright配置
    BROWSER_TYPE: str = "chromium"  # chromium, firefox, webkit
    HEADLESS: bool = False
    SLOW_MO: int = 100  # 操作延迟(毫秒)
    
    # 录制配置
    ENABLE_SCREENSHOTS: bool = True
    ENABLE_TEXT_EXTRACTION: bool = True
    ENABLE_TRACING: bool = True
    SCREENSHOT_QUALITY: int = 90
    
    # 导出配置
    EXCEL_TEMPLATE: str = "test_case_template.xlsx"
    WORD_TEMPLATE: str = "test_case_template.docx"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = str(BASE_DIR / "logs" / "app.log")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保必要的目录存在
        self.create_directories()
    
    def create_directories(self):
        """创建必要的目录"""
        directories = [
            self.RECORDINGS_DIR,
            self.SCREENSHOTS_DIR,
            self.EXPORTS_DIR,
            self.TEMPLATES_DIR,
            self.STATIC_DIR,
            self.LOGS_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

# 创建全局设置实例
settings = Settings()

# 操作类型映射
ACTION_TYPES = {
    "click": "点击",
    "fill": "输入",
    "select": "选择", 
    "check": "勾选",
    "uncheck": "取消勾选",
    "hover": "悬停",
    "goto": "导航到",
    "wait": "等待",
    "screenshot": "截图",
    "scroll": "滚动"
}

# 元素类型映射
ELEMENT_TYPES = {
    "button": "按钮",
    "input": "输入框",
    "select": "下拉框",
    "checkbox": "复选框",
    "radio": "单选按钮",
    "link": "链接",
    "text": "文本",
    "image": "图片",
    "div": "区域"
} 