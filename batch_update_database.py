"""
批量更新消防器材表和微型消防站表
包含备份、清空、导入、验证、恢复等功能
"""
import os
import sys
import sqlite3
import shutil
import pandas as pd
from datetime import datetime, date
import traceback
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.equipment import FireEquipment
from app.models.station import FireStation, ResponsiblePerson

# 配置日志
log_dir = 'e:/safety/logs'
os.makedirs(log_dir, exist_ok=True)

log_filename = os.path.join(log_dir, f'batch_update_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def normalize_columns(df, alias_map):
    """标准化列名：去空格并按别名映射为统一列名"""
    normalized = {col: str(col).strip() for col in df.columns}
    df = df.rename(columns=normalized)

    remap = {}
    for col in df.columns:
        remap[col] = alias_map.get(col, col)
    return df.rename(columns=remap)


def normalize_area_code(value):
    """将区域编码标准化为纯数字字符串（如 1.0 -> '1'）"""
    if pd.isna(value):
        return ''

    text = str(value).strip()
    if not text:
        return ''

    try:
        number = float(text)
        if number.is_integer():
            return str(int(number))
    except Exception:
        pass

    return text

class DatabaseUpdater:
    """数据库批量更新管理类"""
    
    def __init__(self):
        self.app = create_app()
        db_uri = self.app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if isinstance(db_uri, str) and db_uri.startswith('sqlite:///'):
            raw_path = db_uri.replace('sqlite:///', '', 1)
            self.db_path = raw_path if os.path.isabs(raw_path) else os.path.abspath(raw_path)
        else:
            self.db_path = os.path.abspath('instance/safety.db')
        self.backup_dir = 'e:/safety/data/backups'
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_name = f'backup_{self.timestamp}'
        os.makedirs(self.backup_dir, exist_ok=True)
        self.valid_area_codes = set()  # 存储有效的区域编码
    
    def load_valid_area_codes(self):
        """加载有效的区域编码"""
        with self.app.app_context():
            codes = db.session.query(ResponsiblePerson.area_code).distinct().all()
            self.valid_area_codes = {str(code[0]) for code in codes}
            logger.info(f"加载了 {len(self.valid_area_codes)} 个有效的区域编码")
            return self.valid_area_codes
    
    def backup_database(self):
        """备份整个数据库"""
        try:
            logger.info("=" * 60)
            logger.info("【第1步】开始备份数据库")
            logger.info("=" * 60)
            
            backup_path = os.path.join(self.backup_dir, f'{self.backup_name}.db')
            shutil.copy2(self.db_path, backup_path)
            
            logger.info(f"✓ 数据库备份成功: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"✗ 数据库备份失败: {str(e)}")
            raise
    
    def backup_tables_to_csv(self):
        """将两个表导出为CSV作为备份"""
        try:
            logger.info("【备份】导出表数据为CSV")
            backup_path = os.path.join(self.backup_dir, self.backup_name)
            os.makedirs(backup_path, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # 导出消防器材表
                equipment_df = pd.read_sql_query('SELECT * FROM fire_equipment', conn)
                equipment_csv = os.path.join(backup_path, 'fire_equipment_backup.csv')
                equipment_df.to_csv(equipment_csv, index=False, encoding='utf-8-sig')
                logger.info(f"✓ 消防器材表备份: {equipment_csv} ({len(equipment_df)} 行)")

                # 导出微型消防站表
                station_df = pd.read_sql_query('SELECT * FROM fire_station', conn)
                station_csv = os.path.join(backup_path, 'fire_station_backup.csv')
                station_df.to_csv(station_csv, index=False, encoding='utf-8-sig')
                logger.info(f"✓ 微型消防站表备份: {station_csv} ({len(station_df)} 行)")

            return backup_path
        except Exception as e:
            logger.error(f"✗ 导出表数据失败: {str(e)}")
            raise
    
    def clear_tables(self):
        """清空两个表的所有数据"""
        try:
            logger.info("=" * 60)
            logger.info("【第2步】清空表数据")
            logger.info("=" * 60)
            
            with self.app.app_context():
                equipment_count = FireEquipment.query.count()
                station_count = FireStation.query.count()
                
                logger.info(f"删除前 - 消防器材表: {equipment_count} 条")
                logger.info(f"删除前 - 微型消防站表: {station_count} 条")
                
                # 清空表
                FireEquipment.query.delete()
                FireStation.query.delete()
                db.session.commit()
                
                logger.info("✓ 表数据已清空")
        except Exception as e:
            logger.error(f"✗ 清空表失败: {str(e)}")
            db.session.rollback()
            raise
    
    def import_equipment_data(self, excel_path):
        """导入消防器材数据"""
        try:
            logger.info("=" * 60)
            logger.info("【第3步】导入消防器材数据")
            logger.info("=" * 60)
            
            if not os.path.exists(excel_path):
                raise FileNotFoundError(f"Excel文件不存在: {excel_path}")
            
            # 读取Excel文件
            logger.info(f"正在读取: {excel_path}")
            df = pd.read_excel(excel_path, sheet_name='消防器材')
            df = normalize_columns(df, {
                '使用限': '使用年限',
                '使用期限': '使用年限',
                '有效期': '到期日期',
                '有效期时间': '到期日期'
            })
            
            df = df.dropna(how='all')
            logger.info(f"读取到 {len(df)} 行数据")
            
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
            
            with self.app.app_context():
                success_count = 0
                error_count = 0
                errors = []
                
                for idx, row in df.iterrows():
                    try:
                        if row.isna().all():
                            continue

                        data = {}
                        
                        # 映射列名
                        for excel_col, db_col in column_mapping.items():
                            if excel_col in df.columns:
                                value = row[excel_col]
                                data[db_col] = value if pd.notna(value) else None
                        
                        # 验证区域编码
                        if data.get('area_code'):
                            area_code = normalize_area_code(data['area_code'])
                            if area_code not in self.valid_area_codes:
                                raise ValueError(f"无效的区域编码: {area_code}. 有效的区域编码为: {', '.join(sorted(self.valid_area_codes))}")
                            data['area_code'] = int(area_code) if area_code.isdigit() else area_code
                        else:
                            raise ValueError("区域编码不能为空")
                        
                        # 处理日期
                        if data.get('production_date'):
                            if isinstance(data['production_date'], pd.Timestamp):
                                data['production_date'] = data['production_date'].date()
                            elif isinstance(data['production_date'], datetime):
                                data['production_date'] = data['production_date'].date()
                            elif isinstance(data['production_date'], date):
                                pass
                            elif isinstance(data['production_date'], str):
                                data['production_date'] = datetime.strptime(
                                    data['production_date'], '%Y-%m-%d'
                                ).date()

                        if data.get('expiration_date'):
                            if isinstance(data['expiration_date'], pd.Timestamp):
                                data['expiration_date'] = data['expiration_date'].strftime('%Y-%m-%d')
                            elif isinstance(data['expiration_date'], datetime):
                                data['expiration_date'] = data['expiration_date'].strftime('%Y-%m-%d')
                            elif isinstance(data['expiration_date'], date):
                                data['expiration_date'] = data['expiration_date'].strftime('%Y-%m-%d')
                            else:
                                data['expiration_date'] = str(data['expiration_date']).strip()

                        if data.get('service_life') is not None:
                            service_life = data['service_life']
                            if isinstance(service_life, (int, float)):
                                data['service_life'] = str(int(service_life)) if float(service_life).is_integer() else str(service_life)
                            else:
                                data['service_life'] = str(service_life).strip()
                        
                        # 处理数值字段
                        if data.get('quantity'):
                            data['quantity'] = int(data['quantity'])
                        
                        # 处理必填字段
                        for field in ['installation_floor', 'installation_location', 
                                     'equipment_type', 'equipment_name', 'model', 
                                     'weight', 'service_life', 'expiration_date', 'remark']:
                            if field not in data or data[field] is None:
                                data[field] = ''
                        
                        equipment = FireEquipment(**data)
                        db.session.add(equipment)
                        success_count += 1
                        
                        # 每100条提交一次
                        if (idx + 1) % 100 == 0:
                            db.session.commit()
                            logger.info(f"  ├─ 已导入 {idx + 1} 条")
                    
                    except Exception as e:
                        db.session.rollback()
                        error_count += 1
                        errors.append(f"第{idx + 1}行: {str(e)}")
                        logger.warning(f"  ├─ 第{idx + 1}行错误: {str(e)}")
                
                # 提交剩余数据
                db.session.commit()
                
                logger.info(f"✓ 消防器材数据导入完成")
                logger.info(f"  ├─ 成功: {success_count} 条")
                logger.info(f"  └─ 失败: {error_count} 条")
                
                return success_count, error_count, errors
        
        except Exception as e:
            logger.error(f"✗ 导入消防器材数据失败: {str(e)}")
            with self.app.app_context():
                db.session.rollback()
            raise
    
    def import_station_data(self, excel_path):
        """导入微型消防站数据"""
        try:
            logger.info("=" * 60)
            logger.info("【第4步】导入微型消防站数据")
            logger.info("=" * 60)
            
            if not os.path.exists(excel_path):
                raise FileNotFoundError(f"Excel文件不存在: {excel_path}")
            
            # 读取Excel文件
            logger.info(f"正在读取: {excel_path}")
            df = pd.read_excel(excel_path, sheet_name='微型消防站')
            df = normalize_columns(df, {
                '物资名称': '物品名称'
            })
            
            df = df.dropna(how='all')
            logger.info(f"读取到 {len(df)} 行数据")
            
            column_mapping = {
                '区域编码': 'area_code',
                '区域名称': 'area_name',
                '物品名称': 'item_name',
                '生产厂家': 'manufacturer',
                '型号': 'model',
                '数量': 'quantity',
                '生产日期': 'production_date',
                '合格证': 'certificate',
                '合格证编号': 'certificate_no',
                '备注': 'remark'
            }
            
            with self.app.app_context():
                success_count = 0
                error_count = 0
                errors = []
                
                for idx, row in df.iterrows():
                    try:
                        if row.isna().all():
                            continue

                        data = {}
                        
                        # 映射列名
                        for excel_col, db_col in column_mapping.items():
                            if excel_col in df.columns:
                                value = row[excel_col]
                                data[db_col] = value if pd.notna(value) else None
                        
                        # 验证区域编码
                        if data.get('area_code'):
                            area_code = normalize_area_code(data['area_code'])
                            if area_code not in self.valid_area_codes:
                                raise ValueError(f"无效的区域编码: {area_code}. 有效的区域编码为: {', '.join(sorted(self.valid_area_codes))}")
                            data['area_code'] = area_code
                        else:
                            raise ValueError("区域编码不能为空")
                        
                        # 处理日期
                        if data.get('production_date'):
                            if isinstance(data['production_date'], pd.Timestamp):
                                data['production_date'] = data['production_date'].date()
                            elif isinstance(data['production_date'], datetime):
                                data['production_date'] = data['production_date'].date()
                            elif isinstance(data['production_date'], date):
                                pass
                            elif isinstance(data['production_date'], str):
                                data['production_date'] = datetime.strptime(
                                    data['production_date'], '%Y-%m-%d'
                                ).date()
                        
                        station = FireStation(**data)
                        db.session.add(station)
                        success_count += 1
                        
                        # 每100条提交一次
                        if (idx + 1) % 100 == 0:
                            db.session.commit()
                            logger.info(f"  ├─ 已导入 {idx + 1} 条")
                    
                    except Exception as e:
                        db.session.rollback()
                        error_count += 1
                        errors.append(f"第{idx + 1}行: {str(e)}")
                        logger.warning(f"  ├─ 第{idx + 1}行错误: {str(e)}")
                
                # 提交剩余数据
                db.session.commit()
                
                logger.info(f"✓ 微型消防站数据导入完成")
                logger.info(f"  ├─ 成功: {success_count} 条")
                logger.info(f"  └─ 失败: {error_count} 条")
                
                return success_count, error_count, errors
        
        except Exception as e:
            logger.error(f"✗ 导入微型消防站数据失败: {str(e)}")
            with self.app.app_context():
                db.session.rollback()
            raise
    
    def verify_data(self):
        """验证导入的数据"""
        try:
            logger.info("=" * 60)
            logger.info("【第5步】验证导入数据")
            logger.info("=" * 60)
            
            with self.app.app_context():
                equipment_count = FireEquipment.query.count()
                station_count = FireStation.query.count()
                
                logger.info(f"✓ 消防器材表: {equipment_count} 条记录")
                logger.info(f"✓ 微型消防站表: {station_count} 条记录")
                
                # 检查数据完整性
                equipment_without_name = FireEquipment.query.filter(
                    FireEquipment.equipment_name == ''
                ).count()
                
                station_without_name = FireStation.query.filter(
                    FireStation.item_name == ''
                ).count()
                
                if equipment_without_name > 0:
                    logger.warning(f"⚠ 警告: 消防器材表有 {equipment_without_name} 条记录缺少名称")
                
                if station_without_name > 0:
                    logger.warning(f"⚠ 警告: 微型消防站表有 {station_without_name} 条记录缺少名称")
                
                return equipment_count, station_count
        
        except Exception as e:
            logger.error(f"✗ 数据验证失败: {str(e)}")
            raise
    
    def delete_backup(self, backup_path):
        """删除备份"""
        try:
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
                logger.info(f"✓ 备份已删除: {backup_path}")
        except Exception as e:
            logger.error(f"✗ 删除备份失败: {str(e)}")
    
    def restore_backup(self, backup_db_path):
        """恢复数据库备份"""
        try:
            logger.info("=" * 60)
            logger.info("【恢复】恢复数据库备份")
            logger.info("=" * 60)
            
            # 关闭所有数据库连接
            db.session.close_all()
            
            if os.path.exists(backup_db_path):
                shutil.copy2(backup_db_path, self.db_path)
                logger.info(f"✓ 数据库已从备份恢复")
            else:
                logger.error(f"✗ 备份文件不存在: {backup_db_path}")
        except Exception as e:
            logger.error(f"✗ 恢复备份失败: {str(e)}")
            raise
    
    def run_full_update(self, excel_path):
        """执行完整的数据库更新流程"""
        backup_db_path = None
        backup_csv_path = None
        
        try:
            logger.info("\n")
            logger.info("╔" + "=" * 58 + "╗")
            logger.info("║" + " " * 10 + "消防器材数据库批量更新程序" + " " * 16 + "║")
            logger.info("╚" + "=" * 58 + "╝")
            
            # 加载有效的区域编码
            logger.info("=" * 60)
            logger.info("【准备】加载有效的区域编码")
            logger.info("=" * 60)
            valid_codes = self.load_valid_area_codes()
            if not valid_codes:
                logger.error("✗ 错误: 没有找到有效的区域编码")
                logger.error("  请先在系统中为微型消防站设置负责人信息")
                return False
            logger.info(f"✓ 成功加载 {len(valid_codes)} 个有效的区域编码")
            
            # 第1步：备份
            backup_db_path = self.backup_database()
            backup_csv_path = self.backup_tables_to_csv()
            
            # 第2步：清空表
            self.clear_tables()
            
            # 第3步：导入消防器材数据
            equip_success, equip_error, equip_errors = self.import_equipment_data(excel_path)
            
            # 第4步：导入微型消防站数据
            station_success, station_error, station_errors = self.import_station_data(excel_path)
            
            # 第5步：验证数据
            equipment_count, station_count = self.verify_data()
            
            # 总结
            logger.info("\n")
            logger.info("=" * 60)
            logger.info("【完成】数据库更新完成")
            logger.info("=" * 60)
            logger.info(f"消防器材表: {equipment_count} 条")
            logger.info(f"微型消防站表: {station_count} 条")
            logger.info(f"备份位置: {backup_db_path}")
            logger.info(f"详细日志: {log_filename}")
            
            # 询问是否删除备份
            user_input = input("\n✓ 数据导入成功！现在是否删除备份？(y/n): ").lower()
            if user_input == 'y':
                self.delete_backup(backup_csv_path)
                logger.info("✓ 备份已删除")
            else:
                logger.info(f"✓ 备份保留在: {backup_csv_path}")
            
            return True
        
        except Exception as e:
            logger.error("\n" + "=" * 60)
            logger.error("【失败】数据库更新失败，准备恢复备份")
            logger.error("=" * 60)
            logger.error(f"错误信息: {str(e)}")
            traceback.print_exc()
            
            # 尝试恢复备份
            if backup_db_path and os.path.exists(backup_db_path):
                user_input = input("\n是否恢复备份？(y/n): ").lower()
                if user_input == 'y':
                    self.restore_backup(backup_db_path)
                    logger.info("✓ 数据库已恢复")
            
            return False


if __name__ == '__main__':
    updater = DatabaseUpdater()
    
    # 获取Excel文件路径
    excel_path = 'e:/safety/data/batch_update_template.xlsx'
    
    if not os.path.exists(excel_path):
        logger.error(f"Excel文件不存在: {excel_path}")
        logger.error("请先创建数据文件")
        sys.exit(1)
    
    # 执行更新
    success = updater.run_full_update(excel_path)
    sys.exit(0 if success else 1)
