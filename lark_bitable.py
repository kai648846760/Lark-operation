from baseopensdk import BaseClient, JSON
from baseopensdk.api.base.v1 import *
from baseopensdk import LARK_DOMAIN
import json
import time
from typing import List, Dict, Any, Optional


class LarkBitable:
    """Lark多维表格操作类，提供标准化的数据读取、更新、创建和删除功能"""

    def __init__(self, app_token: str, personal_token: str):
        """
        初始化Lark多维表格客户端

        Args:
            app_token: 多维表格应用Token（从URL的base/后获取）
            personal_token: 个人授权码（格式为pt-开头）
        """
        self.app_token = app_token
        self.personal_token = personal_token
        self.client = self._init_client()

    def _init_client(self) -> BaseClient:
        """初始化并返回Lark客户端实例"""
        return BaseClient.builder() \
            .app_token(self.app_token) \
            .personal_base_token(self.personal_token) \
            .domain(LARK_DOMAIN) \
            .build()

    def get_all_records(self, table_id: str, page_size: int = 100) -> List[Dict[str, Any]]:
        """
        获取表格所有记录（自动处理分页）

        Args:
            table_id: 表格ID（从URL的table=参数获取）
            page_size: 每页记录数（最大200，默认100）

        Returns:
            包含所有记录的列表，每条记录为字典格式

        Example:
            records = lark.get_all_records("tbl12345")
            for record in records:
                print(record["record_id"], record["fields"])
        """
        all_records = []
        page_token = ""

        while True:
            request = self._build_list_request(table_id, page_size, page_token)
            response = self._call_api(request, "list")

            if not response:
                break

            all_records.extend(self._parse_records(response))
            page_token = self._get_next_page_token(response)

            if not page_token:
                break

            time.sleep(0.5)  # 防止请求过于频繁

        return all_records

    def update_record(self, table_id: str, record_id: str, fields: Dict[str, Any]) -> bool:
        """
        更新指定记录的字段值

        Args:
            table_id: 表格ID
            record_id: 记录ID
            fields: 要更新的字段字典（如{"字段名": "新值"}）

        Returns:
            更新是否成功

        Example:
            success = lark.update_record(
                "tbl12345",
                "rec67890",
                {"状态": "已完成", "更新时间": "2023-10-01"}
            )
        """
        request = self._build_update_request(table_id, record_id, fields)
        response = self._call_api(request, "update")
        return response.code == 0 if response else False

    def create_record(self, table_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        创建新记录并返回记录信息

        Args:
            table_id: 表格ID
            fields: 新记录的字段字典（必须包含表格必填字段）

        Returns:
            新记录信息（成功）或None（失败）

        Example:
            new_record = lark.create_record(
                "tbl12345",
                {"名称": "新条目", "数值": 100, "日期": "2023-10-01"}
            )
            if new_record:
                print("创建成功，ID:", new_record["record_id"])
        """
        request = self._build_create_request(table_id, fields)
        response = self._call_api(request, "create")
        return self._parse_create_response(response)

    def delete_record(self, table_id: str, record_id: str) -> bool:
        """
        删除指定记录（谨慎使用，操作不可逆）

        Args:
            table_id: 表格ID
            record_id: 要删除的记录ID

        Returns:
            删除是否成功

        Example:
            success = lark.delete_record("tbl12345", "rec67890")
            if success:
                print("记录已删除")
        """
        request = self._build_delete_request(table_id, record_id)
        response = self._call_api(request, "delete")
        return response.code == 0 if response else False

    # 内部辅助方法（以单下划线开头表示内部使用）
    def _build_list_request(self, table_id: str, page_size: int, page_token: str) -> ListAppTableRecordRequest:
        """构建记录列表请求对象"""
        return ListAppTableRecordRequest.builder() \
            .table_id(table_id) \
            .page_size(min(page_size, 200)) \
            .page_token(page_token) \
            .build()

    def _build_update_request(self, table_id: str, record_id: str, fields: Dict[str, Any]) -> UpdateAppTableRecordRequest:
        """构建记录更新请求对象"""
        return UpdateAppTableRecordRequest.builder() \
            .table_id(table_id) \
            .record_id(record_id) \
            .request_body(AppTableRecord.builder().fields(fields).build()) \
            .build()

    def _build_create_request(self, table_id: str, fields: Dict[str, Any]) -> CreateAppTableRecordRequest:
        """构建记录创建请求对象"""
        return CreateAppTableRecordRequest.builder() \
            .table_id(table_id) \
            .request_body(AppTableRecord.builder().fields(fields).build()) \
            .build()

    def _build_delete_request(self, table_id: str, record_id: str) -> DeleteAppTableRecordRequest:
        """构建记录删除请求对象"""
        return DeleteAppTableRecordRequest.builder() \
            .table_id(table_id) \
            .record_id(record_id) \
            .build()

    def _call_api(self, request: Any, method: str) -> Any:
        """统一API调用处理"""
        try:
            if method == "list":
                return self.client.base.v1.app_table_record.list(request)
            elif method == "update":
                return self.client.base.v1.app_table_record.update(request)
            elif method == "create":
                return self.client.base.v1.app_table_record.create(request)
            elif method == "delete":
                return self.client.base.v1.app_table_record.delete(request)
            return None
        except Exception as e:
            print(f"API调用异常 [{method}]: {str(e)}")
            return None

    def _parse_records(self, response: Any) -> List[Dict[str, Any]]:
        """解析记录列表响应"""
        if not response or response.code != 0:
            return []
        return [{"record_id": item.record_id, "fields": item.fields} for item in response.data.items] if response.data else []

    def _get_next_page_token(self, response: Any) -> str:
        """获取下一页令牌"""
        return response.data.page_token if response and response.data else ""

    def _parse_create_response(self, response: Any) -> Optional[Dict[str, Any]]:
        """解析创建记录响应"""
        if not response or response.code != 0:
            print(f"创建记录失败: {response.code} - {response.msg}")
            return None
        return json.loads(JSON.marshal(response.data, indent=4)) if response.data else None


if __name__ == "__main__":
    # 配置信息（请替换为实际值）
    APP_TOKEN = 'R05rb9w0TaM6UFsryGvli2Xlgnd'  # 从表格URL的base/后获取
    PERSONAL_TOKEN = 'pt-0zbxVu9jxpoMH0KgQBCi3XPQYRpfm2IhaEL7SmiXAQAAHwABIh9AAMA4UuZk'  # 格式为pt-开头
    # TABLE_ID = 'tblcvX11EyHYOn5A'  # 从表格URL的table=参数获取
    TABLE_ID = 'tblm6c6W5vWFmzJv'  # 从表格URL的table=参数获取

    try:
        # 1. 初始化客户端
        lark = LarkBitable(APP_TOKEN, PERSONAL_TOKEN)
        print("✅ 客户端初始化成功")

        # 2. 读取所有记录（查）
        print("\n===== 示例1: 读取所有记录 =====")
        records = lark.get_all_records(TABLE_ID)
        print(f"成功读取 {len(records)} 条记录")

        if records:
            for i, record in enumerate(records, 1):
                print(
                    f"  记录{i}: ID={record['record_id']}, 字段={record['fields']}")

                # --------------------------------------------------------
                # # 3. 更新记录（改）
                # print("\n===== 示例2: 更新记录 =====")
                # target_record_id = record["record_id"]
                # update_fields = {
                #     "请求方式": "POST",
                #     "断言规则": "fjkajflajfkl",
                #     "接口路径": "https://api.larkoffice.com/open-apis/bitable/v1/apps/app_1234567890123456789012345678901234567890/tables/tbl1234567890123456789012345678901234567890/records",
                #     "请求头": "Content-Type: application/json",
                #     "请求体": "{\"title\":\"API测试记录\",\"fields\":{\"数值字段\":100}}",
                # }
                # if lark.update_record(TABLE_ID, target_record_id, update_fields):
                #     print(f"✅ 记录{target_record_id}更新成功")
                # else:
                #     print(f"❌ 记录{target_record_id}更新失败")
                # --------------------------------------------------------

                # # 4. 删除记录（删 - 谨慎使用，默认注释）
                # print("\n===== 示例3: 删除记录 =====")
                # delete_record_id = record["record_id"]
                # print(f"⚠️ 准备删除记录: {delete_record_id}")

                # if lark.delete_record(TABLE_ID, delete_record_id):
                #     print(f"✅ 记录{delete_record_id}删除成功")
                # else:
                #     print(f"❌ 记录{delete_record_id}删除失败")
                # --------------------------------------------------------

        else:
            print("表格中无记录")

        # 5. 创建新记录（增）
        # print("\n===== 示例4: 创建新记录 =====")
        # new_record_fields = {
        #     "请求方式": "POST",
        #     "断言规则": "fjkajflajfkl",
        #     "接口路径": "https://api.larkoffice.com/open-apis/bitable/v1/apps/app_1234567890123456789012345678901234567890/tables/tbl1234567890123456789012345678901234567890/records",
        #     "请求头": "Content-Type: application/json",
        #     "请求体": "{\"title\":\"API测试记录\",\"fields\":{\"数值字段\":100}}",
        # }
        # new_record = lark.create_record(TABLE_ID, new_record_fields)

    except Exception as e:
        print(f"程序执行异常: {str(e)}")
