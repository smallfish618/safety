#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查邮件日志 - 验证邮件是否成功发送
"""

import sqlite3
import os
from datetime import datetime, timedelta

def check_mail_logs():
    """检查最近的邮件日志"""
    db_path = os.path.join('data', 'database.db')
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查邮件日志表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('mail_log', 'mail_logs')")
        if not cursor.fetchone():
            print("❌ 邮件日志表不存在")
            return
        
        # 查询最近30分钟的邮件记录
        time_limit = (datetime.now() - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            SELECT id, sender, recipient_name, recipient, subject, status, error_message, send_time
            FROM mail_logs
            WHERE send_time > ?
            ORDER BY send_time DESC
            LIMIT 20
        """, (time_limit,))
        
        logs = cursor.fetchall()
        
        if not logs:
            print("\n📭 最近30分钟内没有邮件发送记录")
            print("\n💡 建议：在web界面发送邮件后再运行此脚本")
        else:
            print("\n📧 最近的邮件发送记录（最近30分钟）：")
            print("=" * 120)
            print(f"{'ID':<5} {'发件人':<20} {'收件人名':<12} {'邮箱':<25} {'状态':<8} {'发送时间':<20}")
            print("-" * 120)
            
            success_count = 0
            failure_count = 0
            
            for log in logs:
                log_id, sender, recipient_name, recipient, subject, status, error_msg, send_time = log
                status_display = "✅ 成功" if status == "success" else "❌ 失败"
                
                if status == "success":
                    success_count += 1
                else:
                    failure_count += 1
                
                print(f"{log_id:<5} {sender:<20} {recipient_name:<12} {recipient:<25} {status_display:<8} {send_time:<20}")
                
                # 如果失败，显示错误信息
                if status == "failed" and error_msg:
                    print(f"       └─ 错误: {error_msg}")
            
            print("=" * 120)
            print(f"\n📊 统计信息:")
            print(f"   ✅ 成功: {success_count} 条")
            print(f"   ❌ 失败: {failure_count} 条")
            print(f"   📈 总计: {len(logs)} 条")
            
            # 显示最新的邮件详情（如果存在失败）
            if failure_count > 0:
                print("\n⚠️  最新失败的邮件详情：")
                for log in logs:
                    if log[5] == 'failed':
                        print(f"   收件人: {log[2]} ({log[3]})")
                        print(f"   主题: {log[4]}")
                        print(f"   错误: {log[6]}")
                        print(f"   时间: {log[7]}")
                        break
            
        conn.close()
        
    except Exception as e:
        print(f"❌ 查询邮件日志时出错: {e}")

if __name__ == "__main__":
    print("🔍 邮件日志检查工具")
    print("=" * 120)
    check_mail_logs()
