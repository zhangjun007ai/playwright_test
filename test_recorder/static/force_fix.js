// 强制停止按钮修复 - 绕过所有冲突
(function() {
    'use strict';
    
    console.log('🚨 强制停止按钮修复启动...');
    
    // 强制等待并修复
    function forceFix() {
        const stopBtn = document.getElementById('stopBtn');
        if (!stopBtn) {
            console.log('⏱️ 等待停止按钮出现...');
            setTimeout(forceFix, 100);
            return;
        }
        
        console.log('🎯 找到停止按钮，开始强制修复...');
        
        // 1. 暴力清除所有事件监听器
        const parent = stopBtn.parentNode;
        const newBtn = document.createElement('button');
        
        // 复制所有属性
        newBtn.type = 'button';
        newBtn.className = stopBtn.className;
        newBtn.id = 'stopBtn';
        newBtn.innerHTML = stopBtn.innerHTML;
        newBtn.disabled = stopBtn.disabled;
        
        // 替换按钮
        parent.replaceChild(newBtn, stopBtn);
        
        console.log('🔄 按钮已完全重建');
        
        // 2. 创建超级简单的点击处理器
        newBtn.addEventListener('click', async function(e) {
            console.log('🛑 强制停止处理器触发！');
            e.preventDefault();
            e.stopImmediatePropagation();
            
            // 强制启用按钮（临时）
            if (newBtn.disabled) {
                console.log('⚠️ 按钮被禁用，强制启用进行测试');
                const shouldProceed = confirm('停止按钮当前被禁用。\n\n是否强制发送停止指令？\n\n点击"确定"继续，"取消"退出。');
                if (!shouldProceed) {
                    console.log('🚫 用户取消操作');
                    return;
                }
            }
            
            // 显示处理状态
            const originalHTML = newBtn.innerHTML;
            newBtn.disabled = true;
            newBtn.innerHTML = '🔄 处理中...';
            
            try {
                console.log('📤 发送停止请求...');
                
                const response = await fetch('/api/recording/stop', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                });
                
                console.log('📥 响应状态:', response.status);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const result = await response.json();
                console.log('📋 API响应:', result);
                
                if (result.success) {
                    console.log('✅ 停止成功！');
                    alert('✅ 录制已成功停止！\n\n' + (result.message || '操作完成'));
                    
                    // 更新按钮状态
                    newBtn.disabled = true;
                    newBtn.className = 'btn btn-secondary';
                    newBtn.innerHTML = '<i class="bi bi-stop-circle"></i> 停止录制';
                    
                    // 启用开始按钮
                    const startBtn = document.getElementById('startBtn');
                    if (startBtn) {
                        startBtn.disabled = false;
                    }
                    
                    // 更新全局状态
                    if (typeof window.isRecording !== 'undefined') {
                        window.isRecording = false;
                    }
                    
                    // 刷新页面数据
                    if (typeof window.loadSessions === 'function') {
                        setTimeout(window.loadSessions, 1000);
                    }
                    
                } else {
                    throw new Error(result.error || result.message || '停止失败');
                }
                
            } catch (error) {
                console.error('❌ 停止失败:', error);
                alert('❌ 停止录制失败：\n\n' + error.message + '\n\n请检查控制台查看详细信息。');
            } finally {
                // 恢复按钮
                newBtn.innerHTML = originalHTML;
                // 不在这里修改disabled状态，让其他逻辑处理
            }
        });
        
        // 3. 创建状态强制更新器
        function forceUpdateButtonState() {
            try {
                const isRecording = typeof window.isRecording !== 'undefined' ? window.isRecording : false;
                
                if (isRecording) {
                    newBtn.disabled = false;
                    newBtn.className = 'btn btn-danger';
                } else {
                    newBtn.disabled = true;
                    newBtn.className = 'btn btn-secondary';
                }
                
                console.log('🎨 强制更新按钮状态:', { isRecording, disabled: newBtn.disabled });
            } catch (error) {
                console.warn('⚠️ 状态更新警告:', error);
            }
        }
        
        // 4. 定期强制更新
        setInterval(forceUpdateButtonState, 1000);
        
        // 5. 立即更新一次
        forceUpdateButtonState();
        
        // 6. 暴露强制调试接口
        window.forceStopRecording = function() {
            console.log('🚨 手动触发强制停止');
            newBtn.click();
        };
        
        window.forceEnableStopButton = function() {
            console.log('🚨 强制启用停止按钮');
            newBtn.disabled = false;
            newBtn.className = 'btn btn-danger';
        };
        
        window.forceTestAPI = async function() {
            console.log('🚨 强制测试API');
            try {
                const response = await fetch('/api/recording/stop', { method: 'POST' });
                const result = await response.json();
                console.log('强制API测试结果:', result);
                alert('API测试结果: ' + JSON.stringify(result, null, 2));
            } catch (error) {
                console.error('强制API测试失败:', error);
                alert('API测试失败: ' + error.message);
            }
        };
        
        console.log('✅ 强制修复完成！');
        console.log('💡 调试命令:');
        console.log('  - forceStopRecording() // 强制触发停止');
        console.log('  - forceEnableStopButton() // 强制启用按钮');
        console.log('  - forceTestAPI() // 强制测试API');
        
        // 显示修复完成通知
        setTimeout(() => {
            if (typeof alert !== 'undefined') {
                alert('🛠️ 强制修复已完成！\n\n停止按钮现在应该可以工作了。\n\n如果还有问题，请按F12打开控制台查看调试信息。');
            }
        }, 1000);
    }
    
    // 立即开始修复
    forceFix();
    
})(); 