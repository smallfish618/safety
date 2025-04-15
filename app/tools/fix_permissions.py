
from app import create_app, db
from app.models.user import Permission

def fix_permissions():
    """修复现有权限，确保有新增、编辑或删除权限的用户也有查看权限"""
    app = create_app()
    
    with app.app_context():
        # 获取所有权限记录
        permissions = Permission.query.all()
        fixed_count = 0
        
        for perm in permissions:
            # 如果有新增、编辑或删除权限但没有查看权限
            if (perm.can_add or perm.can_edit or perm.can_delete) and not perm.can_view:
                # 启用查看权限
                perm.can_view = True
                fixed_count += 1
                print(f"为用户 {perm.user_id} 修复权限: 操作={perm.operation_type}, 区域={perm.area_id}")
        
        if fixed_count > 0:
            db.session.commit()
            print(f"成功修复了 {fixed_count} 条权限记录")
        else:
            print("没有需要修复的权限记录")

if __name__ == "__main__":
    fix_permissions()
