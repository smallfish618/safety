from app import db
from datetime import datetime

class FireStation(db.Model):
    """微型消防站物资表"""
    __tablename__ = 'fire_station'

    id = db.Column(db.Integer, primary_key=True)  # 自增主键
    area_code = db.Column(db.String(50), nullable=False, index=True)  # 设备区域编码
    area_name = db.Column(db.String(100))  # 设备区域
    item_name = db.Column(db.String(100))  # 物品名称
    manufacturer = db.Column(db.String(150))  # 生产厂家
    model = db.Column(db.String(100))  # 型号
    quantity = db.Column(db.String(100))  # 数量
    production_date = db.Column(db.Date)  # 生产日期
    certificate = db.Column(db.String(100))  # 合格证
    certificate_no = db.Column(db.String(100))  # 合格证编号
    remark = db.Column(db.String(100))  # 备注

    def __repr__(self):
        return f'<FireStation {self.item_name}>'

class EquipmentExpiry(db.Model):
    """微型消防站物资设备有效期表"""
    id = db.Column(db.Integer, primary_key=True)
    item_category = db.Column(db.String(50))  # 物资分类
    item_name = db.Column(db.String(50))  # 物品名称
    normal_expiry = db.Column(db.Float)  # 正常使用有效期
    mandatory_expiry = db.Column(db.Float)  # 强制报废期
    description = db.Column(db.String(500))  # 说明
    
class ResponsiblePerson(db.Model):
    """微型消防站物资负责人表"""
    id = db.Column(db.Integer, primary_key=True)
    area_code = db.Column(db.String(50))  # 修改为字符串类型，不再作为外键
    area_name = db.Column(db.String(50))  # 设备区域
    person_name = db.Column(db.String(30))  # 负责人姓名
    contact = db.Column(db.String(30))  # 负责人联系方式
    email = db.Column(db.String(50))  # 负责人邮件地址