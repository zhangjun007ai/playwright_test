#!/usr/bin/env python3
"""Playwright元素分析器 - 将DOM元素信息转换为Playwright语义化选择器"""

import re
from typing import Dict, Optional, List, Tuple
from loguru import logger


class PlaywrightElementAnalyzer:
    """Playwright元素分析器"""
    
    # 角色映射表
    ROLE_MAPPING = {
        'BUTTON': 'button',
        'A': 'link',
        'INPUT': {
            'submit': 'button',
            'button': 'button',
            'checkbox': 'checkbox',
            'radio': 'radio',
            'text': 'textbox',
            'email': 'textbox',
            'password': 'textbox',
            'search': 'searchbox',
            'tel': 'textbox',
            'url': 'textbox',
            'number': 'spinbutton'
        },
        'TEXTAREA': 'textbox',
        'SELECT': 'combobox',
        'OPTION': 'option',
        'IMG': 'img',
        'H1': 'heading',
        'H2': 'heading',
        'H3': 'heading',
        'H4': 'heading',
        'H5': 'heading',
        'H6': 'heading',
        'NAV': 'navigation',
        'MAIN': 'main',
        'ARTICLE': 'article',
        'SECTION': 'region',
        'ASIDE': 'complementary',
        'HEADER': 'banner',
        'FOOTER': 'contentinfo',
        'TABLE': 'table',
        'ROW': 'row',
        'CELL': 'cell',
        'COLUMNHEADER': 'columnheader',
        'ROWHEADER': 'rowheader'
    }
    
    def __init__(self):
        pass
    
    def analyze_element(self, element_info: Dict) -> Dict:
        """分析元素并生成Playwright选择器信息"""
        try:
            tag_name = element_info.get('tagName', '').upper()
            element_type = element_info.get('type', '').lower()
            text = element_info.get('text', '').strip()
            element_id = element_info.get('id', '')
            class_name = element_info.get('className', '')
            href = element_info.get('href', '')
            placeholder = element_info.get('placeholder', '')
            
            # 分析元素角色
            role = self._get_element_role(tag_name, element_type, class_name)
            
            # 生成选择器策略
            selectors = self._generate_selectors(
                tag_name, element_type, text, element_id, 
                class_name, href, placeholder, role
            )
            
            # 生成操作方法
            action_method = self._get_action_method(tag_name, element_type, role)
            
            return {
                'tag_name': tag_name,
                'type': element_type,
                'role': role,
                'text': text,
                'selectors': selectors,
                'action_method': action_method,
                'element_id': element_id,
                'class_name': class_name,
                'href': href,
                'placeholder': placeholder
            }
            
        except Exception as e:
            logger.error(f"分析元素失败: {e}")
            return {
                'tag_name': element_info.get('tagName', ''),
                'selectors': [{'method': 'locator', 'args': [element_info.get('selector', 'unknown')]}],
                'action_method': 'click'
            }
    
    def _get_element_role(self, tag_name: str, element_type: str, class_name: str) -> Optional[str]:
        """获取元素的语义角色"""
        try:
            # 首先检查标签名映射
            if tag_name in self.ROLE_MAPPING:
                role_info = self.ROLE_MAPPING[tag_name]
                if isinstance(role_info, dict):
                    # 对于INPUT等标签，需要根据type属性确定角色
                    return role_info.get(element_type, 'textbox')
                else:
                    return role_info
            
            # 检查类名中的角色提示
            if class_name:
                class_lower = class_name.lower()
                if 'btn' in class_lower or 'button' in class_lower:
                    return 'button'
                elif 'link' in class_lower:
                    return 'link'
                elif 'nav' in class_lower or 'menu' in class_lower:
                    return 'navigation'
                elif 'search' in class_lower:
                    return 'searchbox'
                elif 'input' in class_lower or 'form' in class_lower:
                    return 'textbox'
            
            return None
            
        except Exception:
            return None
    
    def _generate_selectors(self, tag_name: str, element_type: str, text: str, 
                          element_id: str, class_name: str, href: str, 
                          placeholder: str, role: Optional[str]) -> List[Dict]:
        """生成多种Playwright选择器策略，按优先级排序"""
        selectors = []
        
        try:
            # 1. get_by_role - 最优先
            if role and text:
                clean_text = self._clean_text(text)
                if clean_text:
                    selectors.append({
                        'method': 'get_by_role',
                        'args': [role],
                        'kwargs': {'name': clean_text},
                        'priority': 1
                    })
            
            # 2. get_by_text - 对于有文本的元素
            if text and len(text.strip()) > 0 and len(text.strip()) < 50:
                clean_text = self._clean_text(text)
                if clean_text:
                    selectors.append({
                        'method': 'get_by_text',
                        'args': [clean_text],
                        'priority': 2
                    })
            
            # 3. get_by_placeholder - 对于有placeholder的输入框
            if placeholder:
                selectors.append({
                    'method': 'get_by_placeholder',
                    'args': [placeholder],
                    'priority': 3
                })
            
            # 4. get_by_label - 通过关联的label查找
            # 这里可以扩展，分析附近的label元素
            
            # 5. get_by_test_id - 如果有data-testid属性
            # 这里可以扩展检查data-testid属性
            
            # 6. 基于ID的选择器
            if element_id:
                selectors.append({
                    'method': 'locator',
                    'args': [f'#{element_id}'],
                    'priority': 6
                })
            
            # 7. 基于类名的选择器
            if class_name:
                main_class = class_name.split()[0] if class_name else ''
                if main_class:
                    selectors.append({
                        'method': 'locator',
                        'args': [f'.{main_class}'],
                        'priority': 7
                    })
            
            # 8. CSS选择器组合
            css_parts = []
            if tag_name:
                css_parts.append(tag_name.lower())
            if element_type:
                css_parts.append(f'[type="{element_type}"]')
            
            if css_parts:
                css_selector = ''.join(css_parts)
                selectors.append({
                    'method': 'locator',
                    'args': [css_selector],
                    'priority': 8
                })
            
            # 按优先级排序
            selectors.sort(key=lambda x: x.get('priority', 99))
            
            # 如果没有找到合适的选择器，使用基本的标签名
            if not selectors:
                selectors.append({
                    'method': 'locator',
                    'args': [tag_name.lower() if tag_name else 'unknown'],
                    'priority': 99
                })
            
            return selectors
            
        except Exception as e:
            logger.error(f"生成选择器失败: {e}")
            return [{'method': 'locator', 'args': ['unknown'], 'priority': 99}]
    
    def _clean_text(self, text: str) -> str:
        """清理文本内容，使其适合作为选择器参数"""
        if not text:
            return ""
        
        # 移除多余的空白字符
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # 限制长度
        if len(cleaned) > 30:
            cleaned = cleaned[:30].strip()
        
        # 移除特殊字符（可选）
        # cleaned = re.sub(r'[^\w\s\u4e00-\u9fff]', '', cleaned)
        
        return cleaned
    
    def _get_action_method(self, tag_name: str, element_type: str, role: Optional[str]) -> str:
        """根据元素类型确定最适合的操作方法"""
        try:
            # 根据角色确定操作
            if role in ['button', 'link']:
                return 'click'
            elif role in ['textbox', 'searchbox']:
                return 'fill'
            elif role == 'checkbox':
                return 'check'  # 或 'uncheck'
            elif role == 'radio':
                return 'check'
            elif role == 'combobox':
                return 'select_option'
            
            # 根据标签名确定操作
            if tag_name == 'A':
                return 'click'
            elif tag_name == 'BUTTON':
                return 'click'
            elif tag_name == 'INPUT':
                if element_type in ['submit', 'button']:
                    return 'click'
                elif element_type in ['text', 'email', 'password', 'search']:
                    return 'fill'
                elif element_type == 'checkbox':
                    return 'check'
                elif element_type == 'radio':
                    return 'check'
            elif tag_name == 'TEXTAREA':
                return 'fill'
            elif tag_name == 'SELECT':
                return 'select_option'
            
            # 默认操作
            return 'click'
            
        except Exception:
            return 'click'
    
    def get_best_selector(self, selectors: List[Dict]) -> Dict:
        """获取最佳选择器"""
        if not selectors:
            return {'method': 'locator', 'args': ['unknown']}
        
        # 返回优先级最高的选择器
        return selectors[0]
    
    def format_selector_code(self, selector: Dict) -> str:
        """将选择器信息格式化为Playwright代码"""
        try:
            method = selector['method']
            args = selector.get('args', [])
            kwargs = selector.get('kwargs', {})
            
            # 构建参数字符串
            arg_parts = []
            
            # 添加位置参数
            for arg in args:
                if isinstance(arg, str):
                    arg_parts.append(f'"{arg}"')
                else:
                    arg_parts.append(str(arg))
            
            # 添加关键字参数
            for key, value in kwargs.items():
                if isinstance(value, str):
                    arg_parts.append(f'{key}="{value}"')
                else:
                    arg_parts.append(f'{key}={value}')
            
            args_str = ', '.join(arg_parts)
            return f'{method}({args_str})'
            
        except Exception as e:
            logger.error(f"格式化选择器代码失败: {e}")
            return 'locator("unknown")'


# 全局分析器实例
playwright_analyzer = PlaywrightElementAnalyzer() 