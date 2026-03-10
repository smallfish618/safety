# 消防器材数据库批量更新方案

## 一、方案概述

这是一个完整的、安全的数据库批量更新解决方案，包括以下核心功能：

- ✅ **自动备份**：更新前自动备份数据库和表数据
- ✅ **批量导入**：支持从Excel导入大量数据
- ✅ **数据验证**：导入前后进行数据验证
- ✅ **异常恢复**：出错时自动恢复备份
- ✅ **详细日志**：完整的操作日志记录

## 二、数据库表结构与区域编码

### 重要：区域编码来源

**区域编码不是自由设置的，而是必须来自"微型消防站物资负责人表"（ResponsiblePerson）！**

系统中已有以下有效的区域编码：

| 编码 | 区域名称 |
|------|--------|
| 1 | 信息中心 |
| 2 | 全面通讯部 |
| 3 | 办公楼 |
| 4 | 货运防火公司 |
| 5 | 商业防火公司 |
| 6 | 办公楼 |
| 7 | 航线防火公司 |
| 8 | 航空防火公司 |
| 9 | 航运防火公司 |
| 10 | 港湾防火公司 |
| 11 | 港口区域 |
| 12 | 物流防火公司 |
| 13 | 运营中心 |

**⚠️ 填写数据时，区域编码只能使用上面列表中的编码！**

| 字段名 | 类型 | 说明 | 必填 |
|-------|------|------|------|
| 区域编码 | 整数 | 设备区域编码 | ✓ |
| 区域名称 | 文本 | 设备区域名称 | ✓ |
| 楼层 | 文本 | 安装楼层 | ✓ |
| 安装位置 | 文本 | 具体安装位置 | ✓ |
| 器材类型 | 文本 | 如"灭火器"、"烟感报警器" | ✓ |
| 器材名称 | 文本 | 具体器材名称 | ✓ |
| 型号 | 文本 | 品牌和型号 | ✓ |
| 重量 | 文本 | 如"8kg" | ✓ |
| 数量 | 整数 | 数量 |  |
| 生产日期 | 日期 | YYYY-MM-DD |  |
| 使用年限 | 文本 | 如"5年"、"8年" | ✓ |
| 到期日期 | 文本 | YYYY-MM-DD | ✓ |
| 备注 | 文本 |  |  |

### 2. 微型消防站表（fire_station）

| 字段名 | 类型 | 说明 | 必填 |
|-------|------|------|------|
| 区域编码 | 文本 | 设备区域编码 | ✓ |
| 区域名称 | 文本 | 设备区域名称 | ✓ |
| 物品名称 | 文本 | 物品名称 | ✓ |
| 生产厂家 | 文本 | 生产厂家 |  |
| 型号 | 文本 | 规格型号 |  |
| 数量 | 文本 | 如"2件"、"4组" |  |
| 生产日期 | 日期 | YYYY-MM-DD |  |
| 合格证 | 文本 | "有"或"无" |  |
| 合格证编号 | 文本 | 证号 |  |
| 备注 | 文本 |  |  |

## 三、操作步骤

### 步骤1：生成Excel模板

打开终端，在项目根目录执行：

```bash
python create_excel_template.py
```

输出示例：
```
✓ Excel模板已创建: e:/safety/data/batch_update_template.xlsx
✓ Sheet页签:
  1. 使用说明 - 查看字段说明和注意事项
  2. 消防器材 - 填写消防器材数据
  3. 微型消防站 - 填写微型消防站数据
```

### 步骤2：填写数据

1. 打开生成的Excel文件：`e:/safety/data/batch_update_template.xlsx`
2. **重点：** 查看"**使用说明**"Sheet，找到"有效的区域编码列表"
3. 确保你的数据中的区域编码来自该列表
4. 在"**消防器材**"Sheet填写消防器材数据
5. 在"**微型消防站**"Sheet填写微型消防站数据
6. 保存文件

#### 特别注意：区域编码

```
✓ 必须使用这些有效的区域编码：
  1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13

✗ 不能使用未在"使用说明"页中列出的编码
```

### 步骤3：验证数据（新增重要步骤）

在导入前，强烈建议先验证Excel数据的有效性：

```bash
python validate_excel_data.py
```

这个脚本会检查：
- ✓ 区域编码是否有效
- ✓ 必填字段是否完整
- ✓ 日期格式是否正确
- ✓ 数据的逻辑一致性

**验证通过后再执行导入！**

### 步骤4：执行数据导入

在终端执行：

```bash
python batch_update_database.py
```

#### 执行流程详解：

```
【第1步】备份数据库
├─ 保存完整的数据库文件
└─ 导出表数据为CSV格式

【第2步】清空表数据
├─ 清空消防器材表
└─ 清空微型消防站表

【第3步】导入消防器材数据
├─ 读取Excel数据
├─ 验证和转换格式
└─ 逐行插入数据库

【第4步】导入微型消防站数据
├─ 读取Excel数据
├─ 验证和转换格式
└─ 逐行插入数据库

【第5步】验证导入数据
├─ 统计导入的记录数
└─ 检查数据完整性
```

