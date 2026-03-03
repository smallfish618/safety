#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
诊断邮件发送问题 - 检查负责人邮箱数据
"""
import sys
from app import create_app, db
from app.models.station import ResponsiblePerson
from app.models.equipment import FireEquipment

app = create_app()

with app.app_context():
    # 检查负责人表
    print("=" * 60)
    print("检查 ResponsiblePerson 表")
    print("=" * 60)
    
    responsible_persons = ResponsiblePerson.query.all()
    print(f"\n总负责人数: {len(responsible_persons)}")
    
    if responsible_persons:
        print("\n负责人详情:")
        print(f"{'ID':<5} {'姓名':<15} {'邮箱':<30} {'区域':<15}")
        print("-" * 65)
        
        for person in responsible_persons:
            email_status = "✓ 有效" if (person.email and '@' in person.email) else "✗ 无效/空"
            print(f"{person.id:<5} {person.person_name:<15} {(person.email or 'N/A'):<30} {(person.area_name or 'N/A'):<15}")
            
    else:
        print("\n❌ 没有找到任何负责人记录！")
    
    # 统计邮箱有效性
    print("\n" + "=" * 60)
    print("邮箱有效性统计")
    print("=" * 60)
    
    valid_emails = 0
    invalid_emails = 0
    empty_emails = 0
    
    for person in responsible_persons:
        if not person.email:
            empty_emails += 1
        elif '@' in person.email:
            valid_emails += 1
        else:
            invalid_emails += 1
    
    print(f"有效邮箱: {valid_emails} 个")
    print(f"无效邮箱: {invalid_emails} 个")
    print(f"空邮箱: {empty_emails} 个")
    print(f"总计: {len(responsible_persons)} 个")
    
    # 检查物品数据中的负责人
    print("\n" + "=" * 60)
    print("检查物品中的负责人关联")
    print("=" * 60)
    
    station_items = db.session.query(
        "SELECT DISTINCT area_code, area_name FROM fire_station"
    ).all()
    
    print(f"\n微型站物资中的不同区域: {len(station_items)} 个")
    
    # 创建area_code到负责人的映射
    responsible_dict = {}
    for person in responsible_persons:
        responsible_dict[person.area_code] = person.person_name
    
    print("\n区域与负责人关联:")
    print(f"{'区域代码':<15} {'区域名称':<20} {'对应负责人':<20}")
    print("-" * 55)
    
    for person in responsible_persons:
        print(f"{(person.area_code or 'N/A'):<15} {(person.area_name or 'N/A'):<20} {person.person_name:<20}")
    
    # 测试邮件发送配置
    print("\n" + "=" * 60)
    print("邮件服务器配置检查")
    print("=" * 60)
    
    from flask import current_app
    
    mail_config = {
        'MAIL_SERVER': current_app.config.get('MAIL_SERVER'),
        'MAIL_PORT': current_app.config.get('MAIL_PORT'),
        'MAIL_USERNAME': current_app.config.get('MAIL_USERNAME'),
        'MAIL_USE_SSL': current_app.config.get('MAIL_USE_SSL', False),
        'MAIL_USE_TLS': current_app.config.get('MAIL_USE_TLS', False),
        'MAIL_DEFAULT_SENDER': current_app.config.get('MAIL_DEFAULT_SENDER'),
    }
    
    for key, value in mail_config.items():
        if key == 'MAIL_USERNAME':
            print(f"{key}: {value}")
        elif key == 'MAIL_DEFAULT_SENDER':
            print(f"{key}: {value}")
        else:
            print(f"{key}: {value}")
    
    # 检查密码
    import os
    mail_password = current_app.config.get('MAIL_PASSWORD')
    env_password = os.environ.get('MAIL_PASSWORD')
    
    if mail_password:
        print(f"MAIL_PASSWORD: 已设置（配置文件）")
    elif env_password:
        print(f"MAIL_PASSWORD: 已设置（环境变量）")
    else:
        print(f"MAIL_PASSWORD: ❌ 未设置")
    
    print("\n" + "=" * 60)
    print("诊断完成！")
    print("=" * 60)
