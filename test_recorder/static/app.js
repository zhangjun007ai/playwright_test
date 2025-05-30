// 全局变量
let ws = null;
let isRecording = false;
let recordingStartTime = null;
let currentSessionId = null;
let recordingTimer = null;
let actionCount = 0;
let realtimeCodeLines = [];
let fullPlaywrightCode = '';
let currentRecorderType = 'realtime';

// 调试面板功能
let debugMessageCount = 0;
let isDebugPanelVisible = true;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成，开始初始化...');
    
    initializeWebSocket();
    initializeEventListeners();
    loadSessions();
    updateUI();
});

// 初始化WebSocket连接
function initializeWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    console.log('正在连接WebSocket:', wsUrl);
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = function() {
        console.log('WebSocket连接已建立');
        updateWSStatus('已连接', 'success');
        updateDebugInfo('ws_connected');
        
        // 发送心跳
        ws.send(JSON.stringify({type: 'ping'}));
    };
    
    ws.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('收到WebSocket消息:', data);
            updateDebugInfo('message_received', {messageType: data.type});
            handleWebSocketMessage(data);
        } catch (error) {
            console.error('解析WebSocket消息失败:', error);
        }
    };
    
    ws.onclose = function() {
        console.log('WebSocket连接已关闭');
        updateWSStatus('已断开', 'danger');
        updateDebugInfo('ws_disconnected');
        
        // 尝试重连
        setTimeout(initializeWebSocket, 3000);
    };
    
    ws.onerror = function(error) {
        console.error('WebSocket错误:', error);
        updateWSStatus('连接错误', 'danger');
        updateDebugInfo('ws_disconnected');
    };
}

// 处理WebSocket消息
function handleWebSocketMessage(data) {
    console.log('处理WebSocket消息:', data.type, data);
    
    try {
        switch(data.type) {
            case 'pong':
                // 心跳响应
                console.debug('收到心跳响应');
                break;
                
            case 'recording_started':
                console.log('录制已开始:', data);
                currentSessionId = data.session_id;
                if (data.recorder_type) {
                    currentRecorderType = data.recorder_type;
                }
                handleRecordingStarted(data);
                break;
                
            case 'recording_stopped':
                console.log('录制已停止:', data);
                handleRecordingStopped(data);
                break;
                
            case 'action_recorded':
                console.log('收到操作记录:', data);
                const recorderInfo = data.recorder_type ? ` (${data.recorder_type})` : '';
                console.log(`处理来自${data.recorder_type || '未知'}录制器的操作记录`);
                
                if (data.action) {
                    data.action.recorder_type = data.recorder_type;
                    handleActionRecorded(data.action);
                } else {
                    console.error('操作记录消息格式错误，缺少action字段:', data);
                    showNotification(`接收到格式错误的操作记录${recorderInfo}`, 'warning');
                }
                break;
                
            default:
                console.log('未知消息类型:', data.type);
        }
    } catch (error) {
        console.error('处理WebSocket消息时发生错误:', error);
        console.error('消息内容:', data);
        showNotification(`消息处理错误: ${error.message}`, 'danger');
    }
}

// 处理录制开始
function handleRecordingStarted(data) {
    try {
        console.log('开始处理录制开始事件');
        isRecording = true;
        recordingStartTime = new Date();
        actionCount = 0;
        realtimeCodeLines = [];
        
        updateUI();
        startRecordingTimer();
        
        // 清空之前的显示
        clearRealtimeDisplay();
        clearCodeDisplay();
        
        showNotification('录制已开始', 'success');
        console.log('录制开始事件处理完成');
    } catch (error) {
        console.error('处理录制开始事件时发生错误:', error);
        showNotification(`录制开始处理错误: ${error.message}`, 'danger');
    }
}

