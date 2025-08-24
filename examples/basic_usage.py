#!/usr/bin/env python3
"""
Lark API 自动化测试框架基础使用示例

演示如何使用框架进行API测试
"""

import os
from lark_tester import LarkAPITester, setup_logging

# 设置日志
setup_logging(level="INFO", use_rich=True)

def main():
    """主函数"""
    print("🚀 Lark API 自动化测试框架示例")
    print("=" * 50)
    
    # 从环境变量或直接配置获取认证信息
    personal_token = os.getenv('LARK_PERSONAL_TOKEN', 'pt-CNVPlr8MqYPOTCBoYuJ_jQtCU8Nf46BPXlPE5WSKAQAAAkCAygSAwRqXvIsh')
    app_token = os.getenv('LARK_APP_TOKEN', 'UMlnbC7J4aP63AscoX9cdovCn7f') 
    table_id = os.getenv('LARK_TABLE_ID', 'tblIiquTXHImD3n6')
    api_base_url = os.getenv('API_BASE_URL', 'https://api.example.com')
    
    try:
        # 初始化测试器
        print("🔧 初始化API测试器...")
        tester = LarkAPITester(
            personal_token=personal_token,
            app_token=app_token,
            table_id=table_id,
            api_base_url=api_base_url,
            config_env="production"
        )
        
        # 验证表格结构
        print("\n🔍 验证表格结构...")
        validation = tester.validate_table()
        
        print(f"📊 表格统计:")
        print(f"  总记录数: {validation['total_records']}")
        print(f"  有效记录: {validation['valid_records']}")
        print(f"  表格字段: {', '.join(validation['all_fields'])}")
        
        if not validation['is_valid']:
            print("❌ 表格验证失败，无有效测试用例")
            return
        
        # 执行API测试
        print(f"\n🧪 开始执行API测试...")
        results = tester.run_tests()
        
        # 显示结果
        print(f"\n📈 测试结果:")
        print(f"  总测试数: {results.total}")
        print(f"  通过数量: {results.passed}")
        print(f"  失败数量: {results.failed}")
        print(f"  通过率: {results.pass_rate:.1f}%")
        print(f"  执行时间: {results.duration:.2f}秒")
        
        # 根据结果提供建议
        if results.failed == 0:
            print("🎉 所有测试都通过了！")
        else:
            print(f"⚠️  有 {results.failed} 个测试失败，请检查表格中的错误信息")
            
        # 显示部分失败测试的详情
        if results.failed > 0:
            print(f"\n❌ 失败测试详情:")
            failed_tests = [r for r in results.results if r.get('是否通过') == 'FAIL']
            for i, test in enumerate(failed_tests[:3], 1):  # 只显示前3个
                print(f"  {i}. 错误: {test.get('错误信息', 'Unknown error')}")
            
            if len(failed_tests) > 3:
                print(f"  ... 还有 {len(failed_tests) - 3} 个失败测试")
                
    except Exception as e:
        print(f"💥 执行异常: {str(e)}")
        print("请检查配置信息和网络连接")


if __name__ == "__main__":
    main()