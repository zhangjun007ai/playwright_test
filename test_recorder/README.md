# 测试用例自动录制生成系统

基于Playwright的智能化测试用例录制与生成平台，帮助测试工程师高效创建标准化测试用例文档。

## 🎯 功能特性

### 核心功能
- **实时录制**: 自动捕获UI操作，包括点击、输入、选择等
- **智能截图**: 每个操作步骤自动截图，支持全页面截图
- **文本提取**: 自动提取页面文本内容，辅助理解页面状态
- **AI生成**: 智能生成标准化的测试用例描述和预期结果

### 导出功能
- **Excel导出**: 生成标准测试用例表格，包含步骤和截图
- **Word导出**: 生成完整的测试用例文档
- **JSON导出**: 结构化数据，便于系统集成

### 管理功能
- **会话管理**: 历史录制会话的查看、删除、重新生成
- **可视化界面**: 现代化Web界面，操作简单直观
- **实时监控**: WebSocket实时显示录制状态和操作记录

## 🚀 快速开始

### 环境要求
- Python 3.9+
- Windows/macOS/Linux
- 2GB+ 可用内存

### 安装步骤

1. **克隆项目**
```bash
git clone <project-url>
cd test_recorder
```

2. **安装Python依赖**
```bash
pip install -r requirements.txt
```

3. **安装Playwright浏览器**
```bash
playwright install chromium
playwright install firefox  # 可选
playwright install webkit   # 可选
```

4. **启动系统**
```bash
python main.py
```

5. **访问Web界面**
打开浏览器访问: http://127.0.0.1:8000

## 📖 使用指南

### 基本使用流程

1. **开始录制**
   - 在左侧面板填写测试用例名称
   - 可选填写描述和目标URL
   - 点击"开始录制"按钮

2. **执行操作**
   - 在打开的浏览器中执行测试操作
   - 系统自动记录每个操作并截图
   - 实时查看操作记录

3. **停止录制**
   - 完成测试后点击"停止录制"
   - 系统保存录制数据

4. **生成测试用例**
   - 切换到"预览测试用例"标签页
   - 点击"生成测试用例"按钮
   - AI自动生成标准化描述

5. **导出文档**
   - 选择导出格式(Excel/Word/JSON)
   - 配置导出选项
   - 点击导出并下载文件

### 高级功能

#### 会话管理
- 查看历史录制会话
- 重新生成测试用例
- 删除不需要的会话

#### 导航控制
- 录制过程中可以导航到新URL
- 支持多页面操作录制

#### 自定义配置
编辑 `config/settings.py` 文件可以修改:
- 浏览器类型 (chromium/firefox/webkit)
- 截图质量
- 录制延迟
- 存储路径

## 🏗️ 项目结构

```
test_recorder/
├── config/                 # 配置文件
│   └── settings.py         # 系统配置
├── core/                   # 核心模块
│   ├── models.py          # 数据模型
│   ├── recorder.py        # 录制引擎
│   └── ai_generator.py    # AI生成器
├── web/                    # Web服务
│   └── api.py             # FastAPI接口
├── utils/                  # 工具模块
│   ├── file_manager.py    # 文件管理
│   └── export_handler.py  # 导出处理
├── templates/              # 模板文件
│   └── index.html         # 主页面
├── static/                 # 静态资源
│   └── js/app.js          # 前端应用
├── requirements.txt        # 依赖清单
├── main.py                # 应用入口
└── README.md              # 说明文档
```

## 🛠️ 技术架构

### 后端技术栈
- **Playwright**: 浏览器自动化框架
- **FastAPI**: 现代Web框架
- **Pydantic**: 数据验证
- **WebSocket**: 实时通信
- **OpenPyXL/python-docx**: 文档生成

### 前端技术栈
- **Bootstrap 5**: UI框架
- **Vanilla JavaScript**: 原生JS
- **WebSocket**: 实时通信

### 核心组件

#### 录制引擎 (core/recorder.py)
- 基于Playwright的操作捕获
- JavaScript注入监听用户交互
- 自动截图和文本提取
- WebSocket实时通信

#### AI生成器 (core/ai_generator.py)
- 操作记录分析
- 智能描述生成
- 预期结果推断
- 测试用例结构化

#### 导出处理器 (utils/export_handler.py)
- 多格式导出支持
- 模板系统
- 截图嵌入
- 数据格式化

## 🔧 配置说明

### 基础配置
```python
# config/settings.py
HOST = "127.0.0.1"          # 服务地址
PORT = 8000                 # 服务端口
BROWSER_TYPE = "chromium"   # 浏览器类型
HEADLESS = False            # 是否无头模式
SLOW_MO = 100              # 操作延迟(ms)
```

### 录制配置
```python
ENABLE_SCREENSHOTS = True   # 启用截图
ENABLE_TEXT_EXTRACTION = True  # 启用文本提取
ENABLE_TRACING = True      # 启用追踪
SCREENSHOT_QUALITY = 90    # 截图质量
```

## 🚨 常见问题

### Q: 浏览器启动失败
A: 确保已安装Playwright浏览器:
```bash
playwright install chromium
```

### Q: 操作没有被记录
A: 检查是否正确开始录制，确保在系统打开的浏览器窗口中操作

### Q: 导出文件打不开
A: 确保系统安装了对应的软件(Excel/Word)，或者尝试其他格式

### Q: 内存占用过高
A: 可以在设置中降低截图质量，或关闭追踪功能

## 📝 更新日志

### v1.0.0 (当前版本)
- ✅ 基础录制功能
- ✅ AI测试用例生成
- ✅ 多格式导出
- ✅ Web管理界面
- ✅ 会话管理
- ✅ 实时监控

### 计划功能
- 🔄 批量测试用例生成
- 🔄 测试用例模板自定义
- 🔄 云端存储支持
- 🔄 团队协作功能

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 支持与反馈

- 问题反馈: 请在GitHub Issues中提交
- 功能建议: 欢迎提交Feature Request
- 技术交流: 欢迎加入讨论

---

**⭐ 如果这个项目对你有帮助，请给一个Star支持!** 