// 处理录制停止
function handleRecordingStopped(data) {
    try {
        console.log('开始处理录制停止事件');
        isRecording = false;
        recordingStartTime = null;
        
        updateUI();
        stopRecordingTimer();
        
        // 生成完整代码
        generateFullPlaywrightCode();
        
        showNotification(`录制已停止，共记录 ${data.action_count} 个操作`, 'info');
        
        // 刷新会话列表
        loadSessions();
        
        // 启用导出按钮
        const exportBtn = document.getElementById('export-btn');
        if (exportBtn) {
            exportBtn.disabled = false;
        }
        console.log('录制停止事件处理完成');
    } catch (error) {
        console.error('处理录制停止事件时发生错误:', error);
        showNotification(`录制停止处理错误: ${error.message}`, 'danger');
    }
}

// 处理操作记录
function handleActionRecorded(action) {
    try {
        console.log('开始处理操作记录:', action);
        
        // 验证操作记录的必要字段
        if (!action) {
            throw new Error('操作记录为空');
        }
        
        if (!action.action_type) {
            console.warn('操作记录缺少action_type字段:', action);
        }
        
        actionCount++;
        updateActionCount();
        console.log(`操作计数器更新为: ${actionCount}`);
        
        // 添加到实时显示
        console.log('添加操作到实时显示');
        addActionToRealtime(action);
        
        // 添加代码行到实时代码显示
        if (action.playwright_code) {
            console.log('添加Playwright代码行:', action.playwright_code);
            addCodeLineToRealtime(action.playwright_code, action);
        } else {
            console.warn('操作记录缺少playwright_code字段:', action);
        }
        
        console.log('操作记录处理完成:', action.action_type);
        updateDebugInfo('action_processed');
    } catch (error) {
        console.error('处理操作记录时发生错误:', error);
        console.error('操作记录内容:', action);
        showNotification(`操作记录处理错误: ${error.message}`, 'danger');
    }

}

// 添加操作到实时显示
function addActionToRealtime(action) {
    try {
        const realtimeContainer = document.getElementById('realtime-actions');
        if (!realtimeContainer) {
            console.warn('实时显示容器不存在');
            return;
        }
        
        const actionDiv = document.createElement('div');
        actionDiv.className = 'action-item p-3 mb-2 border rounded';
        
        // 新增：录制器类型标识
        const recorderBadge = action.recorder_type ? 
            `<span class="badge bg-info me-2">${action.recorder_type === 'inspector' ? 'Inspector' : '实时'}</span>` : '';
        
        const screenshot = action.screenshot_path ? 
            `<img src="${action.screenshot_path}" class="screenshot-preview mt-2" style="max-width: 200px;" onclick="showScreenshot('${action.screenshot_path}')">` : '';
        
        const elementInfo = formatElementInfo(action.element_info, action.analyzed_element);
        
        actionDiv.innerHTML = `
            <div class="d-flex align-items-start">
                <span class="action-counter">${actionCount}</span>
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center mb-1">
                        ${recorderBadge}
                        <span class="badge ${getActionBadgeColor(action.action_type)} action-type-badge me-2">
                            ${action.action_type || '未知操作'}
                        </span>
                        <small class="text-muted">${new Date(action.timestamp).toLocaleTimeString()}</small>
                    </div>
                    <div class="fw-bold">${escapeHtml(action.description || '无描述')}</div>
                    <div class="element-info">${elementInfo}</div>
                    ${screenshot}
                </div>
            </div>
        `;
        
        // 添加高亮效果
        actionDiv.classList.add('highlight-code');
        
        realtimeContainer.appendChild(actionDiv);
        
        // 滚动到最新操作
        actionDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // 移除高亮效果
        setTimeout(() => {
            actionDiv.classList.remove('highlight-code');
        }, 2000);
        
        console.log('操作已添加到实时显示:', action.action_type);
    } catch (error) {
        console.error('添加操作到实时显示时出错:', error);
    }
}

