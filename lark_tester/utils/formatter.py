"""
数据格式化工具模块

提供测试数据的格式化和转换功能
"""

import json
import re
from typing import Dict, Any, Optional, Union


def format_test_result(
    status_code: int,
    response_body: str,
    response_time: float,
    is_passed: bool,
    error_message: str = ""
) -> Dict[str, str]:
    """
    格式化测试结果为表格字段格式
    
    Args:
        status_code: 响应状态码
        response_body: 响应体内容
        response_time: 响应时间(秒)
        is_passed: 是否通过测试
        error_message: 错误信息
        
    Returns:
        格式化后的测试结果字典
    """
    # 使用表格中实际存在的字段名
    result = {
        '响应状态码': str(status_code),  # 使用表格中的字段名
        '响应体': format_response_body(response_body),
        # '响应时间': str(int(response_time * 1000)),  # 暂时跳过，避免数字字段错误
        '是否通过': 'PASS' if is_passed else 'FAIL'
    }
    
    # 如果有错误信息，可以放在响应体中或在是否通过字段中体现
    if error_message and not is_passed:
        result['响应体'] = f"错误: {error_message}\n\n原响应: {result['响应体']}"
    
    return result


def format_response_body(response_body: str, max_length: int = 2000) -> str:
    """
    格式化响应体内容，确保适合表格显示
    
    Args:
        response_body: 响应体内容
        max_length: 最大长度限制
        
    Returns:
        格式化后的响应体
    """
    if not response_body:
        return ""
    
    # 尝试格式化JSON
    try:
        parsed = json.loads(response_body)
        formatted = json.dumps(parsed, ensure_ascii=False, indent=2)
        
        # 如果太长，截断并添加提示
        if len(formatted) > max_length:
            formatted = formatted[:max_length] + "\n...(内容被截断)"
        
        return formatted
    except json.JSONDecodeError:
        # 不是JSON，直接处理字符串
        if len(response_body) > max_length:
            return response_body[:max_length] + "...(内容被截断)"
        return response_body


def parse_headers(headers_str: str) -> Dict[str, str]:
    """
    解析请求头字符串为字典
    
    Args:
        headers_str: 请求头字符串（JSON格式或键值对格式）
        
    Returns:
        请求头字典
    """
    if not headers_str:
        return {}
    
    try:
        # 尝试解析JSON格式
        return json.loads(headers_str)
    except json.JSONDecodeError:
        # 尝试修复常见的JSON格式问题
        try:
            import re
            # 将单引号替换为双引号
            fixed_headers = re.sub(r"'", '"', headers_str)
            return json.loads(fixed_headers)
        except json.JSONDecodeError:
            # 尝试解析键值对格式 (key: value)
            headers = {}
            lines = headers_str.strip().split('\n')
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
            return headers


def parse_request_body(body_str: str) -> Union[Dict[str, Any], str]:
    """
    解析请求体字符串
    
    Args:
        body_str: 请求体字符串
        
    Returns:
        解析后的请求体（字典或字符串）
    """
    if not body_str:
        return ""
    
    try:
        # 尝试解析JSON
        return json.loads(body_str)
    except json.JSONDecodeError:
        # 尝试修复常见的JSON格式问题
        try:
            import re
            # 1. 去除首尾空白
            fixed_body = body_str.strip()
            # 2. 将单引号替换为双引号
            fixed_body = re.sub(r"'", '"', fixed_body)
            # 3. 去除结束前的多余逗号
            fixed_body = re.sub(r',\s*}', '}', fixed_body)
            fixed_body = re.sub(r',\s*]', ']', fixed_body)
            return json.loads(fixed_body)
        except json.JSONDecodeError:
            # 如果仍然解析失败，返回原始字符串
            return body_str


def format_url(base_url: str, path: str) -> str:
    """
    格式化完整的URL
    
    Args:
        base_url: 基础URL
        path: 接口路径
        
    Returns:
        完整的URL
    """
    if path.startswith('http'):
        return path
    
    # 确保base_url以/结尾，path不以/开头
    base_url = base_url.rstrip('/')
    path = path.lstrip('/')
    
    return f"{base_url}/{path}"


def format_duration(seconds: float) -> str:
    """
    格式化时间长度为可读格式
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化的时间字符串
    """
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m{remaining_seconds:.1f}s"


def extract_variables_from_text(text: str) -> list:
    """
    从文本中提取变量（${variable}格式）
    
    Args:
        text: 包含变量的文本
        
    Returns:
        变量名列表
    """
    if not text:
        return []
    
    pattern = r'\$\{([^}]+)\}'
    matches = re.findall(pattern, text)
    return list(set(matches))  # 去重


def replace_variables(text: str, variables: Dict[str, str]) -> str:
    """
    替换文本中的变量
    
    Args:
        text: 包含变量的文本
        variables: 变量字典
        
    Returns:
        替换后的文本
    """
    if not text or not variables:
        return text
    
    for var_name, var_value in variables.items():
        pattern = f"${{{var_name}}}"
        text = text.replace(pattern, str(var_value))
    
    return text


def sanitize_field_name(name: str) -> str:
    """
    清理字段名，确保符合命名规范
    
    Args:
        name: 原始字段名
        
    Returns:
        清理后的字段名
    """
    if not name:
        return ""
    
    # 移除特殊字符，保留中文、英文、数字和下划线
    sanitized = re.sub(r'[^\w\u4e00-\u9fff]', '_', name)
    
    # 移除连续的下划线
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # 移除开头和结尾的下划线
    sanitized = sanitized.strip('_')
    
    return sanitized or "unknown_field"