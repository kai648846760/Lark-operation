"""
配置表读取模块

从Lark多维表格中动态读取配置信息
"""

from typing import Dict, Any, Optional
from .lark_client import LarkClient
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConfigTableReader:
    """配置表读取器"""
    
    def __init__(self, lark_client: LarkClient, config_table_id: str):
        """
        初始化配置表读取器
        
        Args:
            lark_client: Lark客户端实例
            config_table_id: 配置表ID
        """
        self.lark_client = lark_client
        self.config_table_id = config_table_id
        self._config_cache = {}
    
    def load_config(self) -> Dict[str, Any]:
        """
        从配置表加载配置
        
        Returns:
            配置字典
        """
        try:
            logger.info(f"从配置表 {self.config_table_id} 加载配置...")
            
            records = self.lark_client.get_all_records(self.config_table_id)
            logger.info(f"找到 {len(records)} 条配置记录")
            
            config = {}
            
            for record in records:
                fields = record['fields']
                
                # 提取API域名配置
                host = fields.get('host')
                is_enabled = fields.get('是否开启')
                remark = fields.get('备注')
                
                if host and is_enabled == '是':
                    config['api_base_url'] = host
                    logger.info(f"从配置表读取API域名: {host} ({remark})")
                    break
            
            # 如果没有找到有效配置，使用默认值
            if 'api_base_url' not in config:
                logger.warning("配置表中没有找到有效的API域名配置")
                config['api_base_url'] = ""
            
            self._config_cache = config
            return config
            
        except Exception as e:
            logger.error(f"读取配置表失败: {str(e)}")
            return {'api_base_url': ""}
    
    def get_api_base_url(self) -> str:
        """
        获取API基础URL
        
        Returns:
            API基础URL
        """
        if not self._config_cache:
            self.load_config()
        
        return self._config_cache.get('api_base_url', "")
    
    def refresh_config(self) -> Dict[str, Any]:
        """
        刷新配置缓存
        
        Returns:
            最新的配置字典
        """
        self._config_cache.clear()
        return self.load_config()


def create_config_reader(
    personal_token: str, 
    app_token: str, 
    config_table_id: str
) -> ConfigTableReader:
    """
    创建配置表读取器
    
    Args:
        personal_token: 个人令牌
        app_token: 应用令牌
        config_table_id: 配置表ID
        
    Returns:
        配置表读取器实例
    """
    lark_client = LarkClient(personal_token, app_token)
    return ConfigTableReader(lark_client, config_table_id)