// 添加代码行到实时代码显示
function addCodeLineToRealtime(code, action) {
    try {
        console.log('开始添加代码行到实时显示:', code);
        
        realtimeCodeLines.push({
            code: code,
            action: action,
            timestamp: new Date()
        });
        
        const container = document.getElementById('realtime-code-lines');
        if (!container) {
            throw new Error('找不到realtime-code-lines容器元素');
        }
        
        // 如果是第一行代码，清空占位内容
        if (realtimeCodeLines.length === 1) {
            console.log('清空代码区域占位内容');
            container.innerHTML = '';
        }
        
        const codeDiv = document.createElement('div');
        codeDiv.className = 'playwright-code-container mb-2 highlight-code';
        
        // 安全地获取数据
        const actionType = action.action_type || 'unknown';
        const description = action.description || '';
        
        codeDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-1">
                <small class="text-muted">步骤 ${realtimeCodeLines.length}: ${actionType}</small>
                <button class="btn btn-sm btn-outline-primary" onclick="copyCodeLine('${escapeHtml(code)}')">
                    📋 复制
                </button>
            </div>
            <pre class="playwright-code mb-0">${escapeHtml(code)}</pre>
            <small class="text-muted d-block mt-1">${escapeHtml(description)}</small>
        `;
        
        container.appendChild(codeDiv);
        console.log('代码行已添加到DOM');
        
        // 滚动到最新代码
        codeDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        console.log('已滚动到最新代码行');
        
    } catch (error) {
        console.error('添加代码行到实时显示时发生错误:', error);
        console.error('代码内容:', code);
        console.error('操作内容:', action);
        showNotification(`代码显示更新错误: ${error.message}`, 'danger');
    }
}

// 生成完整的Playwright代码
function generateFullPlaywrightCode() {
    if (realtimeCodeLines.length === 0) {
        return;
    }
    
    const imports = `import asyncio
import re
from playwright.async_api import Playwright, async_playwright, expect`;
    
    const runFunction = `async def run(playwright: Playwright) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    ${realtimeCodeLines.map(item => `    ${item.code}`).join('\n    ')}

    # ---------------------
    await context.close()
    await browser.close()`;
    
    const mainFunction = `async def main() -> None:
    async with async_playwright() as playwright:
        await run(playwright)`;
    
    const execution = `asyncio.run(main())`;
    
    fullPlaywrightCode = `${imports}


${runFunction}


${mainFunction}


${execution}`;
    
    // 更新完整代码显示
    const codeElement = document.getElementById('full-playwright-code');
    if (codeElement) {
        codeElement.textContent = fullPlaywrightCode;
    }
}

// 格式化元素信息
function formatElementInfo(elementInfo, analyzedElement) {
    const info = analyzedElement || elementInfo || {};
    const parts = [];
    
    if (info.role) {
        parts.push(`角色: ${info.role}`);
    }
    
    if (info.text && info.text.trim()) {
        parts.push(`文本: "${info.text.substring(0, 30)}${info.text.length > 30 ? '...' : ''}"`);
    }
    
    if (info.id || info.element_id) {
        parts.push(`ID: ${info.id || info.element_id}`);
    }
    
    if (info.className || info.class_name) {
        const className = info.className || info.class_name;
        parts.push(`类名: ${className.split(' ')[0]}`);
    }
    
    if (info.tagName || info.tag_name) {
        parts.push(`标签: ${(info.tagName || info.tag_name).toLowerCase()}`);
    }
    
    return parts.length > 0 ? parts.join(' | ') : '无详细信息';
}

// 获取操作类型对应的徽章颜色
function getActionBadgeColor(actionType) {
    const colors = {
        'click': 'primary',
        'input': 'success',
        'goto': 'info',
        'keypress': 'warning',
        'select': 'secondary',
        'load': 'light'
    };
    return colors[actionType] || 'dark';
}

// 初始化事件监听器
function initializeEventListeners() {
    // 录制表单提交
    const recordingForm = document.getElementById('recording-form');
    if (recordingForm) {
        recordingForm.addEventListener('submit', function(e) {
            e.preventDefault();
            startRecording();
        });
    }
    
    // 停止录制按钮
    const stopBtn = document.getElementById('stopBtn');
    if (stopBtn) {
        stopBtn.addEventListener('click', stopRecording);
    }
    
    // 新增：录制器类型选择变更事件
    const recorderTypeSelect = document.getElementById('recorderType');
    if (recorderTypeSelect) {
        recorderTypeSelect.addEventListener('change', function() {
            currentRecorderType = this.value;
            updateRecorderTypeHelp();
            console.log('录制器类型已切换为:', currentRecorderType);
        });
        
        // 初始化帮助文本
        updateRecorderTypeHelp();
    }
    
    // 导出表单提交
    const exportForm = document.getElementById('export-form');
    if (exportForm) {
        exportForm.addEventListener('submit', function(e) {
            e.preventDefault();
            exportTestCase();
        });
    }
    
    console.log('事件监听器初始化完成');
}

// 新增：更新录制器类型帮助文本
function updateRecorderTypeHelp() {
    const helpText = document.getElementById('recorder-help-text');
    if (helpText) {
        if (currentRecorderType === 'inspector') {
            helpText.textContent = 'Playwright Inspector：使用官方codegen工具，更准确但需要在新窗口操作';
        } else {
            helpText.textContent = '实时录制器：通过浏览器扩展捕获操作';
        }
    }
}

// 开始录制
async function startRecording() {
    const testName = document.getElementById('testName').value.trim();
    const testDescription = document.getElementById('testDescription').value.trim();
    const recorderType = document.getElementById('recorderType').value;
    
    if (!testName) {
        showNotification('请输入测试用例名称', 'warning');
        return;
    }
    
    try {
        console.log(`开始${recorderType}录制:`, testName);
        
        const response = await fetch('/api/recording/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                test_name: testName,
                description: testDescription,
                recorder_type: recorderType
            }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentSessionId = data.session_id;
            currentRecorderType = data.recorder_type;
            
            // 显示录制器特定的说明
            if (data.instructions) {
                showNotification(data.instructions, 'info', 8000);
            }
            
            console.log(`${data.recorder_type}录制开始成功:`, data.message);
        } else {
            throw new Error(data.error || '开始录制失败');
        }
    } catch (error) {
        console.error('开始录制失败:', error);
        showNotification(`开始录制失败: ${error.message}`, 'danger');
    }
}

// 停止录制
async function stopRecording() {
    try {
        const response = await fetch('/api/recording/stop', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('录制停止成功:', result);
            // WebSocket会处理录制停止的状态更新
        } else {
            showNotification(`停止录制失败: ${result.error}`, 'danger');
        }
    } catch (error) {
        console.error('停止录制失败:', error);
        showNotification('停止录制失败: 网络错误', 'danger');
    }
}

// 生成测试用例
async function generateTestCase() {
    if (!currentSessionId) {
        showNotification('没有可用的录制会话', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`/api/generate-testcase/${currentSessionId}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayTestCase(result.test_case);
            showNotification('测试用例生成成功', 'success');
        } else {
            showNotification(`生成测试用例失败: ${result.error}`, 'danger');
        }
    } catch (error) {
        console.error('生成测试用例失败:', error);
        showNotification('生成测试用例失败: 网络错误', 'danger');
    }
}

