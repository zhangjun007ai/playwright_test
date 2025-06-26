#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pytest 自动化测试框架 Web UI 后端服务
基于 Flask 提供 RESTful API 接口
"""

import os
import sys
import json
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import yaml

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.read_files_tools.get_yaml_data_analysis import GetTestCase
from utils.read_files_tools.case_automatic_control import TestCaseAutomaticGeneration
from common.setting import ensure_path_sep
from utils import config

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局变量存储测试执行状态
test_execution_status = {
    'running': False,
    'logs': [],
    'results': None
}

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'message': 'Pytest Auto API Web UI Backend is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取项目配置信息"""
    try:
        config_data = {
            'project_name': getattr(config, 'project_name', ''),
            'env': getattr(config, 'env', ''),
            'tester_name': getattr(config, 'tester_name', ''),
            'host': getattr(config, 'host', ''),
            'notification_type': getattr(config, 'notification_type', 0),
            'mysql_switch': False
        }

        # 安全地获取 mysql_db 配置
        if hasattr(config, 'mysql_db') and isinstance(config.mysql_db, dict):
            config_data['mysql_switch'] = config.mysql_db.get('switch', False)
        elif hasattr(config, 'mysql_db') and hasattr(config.mysql_db, 'switch'):
            config_data['mysql_switch'] = config.mysql_db.switch
        return jsonify({
            'code': 200,
            'data': config_data,
            'message': '配置获取成功'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'配置获取失败: {str(e)}'
        }), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    """更新项目配置"""
    try:
        data = request.get_json()
        config_file_path = project_root / 'common' / 'config.yaml'
        
        # 读取现有配置
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # 更新配置
        if 'project_name' in data:
            config_data['project_name'] = data['project_name']
        if 'env' in data:
            config_data['env'] = data['env']
        if 'tester_name' in data:
            config_data['tester_name'] = data['tester_name']
        if 'host' in data:
            config_data['host'] = data['host']
        if 'notification_type' in data:
            config_data['notification_type'] = data['notification_type']
        
        # 写回配置文件
        with open(config_file_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_data, f, default_flow_style=False, allow_unicode=True)
        
        return jsonify({
            'code': 200,
            'message': '配置更新成功'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'配置更新失败: {str(e)}'
        }), 500

@app.route('/api/test-cases', methods=['GET'])
def get_test_cases():
    """获取所有测试用例"""
    try:
        test_cases = []
        data_dir = project_root / 'data'
        
        # 遍历所有 YAML 文件
        for yaml_file in data_dir.rglob('*.yaml'):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                
                # 提取用例信息
                case_common = content.get('case_common', {})
                module_name = yaml_file.parent.name
                file_name = yaml_file.stem
                
                # 提取具体用例
                cases = []
                for key, value in content.items():
                    if key != 'case_common' and isinstance(value, dict):
                        cases.append({
                            'case_id': key,
                            'detail': value.get('detail', ''),
                            'method': value.get('method', ''),
                            'url': value.get('url', ''),
                            'is_run': value.get('is_run', True)
                        })
                
                test_cases.append({
                    'module': module_name,
                    'file': file_name,
                    'file_path': str(yaml_file.relative_to(project_root)),
                    'epic': case_common.get('allureEpic', ''),
                    'feature': case_common.get('allureFeature', ''),
                    'story': case_common.get('allureStory', ''),
                    'cases': cases
                })
            except Exception as e:
                print(f"解析文件 {yaml_file} 失败: {e}")
                continue
        
        return jsonify({
            'code': 200,
            'data': test_cases,
            'message': '测试用例获取成功'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'测试用例获取失败: {str(e)}'
        }), 500

@app.route('/api/test-cases/<path:file_path>', methods=['GET'])
def get_test_case_content(file_path):
    """获取指定测试用例文件内容"""
    try:
        full_path = project_root / file_path
        if not full_path.exists():
            return jsonify({
                'code': 404,
                'message': '文件不存在'
            }), 404
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'code': 200,
            'data': {
                'content': content,
                'file_path': file_path
            },
            'message': '文件内容获取成功'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'文件内容获取失败: {str(e)}'
        }), 500

@app.route('/api/test-cases/<path:file_path>', methods=['POST'])
def save_test_case_content(file_path):
    """保存测试用例文件内容"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        full_path = project_root / file_path
        
        # 确保目录存在
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 验证 YAML 格式
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            return jsonify({
                'code': 400,
                'message': f'YAML 格式错误: {str(e)}'
            }), 400
        
        # 保存文件
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            'code': 200,
            'message': '文件保存成功'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'文件保存失败: {str(e)}'
        }), 500

@app.route('/api/generate-code', methods=['POST'])
def generate_test_code():
    """生成测试代码"""
    try:
        # 调用代码生成器
        generator = TestCaseAutomaticGeneration()
        generator.get_case_automatic()
        
        return jsonify({
            'code': 200,
            'message': '测试代码生成成功'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'测试代码生成失败: {str(e)}'
        }), 500

def run_tests_async():
    """异步执行测试"""
    global test_execution_status
    
    try:
        test_execution_status['running'] = True
        test_execution_status['logs'] = []
        
        # 切换到项目根目录
        os.chdir(project_root)
        
        # 执行测试命令
        process = subprocess.Popen(
            ['python', 'run.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # 实时读取输出
        for line in process.stdout:
            test_execution_status['logs'].append({
                'timestamp': datetime.now().isoformat(),
                'message': line.strip()
            })
        
        process.wait()
        
        # 读取测试结果
        try:
            # 这里可以解析 allure 报告或日志文件获取结果
            test_execution_status['results'] = {
                'status': 'completed',
                'return_code': process.returncode
            }
        except:
            test_execution_status['results'] = {
                'status': 'completed',
                'return_code': process.returncode
            }
        
    except Exception as e:
        test_execution_status['logs'].append({
            'timestamp': datetime.now().isoformat(),
            'message': f'执行错误: {str(e)}'
        })
        test_execution_status['results'] = {
            'status': 'error',
            'error': str(e)
        }
    finally:
        test_execution_status['running'] = False

@app.route('/api/execute/start', methods=['POST'])
def start_test_execution():
    """开始执行测试"""
    global test_execution_status
    
    if test_execution_status['running']:
        return jsonify({
            'code': 400,
            'message': '测试正在执行中，请等待完成'
        }), 400
    
    # 在新线程中执行测试
    thread = threading.Thread(target=run_tests_async)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'code': 200,
        'message': '测试执行已开始'
    })

@app.route('/api/execute/status', methods=['GET'])
def get_execution_status():
    """获取测试执行状态"""
    return jsonify({
        'code': 200,
        'data': test_execution_status
    })

@app.route('/api/execute/logs', methods=['GET'])
def get_execution_logs():
    """获取执行日志"""
    limit = request.args.get('limit', 100, type=int)
    logs = test_execution_status['logs'][-limit:] if test_execution_status['logs'] else []
    
    return jsonify({
        'code': 200,
        'data': logs
    })

if __name__ == '__main__':
    print("启动 Pytest Auto API Web UI 后端服务...")
    print(f"项目根目录: {project_root}")
    app.run(host='0.0.0.0', port=5000, debug=True)
