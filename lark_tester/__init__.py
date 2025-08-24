"""
Lark API 自动化测试框架

基于飞书多维表格的API自动化测试框架，支持：
- 从多维表格读取测试用例
- 执行HTTP API测试
- 将测试结果回写到表格
- 生成测试报告和统计
"""

__version__ = "1.0.0"
__author__ = "Lark API Tester Team"
__email__ = "dev@example.com"

from .core.lark_client import LarkClient
from .core.api_client import APIClient, AssertionValidator
from .core.test_executor import TestExecutor, TestResults
from .core.config_manager import ConfigManager, config_manager
from .core.config_table import create_config_reader

from .utils.logger import setup_logging, get_logger
from .utils.validator import validate_test_case, validate_config
from .utils.formatter import format_test_result, format_response_body

__all__ = [
    # 版本信息
    "__version__",
    "__author__", 
    "__email__",
    
    # 核心类
    "LarkClient",
    "APIClient", 
    "AssertionValidator",
    "TestExecutor",
    "TestResults",
    "ConfigManager",
    "config_manager",
    "create_config_reader",
    
    # 工具函数
    "setup_logging",
    "get_logger",
    "validate_test_case",
    "validate_config",
    "format_test_result",
    "format_response_body",
]


class LarkAPITester:
    """
    Lark API测试器主类 - 简化的入口类
    
    提供简单的API来执行完整的测试流程
    """
    
    def __init__(
        self,
        personal_token: str,
        app_token: str,
        table_id: str,
        api_base_url: str = "",
        config_env: str = "default",
        config_table_id: str = ""  # 优先使用参数，其次使用配置文件
    ):
        """
        初始化Lark API测试器
        
        Args:
            personal_token: 个人访问令牌
            app_token: 应用令牌
            table_id: 表格ID
            api_base_url: API基础URL（如果为空则从配置表读取）
            config_env: 配置环境
            config_table_id: 配置表ID（优先使用参数，其次使用配置文件）
        """
        self.table_id = table_id
        
        # 初始化组件
        self.lark_client = LarkClient(personal_token, app_token)
        
        # 加载配置
        config = config_manager.load_config(config_env)
        
        # 如果api_base_url为空，尝试从配置表读取
        if not api_base_url:
            # 优先使用参数中的config_table_id，其次使用配置文件中的
            if not config_table_id:
                config_table_id = config.get('config_table_id', '')
            
            if config_table_id:
                try:
                    config_reader = create_config_reader(personal_token, app_token, config_table_id)
                    dynamic_config = config_reader.load_config()
                    api_base_url = dynamic_config.get('api_base_url', '')
                    if api_base_url:
                        print(f"⚙️  从配置表读取API域名: {api_base_url}")
                except Exception as e:
                    print(f"⚠️  读取配置表失败: {str(e)}")
            else:
                print("⚠️  未配置 config_table_id，跳过配置表读取")
        
        self.api_client = APIClient(base_url=api_base_url)
        
        self.executor = TestExecutor(
            lark_client=self.lark_client,
            api_client=self.api_client,
            config=config
        )
    
    def run_tests(self) -> TestResults:
        """
        执行所有测试
        
        Returns:
            测试结果统计
        """
        return self.executor.run_full_test_cycle(self.table_id)
    
    def validate_table(self) -> dict:
        """
        验证表格结构
        
        Returns:
            验证结果字典
        """
        records = self.lark_client.get_all_records(self.table_id)
        
        # 分析字段结构
        all_fields = set()
        valid_count = 0
        
        for record in records:
            fields = record['fields']
            all_fields.update(fields.keys())
            
            if fields.get('接口路径') and fields.get('请求方法'):
                valid_count += 1
        
        return {
            'total_records': len(records),
            'valid_records': valid_count,
            'all_fields': list(all_fields),
            'is_valid': valid_count > 0
        }


# 设置默认日志
setup_logging()