// 导出测试用例
async function exportTestCase() {
    if (!currentSessionId) {
        showNotification('没有可用的录制会话', 'warning');
        return;
    }
    
    const format = document.getElementById('export-format').value;
    const includeScreenshots = document.getElementById('include-screenshots').checked;
    const author = document.getElementById('author').value;
    const version = document.getElementById('version').value;
    const remarks = document.getElementById('remarks').value;
    
    try {
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                format: format,
                include_screenshots: includeScreenshots,
                author: author,
                version: version,
                remarks: remarks
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 下载文件
            window.open(result.download_url, '_blank');
            showNotification('导出成功', 'success');
        } else {
            showNotification(`导出失败: ${result.error}`, 'danger');
        }
    } catch (error) {
        console.error('导出失败:', error);
        showNotification('导出失败: 网络错误', 'danger');
    }
}

// 加载会话列表
async function loadSessions() {
    try {
        const response = await fetch('/api/sessions');
        const result = await response.json();
        
        if (result.success) {
            displaySessions(result.sessions);
        } else {
            console.error('加载会话失败:', result.error);
        }
    } catch (error) {
        console.error('加载会话失败:', error);
    }
}

// 显示会话列表
function displaySessions(sessions) {
    const container = document.getElementById('sessions-list');
    if (!container) return;
    
    if (!sessions || sessions.length === 0) {
        container.innerHTML = '<div class="text-muted">暂无历史记录</div>';
        return;
    }
    
    container.innerHTML = sessions.map(session => `
        <div class="card mb-2">
            <div class="card-body p-2">
                <h6 class="card-title mb-1">${session.name}</h6>
                <p class="card-text small text-muted">${session.description || '无描述'}</p>
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">${new Date(session.start_time).toLocaleString()}</small>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="loadSession('${session.id}')">加载</button>
                        <button class="btn btn-outline-danger" onclick="deleteSession('${session.id}')">删除</button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

// 显示测试用例
function displayTestCase(testCase) {
    const container = document.getElementById('testcase-preview');
    if (!container) return;
    
    container.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h5>${testCase.title}</h5>
            </div>
            <div class="card-body">
                <p><strong>描述:</strong> ${testCase.description}</p>
                <p><strong>前置条件:</strong> ${testCase.preconditions}</p>
                
                <h6>测试步骤:</h6>
                <ol>
                    ${testCase.steps.map(step => `
                        <li>${step.description}
                            ${step.expected_result ? `<br><small class="text-muted">预期结果: ${step.expected_result}</small>` : ''}
                        </li>
                    `).join('')}
                </ol>
                
                <p><strong>预期结果:</strong> ${testCase.expected_result}</p>
            </div>
        </div>
    `;
}

// 工具函数
function updateUI() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    
    if (isRecording) {
        if (startBtn) startBtn.disabled = true;
        if (stopBtn) stopBtn.disabled = false;
        if (statusDot) {
            statusDot.className = 'status-indicator status-recording';
        }
        if (statusText) statusText.textContent = '正在录制中...';
    } else {
        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
        if (statusDot) {
            statusDot.className = 'status-indicator status-idle';
        }
        if (statusText) statusText.textContent = '系统就绪';
    }
}

