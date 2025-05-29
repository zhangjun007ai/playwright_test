// 终极停止按钮修复脚本
(function() {
    'use strict';
    
    console.log('🛠️ 启动终极停止按钮修复程序...');
    
    let isFixApplied = false;
    let debugInfo = {
        fixAttempts: 0,
        lastError: null,
        buttonState: 'unknown'
    };
    
    // 强制等待DOM完全加载
    function waitForDOM() {
        return new Promise((resolve) => {
            if (document.readyState === 'complete') {
                resolve();
            } else {
                window.addEventListener('load', resolve);
            }
        });
    }
    
    // 检查所有必要的元素
    function checkRequiredElements() {
        const elements = {
            stopBtn: document.getElementById('stopBtn'),
            startBtn: document.getElementById('startBtn'),
            recordingForm: document.getElementById('recording-form')
        };
        
        console.log('📋 检查必要元素:', elements);
        
        for (const [name, element] of Object.entries(elements)) {
            if (!element) {
                console.error(`❌ 缺少必要元素: ${name}`);
                return false;
            }
        }
        
        return true;
    }
    
    // 检查Bootstrap和其他依赖
    function checkDependencies() {
        const checks = {
            bootstrap: typeof bootstrap !== 'undefined',
            fetch: typeof fetch !== 'undefined',
            Promise: typeof Promise !== 'undefined'
        };
        
        console.log('🔍 依赖检查:', checks);
        
        return Object.values(checks).every(Boolean);
    }
    
    // 清理所有事件监听器
    function cleanupEventListeners(element) {
        const newElement = element.cloneNode(true);
        element.parentNode.replaceChild(newElement, element);
        return newElement;
    }
    
    // 强制修复停止按钮
    function ultimateStopButtonFix() {
        try {
            debugInfo.fixAttempts++;
            console.log(`🔧 第 ${debugInfo.fixAttempts} 次修复尝试...`);
            
            // 1. 检查必要元素
            if (!checkRequiredElements()) {
                throw new Error('缺少必要的DOM元素');
            }
            
            // 2. 检查依赖
            if (!checkDependencies()) {
                console.warn('⚠️ 某些依赖可能未加载完全');
            }
            
            // 3. 获取按钮元素
            let stopBtn = document.getElementById('stopBtn');
            const startBtn = document.getElementById('startBtn');
            
            // 4. 清理并重新创建停止按钮
            console.log('🧹 清理旧的事件监听器...');
            stopBtn = cleanupEventListeners(stopBtn);
            
            // 5. 强制设置按钮属性
            stopBtn.type = 'button';
            stopBtn.id = 'stopBtn';
            
            // 6. 创建强化的状态管理器
            const StateManager = {
                _isRecording: false,
                
                set isRecording(value) {
                    this._isRecording = value;
                    this.updateUI();
                    console.log('📊 录制状态更新:', value);
                },
                
                get isRecording() {
                    return this._isRecording;
                },
                
                updateUI() {
                    try {
                        if (this._isRecording) {
                            stopBtn.disabled = false;
                            stopBtn.className = 'btn btn-danger';
                            stopBtn.innerHTML = '<i class="bi bi-stop-circle"></i> 停止录制';
                            if (startBtn) {
                                startBtn.disabled = true;
                            }
                            debugInfo.buttonState = 'recording';
                        } else {
                            stopBtn.disabled = true;
                            stopBtn.className = 'btn btn-secondary';
                            stopBtn.innerHTML = '<i class="bi bi-stop-circle"></i> 停止录制';
                            if (startBtn) {
                                startBtn.disabled = false;
                            }
                            debugInfo.buttonState = 'idle';
                        }
                        
                        console.log('🎨 UI状态更新完成:', {
                            isRecording: this._isRecording,
                            stopBtnDisabled: stopBtn.disabled,
                            stopBtnClass: stopBtn.className
                        });
                    } catch (error) {
                        console.error('❌ UI更新失败:', error);
                    }
                }
            };
            
            // 7. 监听全局isRecording变量变化
            if (typeof window.isRecording !== 'undefined') {
                StateManager.isRecording = window.isRecording;
                
                // 使用Proxy监听变量变化（如果支持）
                if (typeof Proxy !== 'undefined') {
                    try {
                        window.isRecording = new Proxy({value: window.isRecording}, {
                            set(target, property, value) {
                                if (property === 'value') {
                                    StateManager.isRecording = value;
                                    target[property] = value;
                                }
                                return true;
                            },
                            get(target, property) {
                                return target[property];
                            }
                        }).value;
                    } catch (e) {
                        console.warn('⚠️ 无法设置Proxy监听');
                    }
                }
            }
            
            // 8. 创建超级强化的点击处理器
            const superStopHandler = async function(event) {
                console.log('🛑 超级停止处理器被触发!');
                console.log('📊 当前调试信息:', debugInfo);
                
                event.preventDefault();
                event.stopPropagation();
                event.stopImmediatePropagation();
                
                // 检查录制状态
                const currentRecordingState = StateManager.isRecording || 
                                            (typeof window.isRecording !== 'undefined' && window.isRecording) ||
                                            false;
                
                console.log('📊 录制状态检查:', {
                    stateManager: StateManager.isRecording,
                    windowVar: typeof window.isRecording !== 'undefined' ? window.isRecording : 'undefined',
                    final: currentRecordingState
                });
                
                if (!currentRecordingState) {
                    const forceStop = confirm('⚠️ 系统显示当前不在录制状态。\n\n是否强制发送停止指令？\n\n（如果录制确实在进行中，请点击"确定"）');
                    if (!forceStop) {
                        console.log('🚫 用户取消强制停止');
                        return;
                    }
                }
                
                // 禁用按钮，显示加载状态
                stopBtn.disabled = true;
                stopBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> 正在停止...';
                
                try {
                    console.log('📤 发送停止请求到 /api/recording/stop');
                    
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10秒超时
                    
                    const response = await fetch('/api/recording/stop', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        },
                        signal: controller.signal
                    });
                    
                    clearTimeout(timeoutId);
                    
                    console.log('📥 响应状态:', response.status, response.statusText);
                    
                    let result;
                    const contentType = response.headers.get('content-type');
                    
                    if (contentType && contentType.includes('application/json')) {
                        result = await response.json();
                    } else {
                        const text = await response.text();
                        console.warn('⚠️ 非JSON响应:', text);
                        result = { success: false, error: '服务器返回非JSON响应: ' + text };
                    }
                    
                    console.log('📋 解析后的响应:', result);
                    
                    if (response.ok && result.success) {
                        console.log('✅ 停止录制成功!');
                        
                        // 更新状态
                        StateManager.isRecording = false;
                        if (typeof window.isRecording !== 'undefined') {
                            window.isRecording = false;
                        }
                        
                        // 显示成功消息
                        const message = result.message || '录制已成功停止';
                        if (typeof showNotification === 'function') {
                            showNotification(message, 'success');
                        } else {
                            alert('✅ ' + message);
                        }
                        
                        // 刷新会话列表
                        if (typeof loadSessions === 'function') {
                            setTimeout(loadSessions, 500);
                        }
                        
                        // 触发自定义事件
                        window.dispatchEvent(new CustomEvent('recording-stopped', { detail: result }));
                        
                    } else {
                        throw new Error(result.error || result.message || `HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                } catch (error) {
                    console.error('❌ 停止录制失败:', error);
                    debugInfo.lastError = error.message;
                    
                    let errorMessage = '停止录制失败: ';
                    if (error.name === 'AbortError') {
                        errorMessage += '请求超时';
                    } else if (error.message) {
                        errorMessage += error.message;
                    } else {
                        errorMessage += '未知错误';
                    }
                    
                    if (typeof showNotification === 'function') {
                        showNotification(errorMessage, 'danger');
                    } else {
                        alert('❌ ' + errorMessage);
                    }
                } finally {
                    // 恢复按钮状态
                    StateManager.updateUI();
                }
            };
            
            // 9. 绑定事件监听器（多重绑定确保生效）
            console.log('🔗 绑定事件监听器...');
            
            stopBtn.addEventListener('click', superStopHandler, true); // 捕获阶段
            stopBtn.addEventListener('click', superStopHandler, false); // 冒泡阶段
            stopBtn.onclick = superStopHandler; // 直接绑定
            
            // 10. 定期状态同步
            setInterval(() => {
                try {
                    if (typeof window.isRecording !== 'undefined' && 
                        StateManager.isRecording !== window.isRecording) {
                        console.log('🔄 同步录制状态:', window.isRecording);
                        StateManager.isRecording = window.isRecording;
                    }
                } catch (error) {
                    console.warn('⚠️ 状态同步警告:', error);
                }
            }, 1000);
            
            // 11. 初始化状态
            StateManager.updateUI();
            
            // 12. 暴露全局调试接口
            window.ultimateStopFix = {
                StateManager,
                debugInfo,
                manualStop: () => stopBtn.click(),
                forceStop: superStopHandler,
                reapplyFix: ultimateStopButtonFix,
                checkStatus: () => {
                    console.log('🔍 当前状态:', {
                        debugInfo,
                        stateManager: StateManager.isRecording,
                        windowVar: typeof window.isRecording !== 'undefined' ? window.isRecording : 'undefined',
                        buttonDisabled: stopBtn.disabled,
                        buttonClass: stopBtn.className
                    });
                }
            };
            
            console.log('✅ 终极停止按钮修复完成!');
            console.log('💡 可用调试命令:');
            console.log('  - ultimateStopFix.manualStop() // 手动触发停止');
            console.log('  - ultimateStopFix.forceStop() // 强制停止');
            console.log('  - ultimateStopFix.checkStatus() // 检查状态');
            console.log('  - ultimateStopFix.reapplyFix() // 重新应用修复');
            
            isFixApplied = true;
            return true;
            
        } catch (error) {
            console.error('❌ 终极修复失败:', error);
            debugInfo.lastError = error.message;
            
            // 如果修复失败，至少尝试基本修复
            try {
                const stopBtn = document.getElementById('stopBtn');
                if (stopBtn) {
                    stopBtn.addEventListener('click', async () => {
                        const response = await fetch('/api/recording/stop', { method: 'POST' });
                        const result = await response.json();
                        console.log('基本停止结果:', result);
                        alert(result.success ? '停止成功' : '停止失败: ' + result.error);
                    });
                    console.log('🔧 应用了基本修复');
                }
            } catch (basicError) {
                console.error('❌ 连基本修复都失败了:', basicError);
            }
            
            return false;
        }
    }
    
    // 等待DOM加载完成后执行修复
    waitForDOM().then(() => {
        console.log('📄 DOM加载完成，开始修复...');
        ultimateStopButtonFix();
    });
    
    // 如果DOM已经加载但修复未应用，立即执行
    if (document.readyState === 'complete' && !isFixApplied) {
        setTimeout(ultimateStopButtonFix, 100);
    }
    
})(); 