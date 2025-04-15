# 导入所有模型类以便其他模块可以直接从app.models导入它们
from app.models.user import User, Permission
from app.models.station import FireStation, EquipmentExpiry, ResponsiblePerson
from app.models.equipment import FireEquipment
from app.models.mail_log import MailLog  # 添加这一行导入MailLog类

# 此处可能有其他导入语句...
