"""
命令行接口模块

提供Lark API测试框架的命令行工具
"""

import click
import sys
from typing import Optional

from .core.config_manager import config_manager
from .core.lark_client import LarkClient
from .core.api_client import APIClient
from .core.test_executor import TestExecutor
from .core.config_table import create_config_reader
from .utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


@click.group()
@click.option(
    '--env', 
    default='production', 
    help='配置环境 (default, production, development等)'
)
@click.option(
    '--log-level', 
    default=None, 
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
    help='日志级别'
)
@click.pass_context
def cli(ctx: click.Context, env: str, log_level: Optional[str]):
    """Lark API 自动化测试框架"""
    ctx.ensure_object(dict)
    ctx.obj['env'] = env
    
    # 加载配置
    config = config_manager.load_config(env)
    ctx.obj['config'] = config
    
    # 设置日志
    if log_level:
        config['log_level'] = log_level
    
    setup_logging(
        level=config.get('log_level', 'INFO'),
        use_rich=config.get('enable_rich_logging', True)
    )


@cli.command()
@click.pass_context
def run_tests(ctx: click.Context):
    """执行所有API测试"""
    config = ctx.obj['config']
    
    try:
        # 验证必需配置
        required_fields = ['personal_token', 'app_token', 'table_id']
        missing_fields = [field for field in required_fields if not config.get(field)]
        
        if missing_fields:
            click.echo(f"❌ 缺少必需配置: {', '.join(missing_fields)}", err=True)
            click.echo("请检查配置文件或设置环境变量", err=True)
            sys.exit(1)
        
        # 初始化组件
        lark_config = config_manager.get_lark_config(ctx.obj['env'])
        api_config = config_manager.get_api_config(ctx.obj['env'])
        
        click.echo("🚀 初始化测试组件...")
        
        lark_client = LarkClient(
            app_token=lark_config['app_token'],
            personal_token=lark_config['personal_token']
        )
        
        # 读取配置表中的API域名配置
        click.echo("📊 读取配置表...")
        config_table_id = lark_config.get('config_table_id')  # 从配置文件读取
        
        if not config_table_id:
            click.echo("⚠️  未配置 config_table_id，跳过配置表读取")
            api_base_url = api_config['base_url']
        else:
            config_reader = create_config_reader(
                lark_config['personal_token'],
                lark_config['app_token'],
                config_table_id
            )
            
            # 获取动态配置
            dynamic_config = config_reader.load_config()
            api_base_url = dynamic_config.get('api_base_url', api_config['base_url'])
        
        if api_base_url:
            click.echo(f"⚙️  使用配置表中API域名: {api_base_url}")
        else:
            click.echo("⚠️  未找到有效的API域名配置")
        
        api_client = APIClient(
            base_url=api_base_url,
            timeout=api_config['timeout'],
            max_retries=api_config['max_retries'],
            retry_delay=api_config['retry_delay']
        )
        
        executor = TestExecutor(
            lark_client=lark_client,
            api_client=api_client,
            config=api_config
        )
        
        # 执行测试
        click.echo("📋 开始执行API测试...")
        
        results = executor.run_full_test_cycle(lark_config['table_id'])
        
        # 显示结果
        click.echo("\n" + "="*50)
        click.echo("📊 测试结果摘要")
        click.echo("="*50)
        click.echo(results.summary())
        
        if results.failed > 0:
            click.echo(f"\n❌ {results.failed} 个测试失败")
            sys.exit(1)
        else:
            click.echo(f"\n✅ 所有测试通过!")
        
    except Exception as e:
        logger.error(f"执行测试失败: {str(e)}")
        click.echo(f"❌ 执行失败: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--table-id', help='指定表格ID')
@click.pass_context
def validate_table(ctx: click.Context, table_id: Optional[str]):
    """验证表格结构和数据"""
    config = ctx.obj['config']
    
    try:
        # 获取表格ID
        if not table_id:
            table_id = config.get('table_id')
        
        if not table_id:
            click.echo("❌ 未指定表格ID", err=True)
            sys.exit(1)
        
        # 初始化客户端
        lark_config = config_manager.get_lark_config(ctx.obj['env'])
        lark_client = LarkClient(
            app_token=lark_config['app_token'],
            personal_token=lark_config['personal_token']
        )
        
        click.echo(f"🔍 验证表格: {table_id}")
        
        # 加载记录
        records = lark_client.get_all_records(table_id)
        click.echo(f"📋 找到 {len(records)} 条记录")
        
        if not records:
            click.echo("⚠️  表格为空")
            return
        
        # 分析字段结构
        all_fields = set()
        for record in records:
            all_fields.update(record['fields'].keys())
        
        click.echo(f"\n📊 字段分析:")
        click.echo(f"字段总数: {len(all_fields)}")
        
        # 检查必需字段
        required_fields = ['接口编号', '接口路径', '请求方法']
        missing_fields = [field for field in required_fields if field not in all_fields]
        
        if missing_fields:
            click.echo(f"❌ 缺少必需字段: {', '.join(missing_fields)}")
        else:
            click.echo("✅ 所有必需字段都存在")
        
        # 统计测试用例状态
        valid_count = 0
        for record in records:
            fields = record['fields']
            if fields.get('接口路径') and fields.get('请求方法'):
                valid_count += 1
        
        click.echo(f"\n📈 测试用例统计:")
        click.echo(f"有效测试用例: {valid_count}/{len(records)}")
        
        if valid_count == 0:
            click.echo("❌ 没有有效的测试用例")
        elif valid_count < len(records):
            click.echo(f"⚠️  有 {len(records) - valid_count} 条无效记录")
        else:
            click.echo("✅ 所有记录都是有效的测试用例")
        
    except Exception as e:
        logger.error(f"验证表格失败: {str(e)}")
        click.echo(f"❌ 验证失败: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def show_config(ctx: click.Context):
    """显示当前配置"""
    config = ctx.obj['config']
    env = ctx.obj['env']
    
    click.echo(f"📋 当前配置环境: {env}")
    click.echo("="*40)
    
    # 显示主要配置项
    sections = {
        "Lark配置": ['personal_token', 'app_token', 'table_id', 'domain'],
        "API配置": ['api_base_url', 'request_timeout', 'max_retries', 'retry_delay'],
        "日志配置": ['log_level', 'enable_rich_logging'],
        "其他配置": ['max_response_length', 'enable_assertions', 'fail_fast']
    }
    
    for section_name, fields in sections.items():
        click.echo(f"\n{section_name}:")
        for field in fields:
            value = config.get(field, 'N/A')
            # 隐藏敏感信息
            if 'token' in field and value and value != 'N/A':
                value = value[:8] + '...' + value[-8:] if len(value) > 16 else '***'
            click.echo(f"  {field}: {value}")


@cli.command()
@click.pass_context
def list_envs(ctx: click.Context):
    """列出所有可用的配置环境"""
    envs = config_manager.list_environments()
    
    click.echo("📋 可用的配置环境:")
    for env in envs:
        current = " (当前)" if env == ctx.obj['env'] else ""
        click.echo(f"  • {env}{current}")


@cli.command()
@click.pass_context
def init_config(ctx: click.Context):
    """初始化默认配置文件"""
    click.echo("🔧 初始化默认配置...")
    
    success = config_manager.create_default_config()
    
    if success:
        click.echo("✅ 默认配置文件已创建")
        click.echo("请编辑 config/default.yaml 文件以配置您的认证信息")
    else:
        click.echo("❌ 创建配置文件失败", err=True)
        sys.exit(1)


def main():
    """主入口函数"""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n⚠️  用户中断操作")
        sys.exit(130)
    except Exception as e:
        logger.error(f"程序异常: {str(e)}")
        click.echo(f"💥 程序异常: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()