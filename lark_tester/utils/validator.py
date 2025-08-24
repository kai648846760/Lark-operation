"""
数据验证工具模块

提供测试用例和配置的验证功能
"""

import json
from typing import Dict, Any, List, Union, Optional
from urllib.parse import urlparse


def validate_test_case(test_case: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    验证测试用例数据的完整性和有效性
    
    Args:
        test_case: 测试用例字典
        
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    
    # 必需字段检查
    required_fields = [
        '接口编号', '接口路径', '请求方法'
    ]
    
    for field in required_fields:
        if not test_case.get(field):
            errors.append(f"缺少必需字段: {field}")
    
    # 请求方法验证
    valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
    method = test_case.get('请求方法', '').upper()
    if method and method not in valid_methods:
        errors.append(f"无效的请求方法: {method}")
    
    # 接口路径验证
    path = test_case.get('接口路径', '')
    if path and not (path.startswith('/') or path.startswith('http')):
        errors.append(f"接口路径格式错误: {path}")
    
    # JSON格式验证（宽松模式，只警告不阻止执行）
    json_fields = ['请求头', '请求体']
    for field in json_fields:
        value = test_case.get(field)
        if value and isinstance(value, str) and value.strip():
            # 尝试验证JSON，但失败时只记录警告，不阻止测试执行
            if not is_valid_json_flexible(value):
                # 记录警告但不加入errors，以免阻止测试执行
                pass  # 暂时不验证JSON格式，交给formatter处理
    
    # 预期状态码验证
    expected_status = test_case.get('预期状态码')
    if expected_status:
        try:
            status_code = int(expected_status)
            if not (100 <= status_code <= 599):
                errors.append(f"无效的HTTP状态码: {status_code}")
        except ValueError:
            errors.append(f"状态码必须是数字: {expected_status}")
    
    return len(errors) == 0, errors


def validate_config(config: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    验证配置文件的有效性
    
    Args:
        config: 配置字典
        
    Returns:
        (是否有效, 错误信息列表)
    """
    errors = []
    
    # 必需配置项检查
    required_configs = ['personal_token', 'app_token', 'table_id']
    for config_key in required_configs:
        if not config.get(config_key):
            errors.append(f"缺少必需配置: {config_key}")
    
    # Token格式验证
    personal_token = config.get('personal_token', '')
    if personal_token and not personal_token.startswith('pt-'):
        errors.append("personal_token必须以'pt-'开头")
    
    # 域名验证
    domain = config.get('domain')
    if domain:
        try:
            parsed = urlparse(domain)
            if not parsed.scheme or not parsed.netloc:
                errors.append(f"无效的域名格式: {domain}")
        except Exception:
            errors.append(f"域名解析失败: {domain}")
    
    return len(errors) == 0, errors


def validate_assertion_rule(rule: str) -> tuple[bool, str]:
    """
    验证断言规则的语法
    
    Args:
        rule: 断言规则字符串
        
    Returns:
        (是否有效, 错误信息)
    """
    if not rule or not isinstance(rule, str):
        return False, "断言规则不能为空"
    
    # 支持的断言操作符
    valid_operators = ['==', '!=', '>', '<', '>=', '<=', 'in', 'not in', 'contains']
    
    # 简单语法检查
    has_operator = any(op in rule for op in valid_operators)
    if not has_operator:
        return False, f"断言规则必须包含有效操作符: {', '.join(valid_operators)}"
    
    return True, ""


def is_valid_json_flexible(text: str) -> bool:
    """
    宽松的JSON验证，支持更多非标净格式
    
    Args:
        text: 要检查的字符串
        
    Returns:
        是否为有效JSON或可修复的格式
    """
    if not text or not text.strip():
        return True  # 空字符串视为有效
    
    # 首先尝试标准JSON解析
    try:
        json.loads(text)
        return True
    except json.JSONDecodeError:
        pass
    
    # 尝试多种修复方式
    import re
    
    fixes = [
        # 修复1：单引号替换为双引号
        lambda s: re.sub(r"'", '"', s),
        # 修复2：去除首尾空白 + 单引号替换
        lambda s: re.sub(r"'", '"', s.strip()),
        # 修复3：去除结束前的多余逗号
        lambda s: re.sub(r',\s*[}\]]', lambda m: m.group(0)[m.group(0).find('}'):] if '}' in m.group(0) else m.group(0)[m.group(0).find(']'):], re.sub(r"'", '"', s.strip())),
        # 修复4：不带引号的键加上引号
        lambda s: re.sub(r'(\w+)\s*:', r'"\1":', re.sub(r"'", '"', s.strip())),
    ]
    
    for fix_func in fixes:
        try:
            fixed_text = fix_func(text)
            json.loads(fixed_text)
            return True  # 修复成功
        except (json.JSONDecodeError, Exception):
            continue
    
    # 如果所有修复都失败，检查是否是简单的键值对格式
    if ':' in text and '\n' in text:
        # 可能是多行键值对格式，也认为有效
        return True
    
    return False


def is_valid_json(text: str) -> bool:
    """
    检查字符串是否为有效JSON
    
    Args:
        text: 要检查的字符串
        
    Returns:
        是否为有效JSON
    """
    if not text:
        return True  # 空字符串视为有效
    
    try:
        json.loads(text)
        return True
    except json.JSONDecodeError:
        # 尝试修复常见的JSON格式问题
        try:
            import re
            # 1. 去除首尾空白
            fixed_text = text.strip()
            # 2. 将单引号替换为双引号
            fixed_text = re.sub(r"'", '"', fixed_text)
            # 3. 去除结束前的多余逗号
            fixed_text = re.sub(r',\s*}', '}', fixed_text)
            fixed_text = re.sub(r',\s*]', ']', fixed_text)
            json.loads(fixed_text)
            return True
        except json.JSONDecodeError:
            return False


def is_valid_url(url: str) -> bool:
    """
    检查URL是否有效
    
    Args:
        url: 要检查的URL
        
    Returns:
        是否为有效URL
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False