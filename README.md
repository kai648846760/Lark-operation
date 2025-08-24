# Lark多维表格接口自动化测试框架

> 基于飞书(Lark)多维表格的现代化接口自动化测试解决方案

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Lark](https://img.shields.io/badge/Platform-Lark-orange.svg)](https://www.larksuite.com/)

## 🎯 项目简介

这是一个创新的接口自动化测试框架，将测试用例管理与飞书多维表格深度集成，实现了**可视化测试管理**和**实时结果回写**。通过表格化的测试用例管理，让非技术人员也能轻松参与接口测试，同时为技术团队提供强大的自动化执行能力。

### ✨ 核心特性

- 🔥 **零学习成本**: 在熟悉的多维表格中管理测试用例
- 🚀 **现代化架构**: 基于原始baseopensdk重构，支持最新Python版本
- 🔐 **简化认证**: 只需personal_token，无需复杂应用配置
- 📊 **实时回写**: 测试结果自动回写到表格，形成完整数据闭环
- 🎨 **可视化报告**: 利用Lark图表功能展示测试趋势
- 🔧 **字段管理**: 完整的字段CRUD操作，支持动态表格改造
- 📝 **精简设计**: 13个核心字段，简洁高效易维护

## 🎉 精简表格设计

经过深度优化，框架采用**精简优先**的设计理念，将字段从31个精简至13个核心字段：

### 🎯 核心测试字段 (11个)

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| 接口编号 | 自动编号 | 【系统生成】唯一标识符 | 1, 2, 3... |
| 接口名称 | 文本 | 【必填】功能描述 | 用户登录接口 |
| 接口路径 | 文本 | 【必填】API路径 | /api/auth/login |
| 请求方法 | 单选 | 【必填】HTTP方法 | POST |
| 请求头 | 多行文本 | 【可选】JSON格式 | {"Content-Type": "application/json"} |
| 请求体 | 多行文本 | 【可选】JSON格式 | {"username": "test", "password": "123456"} |
| 预期状态码 | 数字 | 【必填】期望状态码 | 200 |
| 响应状态码 | 文本 | 【系统填写】实际状态码 | 200 |
| 响应体 | 多行文本 | 【系统填写】响应数据 | {"code": "00000", "data": {...}} |
| 断言规则 | 多行文本 | 【可选】验证规则 | {"status_code": "== 200"} |
| 是否通过 | 单选 | 【系统填写】测试结果 | 通过/失败 |

### 📝 辅助管理字段 (2个)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 是否启用 | 复选框 | 【用户控制】测试用例开关 |
| 备注 | 多行文本 | 【可选】补充说明信息 |

## 🚀 快速开始

### 📋 环境要求

- **Python**: 3.8+ 
- **飞书账号**: 具备多维表格访问权限
- **网络**: 能访问 `https://open.larksuite.com`

### ⚡ 快速安装

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/Lark-operation.git
cd Lark-operation

# 2. 安装依赖
pip install -r requirements.txt

# 3. 验证安装
python -m lark_tester.cli --version
```

### 🔐 认证配置

#### 步骤1: 获取授权码

1. 打开你的飞书多维表格
2. 点击右上角 **「插件」** → **「自定义插件」**
3. 选择 **「获取授权码」**
4. 复制生成的 `personal_token`（以`pt-`开头）

#### 步骤2: 配置文件

编辑 `config/production.yaml`：

```yaml
lark:
  # 必填：个人授权码
  personal_token: "pt-your-personal-token-here"  
  
  # 必填：应用Token（从表格URL提取）
  app_token: "your-app-token"  
  
  # 必填：表格ID（从表格URL提取）
  table_id: "your-table-id"   
  
  # 可选：API域名（默认国际版）
  api_domain: "https://open.larksuite.com"  

log:
  level: "INFO"
  format: "%(asctime)s - %(levelname)s - %(message)s"
```

#### 步骤3: 从URL提取配置信息

多维表格URL格式：
```
https://domain.larksuite.com/base/APP_TOKEN?table=TABLE_ID&view=VIEW_ID
```

- `APP_TOKEN`: 位于 `/base/` 和 `?table=` 之间
- `TABLE_ID`: 位于 `?table=` 和 `&view=` 之间

### 🎯 运行测试

```bash
# 执行所有启用的测试用例
python -m lark_tester.cli

# 执行特定编号的测试用例
python -m lark_tester.cli --test-id 1

# 启用详细日志
python -m lark_tester.cli --verbose

# 验证表格结构
python -m lark_tester.cli --validate
```

## 📊 使用指南

### 🔥 基础用例示例

在多维表格中创建测试用例：

```
接口名称: 用户登录接口
接口路径: /api/auth/login
请求方法: POST
请求头: 
{
  "Content-Type": "application/json",
  "User-Agent": "ApiTest/1.0"
}

请求体:
{
  "username": "test_user",
  "password": "123456"
}

预期状态码: 200
断言规则:
{
  "status_code": "== 200",
  "response_json": {
    "$.code": "== '00000'",
    "$.data.token": "!= null"
  }
}

是否启用: ☑️
备注: 基础登录功能测试
```

### 🎭 断言规则详解

框架支持多种断言方式：

```json
{
  // HTTP状态码断言
  "status_code": "== 200",
  
  // 响应时间断言（毫秒）
  "response_time": "< 1000",
  
  // JSONPath响应内容断言
  "response_json": {
    "$.code": "== '00000'",           // 精确匹配
    "$.data.token": "!= null",        // 非空验证
    "$.data.user.id": "> 0",          // 数值比较
    "$.message": "contains '成功'",    // 包含文本
    "$.data.list": "length > 0"      // 数组长度
  }
}
```

### 🔧 高级功能

#### 变量引用（代码层面实现）

框架支持强大的变量引用功能：

```
// 环境变量引用
接口路径: ${env.base_url}/api/user/profile

// 运行时变量引用  
请求头: {"Authorization": "Bearer ${runtime.access_token}"}

// 函数调用
请求体: {"request_id": "${func.uuid()}", "timestamp": ${func.timestamp()}}
```

支持的内置函数：
- `${func.uuid()}` - 生成UUID
- `${func.timestamp()}` - 当前时间戳
- `${func.random(1,100)}` - 随机数
- `${func.datetime()}` - 当前日期时间

## 🏗️ 项目架构

```
Lark-operation/
├── lark_tester/                 # 核心框架
│   ├── core/                   # 核心模块
│   │   ├── lark_client.py      # Lark API客户端（基于原始SDK重构）
│   │   ├── test_executor.py    # 测试执行引擎
│   │   ├── config_manager.py   # 配置管理器
│   │   └── result_manager.py   # 结果回写管理器
│   ├── utils/                  # 工具模块
│   │   ├── logger.py          # 日志工具
│   │   └── validator.py       # 数据验证器
│   └── cli.py                 # 命令行接口
├── config/                     # 配置文件
│   ├── production.yaml        # 生产环境配置
│   └── development.yaml       # 开发环境配置
├── docs/                      # 文档
│   ├── field_usage_guide.md   # 字段使用指南
│   └── context_management_design.md  # 上下文设计
├── examples/                  # 示例代码
└── scripts/                   # 工具脚本
    └── validate_table.py      # 表格验证脚本
```

## 🔧 核心技术特性

### 💪 现代化SDK重构

- **完全兼容**: 保持与原始baseopensdk的认证逻辑一致
- **现代化实现**: 使用requests库替代过时依赖
- **字段管理**: 支持字段的创建、删除、更新、查询操作
- **类型安全**: 严格的字段类型验证和转换

### 🎯 精简设计理念

基于**渐进式功能扩展**原则：

1. **简洁优先**: 13个核心字段满足80%的测试需求
2. **按需扩展**: 复杂功能通过代码层面实现
3. **用户友好**: 新手可快速上手，专家有扩展空间
4. **维护简单**: 字段少、逻辑清晰、文档完整

### 🚀 字段管理API

基于原始baseopensdk的字段管理功能：

```python
from lark_tester.core.lark_client import LarkClient

client = LarkClient(personal_token="pt-xxx", app_token="xxx")

# 创建字段
field = client.create_field(
    table_id="tbl123",
    field_name="新字段",
    field_type=1,  # 多行文本
    description="字段描述"
)

# 列出所有字段
fields = client.list_fields("tbl123")

# 更新字段
client.update_field("tbl123", "fld456", field_name="更新后的字段名")

# 删除字段
client.delete_field("tbl123", "fld456")
```

## 📖 详细文档

- **[字段使用指南](field_usage_guide.md)** - 详细的字段说明和最佳实践
- **[上下文管理设计](context_management_design.md)** - 变量管理和引用功能设计
- **[API文档](docs/api.md)** - 完整的API接口文档
- **[故障排除](docs/troubleshooting.md)** - 常见问题解决方案

## 🛠️ 开发指南

### 环境设置

```bash
# 克隆项目
git clone <repository-url>
cd Lark-operation

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 运行测试
python -m pytest tests/
```

### 代码规范

- **PEP 8**: Python代码风格标准
- **类型提示**: 使用type hints提高代码可读性
- **文档字符串**: 所有公共方法都要有docstring
- **单元测试**: 核心功能必须有测试覆盖

### 贡献流程

1. Fork项目到个人仓库
2. 创建功能分支: `git checkout -b feature/新功能`
3. 编写代码和测试
4. 确保所有测试通过: `python -m pytest`
5. 提交代码: `git commit -m "Add: 新功能描述"`
6. 推送分支: `git push origin feature/新功能`
7. 创建Pull Request

## 🐛 故障排除

### 常见问题

#### 1. 认证失败
```
错误: invalid access token (20005)
解决: 
- 检查personal_token是否正确
- 确认token未过期
- 验证表格访问权限
```

#### 2. 字段不匹配
```
错误: FieldNameNotFound
解决:
- 确保表格字段名与框架要求完全一致
- 检查字段是否已创建
- 使用validate命令验证表格结构
```

#### 3. 网络连接问题
```
错误: Connection timeout
解决:
- 检查网络连接
- 确认API域名配置正确
- 尝试使用代理
```

### 调试模式

```bash
# 启用详细日志
LARK_DEBUG=true python -m lark_tester.cli

# 验证配置
python -m lark_tester.cli --validate

# 测试连接
python -c "from lark_tester.core import LarkClient; print('连接正常')"
```

## 📈 性能与限制

### API限制

- **请求频率**: 建议不超过10次/秒
- **数据量**: 单次最多200条记录
- **字段数量**: 建议不超过50个字段
- **Token有效期**: 通常90天，需定期更新

### 性能优化

- **批量操作**: 使用批量API减少请求次数
- **缓存机制**: 字段信息本地缓存
- **异步执行**: 大量用例可考虑并发执行
- **分页处理**: 大数据集自动分页加载

## 🏆 版本历史

### v2.0.0 (2024-12-25)
- 🎉 **重大更新**: 表格字段从31个精简至13个
- 🔧 **字段管理**: 完整的字段CRUD操作支持
- 🚀 **性能优化**: 基于原始baseopensdk重构
- 📝 **文档完善**: 详细的使用指南和最佳实践

### v1.5.0 (2024-11-20)
- ✨ 新增断言规则支持
- 🔧 改进错误处理机制
- 📊 优化结果回写性能

### v1.0.0 (2024-10-15)
- 🎉 首个正式版本发布
- 🏗️ 基础框架搭建完成
- 📋 核心功能实现

## 🤝 社区支持

### 获取帮助

- **GitHub Issues**: [提交问题](https://github.com/your-repo/issues)
- **讨论区**: [参与讨论](https://github.com/your-repo/discussions)
- **Wiki**: [查看Wiki](https://github.com/your-repo/wiki)

### 贡献方式

- 🐛 **报告Bug**: 通过Issues报告问题
- ✨ **功能建议**: 提出新功能想法
- 📝 **改进文档**: 完善文档和示例
- 💻 **代码贡献**: 提交代码改进

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

感谢以下项目和贡献者：

- **飞书开放平台**: 提供强大的API支持
- **baseopensdk**: 原始SDK实现参考
- **requests**: 现代化HTTP库
- **所有贡献者**: 让这个项目变得更好

---

<div align="center">

**🚀 让接口自动化测试变得简单而强大 🚀**

*基于飞书多维表格的现代化测试解决方案*

[快速开始](#-快速开始) • [使用指南](#-使用指南) • [API文档](docs/api.md) • [贡献指南](#-开发指南)

</div>