### 步骤4：确认结果

导入完成后，程序会询问：

```
✓ 数据导入成功！现在是否删除备份？(y/n):
```

- 输入 `y` → 删除备份（节省空间）
- 输入 `n` → 保留备份（更安全）

## 四、备份和恢复

### 备份文件位置

```
e:/safety/data/backups/
├── backup_20240304_153022.db           # 数据库备份
└── backup_20240304_153022/             # CSV备份目录
    ├── fire_equipment_backup.csv       # 消防器材表备份
    └── fire_station_backup.csv         # 微型消防站表备份
```

### 手动恢复（如果导入失败）

如果导入过程中出现错误，程序会自动询问是否恢复：

```
是否恢复备份？(y/n):
```

- 输入 `y` → 自动恢复到更新前的状态
- 输入 `n` → 保持当前状态（可能不完整）

## 五、日志查看

所有操作记录保存在日志文件中：

```
e:/safety/logs/batch_update_YYYYMMDD_HHMMSS.log
```

查看日志示例：

```bash
# PowerShell
Get-Content e:/safety/logs/batch_update_*.log -Tail 100

# 或在VS Code中打开日志文件查看
```

## 六、常见问题

### Q1: Excel文件格式错误怎么办？

**A:** 执行以下步骤：
1. 删除或重命名旧的Excel文件
2. 重新执行 `python create_excel_template.py` 创建新模板
3. 在新模板中填写数据

### Q2: 出现"找不到Excel文件"错误？

**A:** 检查以下项：
1. 确保Excel文件位置是 `e:/safety/data/batch_update_template.xlsx`
2. 确保文件名未修改
3. 如与未创建，先执行 `python create_excel_template.py`

### Q3: 导入失败，数据没有更新，怎么办？

**A:** 
1. 进程会自动提示是否恢复备份
2. 输入 `y` 自动恢复到备份状态
3. 查看日志文件找出具体错误原因：`e:/safety/logs/batch_update_*.log`
4. 修正Excel数据后重新尝试

### Q4: 可以只更新其中一个表吗？

**A:** 可以修改脚本，在 `batch_update_database.py` 中：
- 只需要注释掉不需要的导入函数调用
- 或创建新的脚本文件调用相应函数

### Q5: 导入后如何验证数据正确性？

**A:** 
1. 登入系统查看数据展示页面
2. 查看导入日志确认导入数量
3. 对比备份的CSV文件验证数据

## 七、高级操作

### 创建自定义备份

如果想在导入前创建额外备份：

```bash
# 在Python脚本中执行
from batch_update_database import DatabaseUpdater

updater = DatabaseUpdater()
backup_path = updater.backup_database()
print(f"备份已创建: {backup_path}")
```

### 只导入部分数据

修改 `batch_update_database.py`，注释掉不需要的表：

```python
# 在 run_full_update 方法中

# 注释掉不需要的导入
# equip_success, equip_error, equip_errors = self.import_equipment_data(excel_path)

# 保留需要的导入
station_success, station_error, station_errors = self.import_station_data(excel_path)
```

### 导出当前数据

```bash
# 导出为CSV
python -c "
import sys
sys.path.insert(0, '.')
from app import create_app, db
from app.models.equipment import FireEquipment, FireStation
import pandas as pd

app = create_app()
with app.app_context():
    equip = pd.read_sql_table('fire_equipment', db.engine)
    station = pd.read_sql_table('fire_station', db.engine)
    
    equip.to_csv('equipment_current.csv', index=False, encoding='utf-8-sig')
    station.to_csv('station_current.csv', index=False, encoding='utf-8-sig')
    
    print('✓ 数据已导出')
"
```

## 八、操作总结

| 操作步骤 | 命令 | 预期结果 |
|---------|------|---------|
| 1. 生成模板 | `python create_excel_template.py` | 创建Excel文件 |
| 2. 填写数据 | 手工在Excel中填写数据 | 准备好导入数据 |
| 3. 执行导入 | `python batch_update_database.py` | 完成数据库更新 |
| 4. 验证数据 | 登入系统查看 | 确认数据正确 |
| 5. 清理备份 | 根据提示选择是否删除 | 可选操作 |

## 九、安全建议

1. **导入前备份**：程序会自动备份，无需手动操作
2. **保留备份**：建议保留至少一周的备份数据
3. **验证数据**：导入后立即检查数据完整性
4. **记录日志**：保存导入日志以备查证
5. **分阶段导入**：如果数据量很大，可分批导入
6. **测试环境**：首次大批量导入建议先在测试库中验证

## 十、技术支持

如遇到问题，请：

1. 查看日志文件：`e:/safety/logs/batch_update_*.log`
2. 检查Excel文件格式和数据
3. 确认数据库连接状态
4. 查看此文档的常见问题部分

---

**最后更新**: 2024年3月4日
**版本**: 1.0
