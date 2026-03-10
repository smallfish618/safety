"""
导入前数据验证脚本
检查Excel数据的有效性，特别是区域编码
"""
import sys
import os
import pandas as pd
sys.path.insert(0, '.')

from app import create_app, db
from app.models.station import ResponsiblePerson


def normalize_columns(df, alias_map):
    """标准化列名：去空格并按别名映射为统一列名"""
    normalized = {col: str(col).strip() for col in df.columns}
    df = df.rename(columns=normalized)

    remap = {}
    for col in df.columns:
        canonical = alias_map.get(col, col)
        remap[col] = canonical
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

def get_valid_area_codes():
    """获取有效的区域编码"""
    app = create_app()
    with app.app_context():
        codes = db.session.query(ResponsiblePerson.area_code).distinct().all()
        return {str(code[0]) for code in codes}

def validate_equipment_data(excel_path):
    """验证消防器材数据"""
    print("\n" + "=" * 60)
    print("验证消防器材数据")
    print("=" * 60)
    
    try:
        df = pd.read_excel(excel_path, sheet_name='消防器材')
        df = normalize_columns(df, {
            '使用限': '使用年限',
            '使用期限': '使用年限',
            '有效期': '到期日期',
            '有效期时间': '到期日期'
        })
        valid_codes = get_valid_area_codes()
        
        print(f"读取到 {len(df)} 行数据")
        print(f"有效的区域编码: {', '.join(sorted(valid_codes))}")
        print()
        
        errors = []
        warnings = []
        
        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel行号 (第1行是表头)
            
            # 检查区域编码
            area_code = normalize_area_code(row['区域编码'])
            if not area_code:
                errors.append(f"第{row_num}行: 区域编码为空")
            elif area_code not in valid_codes:
                errors.append(f"第{row_num}行: 无效的区域编码 '{area_code}'")
            
            # 检查必填字段
            required_fields = ['区域名称', '楼层', '安装位置', '器材类型', '器材名称', 
                             '型号', '重量', '使用年限', '到期日期']
            for field in required_fields:
                if pd.isna(row[field]) or row[field] == '':
                    errors.append(f"第{row_num}行: 必填字段 '{field}' 为空")
            
            # 检查日期格式
            if pd.notna(row['生产日期']):
                try:
                    pd.to_datetime(row['生产日期'], format='%Y-%m-%d')
                except:
                    warnings.append(f"第{row_num}行: 生产日期格式不标准")
        
        # 报告结果
        if errors:
            print(f"[ERROR] 发现 {len(errors)} 个错误:")
            for error in errors[:10]:  # 只显示前10个
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... 还有 {len(errors) - 10} 个错误")
        
        if warnings:
            print(f"\n[WARN] 发现 {len(warnings)} 个警告:")
            for warning in warnings[:5]:
                print(f"  - {warning}")
        
        if not errors:
            print("[OK] 消防器材数据验证通过!")
            return True
        else:
            return False
    
    except Exception as e:
        print(f"[ERROR] 验证失败: {str(e)}")
        return False

def validate_station_data(excel_path):
    """验证微型消防站数据"""
    print("\n" + "=" * 60)
    print("验证微型消防站数据")
    print("=" * 60)
    
    try:
        df = pd.read_excel(excel_path, sheet_name='微型消防站')
        df = normalize_columns(df, {
            '物资名称': '物品名称'
        })
        valid_codes = get_valid_area_codes()
        
        print(f"读取到 {len(df)} 行数据")
        print(f"有效的区域编码: {', '.join(sorted(valid_codes))}")
        print()
        
        errors = []
        warnings = []
        
        for idx, row in df.iterrows():
            row_num = idx + 2
            
            # 检查区域编码
            area_code = normalize_area_code(row['区域编码'])
            if not area_code:
                errors.append(f"第{row_num}行: 区域编码为空")
            elif area_code not in valid_codes:
                errors.append(f"第{row_num}行: 无效的区域编码 '{area_code}'")
            
            # 检查必填字段
            required_fields = ['区域名称', '物品名称']
            for field in required_fields:
                if pd.isna(row[field]) or row[field] == '':
                    errors.append(f"第{row_num}行: 必填字段 '{field}' 为空")
            
            # 检查日期格式
            if pd.notna(row['生产日期']):
                try:
                    pd.to_datetime(row['生产日期'], format='%Y-%m-%d')
                except:
                    warnings.append(f"第{row_num}行: 生产日期格式不标准")
        
        # 报告结果
        if errors:
            print(f"[ERROR] 发现 {len(errors)} 个错误:")
            for error in errors[:10]:
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... 还有 {len(errors) - 10} 个错误")
        
        if warnings:
            print(f"\n[WARN] 发现 {len(warnings)} 个警告:")
            for warning in warnings[:5]:
                print(f"  - {warning}")
        
        if not errors:
            print("[OK] 微型消防站数据验证通过!")
            return True
        else:
            return False
    
    except Exception as e:
        print(f"[ERROR] 验证失败: {str(e)}")
        return False

def validate_all(excel_path):
    """验证所有数据"""
    if not os.path.exists(excel_path):
        print(f"[ERROR] Excel文件不存在: {excel_path}")
        return False
    
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 14 + "数据验证程序" + " " * 30 + "║")
    print("╚" + "=" * 58 + "╝")
    
    equip_valid = validate_equipment_data(excel_path)
    station_valid = validate_station_data(excel_path)
    
    print("\n" + "=" * 60)
    print("验证结果总结")
    print("=" * 60)
    
    if equip_valid and station_valid:
        print("[OK] 所有数据验证通过，可以进行导入!")
        return True
    else:
        print("[ERROR] 存在无效数据，请修正后重新验证!")
        return False

if __name__ == '__main__':
    excel_path = 'e:/safety/data/batch_update_template.xlsx'
    validate_all(excel_path)
