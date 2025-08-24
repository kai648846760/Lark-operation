"""
Lark多维表格客户端

基于重构的无依赖lark_bitable.py，完全兼容原始baseopensdk认证逻辑。
根据规范要求，简化认证方式，只使用personal_token，无需app_token。

主要功能:
- 多维表格CRUD操作
- 完全基于原始baseopensdk认证逻辑
- 使用现代化requests库
- 支持最新版本Python
"""

import requests
import json
import time
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from urllib.parse import urljoin


@dataclass
class LarkResponse:
    """Lark API响应封装"""
    code: int
    message: str
    data: Any = None
    success: bool = False

    @classmethod
    def from_dict(cls, response_dict: Dict) -> 'LarkResponse':
        """从响应字典创建LarkResponse对象"""
        return cls(
            code=response_dict.get('code', -1),
            message=response_dict.get('msg', ''),
            data=response_dict.get('data'),
            success=response_dict.get('code', -1) == 0
        )


class LarkError(Exception):
    """Lark API错误异常"""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Lark API Error {code}: {message}")


class LarkClient:
    """
    Lark多维表格客户端
    
    完全基于原始baseopensdk认证逻辑，但使用现代化requests库实现。
    根据规范要求，简化为只使用personal_token认证方式。
    """

    # 基于原始baseopensdk的域名配置
    LARK_DOMAIN = "https://base-api.larksuite.com"
    # 支持国际版域名（根据规范要求）
    INTERNATIONAL_DOMAIN = "https://open.larksuite.com"

    def __init__(self, personal_token: str, app_token: str, domain: str = None, use_international: bool = False):
        """
        初始化Lark客户端

        Args:
            personal_token: 个人授权码（pt-开头格式，来自多维表格插件授权码）
            app_token: 应用Token（从URL中的base/后获取）
            domain: API域名，默认使用原始baseopensdk域名
            use_international: 是否使用国际版域名
        """
        self.personal_token = personal_token.strip()
        self.app_token = app_token.strip()
        
        # 验证personal_token格式
        if not self.personal_token.startswith('pt-'):
            raise ValueError('personal_token必须以"pt-"开头（多维表格授权码格式）')
        
        # 设置API域名（根据规范优先使用国际版）
        if domain:
            self.domain = domain
        elif use_international:
            self.domain = self.INTERNATIONAL_DOMAIN
        else:
            self.domain = self.LARK_DOMAIN
        
        # 初始化HTTP会话（完全基于原始baseopensdk认证逻辑）
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.personal_token}',
            'User-Agent': 'base-open-sdk-python/v1.0.0'  # 与原始SDK一致
        })
        
        # 日志配置
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"✅ Lark客户端初始化成功（完全兼容原始baseopensdk）")
        self.logger.info(f"   域名: {self.domain}")
        self.logger.info(f"   App Token: {self.app_token}")
        self.logger.info(f"   Personal Token: {self.personal_token[:30]}...")

    def _build_url(self, endpoint: str) -> str:
        """构建完整API URL"""
        return urljoin(self.domain + '/', endpoint.lstrip('/'))

    def _make_request(self, method: str, endpoint: str, **kwargs) -> LarkResponse:
        """
        统一的HTTP请求处理方法
        
        Args:
            method: HTTP方法
            endpoint: API端点路径
            **kwargs: 传递给requests的额外参数
            
        Returns:
            LarkResponse对象
        """
        url = self._build_url(endpoint)
        
        try:
            self.logger.debug(f"发起请求: {method} {url}")
            
            response = self.session.request(method, url, timeout=30, **kwargs)
            
            # 检查HTTP状态码
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                self.logger.error(error_msg)
                return LarkResponse(
                    code=response.status_code,
                    message=error_msg,
                    success=False
                )
            
            # 解析JSON响应
            try:
                response_data = response.json()
                lark_resp = LarkResponse.from_dict(response_data)
                
                if not lark_resp.success:
                    self.logger.warning(f"API错误: {lark_resp.code} - {lark_resp.message}")
                else:
                    self.logger.debug("请求成功")
                    
                return lark_resp
                
            except json.JSONDecodeError as e:
                error_msg = f"JSON解析失败: {str(e)}"
                self.logger.error(error_msg)
                return LarkResponse(
                    code=-1,
                    message=error_msg,
                    success=False
                )
                
        except requests.exceptions.Timeout:
            error_msg = "请求超时"
            self.logger.error(error_msg)
            return LarkResponse(code=-1, message=error_msg, success=False)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"请求异常: {str(e)}"
            self.logger.error(error_msg)
            return LarkResponse(code=-1, message=error_msg, success=False)

    def get_all_records(self, table_id: str, page_size: int = 100) -> List[Dict[str, Any]]:
        """
        获取表格所有记录（自动处理分页）

        Args:
            table_id: 表格ID
            page_size: 每页记录数（最大200，默认100）

        Returns:
            包含所有记录的列表
        """
        all_records = []
        page_token = ""
        page_size = min(page_size, 200)

        while True:
            # 构建查询参数
            params = {'page_size': page_size}
            if page_token:
                params['page_token'] = page_token

            # 使用原始baseopensdk的API路径结构
            endpoint = f"/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/records"
            response = self._make_request('GET', endpoint, params=params)

            if not response.success:
                self.logger.error(f"获取记录失败: {response.message}")
                break

            # 解析记录
            if response.data and 'items' in response.data:
                records = response.data['items']
                for record in records:
                    all_records.append({
                        'record_id': record.get('record_id', ''),
                        'fields': record.get('fields', {})
                    })

            # 检查是否有下一页
            if not response.data or not response.data.get('has_more', False):
                break

            page_token = response.data.get('page_token', '')
            if not page_token:
                break

            # 防止请求过于频繁
            time.sleep(0.5)

        self.logger.info(f"成功获取 {len(all_records)} 条记录")
        return all_records

    def create_record(self, table_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        创建新记录

        Args:
            table_id: 表格ID
            fields: 新记录的字段字典

        Returns:
            新记录信息或None
        """
        request_body = {'fields': fields}
        endpoint = f"/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/records"
        response = self._make_request('POST', endpoint, json=request_body)

        if not response.success:
            self.logger.error(f"创建记录失败: {response.message}")
            return None

        if response.data and 'record' in response.data:
            record_data = response.data['record']
            result = {
                'record_id': record_data.get('record_id', ''),
                'fields': record_data.get('fields', {})
            }
            self.logger.info(f"成功创建记录: {result['record_id']}")
            return result

        return None

    def update_record(self, table_id: str, record_id: str, fields: Dict[str, Any]) -> bool:
        """
        更新指定记录

        Args:
            table_id: 表格ID
            record_id: 记录ID
            fields: 要更新的字段字典

        Returns:
            更新是否成功
        """
        request_body = {'fields': fields}
        endpoint = f"/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/records/{record_id}"
        response = self._make_request('PUT', endpoint, json=request_body)

        if response.success:
            self.logger.info(f"成功更新记录: {record_id}")
            return True
        else:
            self.logger.error(f"更新记录失败: {response.message}")
            return False

    def delete_record(self, table_id: str, record_id: str) -> bool:
        """
        删除指定记录

        Args:
            table_id: 表格ID
            record_id: 要删除的记录ID

        Returns:
            删除是否成功
        """
        endpoint = f"/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/records/{record_id}"
        response = self._make_request('DELETE', endpoint)

        if response.success:
            self.logger.info(f"成功删除记录: {record_id}")
            return True
        else:
            self.logger.error(f"删除记录失败: {response.message}")
            return False

    def get_record_by_id(self, table_id: str, record_id: str) -> Optional[Dict[str, Any]]:
        """
        根据记录ID获取单条记录

        Args:
            table_id: 表格ID
            record_id: 记录ID

        Returns:
            记录信息或None
        """
        endpoint = f"/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/records/{record_id}"
        response = self._make_request('GET', endpoint)

        if response.success and response.data and 'record' in response.data:
            record_data = response.data['record']
            return {
                'record_id': record_data.get('record_id', ''),
                'fields': record_data.get('fields', {})
            }

        return None

    def find_records_by_field(self, table_id: str, field_name: str, field_value: Any) -> List[Dict[str, Any]]:
        """
        根据字段值查找记录

        Args:
            table_id: 表格ID
            field_name: 字段名
            field_value: 要查找的字段值

        Returns:
            匹配的记录列表
        """
        all_records = self.get_all_records(table_id)
        matching_records = []

        for record in all_records:
            if record['fields'].get(field_name) == field_value:
                matching_records.append(record)

        return matching_records

    # ==================== 字段管理功能 ====================
    # 基于原始baseopensdk中的AppTableField API实现
    
    def list_fields(self, table_id: str) -> List[Dict[str, Any]]:
        """
        获取表格所有字段信息
        
        基于原始baseopensdk的AppTableField.list方法
        API路径: /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields
        
        Args:
            table_id: 表格ID
            
        Returns:
            字段信息列表
        """
        endpoint = f"/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/fields"
        response = self._make_request('GET', endpoint)
        
        if response.success and response.data and 'items' in response.data:
            fields = response.data['items']
            self.logger.info(f"成功获取 {len(fields)} 个字段")
            return fields
        else:
            self.logger.error(f"获取字段列表失败: {response.message}")
            return []
    
    def create_field(self, table_id: str, field_name: str, field_type: int, 
                    field_property: Optional[Dict[str, Any]] = None,
                    description: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        创建新字段
        
        基于原始baseopensdk的AppTableField.create方法
        API路径: /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields
        
        Args:
            table_id: 表格ID
            field_name: 字段名称
            field_type: 字段类型（1=多行文本, 2=数字, 3=单选, 4=多选, 5=日期, 7=复选框, 11=人员, 13=电话号码, 15=超链接, 17=附件, 18=单向关联, 19=查找, 20=公式, 21=双向关联, 22=地理位置, 23=群组）
            field_property: 字段属性配置（可选）
            description: 字段描述（可选）
            
        Returns:
            新字段信息或None
            
        Example:
            # 创建多行文本字段
            field = client.create_field("tbl123", "备注", 1)
            
            # 创建单选字段
            property = {
                "options": [
                    {"name": "选项1", "color": 0},
                    {"name": "选项2", "color": 1}
                ]
            }
            field = client.create_field("tbl123", "状态", 3, property)
        """
        # 构建请求体（基于原始baseopensdk的CreateAppTableFieldRequest）
        request_body = {
            "field_name": field_name,
            "type": field_type
        }
        
        if field_property:
            request_body["property"] = field_property
        
        if description:
            request_body["description"] = {"text": description}
        
        endpoint = f"/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/fields"
        response = self._make_request('POST', endpoint, json=request_body)
        
        if response.success and response.data and 'field' in response.data:
            field_data = response.data['field']
            self.logger.info(f"成功创建字段: {field_name} (ID: {field_data.get('field_id', 'N/A')})")
            return field_data
        else:
            self.logger.error(f"创建字段失败: {response.message}")
            return None
    
    def update_field(self, table_id: str, field_id: str, field_name: Optional[str] = None,
                    field_property: Optional[Dict[str, Any]] = None,
                    description: Optional[str] = None) -> bool:
        """
        更新字段信息
        
        基于原始baseopensdk的AppTableField.update方法
        API路径: /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields/{field_id}
        
        Args:
            table_id: 表格ID
            field_id: 字段ID
            field_name: 新字段名称（可选）
            field_property: 新字段属性配置（可选）
            description: 新字段描述（可选）
            
        Returns:
            更新是否成功
        """
        # 构建请求体（基于原始baseopensdk的UpdateAppTableFieldRequest）
        request_body = {}
        
        if field_name:
            request_body["field_name"] = field_name
        
        if field_property:
            request_body["property"] = field_property
        
        if description:
            request_body["description"] = {"text": description}
        
        if not request_body:
            self.logger.warning("更新字段时未提供任何更新内容")
            return False
        
        endpoint = f"/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/fields/{field_id}"
        response = self._make_request('PUT', endpoint, json=request_body)
        
        if response.success:
            self.logger.info(f"成功更新字段: {field_id}")
            return True
        else:
            self.logger.error(f"更新字段失败: {response.message}")
            return False
    
    def delete_field(self, table_id: str, field_id: str) -> bool:
        """
        删除字段（谨慎使用，操作不可逆）
        
        基于原始baseopensdk的AppTableField.delete方法
        API路径: /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields/{field_id}
        
        Args:
            table_id: 表格ID
            field_id: 要删除的字段ID
            
        Returns:
            删除是否成功
        """
        endpoint = f"/open-apis/bitable/v1/apps/{self.app_token}/tables/{table_id}/fields/{field_id}"
        response = self._make_request('DELETE', endpoint)
        
        if response.success:
            self.logger.info(f"成功删除字段: {field_id}")
            return True
        else:
            self.logger.error(f"删除字段失败: {response.message}")
            return False
    
    def get_field_by_name(self, table_id: str, field_name: str) -> Optional[Dict[str, Any]]:
        """
        根据字段名获取字段信息
        
        Args:
            table_id: 表格ID
            field_name: 字段名称
            
        Returns:
            字段信息或None
        """
        fields = self.list_fields(table_id)
        for field in fields:
            if field.get('field_name') == field_name:
                return field
        return None
    
    def ensure_field_exists(self, table_id: str, field_name: str, field_type: int,
                           field_property: Optional[Dict[str, Any]] = None,
                           description: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        确保字段存在，如果不存在则创建
        
        Args:
            table_id: 表格ID
            field_name: 字段名称
            field_type: 字段类型
            field_property: 字段属性配置（可选）
            description: 字段描述（可选）
            
        Returns:
            字段信息或None
        """
        # 先检查字段是否存在
        existing_field = self.get_field_by_name(table_id, field_name)
        if existing_field:
            self.logger.info(f"字段已存在: {field_name}")
            return existing_field
        
        # 字段不存在，创建新字段
        self.logger.info(f"字段不存在，正在创建: {field_name}")
        return self.create_field(table_id, field_name, field_type, field_property, description)