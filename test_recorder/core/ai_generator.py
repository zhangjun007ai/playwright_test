import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from loguru import logger
from config.settings import settings, ACTION_TYPES, ELEMENT_TYPES
from core.models import ActionRecord, TestStep, TestCase, TestSession


class AITestCaseGenerator:
    """AI测试用例生成器"""
    
    def __init__(self):
        self.action_templates = {
            "click": "点击【{element_desc}】{element_type}",
            "fill": "在【{element_desc}】{element_type}中输入\"{value}\"",
            "select": "在【{element_desc}】下拉框中选择\"{value}\"",
            "check": "勾选【{element_desc}】复选框",
            "uncheck": "取消勾选【{element_desc}】复选框",
            "hover": "鼠标悬停在【{element_desc}】{element_type}上",
            "goto": "访问页面：{url}",
            "press": "按下{key}键",
            "wait": "等待{duration}秒"
        }
    
    def generate_test_case(self, session: TestSession) -> TestCase:
        """从会话记录生成完整的测试用例"""
        try:
            # 分析操作记录，生成测试步骤
            test_steps = self._generate_test_steps(session.actions)
            
            # 生成测试用例基本信息
            test_case = TestCase(
                id=f"TC_{session.id[:8]}",
                name=session.name or f"自动录制测试用例_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                description=session.description or self._generate_description(session),
                test_steps=test_steps,
                screenshots=[action.screenshot_path for action in session.actions if action.screenshot_path],
                trace_file=session.trace_file,
                created_time=session.start_time,
                execution_time=session.duration
            )
            
            # 推断测试模块和类别
            test_case.module = self._infer_module(session.actions)
            test_case.category = self._infer_category(session.actions)
            
            # 生成前置条件
            test_case.preconditions = self._generate_preconditions(session.actions)
            
            logger.info(f"成功生成测试用例: {test_case.name}")
            return test_case
            
        except Exception as e:
            logger.error(f"生成测试用例失败: {e}")
            raise
    
    def _generate_test_steps(self, actions: List[ActionRecord]) -> List[TestStep]:
        """生成测试步骤"""
        test_steps = []
        step_number = 1
        
        for action in actions:
            try:
                # 生成步骤描述
                description = self._generate_step_description(action)
                if not description:
                    continue
                
                # 生成预期结果
                expected_result = self._generate_expected_result(action)
                
                test_step = TestStep(
                    step_number=step_number,
                    action=action.action_type,
                    description=description,
                    expected_result=expected_result,
                    screenshot_path=action.screenshot_path or "",
                    status="待执行"
                )
                
                test_steps.append(test_step)
                step_number += 1
                
            except Exception as e:
                logger.warning(f"生成步骤失败: {e}")
                continue
        
        return test_steps
    
    def _generate_step_description(self, action: ActionRecord) -> str:
        """生成单个步骤的描述"""
        try:
            action_type = action.action_type.lower()
            element_info = action.element_info or {}
            
            if action_type == "goto" or action_type == "navigation":
                return f"访问页面：{action.page_url}"
            
            # 获取元素描述
            element_desc = self._get_element_description(element_info)
            element_type = self._get_element_type(element_info)
            
            if action_type in self.action_templates:
                template = self.action_templates[action_type]
                
                # 根据操作类型填充模板
                if action_type == "fill":
                    value = self._extract_input_value(action)
                    return template.format(
                        element_desc=element_desc,
                        element_type=element_type,
                        value=value
                    )
                elif action_type == "select":
                    value = self._extract_select_value(action)
                    return template.format(
                        element_desc=element_desc,
                        value=value
                    )
                elif action_type == "press":
                    key = self._extract_key_value(action)
                    return template.format(key=key)
                else:
                    return template.format(
                        element_desc=element_desc,
                        element_type=element_type
                    )
            
            # 默认描述
            action_name = ACTION_TYPES.get(action_type, action_type)
            return f"{action_name}【{element_desc}】{element_type}"
            
        except Exception as e:
            logger.warning(f"生成步骤描述失败: {e}")
            return f"执行{action.action_type}操作"
    
    def _get_element_description(self, element_info: Dict) -> str:
        """获取元素描述"""
        if not element_info:
            return "未知元素"
        
        # 优先级：文本内容 > placeholder > name > id > 类名
        if element_info.get('text'):
            text = element_info['text'].strip()[:20]
            return text if text else "空文本"
        
        if element_info.get('placeholder'):
            return element_info['placeholder']
        
        if element_info.get('name'):
            return element_info['name']
        
        if element_info.get('id'):
            return element_info['id']
        
        if element_info.get('className'):
            return element_info['className'].split()[0] if element_info['className'] else ""
        
        return element_info.get('tagName', '未知元素')
    
    def _get_element_type(self, element_info: Dict) -> str:
        """获取元素类型描述"""
        if not element_info:
            return ""
        
        tag_name = element_info.get('tagName', '').lower()
        element_type = element_info.get('type', '').lower()
        
        # 根据标签和类型推断
        if tag_name == 'button':
            return "按钮"
        elif tag_name == 'input':
            if element_type == 'text' or element_type == '':
                return "输入框"
            elif element_type == 'password':
                return "密码框"
            elif element_type == 'checkbox':
                return "复选框"
            elif element_type == 'radio':
                return "单选按钮"
            elif element_type == 'submit':
                return "提交按钮"
            else:
                return "输入框"
        elif tag_name == 'select':
            return "下拉框"
        elif tag_name == 'textarea':
            return "文本域"
        elif tag_name == 'a':
            return "链接"
        elif tag_name == 'img':
            return "图片"
        elif tag_name in ['div', 'span']:
            return "区域"
        
        return ELEMENT_TYPES.get(tag_name, "元素")
    
    def _extract_input_value(self, action: ActionRecord) -> str:
        """提取输入值"""
        # 尝试从不同来源获取输入值
        if action.additional_data:
            try:
                if isinstance(action.additional_data, str):
                    # 可能是JSON字符串
                    if action.additional_data.startswith('{'):
                        data = json.loads(action.additional_data)
                        return data.get('value', action.additional_data)
                    else:
                        return action.additional_data
                return str(action.additional_data)
            except:
                pass
        
        if action.element_info and action.element_info.get('value'):
            return action.element_info['value']
        
        return "输入内容"
    
    def _extract_select_value(self, action: ActionRecord) -> str:
        """提取选择值"""
        try:
            if action.additional_data:
                if isinstance(action.additional_data, str) and action.additional_data.startswith('{'):
                    data = json.loads(action.additional_data)
                    return data.get('selectedText', data.get('value', '选择项'))
                return str(action.additional_data)
            
            if action.element_info and action.element_info.get('value'):
                return action.element_info['value']
            
        except:
            pass
        
        return "选择项"
    
    def _extract_key_value(self, action: ActionRecord) -> str:
        """提取按键值"""
        try:
            if action.additional_data:
                if isinstance(action.additional_data, str) and action.additional_data.startswith('{'):
                    data = json.loads(action.additional_data)
                    return data.get('key', 'Enter')
                return str(action.additional_data)
        except:
            pass
        
        return "Enter"
    
    def _generate_expected_result(self, action: ActionRecord) -> str:
        """生成预期结果"""
        action_type = action.action_type.lower()
        
        if action_type == "goto" or action_type == "navigation":
            return f"成功访问页面，页面标题显示为：{action.page_title}"
        
        elif action_type == "click":
            element_desc = self._get_element_description(action.element_info or {})
            return f"成功点击【{element_desc}】，系统响应正常"
        
        elif action_type == "fill":
            element_desc = self._get_element_description(action.element_info or {})
            value = self._extract_input_value(action)
            return f"【{element_desc}】输入框中显示输入的内容：{value}"
        
        elif action_type == "select":
            element_desc = self._get_element_description(action.element_info or {})
            value = self._extract_select_value(action)
            return f"【{element_desc}】下拉框中选中：{value}"
        
        elif action_type in ["check", "uncheck"]:
            element_desc = self._get_element_description(action.element_info or {})
            state = "选中" if action_type == "check" else "取消选中"
            return f"【{element_desc}】复选框状态变为：{state}"
        
        else:
            return "操作执行成功，界面响应正常"
    
    def _generate_description(self, session: TestSession) -> str:
        """生成测试用例描述"""
        if session.description:
            return session.description
        
        # 根据操作记录推断测试目的
        actions = session.actions
        if not actions:
            return "自动录制的UI测试用例"
        
        # 分析主要操作
        action_types = [action.action_type for action in actions]
        
        if "fill" in action_types and "click" in action_types:
            return "包含表单填写和按钮点击的功能测试"
        elif "click" in action_types:
            return "包含界面点击操作的功能测试"
        elif "fill" in action_types:
            return "包含数据输入的功能测试"
        else:
            return "UI界面操作功能测试"
    
    def _infer_module(self, actions: List[ActionRecord]) -> str:
        """推断测试模块"""
        if not actions:
            return "未知模块"
        
        # 从URL路径推断模块
        urls = [action.page_url for action in actions if action.page_url]
        if urls:
            url = urls[0]
            # 简单的URL解析推断模块
            if '/login' in url or '/signin' in url:
                return "登录模块"
            elif '/register' in url or '/signup' in url:
                return "注册模块"
            elif '/user' in url or '/profile' in url:
                return "用户模块"
            elif '/order' in url:
                return "订单模块"
            elif '/product' in url:
                return "产品模块"
            elif '/admin' in url:
                return "管理模块"
        
        return "主要功能模块"
    
    def _infer_category(self, actions: List[ActionRecord]) -> str:
        """推断测试类别"""
        action_types = [action.action_type for action in actions]
        
        if "fill" in action_types:
            return "功能测试-表单操作"
        elif "click" in action_types:
            return "功能测试-界面交互"
        else:
            return "功能测试"
    
    def _generate_preconditions(self, actions: List[ActionRecord]) -> List[str]:
        """生成前置条件"""
        preconditions = []
        
        if actions:
            first_url = actions[0].page_url
            if first_url:
                preconditions.append(f"浏览器已打开并可访问：{first_url}")
            
            # 检查是否需要登录
            urls = [action.page_url for action in actions]
            if any('/login' in url or '/signin' in url for url in urls):
                preconditions.append("用户已具备登录权限")
        
        if not preconditions:
            preconditions.append("系统正常运行，浏览器环境正常")
        
        return preconditions
    
    def generate_batch_test_cases(self, sessions: List[TestSession]) -> List[TestCase]:
        """批量生成测试用例"""
        test_cases = []
        
        for session in sessions:
            try:
                test_case = self.generate_test_case(session)
                test_cases.append(test_case)
            except Exception as e:
                logger.error(f"批量生成测试用例失败，会话ID: {session.id}, 错误: {e}")
                continue
        
        logger.info(f"批量生成完成，成功生成 {len(test_cases)} 个测试用例")
        return test_cases


# 全局AI生成器实例
ai_generator = AITestCaseGenerator() 