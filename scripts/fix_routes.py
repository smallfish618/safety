import os
import sys
import shutil

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def clear_cache_dirs(directory):
    """清理所有__pycache__目录"""
    print(f"正在清理目录: {directory}")
    for root, dirs, files in os.walk(directory):
        if '__pycache__' in dirs:
            pycache_dir = os.path.join(root, '__pycache__')
            print(f"删除缓存目录: {pycache_dir}")
            shutil.rmtree(pycache_dir)
    print("缓存清理完成")

def ensure_equipment_routes_registered():
    """确保equipment路由正确注册"""
    equipment_route_path = os.path.join(project_root, 'app', 'routes', 'equipment.py')
    
    # 检查路由文件是否存在
    if not os.path.exists(equipment_route_path):
        print(f"错误: 未找到消防器材路由文件: {equipment_route_path}")
        return False
    
    # 检查文件内容是否包含必要的路由定义
    with open(equipment_route_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "@equipment_bp.route('/index')" not in content:
        print("错误: equipment.py文件中没有找到'/index'路由!")
        return False
    
    print("消防器材路由文件检查通过")
    return True

def check_app_init():
    """检查app/__init__.py是否正确导入和注册蓝图"""
    init_path = os.path.join(project_root, 'app', '__init__.py')
    
    # 检查文件是否存在
    if not os.path.exists(init_path):
        print(f"错误: 未找到应用初始化文件: {init_path}")
        return False
    
    # 检查文件内容是否包含必要的导入和注册
    with open(init_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "from app.routes.equipment import equipment_bp" not in content:
        print("错误: __init__.py中没有导入equipment_bp!")
        return False
    
    if "app.register_blueprint(equipment_bp, url_prefix='/equipment')" not in content:
        print("错误: __init__.py中没有注册equipment_bp!")
        return False
    
    print("应用初始化文件检查通过")
    return True

def generate_equipment_import_check():
    """创建简单的测试脚本验证蓝图导入情况"""
    test_script_path = os.path.join(project_root, 'scripts', 'test_equipment_import.py')
    
    test_script = """
# 临时测试脚本，验证蓝图导入
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    # 尝试导入equipment_bp
    from app.routes.equipment import equipment_bp
    print("导入成功: equipment_bp")
    
    # 检查路由
    for route in equipment_bp.url_map._rules:
        print(f" - 路由: {route}")
        
except Exception as e:
    print(f"导入失败: {str(e)}")
    import traceback
    traceback.print_exc()
    
print("测试完成")
"""
    
    with open(test_script_path, 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print(f"已生成测试脚本: {test_script_path}")
    return test_script_path

if __name__ == "__main__":
    print("开始修复路由问题...")
    
    # 清理所有缓存目录
    clear_cache_dirs(project_root)
    
    # 检查路由文件和配置
    equipment_routes_ok = ensure_equipment_routes_registered()
    init_ok = check_app_init()
    
    if equipment_routes_ok and init_ok:
        print("\n所有文件检查通过。请完全重启Flask应用后再试。")
        print("如果问题仍然存在，请尝试运行生成的测试脚本验证导入情况。")
        
        # 生成测试脚本
        test_script = generate_equipment_import_check()
        print(f"\n运行以下命令来测试导入:\n  python {os.path.relpath(test_script, project_root)}")
    else:
        print("\n检查未通过。请修复以上问题后再试。")
    
    print("\n建议：在修复后，请确保完全退出并重启Flask应用，而不仅仅是重新加载。")