function updateActionCount() {
    const element = document.getElementById('action-count');
    if (element) {
        element.textContent = actionCount;
    }
}

function updateWSStatus(status, type) {
    const element = document.getElementById('ws-status');
    if (element) {
        element.textContent = status;
        element.className = `badge bg-${type}`;
    }
}

function startRecordingTimer() {
    if (recordingTimer) {
        clearInterval(recordingTimer);
    }
    
    recordingTimer = setInterval(function() {
        if (recordingStartTime) {
            const elapsed = Math.floor((new Date() - recordingStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            
            const element = document.getElementById('recording-time');
            if (element) {
                element.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }
    }, 1000);
}

function stopRecordingTimer() {
    if (recordingTimer) {
        clearInterval(recordingTimer);
        recordingTimer = null;
    }
}

function clearRealtimeDisplay() {
    const container = document.getElementById('realtime-actions');
    if (container) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="bi bi-clock-history fs-1"></i>
                <p class="mt-2">等待录制操作...</p>
            </div>
        `;
    }
}

function clearCodeDisplay() {
    const container = document.getElementById('realtime-code-lines');
    if (container) {
        container.innerHTML = `
            <div class="text-center text-muted py-3">
                <p>开始录制后，这里将显示实时生成的Playwright代码行...</p>
            </div>
        `;
    }
    
    const fullCodeElement = document.getElementById('full-playwright-code');
    if (fullCodeElement) {
        fullCodeElement.textContent = `# 录制完成后将显示完整的Playwright代码
# 代码格式与Playwright Inspector完全一致`;
    }
}

function showScreenshot(screenshotPath) {
    const modal = new bootstrap.Modal(document.getElementById('screenshotModal'));
    const img = document.getElementById('modal-screenshot');
    img.src = `/api/screenshot/${encodeURIComponent(screenshotPath)}`;
    modal.show();
}

function showNotification(message, type = 'info', duration = 3000) {
    // 创建通知元素
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = `top: 80px; right: 20px; z-index: 9999; min-width: 300px;`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // 3秒后自动关闭
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, duration);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Playwright代码相关函数
function copyFullCode() {
    if (!fullPlaywrightCode) {
        showNotification('暂无代码可复制', 'warning');
        return;
    }
    
    navigator.clipboard.writeText(fullPlaywrightCode).then(function() {
        showNotification('代码已复制到剪贴板', 'success');
    }).catch(function(err) {
        console.error('复制失败:', err);
        showNotification('复制失败', 'danger');
    });
}

function copyCodeLine(code) {
    navigator.clipboard.writeText(code).then(function() {
        showNotification('代码行已复制', 'success');
    }).catch(function(err) {
        console.error('复制失败:', err);
        showNotification('复制失败', 'danger');
    });
}

function refreshPlaywrightCode() {
    if (currentSessionId) {
        generateFullPlaywrightCode();
        showNotification('代码已刷新', 'info');
    } else {
        showNotification('没有可用的录制会话', 'warning');
    }
}

// 加载会话
function loadSession(sessionId) {
    currentSessionId = sessionId;
    showNotification('会话已加载', 'info');
    
    // 启用导出按钮
    const exportBtn = document.getElementById('export-btn');
    if (exportBtn) {
        exportBtn.disabled = false;
    }
}

// 删除会话
async function deleteSession(sessionId) {
    if (!confirm('确定要删除这个会话吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/sessions/${sessionId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('会话已删除', 'success');
            loadSessions(); // 重新加载会话列表
        } else {
            showNotification(`删除失败: ${result.error}`, 'danger');
        }
    } catch (error) {
        console.error('删除会话失败:', error);
        showNotification('删除失败: 网络错误', 'danger');
    }
}

// 调试面板功能
function updateDebugInfo(type, data = {}) {
    try {
        const debugWsStatus = document.getElementById('debug-ws-status');
        const debugMessageCount = document.getElementById('debug-message-count');
        const debugActionCount = document.getElementById('debug-action-count');
        const debugCodeLines = document.getElementById('debug-code-lines');
        const debugLastActivity = document.getElementById('debug-last-activity');
        
        const now = new Date().toLocaleTimeString();
        
        switch(type) {
            case 'ws_connected':
                if (debugWsStatus) {
                    debugWsStatus.textContent = '已连接';
                    debugWsStatus.className = 'badge bg-success';
                }
                break;
                
            case 'ws_disconnected':
                if (debugWsStatus) {
                    debugWsStatus.textContent = '已断开';
                    debugWsStatus.className = 'badge bg-danger';
                }
                break;
                
            case 'message_received':
                window.debugMessageCount = (window.debugMessageCount || 0) + 1;
                if (debugMessageCount) {
                    debugMessageCount.textContent = window.debugMessageCount;
                }
                if (debugLastActivity) {
                    debugLastActivity.textContent = `${now} - ${data.messageType || '未知'}`;
                }
                break;
                
            case 'action_processed':
                if (debugActionCount) {
                    debugActionCount.textContent = actionCount;
                }
                if (debugCodeLines) {
                    debugCodeLines.textContent = realtimeCodeLines.length;
                }
                if (debugLastActivity) {
                    debugLastActivity.textContent = `${now} - 操作处理`;
                }
                break;
        }
    } catch (error) {
        console.error('更新调试信息时发生错误:', error);
    }
}

function toggleDebugPanel() {
    const debugPanel = document.getElementById('debug-panel');
    const debugInfo = document.getElementById('debug-info');
    const toggleBtn = debugPanel.querySelector('button');
    
    if (isDebugPanelVisible) {
        debugInfo.style.display = 'none';
        toggleBtn.textContent = '显示';
        isDebugPanelVisible = false;
    } else {
        debugInfo.style.display = 'block';
        toggleBtn.textContent = '隐藏';
        isDebugPanelVisible = true;
    }
}

function clearDebugInfo() {
    window.debugMessageCount = 0;
    updateDebugInfo('action_processed');
    updateDebugInfo('message_received', {messageType: '重置'});
} 