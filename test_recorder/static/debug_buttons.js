// 调试停止按钮的独立脚本
console.log('🔧 开始调试停止按钮功能');

// 检查DOM元素
function checkDOMElements() {
    console.log('📍 检查DOM元素:');
    
    const stopBtn = document.getElementById('stopBtn');
    console.log('stopBtn元素:', stopBtn);
    console.log('stopBtn disabled状态:', stopBtn ? stopBtn.disabled : 'N/A');
    console.log('stopBtn className:', stopBtn ? stopBtn.className : 'N/A');
    
    const startBtn = document.getElementById('startBtn');
    console.log('startBtn元素:', startBtn);
    console.log('startBtn disabled状态:', startBtn ? startBtn.disabled : 'N/A');
    
    return { stopBtn, startBtn };
}

// 检查事件监听器
function checkEventListeners() {
    console.log('📍 检查事件监听器:');
    
    const stopBtn = document.getElementById('stopBtn');
    if (stopBtn) {
        // 获取已绑定的事件监听器（只在支持的浏览器中工作）
        try {
            const listeners = getEventListeners ? getEventListeners(stopBtn) : 'getEventListeners不可用';
            console.log('stopBtn事件监听器:', listeners);
        } catch (e) {
            console.log('无法获取事件监听器信息（正常现象）');
        }
        
        // 测试点击响应
        console.log('手动触发点击事件...');
        const clickEvent = new Event('click', { bubbles: true });
        stopBtn.dispatchEvent(clickEvent);
    }
}

// 测试API连接
async function testStopAPI() {
    console.log('📍 测试停止录制API:');
    
    try {
        const response = await fetch('/api/recording/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        console.log('API响应状态:', response.status);
        console.log('API响应内容:', result);
        
        if (!result.success) {
            console.log('API错误:', result.error || result.message);
        }
        
    } catch (error) {
        console.error('API调用失败:', error);
    }
}

// 检查全局变量
function checkGlobalVariables() {
    console.log('📍 检查全局变量:');
    console.log('isRecording:', typeof isRecording !== 'undefined' ? isRecording : '未定义');
    console.log('currentSessionId:', typeof currentSessionId !== 'undefined' ? currentSessionId : '未定义');
    console.log('ws连接状态:', typeof ws !== 'undefined' && ws ? ws.readyState : '未定义');
}

// 手动绑定停止按钮事件（用于测试）
function manualBindStopButton() {
    console.log('📍 手动绑定停止按钮事件:');
    
    const stopBtn = document.getElementById('stopBtn');
    if (stopBtn) {
        // 移除之前的事件监听器
        const newStopBtn = stopBtn.cloneNode(true);
        stopBtn.parentNode.replaceChild(newStopBtn, stopBtn);
        
        // 添加新的事件监听器
        newStopBtn.addEventListener('click', function() {
            console.log('🚫 停止按钮被点击！');
            
            // 显示确认信息
            if (confirm('确认停止录制？')) {
                console.log('用户确认停止录制');
                testStopAPI();
            }
        });
        
        console.log('✅ 手动绑定完成');
        console.log('请尝试点击停止按钮');
    } else {
        console.error('❌ 找不到停止按钮');
    }
}

// 综合诊断函数
function diagnoseStopButton() {
    console.log('🏥 开始综合诊断...');
    console.log('====================');
    
    checkDOMElements();
    console.log('--------------------');
    checkGlobalVariables();
    console.log('--------------------');
    checkEventListeners();
    console.log('--------------------');
    
    console.log('🔧 如果停止按钮仍然不工作，请尝试运行: manualBindStopButton()');
    console.log('🔧 或者直接测试API: testStopAPI()');
}

// 页面加载完成后自动运行诊断
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', diagnoseStopButton);
} else {
    diagnoseStopButton();
}

// 暴露函数到全局作用域供手动调用
window.debugStopButton = {
    diagnose: diagnoseStopButton,
    checkDOM: checkDOMElements,
    checkEvents: checkEventListeners,
    testAPI: testStopAPI,
    checkVars: checkGlobalVariables,
    manualBind: manualBindStopButton
};

console.log('🔧 调试工具已加载，使用 debugStopButton.diagnose() 开始诊断'); 