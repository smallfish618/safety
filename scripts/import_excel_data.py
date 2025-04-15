import os
import sys
import pandas as pd
from datetime import datetime
import sqlite3
import traceback
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入应用上下文
from app import create_app, db
from app.models.equipment import FireEquipment

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_excel_data():
    """从Excel文件导入消防器材数据到数据库"""
    try:
        # 设置文件路径
        excel_path = 'E:/safety/data/excel/消防器材汇总表.xlsx'
        
        # 确保Excel文件存在
        if not os.path.exists(excel_path):
            logger.error(f"Excel文件不存在: {excel_path}")
            return
        
        # 读取Excel文件
        logger.info(f"正在读取Excel文件: {excel_path}")
        df = pd.read_excel(excel_path)
        
        # 显示Excel文件的基本信息
        logger.info(f"Excel文件包含 {len(df)} 行数据和 {len(df.columns)} 列")
        logger.info(f"Excel文件列名: {df.columns.tolist()}")
        
        # 创建Flask应用上下文
        app = create_app()
        with app.app_context():
            # 检查数据库中是否已有数据
            existing_count = FireEquipment.query.count()
            
            if existing_count > 0:
                user_input = input(f"数据库中已存在 {existing_count} 条记录，是否继续导入？(y/n): ").lower()
                if user_input != 'y':
                    logger.info("导入已取消")
                    return
            
            # 开始导入数据
            success_count = 0
            error_count = 0
            
            # 尝试将Excel列名与数据库字段映射
            # 根据实际Excel文件调整这个映射关系
            column_mapping = {
                '区域编码': 'area_code',
                '区域名称': 'area_name',
                '楼层': 'installation_floor',
                '安装位置': 'installation_location',
                '器材类型': 'equipment_type',
                '器材名称': 'equipment_name',
                '型号': 'model',
                '重量': 'weight',
                '数量': 'quantity',
                '生产日期': 'production_date',
                '使用年限': 'service_life',
                '到期日期': 'expiration_date',
                '备注': 'remark'
            }
            
            # 显示列映射
            logger.info("列映射关系:")
            for excel_col, db_col in column_mapping.items():
                logger.info(f"{excel_col} -> {db_col}")
            
            # 处理每一行数据
            for idx, row in df.iterrows():
                try:
                    # 创建数据字典
                    data = {}
                    
                    # 映射Excel列到数据库字段
                    for excel_col, db_col in column_mapping.items():
                        if excel_col in df.columns:
                            data[db_col] = row[excel_col]
                    
                    # 处理日期格式
                    if 'production_date' in data and pd.notna(data['production_date']):
                        # 如果是日期类型，转换为datetime对象
                        if isinstance(data['production_date'], (datetime, pd.Timestamp)):
                            data['production_date'] = data['production_date'].date()
                        # 如果是字符串类型，尝试解析
                        elif isinstance(data['production_date'], str):
                            try:
                                data['production_date'] = datetime.strptime(data['production_date'], '%Y-%m-%d').date()
                            except ValueError:
                                # 尝试其他可能的日期格式
                                formats = ['%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y', '%m-%d-%Y', '%m/%d/%Y']
                                for fmt in formats:
                                    try:
                                        data['production_date'] = datetime.strptime(data['production_date'], fmt).date()
                                        break
                                    except ValueError:
                                        continue
                                else:
                                    # 如果所有格式都失败，设为None
                                    data['production_date'] = None
                    else:
                        data['production_date'] = None
                    
                    # 确保数值字段类型正确
                    if 'area_code' in data and pd.notna(data['area_code']):
                        data['area_code'] = int(data['area_code'])
                    else:
                        data['area_code'] = 0  # 默认值
                    
                    if 'quantity' in data and pd.notna(data['quantity']):
                        data['quantity'] = int(data['quantity'])
                    else:
                        data['quantity'] = 1  # 默认值
                    
                    # 确保字符串字段不为None
                    text_fields = ['area_name', 'installation_floor', 'installation_location',
                                   'equipment_type', 'equipment_name', 'model', 'weight',
                                   'service_life', 'expiration_date', 'remark']
                    
                    for field in text_fields:
                        if field not in data or pd.isna(data[field]):
                            data[field] = ''  # 默认为空字符串
                    
                    # 创建新记录
                    equipment = FireEquipment(**data)
                    db.session.add(equipment)
                    
                    # 每100条记录提交一次，避免大事务
                    if (idx + 1) % 100 == 0:
                        db.session.commit()
                        logger.info(f"已导入 {idx + 1} 条记录")
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"导入第 {idx + 1} 行数据时出错: {str(e)}")
                    logger.error(f"出错的数据: {row.to_dict()}")
                    traceback.print_exc()
            
            # 最后提交剩余的记录
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"提交最后的记录时出错: {str(e)}")
                traceback.print_exc()
            
            # 输出导入结果
            logger.info(f"导入完成！成功: {success_count} 条, 失败: {error_count} 条")
            
            # 再次查询总记录数
            final_count = FireEquipment.query.count()
            logger.info(f"数据库中现有消防器材记录总数: {final_count}")
    
    except Exception as e:
        logger.error(f"导入过程中发生错误: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    import_excel_data()
