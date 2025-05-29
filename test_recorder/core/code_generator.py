#!/usr/bin/env python3
"""Playwright代码生成器 - 将操作序列转换为标准的Playwright测试代码"""

import re
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

from core.models import ActionRecord
from core.playwright_analyzer import playwright_analyzer


class PlaywrightCodeGenerator:
    """Playwright代码生成器"""
    
    def __init__(self):
        self.current_url = ""
        self.action_sequence = []
    
    def generate_test_code(self, actions: List[ActionRecord], test_name: str = "test") -> str:
        """生成完整的Playwright测试代码"""
        try:
            # 重置状态
            self.current_url = ""
            self.action_sequence = []
            
            # 分析所有操作
            for action in actions:
                self._process_action(action)
            
            # 生成代码
            code = self._generate_full_code(test_name)
            
            return code
            
        except Exception as e:
            logger.error(f"生成测试代码失败: {e}")
            return self._generate_error_code(str(e))
    
    def _process_action(self, action: ActionRecord):
        """处理单个操作记录"""
        try:
            action_type = action.action_type
            
            if action_type == "goto":
                self._process_goto_action(action)
            elif action_type in ["click", "input", "keypress", "select"]:
                self._process_interaction_action(action)
            elif action_type == "load":
                # 页面加载事件通常不需要生成代码
                pass
            else:
                logger.warning(f"未知的操作类型: {action_type}")
                
        except Exception as e:
            logger.error(f"处理操作失败: {e}")
    
    def _process_goto_action(self, action: ActionRecord):
        """处理导航操作"""
        url = action.page_url
        if url and url != "about:blank" and url != self.current_url:
            self.action_sequence.append({
                'type': 'goto',
                'url': url,
                'timestamp': action.timestamp,
                'description': f"导航到: {url}"
            })
            self.current_url = url
    
    def _process_interaction_action(self, action: ActionRecord):
        """处理交互操作"""
        try:
            element_info = action.element_info
            if not element_info:
                return
            
            # 使用Playwright分析器分析元素
            analyzed = playwright_analyzer.analyze_element(element_info)
            
            # 获取最佳选择器
            best_selector = playwright_analyzer.get_best_selector(analyzed['selectors'])
            action_method = analyzed['action_method']
            
            # 根据操作类型调整方法
            if action.action_type == "input":
                action_method = "fill"
                # 从additional_data中获取输入值
                try:
                    import json
                    additional_data = json.loads(action.additional_data) if action.additional_data else {}
                    input_value = additional_data.get('value', '')
                except:
                    input_value = ""
            elif action.action_type == "select":
                action_method = "select_option"
                try:
                    import json
                    additional_data = json.loads(action.additional_data) if action.additional_data else {}
                    select_value = additional_data.get('selectedText', '')
                except:
                    select_value = ""
            else:
                input_value = None
                select_value = None
            
            # 生成代码行
            selector_code = playwright_analyzer.format_selector_code(best_selector)
            
            if action_method == "fill" and input_value is not None:
                code_line = f'await page.{selector_code}.{action_method}("{input_value}")'
            elif action_method == "select_option" and select_value:
                code_line = f'await page.{selector_code}.{action_method}("{select_value}")'
            else:
                code_line = f'await page.{selector_code}.{action_method}()'
            
            self.action_sequence.append({
                'type': 'interaction',
                'action_type': action.action_type,
                'code_line': code_line,
                'timestamp': action.timestamp,
                'description': action.description,
                'selector': best_selector,
                'element_info': analyzed
            })
            
        except Exception as e:
            logger.error(f"处理交互操作失败: {e}")
    
    def _generate_full_code(self, test_name: str) -> str:
        """生成完整的测试代码"""
        try:
            # 代码模板
            imports = """import asyncio
import re
from playwright.async_api import Playwright, async_playwright, expect"""
            
            # 生成run函数
            run_function = self._generate_run_function()
            
            # 生成main函数
            main_function = """async def main() -> None:
    async with async_playwright() as playwright:
        await run(playwright)"""
            
            # 生成执行代码
            execution = """asyncio.run(main())"""
            
            # 组合完整代码
            full_code = f"""{imports}


{run_function}


{main_function}


{execution}"""
            
            return full_code
            
        except Exception as e:
            logger.error(f"生成完整代码失败: {e}")
            return self._generate_error_code(str(e))
    
    def _generate_run_function(self) -> str:
        """生成run函数体"""
        try:
            lines = []
            lines.append("async def run(playwright: Playwright) -> None:")
            lines.append("    browser = await playwright.chromium.launch(headless=False)")
            lines.append("    context = await browser.new_context()")
            lines.append("    page = await context.new_page()")
            
            # 添加操作代码
            for action in self.action_sequence:
                if action['type'] == 'goto':
                    lines.append(f'    await page.goto("{action["url"]}")')
                elif action['type'] == 'interaction':
                    lines.append(f"    {action['code_line']}")
            
            # 添加清理代码
            lines.append("")
            lines.append("    # ---------------------")
            lines.append("    await context.close()")
            lines.append("    await browser.close()")
            
            return '\n'.join(lines)
            
        except Exception as e:
            logger.error(f"生成run函数失败: {e}")
            return "async def run(playwright: Playwright) -> None:\n    pass"
    
    def _generate_error_code(self, error_msg: str) -> str:
        """生成错误提示代码"""
        return f"""# 代码生成失败: {error_msg}
import asyncio
from playwright.async_api import async_playwright

async def main():
    print("代码生成过程中出现错误，请检查录制数据")
    print("错误信息: {error_msg}")

asyncio.run(main())"""
    
    def generate_action_code(self, action: ActionRecord) -> str:
        """为单个操作生成代码（用于实时显示）"""
        try:
            if action.action_type == "goto":
                return f'await page.goto("{action.page_url}")'
            
            elif action.action_type in ["click", "input", "keypress", "select"]:
                element_info = action.element_info
                if not element_info:
                    return "# 无法获取元素信息"
                
                # 使用Playwright分析器分析元素
                analyzed = playwright_analyzer.analyze_element(element_info)
                best_selector = playwright_analyzer.get_best_selector(analyzed['selectors'])
                selector_code = playwright_analyzer.format_selector_code(best_selector)
                
                if action.action_type == "input":
                    try:
                        import json
                        additional_data = json.loads(action.additional_data) if action.additional_data else {}
                        input_value = additional_data.get('value', '')
                        return f'await page.{selector_code}.fill("{input_value}")'
                    except:
                        return f'await page.{selector_code}.fill("")'
                
                elif action.action_type == "select":
                    try:
                        import json
                        additional_data = json.loads(action.additional_data) if action.additional_data else {}
                        select_value = additional_data.get('selectedText', '')
                        
                        # 生成更平滑的选择代码
                        code = [
                            f'# 定位并等待下拉框元素',
                            f'select_element = page.locator({best_selector})',
                            f'await select_element.wait_for(state="visible")',
                            f'# 直接选择选项，不需要额外的点击',
                            f'await select_element.select_option(label="{select_value}")',
                            f'# 验证选择是否成功',
                            f'selected_text = await select_element.evaluate("el => el.options[el.selectedIndex].text")',
                            f'if selected_text != "{select_value}":',
                            f'    raise Exception(f"选择验证失败：期望 {select_value}，实际 {{selected_text}}")'
                        ]
                        return '\n    '.join(code)
                    except:
                        return f'await page.{selector_code}.click()'
                
                else:  # click, keypress
                    try:
                        import json
                        additional_data = json.loads(action.additional_data) if action.additional_data else {}
                        # 如果是下拉框的点击，只等待元素可见
                        if additional_data.get('isSelect'):
                            code = [
                                f'# 等待下拉框元素可见',
                                f'await page.{selector_code}.wait_for(state="visible")'
                            ]
                            return '\n    '.join(code)
                        return f'await page.{selector_code}.click()'
                    except:
                        return f'await page.{selector_code}.click()'
            
            else:
                return f"# 操作类型: {action.action_type}"
                
        except Exception as e:
            logger.error(f"生成操作代码失败: {e}")
            return f"# 生成代码失败: {str(e)}"
    
    def optimize_code(self, code: str) -> str:
        """优化生成的代码"""
        try:
            lines = code.split('\n')
            optimized_lines = []
            
            prev_goto = None
            for line in lines:
                # 去除重复的goto操作
                if 'await page.goto(' in line:
                    if line != prev_goto:
                        optimized_lines.append(line)
                        prev_goto = line
                else:
                    optimized_lines.append(line)
            
            return '\n'.join(optimized_lines)
            
        except Exception as e:
            logger.error(f"代码优化失败: {e}")
            return code


# 全局代码生成器实例
code_generator = PlaywrightCodeGenerator() 