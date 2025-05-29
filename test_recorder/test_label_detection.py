#!/usr/bin/env python3
"""
标签识别功能测试
演示如何识别输入框的标签并生成友好的描述
"""

import asyncio
import time
from core.realtime_recorder import realtime_recorder

async def test_label_detection():
    """测试标签识别功能"""
    
    # 创建测试HTML页面
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>标签识别测试页面</title>
        <meta charset="UTF-8">
        <style>
            .required::before {
                content: "*";
                color: red;
                margin-right: 4px;
            }
            .form-item {
                margin: 10px 0;
            }
            label {
                display: inline-block;
                min-width: 100px;
            }
        </style>
    </head>
    <body>
        <h1>标签识别测试</h1>
        
        <!-- 测试场景1: 带星号和冒号的表单项 -->
        <div class="form-item">
            <label class="required">参数名称：</label>
            <input type="text" id="configName" name="configName">
        </div>
        
        <!-- 测试场景2: 带序号的表单项 -->
        <div class="form-item">
            <label>1. 参数键名：</label>
            <input type="text" id="configKey" name="configKey">
        </div>
        
        <!-- 测试场景3: 带括号的表单项 -->
        <div class="form-item">
            <label>参数值(必填)：</label>
            <input type="text" id="configValue" name="configValue">
        </div>
        
        <!-- 测试场景4: 带提示词的表单项 -->
        <div class="form-item">
            <label>系统内置：</label>
            <select id="configType" name="configType">
                <option value="">请选择类型</option>
                <option value="1">是</option>
                <option value="0">否</option>
            </select>
        </div>
        
        <!-- 测试场景5: 表格布局 -->
        <table>
            <tr>
                <th class="required">备注说明：</th>
                <td><textarea id="remark" name="remark"></textarea></td>
            </tr>
        </table>
        
        <!-- 测试场景6: 纯文本标签 -->
        <div class="form-item">
            <span class="required">排序号</span>
            <input type="number" id="orderNum" name="orderNum">
        </div>
        
        <!-- 按钮测试 -->
        <div class="form-item">
            <button type="submit">确定</button>
            <button type="button">取消</button>
        </div>
        
        <script>
            // 添加一些交互事件便于测试
            setTimeout(() => {
                console.log('测试页面已加载完成');
            }, 1000);
        </script>
    </body>
    </html>
    """
    
    print("🚀 开始标签识别功能测试...")
    
    try:
        # 初始化录制器
        realtime_recorder.initialize()
        
        # 开始录制
        session_id = realtime_recorder.start_recording("标签识别测试", "测试智能标签识别功能")
        
        print(f"✅ 录制已开始，会话ID: {session_id}")
        print("📝 浏览器已启动，请执行以下操作来测试标签识别：")
        print()
        print("🔹 在【参数名称】输入框中输入一些文字")
        print("🔹 在【参数键名】输入框中输入一些文字") 
        print("🔹 在【参数值】输入框中输入参数值")
        print("🔹 在【系统内置】下拉框中选择一个选项")
        print("🔹 在【备注说明】文本区域中输入文字")
        print("🔹 点击【确定】按钮")
        print()
        print("⏰ 将在60秒后自动停止录制...")
        
        # 等待用户操作
        await asyncio.sleep(5)  # 等待浏览器启动
        
        # 导航到测试页面（使用data URL）
        import base64
        html_encoded = base64.b64encode(test_html.encode('utf-8')).decode('utf-8')
        data_url = f"data:text/html;charset=utf-8;base64,{html_encoded}"
        
        if realtime_recorder.page:
            await realtime_recorder.page.goto(data_url)
            print("📄 测试页面已加载")
        
        # 等待用户测试
        await asyncio.sleep(55)
        
        # 停止录制
        session = realtime_recorder.stop_recording()
        
        print("✅ 录制已完成")
        print(f"📊 总操作数: {len(session.actions)}")
        print()
        print("🔍 操作记录分析:")
        
        for i, action in enumerate(session.actions, 1):
            print(f"{i:2d}. {action.page_title}")
            if hasattr(action, 'description'):
                print(f"    描述: {action.description}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    finally:
        # 清理资源
        try:
            realtime_recorder.cleanup()
        except:
            pass

def main():
    """主函数"""
    print("=" * 60)
    print("🧪 Playwright Python 录制系统 - 标签识别功能测试")
    print("=" * 60)
    print()
    
    # 运行异步测试
    success = asyncio.run(test_label_detection())
    
    if success:
        print("🎉 标签识别功能测试完成！")
        print("✨ 现在录制系统能够智能识别输入框标签，生成更友好的描述")
    else:
        print("💔 测试失败，请检查日志")

if __name__ == "__main__":
    main() 