#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速修复邮件发送问题 - 为所有负责人设置默认邮箱
"""
import sqlite3
import os
import sys

# 数据库文件路径
possible_paths = [
    'data/database.db',
    './data/database.db',
    'e:\\safety\\data\\database.db',
]

db_path = None
for path in possible_paths:
    if os.path.exists(path):
        db_path = path
        break

if not db_path:
    print("错误: 找不到数据库文件")
    print(f"尝试过的路径: {possible_paths}")
    sys.exit(1)

print(f"\n使用数据库: {db_path}\n")

# 连接到数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 70)
print("负责人邮箱快速修复程序")
print("=" * 70)

# 查询当前的负责人邮箱情况
cursor.execute("""
    SELECT id, person_name, email, contact 
    FROM responsible_person 
    ORDER BY id
""")

rows = cursor.fetchall()
print(f"\n找到 {len(rows)} 个负责人\n")

# 显示当前邮箱信息
print("当前邮箱信息:")
print(f"{'ID':<5} {'姓名':<15} {'邮箱':<30} {'联系方式':<15}")
print("-" * 65)

people_without_email = []
for row in rows:
    person_id, name, email, contact = row
    if not email or '@' not in email:
        people_without_email.append((person_id, name, contact))
    print(f"{person_id:<5} {name:<15} {(email or '(空)'):<30} {(contact or 'N/A'):<15}")

print(f"\n缺少/无效邮箱的负责人: {len(people_without_email)} 个")

# 询问用户是否要进行修复
if people_without_email:
    print("\n" + "=" * 70)
    print("修复选项:")
    print("=" * 70)
    print("""
1. 为所有负责人设置一个统一的默认邮箱地址（用于测试）
2. 手动为每个负责人设置邮箱地址
3. 退出
    """)
    
    choice = input("请选择 (1/2/3): ").strip()
    
    if choice == '1':
        default_email = input("\n请输入默认邮箱地址 (例如: admin@example.com): ").strip()
        
        if '@' not in default_email:
            print("❌ 邮箱格式无效，需要包含@符号")
            sys.exit(1)
        
        print(f"\n将要为以下负责人设置邮箱: {default_email}\n")
        
        for person_id, name, contact in people_without_email:
            print(f"  - {name}")
        
        confirm = input("\n确认修改？ (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            # 执行更新
            for person_id, name, contact in people_without_email:
                cursor.execute(
                    "UPDATE responsible_person SET email = ? WHERE id = ?",
                    (default_email, person_id)
                )
            
            conn.commit()
            print(f"\n✓ 已成功为 {len(people_without_email)} 个负责人设置邮箱地址")
            print(f"  邮箱地址: {default_email}")
        else:
            print("已取消修改")
            sys.exit(0)
    
    elif choice == '2':
        print("\n请为以下负责人依次输入邮箱:\n")
        
        for person_id, name, contact in people_without_email:
            while True:
                email = input(f"{name} ({contact or '无电话'}) 的邮箱: ").strip()
                if '@' not in email:
                    print("❌ 邮箱格式无效，需要包含@符号，请重新输入")
                    continue
                break
            
            cursor.execute(
                "UPDATE responsible_person SET email = ? WHERE id = ?",
                (email, person_id)
            )
        
        conn.commit()
        print(f"\n✓ 已成功为 {len(people_without_email)} 个负责人设置邮箱地址")
    
    else:
        print("已退出")
        sys.exit(0)
else:
    print("\n✓ 所有负责人都有有效的邮箱地址，无需修复\n")

# 显示修改后的结果
print("\n" + "=" * 70)
print("修改后的邮箱信息:")
print("=" * 70 + "\n")

cursor.execute("""
    SELECT id, person_name, email, contact 
    FROM responsible_person 
    ORDER BY id
""")

rows = cursor.fetchall()
print(f"{'ID':<5} {'姓名':<15} {'邮箱':<30} {'联系方式':<15}")
print("-" * 65)

valid_count = 0
for row in rows:
    person_id, name, email, contact = row
    if email and '@' in email:
        valid_count += 1
    print(f"{person_id:<5} {name:<15} {(email or '(空)'):<30} {(contact or 'N/A'):<15}")

print(f"\n✓ 有有效邮箱的负责人: {valid_count}/{len(rows)}\n")

conn.close()

print("=" * 70)
print("修复完成！现在可以尝试发送预警邮件了。")
print("=" * 70 + "\n")
