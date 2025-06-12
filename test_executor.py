import requests
import json
import re
import time
from typing import Dict, Any, List, Optional
from lark_bitable import LarkBitable


class TestCaseExecutor:
    """接口测试用例执行器，增强日志输出"""

    def __init__(self, app_token: str, personal_token: str, test_table_id: str, config_table_id: str):
        self.lark = LarkBitable(app_token, personal_token)
        self.test_table_id = test_table_id
        self.config_table_id = config_table_id
        self.response_cache = {}
        self.base_url = ""
        self.config = {}
        self.log_level = "DEBUG"  # 日志级别: DEBUG/INFO/WARN/ERROR

    def load_config(self):
        """加载配置表并打印详细日志"""
        print("=== 配置加载开始 ===")
        config_records = self.lark.get_all_records(self.config_table_id)
        print(f"获取到 {len(config_records)} 条配置记录")

        for i, record in enumerate(config_records, 1):
            print(f"  记录{i}: ID={record['record_id']}, 字段={record['fields']}")

        active_configs = [
            r for r in config_records if r["fields"].get("是否开启") == "是"]
        print(f"找到 {len(active_configs)} 条启用配置")

        if not active_configs:
            print("警告: 未找到启用的配置，使用默认空URL")
            return False

        self.config = active_configs[0]["fields"]
        self.base_url = self.config.get("host", "")
        print(f"配置加载完成: base_url={self.base_url}")
        return True

    def clear_previous_results(self):
        """清除测试表结果并打印日志"""
        print("=== 清除旧结果开始 ===")
        test_cases = self.lark.get_all_records(self.test_table_id)
        print(f"找到 {len(test_cases)} 条测试用例需要清除结果")

        success_count = 0
        for test_case in test_cases:
            record_id = test_case["record_id"]
            fields_to_clear = {
                "响应体": "",
                "响应时间": "",
                "响应状态码": "",
                "是否通过": ""
            }
            if self.lark.update_record(self.test_table_id, record_id, fields_to_clear):
                success_count += 1

        print(f"清除完成: 成功 {success_count}/{len(test_cases)}")

    def execute_all_test_cases(self):
        """执行所有测试用例并打印详细日志"""
        print("=== 测试执行开始 ===")

        if not self.load_config():
            print("配置加载失败，终止测试")
            return

        self.clear_previous_results()

        test_cases = self.lark.get_all_records(self.test_table_id)
        print(f"获取到 {len(test_cases)} 条测试用例")

        test_cases.sort(key=lambda x: int(x["fields"].get("接口编号", "999")))

        for i, test_case in enumerate(test_cases, 1):
            # print(test_case, '----<<')
            record_id = test_case["record_id"]
            interface_id = test_case["fields"].get("接口编号", "未设置")
            interface_path = test_case["fields"].get("接口路径", "无路径")

            print(f"\n--- 执行测试用例 {i}/{len(test_cases)} ---")
            print(f"接口编号: {interface_id}, 路径: {interface_path}")

            result = self.execute_test_case(test_case['fields'])
            self.lark.update_record(self.test_table_id, record_id, result)
            time.sleep(0.5)

        print("\n=== 测试执行完成 ===")

    def execute_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试用例并记录详细日志"""
        result = {
            "响应体": "",
            "响应时间": "",
            "响应状态码": "",
            "是否通过": "FAIL"
        }

        print("--- 请求准备 ---", test_case, '--------<<<')
        request_body = test_case.get("请求体", "{}")
        request_headers = test_case.get("请求头", "{}")
        method = test_case.get("请求方法", "GET").upper()
        interface_path = test_case.get("接口路径", "")
        full_url = f"{self.base_url}{interface_path}"

        print(f"请求方法: {method}, URL: {full_url}")
        print(f"原始请求体: {request_body}")
        print(f"原始请求头: {request_headers}")

        try:
            # 解析引用
            resolved_body = self._resolve_references(request_body)
            resolved_headers = self._resolve_references(request_headers)

            print("\n--- 请求变量解析 ---")
            print(f"解析后请求体: {resolved_body}")
            print(f"解析后请求头: {resolved_headers}")

            # 构建请求
            headers = json.loads(resolved_headers) if resolved_headers else {}
            print(f"最终请求头: {headers}")

            # 发送请求
            print("\n--- 发送请求 ---")
            start_time = time.time()

            if method == "GET":
                response = requests.get(
                    full_url,
                    params=json.loads(
                        resolved_body) if resolved_body else None,
                    headers=headers
                )
            elif method in ["POST", "PUT", "PATCH"]:
                response = requests.request(
                    method, full_url,
                    json=json.loads(resolved_body) if resolved_body else None,
                    headers=headers
                )
            else:
                raise ValueError(f"不支持的请求方式: {method}")

            elapsed_time = time.time() - start_time
            result["响应时间"] = f"{elapsed_time * 1000:.2f}ms"
            result["响应状态码"] = str(response.status_code)

            print(f"响应状态码: {response.status_code}")
            print(f"响应时间: {result['响应时间']}")
            print("响应头:")
            for k, v in response.headers.items():
                print(f"  {k}: {v}")

            # 处理响应
            try:
                response_json = response.json()
                result["响应体"] = response_json
                print("\n--- 响应内容（JSON）---")
                print(json.dumps(response_json, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                result["响应体"] = response.text
                print("\n--- 响应内容（文本）---")
                print(result["响应体"][:500] +
                      ("..." if len(result["响应体"]) > 500 else ""))

            # 缓存响应
            interface_id = test_case.get("接口编号", "")
            if interface_id:
                self.response_cache[interface_id] = result["响应体"]
                print(f"缓存接口 {interface_id} 响应")

            # 执行断言
            assertion_rules = test_case.get("断言规则", "{}")
            result["是否通过"] = self._run_assertions(
                result["响应体"], assertion_rules, response.status_code)
            print(f"断言结果: {result['是否通过']}")

        except Exception as e:
            result["响应体"] = f"执行异常: {str(e)}"
            result["是否通过"] = "FAIL"
            print(f"执行异常: {str(e)}")

        return result

    def _resolve_references(self, content: str) -> str:
        """解析引用并记录日志"""
        if not content or not isinstance(content, str):
            return content

        print("\n--- 变量引用解析 ---")
        print(f"待解析内容: {content}")

        pattern = r'\$(\d+)\.([\w\.]+)'
        matches = re.findall(pattern, content)

        if not matches:
            print("未找到变量引用")
            return content

        print(f"找到 {len(matches)} 处变量引用")
        for interface_id, field_path in matches:
            if interface_id in self.response_cache:
                response_data = self.response_cache[interface_id]
                value = self._get_nested_value(response_data, field_path)
                if value is not None:
                    content = content.replace(
                        f"${interface_id}.{field_path}", str(value))
                    print(f"解析 {interface_id}.{field_path} = {value}")
                else:
                    print(f"警告: 无法解析 {interface_id}.{field_path}")
            else:
                print(f"警告: 未找到接口 {interface_id} 的响应缓存")

        print(f"解析后内容: {content}")
        return content

    def _get_nested_value(self, data, path: str):
        """获取嵌套值并记录日志"""
        try:
            parts = re.split(r'\.|\[|\]', path)
            parts = [p for p in parts if p]

            current = data
            path_log = "data"
            for part in parts:
                if part.isdigit():
                    current = current[int(part)]
                    path_log += f"[{part}]"
                else:
                    current = current[part]
                    path_log += f".{part}"
            print(f"获取 {path_log} = {current}")
            return current
        except (KeyError, IndexError, TypeError) as e:
            print(f"获取 {path} 失败: {str(e)}")
            return None

    def _run_assertions(self, response_body, assertion_rules: str, status_code: int) -> str:
        """执行断言并记录日志"""
        print("\n--- 断言执行 ---")
        if not assertion_rules:
            print("无断言规则，使用默认断言: 状态码200")
            result = "PASS" if status_code == 200 else "FAIL"
            print(f"默认断言结果: {result}")
            return result

        try:
            rules = json.loads(assertion_rules)
            print(f"断言规则: {rules}")

            # 状态码断言
            if "status_code" in rules:
                expected_code = rules["status_code"]
                print(f"状态码断言: 期望 {expected_code}, 实际 {status_code}")
                if expected_code != status_code:
                    print("状态码断言失败")
                    return "FAIL"

            # 响应体断言
            if "body" in rules:
                expected_body = rules["body"]
                print("响应体断言:")
                print(f"  期望: {expected_body}")
                print(f"  实际: {response_body}")

                if isinstance(expected_body, dict) and isinstance(response_body, dict):
                    for key, value in expected_body.items():
                        if key not in response_body or response_body[key] != value:
                            print(
                                f"  字段 {key} 断言失败: 期望 {value}, 实际 {response_body.get(key)}")
                            return "FAIL"
                elif response_body != expected_body:
                    print("响应体内容断言失败")
                    return "FAIL"

            print("所有断言通过")
            return "PASS"

        except Exception as e:
            print(f"断言异常: {str(e)}")
            return "FAIL"


if __name__ == "__main__":
    APP_TOKEN = 'R05rb9w0TaM6UFsryGvli2Xlgnd'
    PERSONAL_TOKEN = 'pt-0zbxVu9jxpoMH0KgQBCi3XPQYRpfm2IhaEL7SmiXAQAAHwABIh9AAMA4UuZk'
    TABLE_ID = 'tblcvX11EyHYOn5A'
    CONFIG_TABLE_ID = 'tblm6c6W5vWFmzJv'

    print("=== 测试执行器启动 ===")
    executor = TestCaseExecutor(
        APP_TOKEN,
        PERSONAL_TOKEN,
        TABLE_ID,
        CONFIG_TABLE_ID
    )
    executor.execute_all_test_cases()
