#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复邮件发送问题 - 为负责人添加邮箱地址
"""
import sqlite3
import os

# 数据库文件路径 - 尝试多个可能的位置
possible_paths = [
    'data/database.db',
    './data/database.db',
    'e:\\safety\\data\\database.db',
    'instance/safety.db',
    './instance/safety.db',
    'e:\\safety\\instance\\safety.db',
    'safety.db'
]

db_path = None
for path in possible_paths:
    if os.path.exists(path):
        db_path = path
        break

if not db_path:
    print("错误: 找不到数据库文件")
    print(f"尝试过的路径: {possible_paths}")
    exit(1)

print(f"使用数据库: {db_path}")

# 连接到数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 70)
print("检查负责人表中的邮箱信息")
print("=" * 70)

# 查询负责人表
cursor.execute("""
    SELECT id, person_name, email, contact, area_name 
    FROM responsible_person 
    ORDER BY id
""")

rows = cursor.fetchall()
print(f"\n总负责人数: {len(rows)}")

# 统计邮箱情况
people_without_email = []
people_with_email = []

print("\n负责人详情:")
print(f"{'ID':<5} {'姓名':<15} {'邮箱':<30} {'联系方式':<15} {'区域':<15}")
print("-" * 80)

for row in rows:
    person_id, name, email, contact, area = row
    print(f"{person_id:<5} {name:<15} {(email or '(空)'  ):<30} {(contact or 'N/A'):<15} {(area or 'N/A'):<15}")
    
    if not email or '@' not in email:
        people_without_email.append((person_id, name, contact))
    else:
        people_with_email.append((person_id, name, email))

print("\n" + "=" * 70)
print("邮箱统计")
print("=" * 70)
print(f"有效邮箱: {len(people_with_email)} 个")
print(f"缺少/无效邮箱: {len(people_without_email)} 个")

if people_without_email:
    print("\n需要修复的负责人:")
    print(f"{'ID':<5} {'姓名':<15} {'联系方式':<15}")
    print("-" * 35)
    for person_id, name, contact in people_without_email:
        print(f"{person_id:<5} {name:<15} {(contact or 'N/A'):<15}")
        
    print("\n" + "=" * 70)
    print("修复建议")
    print("=" * 70)
    print("""
根据分析，以下是修复步骤：

1. 访问管理后台的"物资负责人信息"页面
2. 编辑每个负责人，为其添加正确的邮箱地址
3. 邮箱格式必须包含 @ 符号，例如: user@example.com

也可以使用以下SQL语句为示例数据添加邮箱：
    """)
    
    # 生成示例UPDATE语句
    print("\n# 示例SQL更新语句（请根据实际情况修改邮箱地址）:")
    for person_id, name, contact in people_without_email:
        # 根据姓名生成一个示例邮箱（实际应该用真实的邮箱）
        example_email = f"{name}@example.com"
        print(f"UPDATE responsible_person SET email = '{example_email}' WHERE id = {person_id};")
else:
    print("\n✓ 所有负责人都有有效的邮箱地址，无需修复！")

print("\n" + "=" * 70)

conn.close()
