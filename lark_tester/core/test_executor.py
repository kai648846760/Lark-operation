"""
测试执行器模块

负责读取测试用例、执行API测试、收集结果并回写到表格
"""

import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .lark_client import LarkClient
from .api_client import APIClient, AssertionValidator
from ..utils.logger import get_logger
from ..utils.formatter import format_test_result
from ..utils.validator import validate_test_case

logger = get_logger(__name__)


class TestExecutor:
    """API测试执行器"""
    
    def __init__(
        self,
        lark_client: LarkClient,
        api_client: Optional[APIClient] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化测试执行器
        
        Args:
            lark_client: Lark客户端实例
            api_client: API客户端实例
            config: 配置字典
        """
        self.lark_client = lark_client
        self.api_client = api_client or APIClient()
        self.config = config or {}
        self.test_results = []
    
    def load_test_cases(self, table_id: str) -> List[Dict[str, Any]]:
        """
        从表格加载测试用例
        
        Args:
            table_id: 表格ID
            
        Returns:
            测试用例列表
        """
        logger.info(f"从表格 {table_id} 加载测试用例...")
        
        try:
            records = self.lark_client.get_all_records(table_id)
            logger.info(f"成功加载 {len(records)} 条记录")
            
            # 过滤和验证测试用例
            valid_cases = []
            for record in records:
                fields = record.get('fields', {})
                
                # 基本字段检查
                if not fields.get('接口路径') or not fields.get('请求方法'):
                    logger.warning(f"跳过无效记录: {record.get('record_id', 'unknown')}")
                    continue
                
                # 验证测试用例
                is_valid, errors = validate_test_case(fields)
                if not is_valid:
                    logger.warning(f"测试用例验证失败: {errors}")
                    continue
                
                # 添加记录ID到字段中
                fields['_record_id'] = record['record_id']
                valid_cases.append(fields)
            
            logger.info(f"有效测试用例: {len(valid_cases)} 条")
            return valid_cases
            
        except Exception as e:
            logger.error(f"加载测试用例失败: {str(e)}")
            return []
    
    def execute_single_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个测试用例
        
        Args:
            test_case: 测试用例数据
            
        Returns:
            测试结果数据
        """
        test_id = test_case.get('接口编号', 'unknown')
        logger.info(f"执行测试用例: {test_id}")
        
        try:
            # 发送API请求
            status_code, response_body, response_time, error = self.api_client.execute_test_case(test_case)
            
            # 如果请求失败，直接返回失败结果
            if error:
                result = format_test_result(
                    status_code=0,
                    response_body="",
                    response_time=0.0,
                    is_passed=False,
                    error_message=error
                )
                result['_record_id'] = test_case.get('_record_id')
                return result
            
            # 验证响应结果
            expected_status = test_case.get('预期状态码')
            assertion_rules = test_case.get('断言规则')
            
            is_passed, validation_error = AssertionValidator.validate_response(
                response_status=status_code,
                response_body=response_body,
                expected_status=expected_status,
                assertion_rules=assertion_rules
            )
            
            # 格式化测试结果
            result = format_test_result(
                status_code=status_code,
                response_body=response_body,
                response_time=response_time,
                is_passed=is_passed,
                error_message=validation_error if not is_passed else ""
            )
            
            result['_record_id'] = test_case.get('_record_id')
            
            logger.info(f"测试用例 {test_id} 执行完成: {'PASS' if is_passed else 'FAIL'}")
            return result
            
        except Exception as e:
            error_msg = f"执行测试用例异常: {str(e)}"
            logger.error(error_msg)
            
            result = format_test_result(
                status_code=0,
                response_body="",
                response_time=0.0,
                is_passed=False,
                error_message=error_msg
            )
            result['_record_id'] = test_case.get('_record_id')
            return result
    
    def execute_all_tests(self, table_id: str) -> 'TestResults':
        """
        执行所有测试用例
        
        Args:
            table_id: 表格ID
            
        Returns:
            测试结果统计
        """
        logger.info("开始执行所有测试用例...")
        start_time = time.time()
        
        # 加载测试用例
        test_cases = self.load_test_cases(table_id)
        if not test_cases:
            logger.warning("没有找到有效的测试用例")
            return TestResults([], 0, 0, 0, 0.0)
        
        # 执行测试
        results = []
        passed_count = 0
        failed_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"执行进度: {i}/{len(test_cases)}")
            
            result = self.execute_single_test(test_case)
            results.append(result)
            
            if result.get('是否通过') == 'PASS':
                passed_count += 1
            else:
                failed_count += 1
            
            # 可选的延迟，避免请求过于频繁
            delay = self.config.get('request_delay', 0)
            if delay > 0:
                time.sleep(delay)
        
        total_time = time.time() - start_time
        
        # 保存结果
        self.test_results = results
        
        logger.info(f"所有测试执行完成: 总数{len(test_cases)}, 通过{passed_count}, 失败{failed_count}")
        logger.info(f"总耗时: {total_time:.2f}秒")
        
        return TestResults(results, len(test_cases), passed_count, failed_count, total_time)
    
    def write_results_to_table(self, table_id: str, results: List[Dict[str, Any]]) -> bool:
        """
        将测试结果回写到表格
        
        Args:
            table_id: 表格ID
            results: 测试结果列表
            
        Returns:
            是否写入成功
        """
        logger.info(f"将测试结果回写到表格 {table_id}...")
        
        try:
            success_count = 0
            
            for result in results:
                record_id = result.get('_record_id')
                if not record_id:
                    logger.warning("结果缺少记录ID，跳过更新")
                    continue
                
                # 移除内部字段
                update_fields = {k: v for k, v in result.items() if not k.startswith('_')}
                
                try:
                    self.lark_client.update_record(table_id, record_id, update_fields)
                    success_count += 1
                    logger.debug(f"更新记录成功: {record_id}")
                except Exception as e:
                    logger.error(f"更新记录失败 {record_id}: {str(e)}")
                    continue
            
            logger.info(f"结果回写完成: 成功{success_count}/{len(results)}")
            return success_count == len(results)
            
        except Exception as e:
            logger.error(f"回写结果失败: {str(e)}")
            return False
    
    def run_full_test_cycle(self, table_id: str) -> 'TestResults':
        """
        运行完整的测试周期：加载->执行->回写
        
        Args:
            table_id: 表格ID
            
        Returns:
            测试结果统计
        """
        logger.info("开始完整测试周期...")
        
        # 执行所有测试
        results = self.execute_all_tests(table_id)
        
        # 回写结果到表格
        if results.results:
            success = self.write_results_to_table(table_id, results.results)
            if success:
                logger.info("测试结果已成功回写到表格")
            else:
                logger.warning("部分测试结果回写失败")
        
        return results


class TestResults:
    """测试结果统计"""
    
    def __init__(
        self,
        results: List[Dict[str, Any]],
        total: int,
        passed: int,
        failed: int,
        duration: float
    ):
        self.results = results
        self.total = total
        self.passed = passed
        self.failed = failed
        self.duration = duration
        self.pass_rate = (passed / total * 100) if total > 0 else 0.0
    
    def summary(self) -> str:
        """生成测试结果摘要"""
        return (
            f"测试摘要:\n"
            f"  总数: {self.total}\n"
            f"  通过: {self.passed}\n"
            f"  失败: {self.failed}\n"
            f"  通过率: {self.pass_rate:.1f}%\n"
            f"  耗时: {self.duration:.2f}秒"
        )
    
    def __str__(self):
        return self.summary()
