// 停止按钮修复脚本
(function() {
    console.log('🔧 开始修复停止按钮...');
    
    // 等待DOM加载完成
    function initFix() {
        const stopBtn = document.getElementById('stopBtn');
        const startBtn = document.getElementById('startBtn');
        
        if (!stopBtn) {
            console.error('❌ 找不到停止按钮');
            return;
        }
        
        console.log('✅ 找到停止按钮，开始修复...');
        
        // 1. 移除所有现有的点击事件监听器
        const newStopBtn = stopBtn.cloneNode(true);
        stopBtn.parentNode.replaceChild(newStopBtn, stopBtn);
        
        // 2. 确保按钮在录制时可用
        function updateButtonStates() {
            const isCurrentlyRecording = typeof isRecording !== 'undefined' ? isRecording : false;
            
            if (isCurrentlyRecording) {
                if (startBtn) startBtn.disabled = true;
                newStopBtn.disabled = false;
                newStopBtn.classList.remove('btn-secondary');
                newStopBtn.classList.add('btn-danger');
            } else {
                if (startBtn) startBtn.disabled = false;
                newStopBtn.disabled = true;
                newStopBtn.classList.remove('btn-danger');
                newStopBtn.classList.add('btn-secondary');
            }
            
            console.log('按钮状态更新:', {
                isRecording: isCurrentlyRecording,
                stopBtnDisabled: newStopBtn.disabled,
                startBtnDisabled: startBtn ? startBtn.disabled : 'N/A'
            });
        }
        
        // 3. 添加强化的点击事件处理器
        newStopBtn.addEventListener('click', async function(e) {
            console.log('🚫 停止按钮被点击！');
            e.preventDefault();
            e.stopPropagation();
            
            // 检查是否真的在录制
            if (typeof isRecording === 'undefined' || !isRecording) {
                console.log('⚠️ 当前不在录制状态，但仍尝试停止');
                if (!confirm('当前似乎不在录制状态，是否仍要发送停止指令？')) {
                    return;
                }
            }
            
            // 禁用按钮防止重复点击
            newStopBtn.disabled = true;
            newStopBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> 停止中...';
            
            try {
                console.log('📤 发送停止录制请求...');
                
                const response = await fetch('/api/recording/stop', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                console.log('📥 收到响应，状态:', response.status);
                
                if (response.ok) {
                    const result = await response.json();
                    console.log('📋 响应内容:', result);
                    
                    if (result.success) {
                        console.log('✅ 停止录制成功');
                        
                        // 更新UI状态
                        if (typeof isRecording !== 'undefined') {
                            isRecording = false;
                        }
                        updateButtonStates();
                        
                        // 显示成功通知
                        if (typeof showNotification === 'function') {
                            showNotification('录制已停止', 'success');
                        } else {
                            alert('录制已停止');
                        }
                        
                        // 刷新会话列表
                        if (typeof loadSessions === 'function') {
                            loadSessions();
                        }
                    } else {
                        throw new Error(result.error || result.message || '停止录制失败');
                    }
                } else {
                    const errorText = await response.text();
                    throw new Error(`HTTP ${response.status}: ${errorText}`);
                }
                
            } catch (error) {
                console.error('❌ 停止录制失败:', error);
                
                // 显示错误通知
                if (typeof showNotification === 'function') {
                    showNotification(`停止录制失败: ${error.message}`, 'danger');
                } else {
                    alert(`停止录制失败: ${error.message}`);
                }
            } finally {
                // 恢复按钮状态
                newStopBtn.innerHTML = '<i class="bi bi-stop-circle"></i> 停止录制';
                updateButtonStates();
            }
        });
        
        // 4. 监听全局录制状态变化
        if (typeof window.addEventListener === 'function') {
            window.addEventListener('recording-state-changed', updateButtonStates);
        }
        
        // 5. 定期检查状态
        setInterval(updateButtonStates, 1000);
        
        // 6. 初始状态更新
        updateButtonStates();
        
        console.log('✅ 停止按钮修复完成！');
        
        // 暴露手动触发函数
        window.manualStopRecording = function() {
            newStopBtn.click();
        };
        
        console.log('💡 可以通过 manualStopRecording() 手动触发停止录制');
    }
    
    // 等待DOM准备好
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initFix);
    } else {
        initFix();
    }
})(); 