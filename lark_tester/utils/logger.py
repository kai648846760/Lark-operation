"""
日志工具模块

提供统一的日志配置和获取功能
"""

import logging
import sys
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    use_rich: bool = True
) -> None:
    """
    设置全局日志配置
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: 自定义格式字符串
        use_rich: 是否使用rich格式化输出
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 清除现有handlers
    logging.root.handlers = []
    
    if use_rich:
        # 使用rich格式化
        console = Console(stderr=True)
        handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True
        )
        handler.setFormatter(logging.Formatter("%(name)s - %(message)s"))
    else:
        # 使用标准格式化
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(format_string))
    
    logging.basicConfig(
        level=log_level,
        handlers=[handler],
        force=True
    )


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的logger
    
    Args:
        name: logger名称，通常使用__name__
        
    Returns:
        配置好的logger实例
    """
    return logging.getLogger(name)
