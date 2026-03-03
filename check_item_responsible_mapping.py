#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查物品与负责人的关联
"""
import sqlite3
import os
import sys

# 数据库文件路径
db_path = 'data/database.db'

if not os.path.exists(db_path):
    print(f"错误: 找不到数据库文件 {db_path}")
    sys.exit(1)

print(f"使用数据库: {db_path}\n")

# 连接到数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 70)
print("物品与负责人关联检查")
print("=" * 70)

# 检查微型站物资
print("\n【微型站物资 (fire_station)】")
print("-" * 70)

cursor.execute("""
    SELECT COUNT(*) as total,
           COUNT(DISTINCT area_code) as unique_areas
    FROM fire_station
""")

total, unique_areas = cursor.fetchone()
print(f"总物品数: {total}")
print(f"不同的区域编码: {unique_areas}")

# 列出各个区域的统计
cursor.execute("""
    SELECT area_code, area_name, COUNT(*) as count
    FROM fire_station
    GROUP BY area_code, area_name
    ORDER BY area_code
""")

print(f"\n{'区域编码':<10} {'区域名':<20} {'物品数':<10}")
print("-" * 40)
for row in cursor.fetchall():
    area_code, area_name, count = row
    print(f"{(area_code or 'NULL'):<10} {(area_name or 'NULL'):<20} {count:<10}")

# 检查消防器材
print("\n【消防器材 (fire_equipment)】")
print("-" * 70)

cursor.execute("""
    SELECT COUNT(*) as total,
           COUNT(DISTINCT area_code) as unique_areas
    FROM fire_equipment
""")

total2, unique_areas2 = cursor.fetchone()
print(f"总物品数: {total2}")
print(f"不同的区域编码: {unique_areas2}")

# 列出各个区域的统计
cursor.execute("""
    SELECT area_code, area_name, COUNT(*) as count
    FROM fire_equipment
    GROUP BY area_code, area_name
    ORDER BY area_code
""")

print(f"\n{'区域编码':<10} {'区域名':<20} {'設備数':<10}")
print("-" * 40)
for row in cursor.fetchall():
    area_code, area_name, count = row
    print(f"{(area_code or 'NULL'):<10} {(area_name or 'NULL'):<20} {count:<10}")

# 检查负责人与物品的匹配
print("\n【负责人与物品的区域匹配】")
print("-" * 70)

cursor.execute("""
    SELECT rp.id, rp.area_code, rp.person_name, rp.area_name, rp.email
    FROM responsible_person rp
    ORDER BY rp.area_code
""")

responsible_persons = cursor.fetchall()

for rp_id, area_code, person_name, person_area, email in responsible_persons:
    # 查找微型站物资中的匹配
    cursor.execute(
        "SELECT COUNT(*) FROM fire_station WHERE area_code = ?",
        (area_code,)
    )
    station_count = cursor.fetchone()[0]
    
    # 查找消防器材中的匹配
    cursor.execute(
        "SELECT COUNT(*) FROM fire_equipment WHERE area_code = ?",
        (str(area_code) if area_code else None,)
    )
    equipment_count = cursor.fetchone()[0]
    
    status = "✓" if (station_count > 0 or equipment_count > 0) else "⚠"
    print(f"{status} {person_name:<15} (区域代码: {area_code:<10}) - 微型站: {station_count}, 消防器材: {equipment_count}")

# 总结
print("\n" + "=" * 70)
print("总结")
print("=" * 70)
print(f"总负责人数: {len(responsible_persons)}")
print(f"微型站物资总数: {total}")
print(f"消防器材总数: {total2}")
print(f"\n若上面有 ⚠ 符号，说明该负责人没有对应区域的物品")

conn.close()
