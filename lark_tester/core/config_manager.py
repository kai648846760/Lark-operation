"""
配置管理模块

提供配置文件管理、环境变量处理和认证信息管理
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

from ..utils.logger import get_logger
from ..utils.validator import validate_config

logger = get_logger(__name__)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为项目根目录的config文件夹
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # 默认配置目录
            project_root = Path(__file__).parent.parent.parent
            self.config_dir = project_root / "config"
        
        self.config_dir.mkdir(exist_ok=True)
        self._config_cache = {}
    
    def load_config(self, env: str = "default") -> Dict[str, Any]:
        """
        加载指定环境的配置
        
        Args:
            env: 环境名称 (default, development, production等)
            
        Returns:
            配置字典
        """
        if env in self._config_cache:
            return self._config_cache[env]
        
        config = {}
        
        # 加载默认配置
        default_config = self._load_config_file("default.yaml")
        if default_config:
            config.update(default_config)
        
        # 加载环境特定配置
        if env != "default":
            env_config = self._load_config_file(f"{env}.yaml")
            if env_config:
                config.update(env_config)
        
        # 加载环境变量覆盖
        env_overrides = self._load_env_variables()
        config.update(env_overrides)
        
        # 验证配置
        is_valid, errors = validate_config(config)
        if not is_valid:
            logger.warning(f"配置验证失败: {errors}")
        
        # 缓存配置
        self._config_cache[env] = config
        
        logger.info(f"已加载配置环境: {env}")
        return config
    
    def _load_config_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        加载配置文件
        
        Args:
            filename: 配置文件名
            
        Returns:
            配置字典或None
        """
        config_path = self.config_dir / filename
        
        if not config_path.exists():
            logger.debug(f"配置文件不存在: {config_path}")
            return None
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            logger.debug(f"成功加载配置文件: {filename}")
            return config
            
        except Exception as e:
            logger.error(f"加载配置文件失败 {filename}: {str(e)}")
            return None
    
    def _load_env_variables(self) -> Dict[str, Any]:
        """
        从环境变量加载配置
        
        Returns:
            环境变量配置字典
        """
        env_config = {}
        
        # 支持的环境变量映射
        env_mappings = {
            'LARK_PERSONAL_TOKEN': 'personal_token',
            'LARK_APP_TOKEN': 'app_token',
            'LARK_TABLE_ID': 'table_id',
            'LARK_DOMAIN': 'domain',
            'API_BASE_URL': 'api_base_url',
            'REQUEST_TIMEOUT': 'request_timeout',
            'MAX_RETRIES': 'max_retries',
            'REQUEST_DELAY': 'request_delay',
        }
        
        for env_key, config_key in env_mappings.items():
            value = os.getenv(env_key)
            if value:
                # 类型转换
                if config_key in ['request_timeout', 'max_retries']:
                    try:
                        value = int(value)
                    except ValueError:
                        logger.warning(f"环境变量 {env_key} 不是有效整数: {value}")
                        continue
                elif config_key in ['request_delay']:
                    try:
                        value = float(value)
                    except ValueError:
                        logger.warning(f"环境变量 {env_key} 不是有效数字: {value}")
                        continue
                
                env_config[config_key] = value
                logger.debug(f"从环境变量加载: {config_key}")
        
        return env_config
    
    def save_config(self, config: Dict[str, Any], env: str = "default") -> bool:
        """
        保存配置到文件
        
        Args:
            config: 配置字典
            env: 环境名称
            
        Returns:
            是否保存成功
        """
        try:
            config_path = self.config_dir / f"{env}.yaml"
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            # 更新缓存
            self._config_cache[env] = config
            
            logger.info(f"配置已保存到: {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            return False
    
    def get_lark_config(self, env: str = "default") -> Dict[str, str]:
        """
        获取Lark相关配置
        
        Args:
            env: 环境名称
            
        Returns:
            Lark配置字典
        """
        config = self.load_config(env)
        
        lark_config = {
            'personal_token': config.get('personal_token', ''),
            'app_token': config.get('app_token', ''),
            'table_id': config.get('table_id', ''),
            'config_table_id': config.get('config_table_id', ''),  # 新增配置表ID
            'domain': config.get('domain', 'https://base-api.larksuite.com')
        }
        
        return lark_config
    
    def get_api_config(self, env: str = "default") -> Dict[str, Any]:
        """
        获取API测试相关配置
        
        Args:
            env: 环境名称
            
        Returns:
            API配置字典
        """
        config = self.load_config(env)
        
        api_config = {
            'base_url': config.get('api_base_url', ''),
            'timeout': config.get('request_timeout', 30),
            'max_retries': config.get('max_retries', 3),
            'retry_delay': config.get('retry_delay', 1.0),
            'request_delay': config.get('request_delay', 0)
        }
        
        return api_config
    
    def create_default_config(self) -> bool:
        """
        创建默认配置文件
        
        Returns:
            是否创建成功
        """
        default_config = {
            # Lark配置
            'personal_token': '',
            'app_token': '',
            'table_id': '',
            'domain': 'https://base-api.larksuite.com',
            
            # API测试配置
            'api_base_url': '',
            'request_timeout': 30,
            'max_retries': 3,
            'retry_delay': 1.0,
            'request_delay': 0,
            
            # 日志配置
            'log_level': 'INFO',
            'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            
            # 其他配置
            'max_response_length': 2000,
            'enable_rich_logging': True
        }
        
        return self.save_config(default_config, "default")
    
    def list_environments(self) -> list:
        """
        列出所有可用的环境配置
        
        Returns:
            环境名称列表
        """
        environments = []
        
        for config_file in self.config_dir.glob("*.yaml"):
            env_name = config_file.stem
            environments.append(env_name)
        
        return sorted(environments)
    
    def clear_cache(self):
        """清除配置缓存"""
        self._config_cache.clear()
        logger.debug("配置缓存已清除")


# 全局配置管理器实例
config_manager = ConfigManager()