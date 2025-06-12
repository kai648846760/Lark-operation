# Lark-operation

```python
pip install https://lf3-static.bytednsdoc.com/obj/eden-cn/lmeh7phbozvhoz/base-open-sdk/baseopensdk-0.0.13-py3-none-any.whl

pip3 install legacy-cgi 
```


```python-repl
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

    # 4. 删除记录（删 - 谨慎使用，默认注释）
                print("\n===== 示例3: 删除记录 =====")
                delete_record_id = record["record_id"]
                print(f"⚠️ 准备删除记录: {delete_record_id}")

    if lark.delete_record(TABLE_ID, delete_record_id):
                    print(f"✅ 记录{delete_record_id}删除成功")
                else:
                    print(f"❌ 记录{delete_record_id}删除失败")
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

```
