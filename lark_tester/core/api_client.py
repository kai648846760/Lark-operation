"""
HTTP API客户端模块

提供HTTP请求发送、响应处理、超时管理和重试机制
"""

import time
import requests
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urljoin

from ..utils.logger import get_logger
from ..utils.formatter import parse_headers, parse_request_body, format_url

logger = get_logger(__name__)


class APIClient:
    """HTTP API客户端"""
    
    def __init__(
        self, 
        base_url: str = "",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        初始化API客户端
        
        Args:
            base_url: 基础URL
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
    
    def send_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Any = None,
        params: Optional[Dict[str, str]] = None
    ) -> Tuple[int, str, float, Optional[str]]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            headers: 请求头
            data: 请求体数据
            params: URL参数
            
        Returns:
            (状态码, 响应体, 响应时间, 错误信息)
        """
        # 格式化URL
        if self.base_url and not url.startswith('http'):
            url = format_url(self.base_url, url)
        
        # 设置默认请求头
        if headers is None:
            headers = {}
        
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'lark-api-tester/1.0.0'
        
        # 执行请求（带重试机制）
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                
                logger.info(f"发送{method}请求到: {url}")
                logger.debug(f"请求头: {headers}")
                logger.debug(f"请求体: {data}")
                
                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=data if isinstance(data, dict) else None,
                    data=data if not isinstance(data, dict) else None,
                    params=params,
                    timeout=self.timeout
                )
                
                response_time = time.time() - start_time
                
                logger.info(f"响应状态码: {response.status_code}, 响应时间: {response_time:.3f}s")
                
                return (
                    response.status_code,
                    response.text,
                    response_time,
                    None
                )
                
            except requests.exceptions.Timeout:
                error_msg = f"请求超时 (attempt {attempt + 1}/{self.max_retries + 1})"
                logger.warning(error_msg)
                
                if attempt == self.max_retries:
                    return 0, "", 0.0, "请求超时"
                
                time.sleep(self.retry_delay * (attempt + 1))
                
            except requests.exceptions.ConnectionError:
                error_msg = f"连接错误 (attempt {attempt + 1}/{self.max_retries + 1})"
                logger.warning(error_msg)
                
                if attempt == self.max_retries:
                    return 0, "", 0.0, "连接错误"
                
                time.sleep(self.retry_delay * (attempt + 1))
                
            except Exception as e:
                error_msg = f"请求异常: {str(e)}"
                logger.error(error_msg)
                return 0, "", 0.0, error_msg
    
    def execute_test_case(self, test_case: Dict[str, Any]) -> Tuple[int, str, float, Optional[str]]:
        """
        执行单个测试用例
        
        Args:
            test_case: 测试用例数据
            
        Returns:
            (状态码, 响应体, 响应时间, 错误信息)
        """
        try:
            # 提取测试用例信息
            method = test_case.get('请求方法', 'GET').upper()
            path = test_case.get('接口路径', '')
            headers_str = test_case.get('请求头', '')
            body_str = test_case.get('请求体', '')
            
            # 解析请求头和请求体
            headers = parse_headers(headers_str)
            body = parse_request_body(body_str)
            
            # 发送请求
            return self.send_request(
                method=method,
                url=path,
                headers=headers,
                data=body
            )
            
        except Exception as e:
            error_msg = f"执行测试用例失败: {str(e)}"
            logger.error(error_msg)
            return 0, "", 0.0, error_msg
    
    def close(self):
        """关闭会话"""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class AssertionValidator:
    """断言验证器"""
    
    @staticmethod
    def validate_response(
        response_status: int,
        response_body: str,
        expected_status: Optional[str] = None,
        assertion_rules: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        验证响应结果
        
        Args:
            response_status: 实际状态码
            response_body: 实际响应体
            expected_status: 预期状态码
            assertion_rules: 断言规则
            
        Returns:
            (是否通过, 错误信息)
        """
        try:
            # 验证状态码
            if expected_status:
                expected_code = int(expected_status)
                if response_status != expected_code:
                    return False, f"状态码不匹配: 期望{expected_code}, 实际{response_status}"
            
            # 验证断言规则
            if assertion_rules:
                is_valid, error = AssertionValidator._execute_assertion(
                    response_body, assertion_rules
                )
                if not is_valid:
                    return False, f"断言失败: {error}"
            
            return True, ""
            
        except Exception as e:
            return False, f"验证异常: {str(e)}"
    
    @staticmethod
    def _execute_assertion(response_body: str, assertion_rule: str) -> Tuple[bool, str]:
        """
        执行断言规则
        
        Args:
            response_body: 响应体
            assertion_rule: 断言规则
            
        Returns:
            (是否通过, 错误信息)
        """
        try:
            # 简单的断言规则解析和执行
            # 支持格式: status_code == 200, body contains "success"
            
            if 'contains' in assertion_rule:
                # 包含检查
                parts = assertion_rule.split('contains')
                if len(parts) == 2:
                    expected_text = parts[1].strip().strip('"\'')
                    if expected_text not in response_body:
                        return False, f"响应体不包含: {expected_text}"
            
            elif '==' in assertion_rule:
                # 等于检查
                parts = assertion_rule.split('==')
                if len(parts) == 2:
                    field = parts[0].strip()
                    expected = parts[1].strip().strip('"\'')
                    
                    if field == 'status_code':
                        # 状态码已在上层验证
                        pass
                    else:
                        # 其他字段检查（简化版）
                        if expected not in response_body:
                            return False, f"字段{field}值不匹配"
            
            return True, ""
            
        except Exception as e:
            return False, f"断言执行异常: {str(e)}"