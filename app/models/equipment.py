from app import db
from datetime import datetime

class FireEquipment(db.Model):
    """消防器材数据模型"""
    __tablename__ = 'fire_equipment'

    id = db.Column(db.Integer, primary_key=True)
    area_code = db.Column(db.Integer, nullable=False)  # 设备区域编码
    area_name = db.Column(db.String(50), nullable=True)   # 设备区域名称
    installation_floor = db.Column(db.String(50), nullable=False)  #楼层
    installation_location = db.Column(db.String(200), nullable=False)  # 安装位置
    equipment_type = db.Column(db.String(50), nullable=False)     # 器材类型
    equipment_name = db.Column(db.String(100), nullable=False)  # 器材名称
    model = db.Column(db.String(100), nullable=False)             # 品牌型号
    weight = db.Column(db.String(30), nullable=False)                  #重量
    quantity = db.Column(db.Integer, nullable=True)                  # 数量
    production_date = db.Column(db.Date, nullable=True)          # 生产日期
    service_life = db.Column(db.String(30), nullable=False)        #使用年限      
    expiration_date = db.Column(db.String(50), nullable=False)        # 到期日期
    remark = db.Column(db.Text, nullable=False)                   # 备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # 创建时间
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, 
                           onupdate=datetime.utcnow)             # 更新时间

    def __repr__(self):
        return f'<FireEquipment {self.equipment_name}>'
