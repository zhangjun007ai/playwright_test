// 主页面停止按钮修复脚本
(function() {
    'use strict';
    
    console.log('🔧 主页面停止按钮修复开始...');
    
    let fixApplied = false;
    let originalStopRecording = null;
    
    // 等待DOM和其他脚本加载完成
    function waitForReady() {
        return new Promise((resolve) => {
            // 等待DOM完全加载且其他脚本初始化完成
            if (document.readyState === 'complete') {
                setTimeout(resolve, 500); // 额外等待确保其他脚本加载完成
            } else {
                window.addEventListener('load', () => {
                    setTimeout(resolve, 500);
                });
            }
        });
    }
    
    function applyMainPageFix() {
        try {
            console.log('🛠️ 开始应用主页面修复...');
            
            const stopBtn = document.getElementById('stopBtn');
            if (!stopBtn) {
                console.error('❌ 找不到停止按钮');
                return false;
            }
            
            // 1. 保存原始的stopRecording函数（如果存在）
            if (typeof window.stopRecording === 'function') {
                originalStopRecording = window.stopRecording;
                console.log('📦 已保存原始stopRecording函数');
            }
            
            // 2. 创建增强的stopRecording函数
            window.stopRecording = async function() {
                console.log('🛑 增强的stopRecording函数被调用');
                
                try {
                    // 禁用按钮防止重复点击
                    stopBtn.disabled = true;
                    stopBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> 停止中...';
                    
                    const response = await fetch('/api/recording/stop', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    const result = await response.json();
                    console.log('📥 停止录制API响应:', result);
                    
                    if (result.success) {
                        console.log('✅ 停止录制成功');
                        
                        // 更新全局状态
                        if (typeof window.isRecording !== 'undefined') {
                            window.isRecording = false;
                        }
                        
                        // 调用原始的handleRecordingStopped处理器（如果存在）
                        if (typeof window.handleRecordingStopped === 'function') {
                            window.handleRecordingStopped(result);
                        }
                        
                        // 调用原始的updateUI函数（如果存在）
                        if (typeof window.updateUI === 'function') {
                            window.updateUI();
                        }
                        
                        // 显示通知
                        if (typeof window.showNotification === 'function') {
                            window.showNotification(result.message || '录制已停止', 'success');
                        }
                        
                        // 刷新会话列表
                        if (typeof window.loadSessions === 'function') {
                            setTimeout(window.loadSessions, 500);
                        }
                        
                        // 如果有TestRecorderApp实例，也调用它的方法
                        if (typeof window.app !== 'undefined' && window.app.handleRecordingStopped) {
                            window.app.handleRecordingStopped(result);
                        }
                        
                    } else {
                        throw new Error(result.error || result.message || '停止录制失败');
                    }
                    
                } catch (error) {
                    console.error('❌ 停止录制失败:', error);
                    
                    let errorMessage = '停止录制失败: ' + error.message;
                    
                    if (typeof window.showNotification === 'function') {
                        window.showNotification(errorMessage, 'danger');
                    } else {
                        alert(errorMessage);
                    }
                } finally {
                    // 恢复按钮状态
                    stopBtn.innerHTML = '<i class="bi bi-stop-circle"></i> 停止录制';
                    
                    // 确保UI状态正确
                    if (typeof window.updateUI === 'function') {
                        setTimeout(window.updateUI, 100);
                    } else {
                        // 手动更新按钮状态
                        const isCurrentlyRecording = typeof window.isRecording !== 'undefined' ? window.isRecording : false;
                        stopBtn.disabled = !isCurrentlyRecording;
                        stopBtn.className = isCurrentlyRecording ? 'btn btn-danger' : 'btn btn-secondary';
                    }
                }
            };
            
            // 3. 确保停止按钮的click事件正确绑定
            function ensureStopButtonBinding() {
                // 移除所有现有的事件监听器
                const newStopBtn = stopBtn.cloneNode(true);
                stopBtn.parentNode.replaceChild(newStopBtn, stopBtn);
                
                // 绑定新的事件监听器
                newStopBtn.addEventListener('click', async function(e) {
                    console.log('🖱️ 停止按钮点击事件触发');
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // 检查按钮是否应该可用
                    if (newStopBtn.disabled) {
                        console.log('⚠️ 停止按钮当前被禁用');
                        return;
                    }
                    
                    // 调用增强的stopRecording函数
                    await window.stopRecording();
                });
                
                console.log('🔗 停止按钮事件监听器已重新绑定');
                return newStopBtn;
            }
            
            const newStopBtn = ensureStopButtonBinding();
            
            // 4. 监听录制状态变化并自动更新UI
            function createStateWatcher() {
                let lastRecordingState = false;
                
                const watcher = setInterval(() => {
                    try {
                        const currentState = typeof window.isRecording !== 'undefined' ? window.isRecording : false;
                        
                        if (currentState !== lastRecordingState) {
                            console.log('📊 检测到录制状态变化:', lastRecordingState, '->', currentState);
                            lastRecordingState = currentState;
                            
                            // 更新按钮状态
                            newStopBtn.disabled = !currentState;
                            newStopBtn.className = currentState ? 'btn btn-danger' : 'btn btn-secondary';
                            
                            // 触发UI更新
                            if (typeof window.updateUI === 'function') {
                                window.updateUI();
                            }
                        }
                    } catch (error) {
                        console.warn('⚠️ 状态监听器错误:', error);
                    }
                }, 500);
                
                return watcher;
            }
            
            const stateWatcher = createStateWatcher();
            
            // 5. 暴露调试接口
            window.mainPageFix = {
                version: '1.0',
                applied: true,
                stopRecording: window.stopRecording,
                originalStopRecording,
                stateWatcher,
                reapply: applyMainPageFix,
                checkStatus: () => {
                    console.log('🔍 主页面修复状态:', {
                        fixApplied: fixApplied,
                        stopBtnExists: !!document.getElementById('stopBtn'),
                        stopBtnDisabled: document.getElementById('stopBtn')?.disabled,
                        isRecordingVar: typeof window.isRecording !== 'undefined' ? window.isRecording : 'undefined',
                        stopRecordingFunc: typeof window.stopRecording,
                        originalFunc: typeof originalStopRecording
                    });
                }
            };
            
            console.log('✅ 主页面停止按钮修复完成!');
            console.log('💡 调试命令: mainPageFix.checkStatus()');
            
            fixApplied = true;
            return true;
            
        } catch (error) {
            console.error('❌ 主页面修复失败:', error);
            return false;
        }
    }
    
    // 等待页面准备就绪后应用修复
    waitForReady().then(() => {
        console.log('📄 页面准备就绪，应用主页面修复...');
        applyMainPageFix();
    });
    
    // 如果页面已经完全加载，立即尝试修复
    if (document.readyState === 'complete') {
        setTimeout(() => {
            if (!fixApplied) {
                console.log('🔄 备用修复触发...');
                applyMainPageFix();
            }
        }, 1000);
    }
    
})(); 