"""
获取有效的区域编码列表
用于生成Excel模板和数据验证
"""
import sys
sys.path.insert(0, '.')

from app import create_app, db
from app.models.station import ResponsiblePerson

def get_area_codes():
    """获取所有有效的区域编码"""
    app = create_app()
    with app.app_context():
        # 查询所有唯一的区域编码
        area_codes = db.session.query(
            ResponsiblePerson.area_code, 
            ResponsiblePerson.area_name
        ).distinct().order_by(ResponsiblePerson.area_code).all()
        
        return area_codes

def print_area_codes():
    """打印区域编码列表"""
    area_codes = get_area_codes()
    
    print("=" * 60)
    print("有效的区域编码列表")
    print("=" * 60)
    print(f"{'编码':<10} {'区域名称':<40}")
    print("-" * 60)
    
    for code, name in area_codes:
        print(f"{code:<10} {name:<40}")
    
    print("-" * 60)
    print(f"总共: {len(area_codes)} 个区域")
    print("=" * 60)
    
    return area_codes

if __name__ == '__main__':
    area_codes = print_area_codes()
