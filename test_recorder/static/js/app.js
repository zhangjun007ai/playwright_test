// 测试用例录制系统前端应用
class TestRecorderApp {
    constructor() {
        this.ws = null;
        this.currentSessionId = null;
        this.selectedSessionId = null;
        this.isRecording = false;
        this.actionCount = 0;
        
        this.init();
    }
    
    init() {
        // 初始化WebSocket连接
        this.initWebSocket();
        
        // 绑定事件处理器
        this.bindEventHandlers();
        
        // 加载初始数据
        this.loadStatus();
        this.loadSessions();
        
        // 定期刷新状态
        setInterval(() => this.loadStatus(), 5000);
    }
    
    initWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket连接已建立');
            this.showNotification('系统连接成功', 'success');
        };
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleWebSocketMessage(message);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket连接已关闭');
            this.showNotification('连接已断开，正在重连...', 'warning');
            
            // 5秒后重连
            setTimeout(() => this.initWebSocket(), 5000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket错误:', error);
            this.showNotification('连接错误', 'danger');
        };
    }
    
    bindEventHandlers() {
        // 开始录制表单
        document.getElementById('recording-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.startRecording();
        });
        
        // 停止录制按钮
        document.getElementById('stopBtn').addEventListener('click', () => {
            this.stopRecording();
        });
        
        // 录制器类型选择
        document.getElementById('recorderType').addEventListener('change', (e) => {
            const helpText = document.getElementById('recorder-help-text');
            if (e.target.value === 'realtime') {
                helpText.textContent = '实时录制器：通过浏览器扩展捕获操作';
            } else {
                helpText.textContent = 'Playwright Inspector：使用官方录制工具';
            }
        });
        
        // 导航按钮
        document.getElementById('navigate-btn').addEventListener('click', () => {
            this.navigate();
        });
        
        // 刷新会话列表
        document.getElementById('refresh-sessions').addEventListener('click', () => {
            this.loadSessions();
        });
        
        // 生成测试用例按钮
        document.getElementById('generate-testcase-btn').addEventListener('click', () => {
            this.generateTestCase();
        });
        
        // 导出表单
        document.getElementById('export-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.exportTestCase();
        });
        
        // 帮助按钮
        document.getElementById('help-btn').addEventListener('click', () => {
            new bootstrap.Modal(document.getElementById('helpModal')).show();
        });
        
        // 标签页切换事件
        document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                const target = e.target.getAttribute('href');
                if (target === '#preview' && this.selectedSessionId) {
                    this.loadSessionPreview(this.selectedSessionId);
                }
            });
        });
    }
    
    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'recording_started':
                this.handleRecordingStarted(message);
                break;
            case 'recording_stopped':
                this.handleRecordingStopped(message);
                break;
            case 'action_recorded':
                this.handleActionRecorded(message.action);
                break;
            case 'pong':
                // 心跳响应
                break;
            default:
                console.log('未知消息类型:', message.type);
        }
    }
    
    async startRecording() {
        const testName = document.getElementById('testName').value;
        const description = document.getElementById('testDescription').value;
        const recorderType = document.getElementById('recorderType').value;
        
        if (!testName) {
            this.showNotification('请输入测试用例名称', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/recording/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    test_name: testName,
                    description: description,
                    recorder_type: recorderType
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentSessionId = result.session_id;
                this.showNotification('录制已开始', 'success');
                this.updateRecordingState(true);
            } else {
                this.showNotification('开始录制失败', 'danger');
            }
        } catch (error) {
            console.error('开始录制错误:', error);
            this.showNotification('开始录制失败', 'danger');
        }
    }
    
    async stopRecording() {
        try {
            const response = await fetch('/api/recording/stop', {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('录制已停止', 'success');
                this.updateRecordingState(false);
                this.selectedSessionId = this.currentSessionId;
                this.currentSessionId = null;
                
                // 刷新会话列表
                this.loadSessions();
                
                // 启用生成和导出按钮
                document.getElementById('generate-testcase-btn').disabled = false;
                document.getElementById('export-btn').disabled = false;
            } else {
                this.showNotification('停止录制失败', 'danger');
            }
        } catch (error) {
            console.error('停止录制错误:', error);
            this.showNotification('停止录制失败', 'danger');
        }
    }
    
    async navigate() {
        const url = document.getElementById('navigate-url').value;
        
        if (!url) {
            this.showNotification('请输入URL', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/navigate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('导航成功', 'success');
                document.getElementById('navigate-url').value = '';
            } else {
                this.showNotification('导航失败', 'danger');
            }
        } catch (error) {
            console.error('导航错误:', error);
            this.showNotification('导航失败', 'danger');
        }
    }
    
    async loadStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            
            this.updateStatusDisplay(status);
        } catch (error) {
            console.error('加载状态失败:', error);
        }
    }
    
    async loadSessions() {
        try {
            const response = await fetch('/api/sessions');
            const result = await response.json();
            
            this.renderSessionsList(result.sessions);
        } catch (error) {
            console.error('加载会话列表失败:', error);
        }
    }
    
    async generateTestCase() {
        if (!this.selectedSessionId) {
            this.showNotification('请先选择一个会话', 'warning');
            return;
        }
        
        try {
            // 显示加载状态
            const btn = document.getElementById('generate-testcase-btn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<i class="bi bi-hourglass-split"></i> 生成中...';
            btn.disabled = true;
            
            const response = await fetch(`/api/generate-testcase/${this.selectedSessionId}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('测试用例生成成功', 'success');
                this.renderTestCasePreview(result.test_case);
                
                // 切换到预览标签页
                const previewTab = new bootstrap.Tab(document.getElementById('preview-tab'));
                previewTab.show();
            } else {
                this.showNotification('生成测试用例失败', 'danger');
            }
            
            // 恢复按钮状态
            btn.innerHTML = originalText;
            btn.disabled = false;
            
        } catch (error) {
            console.error('生成测试用例错误:', error);
            this.showNotification('生成测试用例失败', 'danger');
            
            // 恢复按钮状态
            const btn = document.getElementById('generate-testcase-btn');
            btn.innerHTML = '<i class="bi bi-magic"></i> 生成测试用例';
            btn.disabled = false;
        }
    }
    
    async exportTestCase() {
        if (!this.selectedSessionId) {
            this.showNotification('请先选择一个会话', 'warning');
            return;
        }
        
        const format = document.getElementById('export-format').value;
        const includeScreenshots = document.getElementById('include-screenshots').checked;
        const author = document.getElementById('export-author').value;
        const version = document.getElementById('export-version').value;
        const remarks = document.getElementById('export-remarks').value;
        
        try {
            const response = await fetch('/api/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.selectedSessionId,
                    format: format,
                    include_screenshots: includeScreenshots,
                    author: author,
                    version: version,
                    remarks: remarks
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('导出成功', 'success');
                
                // 自动下载文件
                const downloadLink = document.createElement('a');
                downloadLink.href = result.download_url;
                downloadLink.download = '';
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
                
            } else {
                this.showNotification('导出失败', 'danger');
            }
        } catch (error) {
            console.error('导出错误:', error);
            this.showNotification('导出失败', 'danger');
        }
    }
    
    updateRecordingState(isRecording) {
        this.isRecording = isRecording;
        
        // 更新按钮状态
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        
        if (isRecording) {
            // 禁用开始按钮，启用停止按钮
            startBtn.disabled = true;
            stopBtn.disabled = false;
            
            // 更新状态显示
            document.getElementById('status-dot').classList.remove('status-idle');
            document.getElementById('status-dot').classList.add('status-recording');
            document.getElementById('status-text').textContent = '录制中';
            
            // 清空操作列表
            document.getElementById('realtime-actions').innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="bi bi-clock-history fs-1"></i>
                    <p class="mt-2">等待录制操作...</p>
                </div>
            `;
            
            // 重置计数器
            this.actionCount = 0;
            document.getElementById('action-count').textContent = '0';
            
        } else {
            // 启用开始按钮，禁用停止按钮
            startBtn.disabled = false;
            stopBtn.disabled = true;
            
            // 更新状态显示
            document.getElementById('status-dot').classList.remove('status-recording');
            document.getElementById('status-dot').classList.add('status-idle');
            document.getElementById('status-text').textContent = '系统就绪';
            
            // 清空表单
            document.getElementById('recording-form').reset();
        }
        
        // 更新WebSocket状态显示
        document.getElementById('ws-status').textContent = isRecording ? '已连接' : '未连接';
        document.getElementById('ws-status').className = `badge ${isRecording ? 'bg-success' : 'bg-secondary'}`;
    }
    
    updateStatusDisplay(status) {
        this.isRecording = status.recording;
        this.actionCount = status.action_count;
        
        document.getElementById('action-count').textContent = `操作数量: ${this.actionCount}`;
        document.getElementById('live-action-count').textContent = this.actionCount;
        
        if (status.recording !== this.isRecording) {
            this.updateRecordingState(status.recording);
        }
    }
    
    handleRecordingStarted(message) {
        this.currentSessionId = message.session_id;
        this.updateRecordingState(true);
        this.showNotification(`开始录制: ${message.test_name}`, 'success');
    }
    
    handleRecordingStopped(message) {
        this.updateRecordingState(false);
        this.selectedSessionId = this.currentSessionId;
        this.currentSessionId = null;
        this.loadSessions();
        this.showNotification('录制已停止', 'info');
    }
    
    handleActionRecorded(action) {
        this.actionCount++;
        this.addActionToList(action);
        this.updateLatestScreenshot(action);
        
        // 更新计数显示
        document.getElementById('action-count').textContent = `操作数量: ${this.actionCount}`;
        document.getElementById('live-action-count').textContent = this.actionCount;
    }
    
    addActionToList(action) {
        const actionsList = document.getElementById('realtime-actions');
        
        // 如果是第一个操作，清空占位符
        if (this.actionCount === 1) {
            actionsList.innerHTML = '';
        }
        
        const actionElement = document.createElement('div');
        actionElement.className = 'list-group-item list-group-item-action';
        
        const time = new Date(action.timestamp).toLocaleTimeString();
        
        // 使用改进后的操作信息
        const title = action.title || this.getActionDescription(action);
        const description = action.description || this.getElementDescription(action.element_info);
        const pageUrl = action.page_url || '';
        
        // 获取操作类型图标
        const icon = this.getActionIcon(action.action_type);
        
        actionElement.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center mb-1">
                        <i class="bi ${icon} me-2 text-primary"></i>
                        <h6 class="mb-0">${title}</h6>
                    </div>
                    <p class="mb-1 text-muted small">${description}</p>
                    ${pageUrl ? `<p class="mb-1 text-info small"><i class="bi bi-link-45deg"></i> ${pageUrl}</p>` : ''}
                    <small class="text-muted"><i class="bi bi-clock"></i> ${time}</small>
                </div>
                <div class="d-flex align-items-center">
                    ${action.screenshot_path ? '<i class="bi bi-camera text-primary me-2"></i>' : ''}
                    <span class="badge bg-secondary">${action.action_type}</span>
                </div>
            </div>
        `;
        
        // 点击查看截图
        if (action.screenshot_path) {
            actionElement.style.cursor = 'pointer';
            actionElement.addEventListener('click', () => {
                this.showScreenshot(action.screenshot_path);
            });
        }
        
        actionsList.appendChild(actionElement);
        
        // 滚动到最新操作
        actionsList.scrollTop = actionsList.scrollHeight;
    }
    
    getActionIcon(actionType) {
        const icons = {
            'goto': 'bi-arrow-right-circle',
            'click': 'bi-cursor',
            'fill': 'bi-pencil',
            'press': 'bi-keyboard',
            'select': 'bi-list',
            'check': 'bi-check-square',
            'uncheck': 'bi-square',
            'hover': 'bi-mouse',
            'wait': 'bi-hourglass-split',
            'navigation': 'bi-globe'
        };
        return icons[actionType] || 'bi-gear';
    }
    
    getActionDescription(action) {
        // 如果有title字段，优先使用
        if (action.title) {
            return action.title;
        }
        
        const actionType = action.action_type;
        const elementInfo = action.element_info || {};
        
        switch (actionType) {
            case 'click':
                return `点击 ${elementInfo.tagName || '元素'}`;
            case 'fill':
                return `在输入框中输入了内容`;
            case 'select':
                return `选择了下拉选项`;
            case 'navigation':
            case 'goto':
                return `导航到页面`;
            case 'press':
                return `按下了按键`;
            case 'check':
                return `勾选了复选框`;
            case 'uncheck':
                return `取消勾选复选框`;
            case 'hover':
                return `鼠标悬停`;
            case 'wait':
                return `等待元素`;
            default:
                return `执行了 ${actionType} 操作`;
        }
    }
    
    getElementDescription(elementInfo) {
        // 如果有description字段，优先使用
        if (elementInfo && elementInfo.description) {
            return elementInfo.description;
        }
        
        if (!elementInfo) return '';
        
        if (elementInfo.text) {
            return `文本: "${elementInfo.text.substring(0, 30)}..."`;
        }
        if (elementInfo.placeholder) {
            return `占位符: "${elementInfo.placeholder}"`;
        }
        if (elementInfo.id) {
            return `ID: "${elementInfo.id}"`;
        }
        if (elementInfo.className) {
            return `类名: "${elementInfo.className.split(' ')[0]}"`;
        }
        if (elementInfo.selector) {
            return `选择器: ${elementInfo.selector.substring(0, 50)}${elementInfo.selector.length > 50 ? '...' : ''}`;
        }
        
        return `${elementInfo.tagName || '未知'} 元素`;
    }
    
    updateLatestScreenshot(action) {
        if (action.screenshot_path) {
            const screenshotContainer = document.getElementById('latest-screenshot');
            screenshotContainer.innerHTML = `
                <img src="/api/screenshot/${encodeURIComponent(action.screenshot_path)}" 
                     class="img-fluid screenshot-thumbnail" 
                     alt="最新截图"
                     onclick="app.showScreenshot('${action.screenshot_path}')">
            `;
        }
    }
    
    showScreenshot(screenshotPath) {
        const modal = new bootstrap.Modal(document.getElementById('screenshotModal'));
        const img = document.getElementById('modal-screenshot');
        img.src = `/api/screenshot/${encodeURIComponent(screenshotPath)}`;
        modal.show();
    }
    
    renderSessionsList(sessions) {
        const sessionsList = document.getElementById('sessions-list');
        
        if (!sessions || sessions.length === 0) {
            sessionsList.innerHTML = '<div class="text-muted small">暂无会话记录</div>';
            return;
        }
        
        sessionsList.innerHTML = '';
        
        sessions.forEach(session => {
            const sessionElement = document.createElement('div');
            sessionElement.className = 'list-group-item list-group-item-action mb-1';
            
            if (session.session_id === this.selectedSessionId) {
                sessionElement.classList.add('active');
            }
            
            const duration = session.duration ? `${Math.round(session.duration)}秒` : '未知';
            const startTime = new Date(session.start_time).toLocaleString();
            
            sessionElement.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${session.name}</h6>
                        <p class="mb-1 small text-muted">操作数: ${session.action_count} | 时长: ${duration}</p>
                        <small class="text-muted">${startTime}</small>
                    </div>
                    <div class="dropdown">
                        <button class="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="dropdown">
                            <i class="bi bi-three-dots-vertical"></i>
                        </button>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="#" onclick="app.selectSession('${session.session_id}')">选择</a></li>
                            <li><a class="dropdown-item" href="#" onclick="app.deleteSession('${session.session_id}')">删除</a></li>
                        </ul>
                    </div>
                </div>
            `;
            
            sessionsList.appendChild(sessionElement);
        });
    }
    
    selectSession(sessionId) {
        this.selectedSessionId = sessionId;
        
        // 更新选中状态
        document.querySelectorAll('#sessions-list .list-group-item').forEach(item => {
            item.classList.remove('active');
        });
        
        event.target.closest('.list-group-item').classList.add('active');
        
        // 启用相关按钮
        document.getElementById('generate-testcase-btn').disabled = false;
        document.getElementById('export-btn').disabled = false;
        
        this.showNotification('会话已选中', 'success');
    }
    
    async deleteSession(sessionId) {
        if (!confirm('确定要删除这个会话吗？此操作不可撤销。')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/sessions/${sessionId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('会话删除成功', 'success');
                
                if (this.selectedSessionId === sessionId) {
                    this.selectedSessionId = null;
                    document.getElementById('generate-testcase-btn').disabled = true;
                    document.getElementById('export-btn').disabled = true;
                }
                
                this.loadSessions();
            } else {
                this.showNotification('删除会话失败', 'danger');
            }
        } catch (error) {
            console.error('删除会话错误:', error);
            this.showNotification('删除会话失败', 'danger');
        }
    }
    
    async loadSessionPreview(sessionId) {
        try {
            const response = await fetch(`/api/sessions/${sessionId}`);
            const result = await response.json();
            
            if (result.session) {
                this.renderSessionPreview(result.session);
            }
        } catch (error) {
            console.error('加载会话预览失败:', error);
        }
    }
    
    renderSessionPreview(session) {
        const previewContainer = document.getElementById('testcase-preview');
        
        if (!session.actions || session.actions.length === 0) {
            previewContainer.innerHTML = '<div class="text-center p-4 text-muted">该会话没有记录任何操作</div>';
            return;
        }
        
        let html = `
            <div class="mb-4">
                <h5>${session.name}</h5>
                <p class="text-muted">${session.description || '暂无描述'}</p>
                <small class="text-muted">
                    录制时间: ${new Date(session.start_time).toLocaleString()} | 
                    操作数: ${session.actions.length}
                </small>
            </div>
            <div class="row">
        `;
        
        session.actions.forEach((action, index) => {
            const time = new Date(action.timestamp).toLocaleTimeString();
            const actionDesc = this.getActionDescription(action);
            const elementDesc = this.getElementDescription(action.element_info);
            
            html += `
                <div class="col-md-6 mb-3">
                    <div class="card step-card">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start">
                                <div class="flex-grow-1">
                                    <h6 class="card-title">步骤 ${index + 1}</h6>
                                    <p class="card-text">${actionDesc}</p>
                                    <small class="text-muted">${elementDesc}</small>
                                    <br><small class="text-muted">${time}</small>
                                </div>
                                ${action.screenshot_path ? 
                                    `<img src="/api/screenshot/${encodeURIComponent(action.screenshot_path)}" 
                                          class="screenshot-thumbnail ms-2" 
                                          onclick="app.showScreenshot('${action.screenshot_path}')" 
                                          alt="截图">` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        previewContainer.innerHTML = html;
    }
    
    renderTestCasePreview(testCase) {
        const previewContainer = document.getElementById('testcase-preview');
        
        let html = `
            <div class="mb-4">
                <h5>${testCase.name}</h5>
                <p>${testCase.description}</p>
                <div class="row">
                    <div class="col-md-3"><strong>用例编号:</strong> ${testCase.id}</div>
                    <div class="col-md-3"><strong>测试模块:</strong> ${testCase.module}</div>
                    <div class="col-md-3"><strong>优先级:</strong> ${testCase.priority}</div>
                    <div class="col-md-3"><strong>类别:</strong> ${testCase.category}</div>
                </div>
            </div>
        `;
        
        if (testCase.preconditions && testCase.preconditions.length > 0) {
            html += `
                <div class="mb-4">
                    <h6>前置条件</h6>
                    <ul>
                        ${testCase.preconditions.map(condition => `<li>${condition}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        html += `
            <div class="mb-4">
                <h6>测试步骤</h6>
                <div class="table-responsive">
                    <table class="table table-bordered">
                        <thead class="table-light">
                            <tr>
                                <th width="10%">步骤</th>
                                <th width="40%">操作步骤</th>
                                <th width="35%">预期结果</th>
                                <th width="15%">截图</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        testCase.test_steps.forEach(step => {
            html += `
                <tr>
                    <td class="text-center">${step.step_number}</td>
                    <td>${step.description}</td>
                    <td>${step.expected_result}</td>
                    <td class="text-center">
                        ${step.screenshot_path ? 
                            `<img src="/api/screenshot/${encodeURIComponent(step.screenshot_path)}" 
                                  class="screenshot-thumbnail" 
                                  onclick="app.showScreenshot('${step.screenshot_path}')" 
                                  alt="步骤截图">` : '无'}
                    </td>
                </tr>
            `;
        });
        
        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        previewContainer.innerHTML = html;
    }
    
    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // 3秒后自动移除
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
}

// 初始化应用
const app = new TestRecorderApp(); 