import os
import importlib
import sys
import traceback

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_blueprint_imports():
    """检查蓝图导入和路由注册状态"""
    print("开始检查蓝图导入情况...")
    
    # 尝试导入蓝图模块
    blueprints = ["auth", "station", "admin", "equipment"]
    import_success = []
    import_fail = []
    
    for bp_name in blueprints:
        try:
            module_path = f"app.routes.{bp_name}"
            module = importlib.import_module(module_path)
            bp_var = f"{bp_name}_bp"
            
            if hasattr(module, bp_var):
                blueprint = getattr(module, bp_var)
                routes = [str(rule) for rule in blueprint.url_map._rules if rule.endpoint.startswith(f"{bp_name}.")]
                import_success.append((bp_name, routes))
                print(f"✅ 成功导入蓝图: {bp_name}, 包含路由: {routes}")
            else:
                import_fail.append((bp_name, f"模块中找不到蓝图变量 '{bp_var}'"))
                print(f"❌ 蓝图变量错误: 在 {module_path} 中找不到 '{bp_var}'")
        except Exception as e:
            import_fail.append((bp_name, str(e)))
            print(f"❌ 导入失败: {bp_name} - {str(e)}")
            traceback.print_exc()
    
    # 检查设备路由是否正确定义
    print("\n检查 equipment 蓝图的路由...")
    try:
        from app.routes.equipment import equipment_bp
        routes = [r for r in equipment_bp.url_map._rules if r.endpoint.startswith("equipment.")]
        
        # 检查是否有根路由或index路由
        has_index = any("equipment.index" == r.endpoint for r in routes)
        has_root = any("equipment." == r.endpoint for r in routes)
        
        if has_index or has_root:
            print(f"✅ equipment 蓝图有index路由")
        else:
            print(f"❌ equipment 蓝图缺少index路由")
            
    except Exception as e:
        print(f"❌ 检查 equipment 路由时出错: {str(e)}")
        traceback.print_exc()
    
    # 尝试从flask应用实例检查已注册的路由
    print("\n尝试从Flask应用实例检查已注册路由...")
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            rules = sorted([str(rule) for rule in app.url_map.iter_rules()])
            equipment_rules = [r for r in rules if "/equipment" in r]
            print(f"应用中的设备相关路由: {equipment_rules}")
    except Exception as e:
        print(f"❌ 检查应用路由时出错: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    check_blueprint_imports()
    print("\n完成检查。请根据上述信息修复可能的问题。")
