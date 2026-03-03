# 消防安全管理系统详细设计文档

## 1. 系统架构设计

### 1.1 总体架构
本系统采用经典的三层架构设计：
- **表示层**：基于HTML5、CSS3和JavaScript构建的Web界面，使用Bootstrap框架提供响应式设计
- **业务逻辑层**：基于Flask框架的Python后端应用，处理核心业务逻辑
- **数据访问层**：使用SQLAlchemy ORM连接SQLite数据库，实现数据持久化

### 1.2 架构图
```
┌───────────────────────────────────────┐
│              客户端浏览器              │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│            Waitress WSGI服务器         │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│               Flask应用                │
├───────────────────────────────────────┤
│  ┌─────────┐  ┌──────────┐ ┌────────┐ │
│  │视图层   │  │业务逻辑层│ │数据访问层│ │
│  │(蓝图)   │  │(服务)    │ │(模型)   │ │
│  └─────────┘  └──────────┘ └────────┘ │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│              SQLite数据库              │
└───────────────────────────────────────┘
```

### 1.3 技术栈选择
- **前端**：HTML5、CSS3、JavaScript、Bootstrap 5、jQuery
- **后端**：Python 3.9+、Flask 2.0+、SQLAlchemy
- **数据库**：SQLite
- **任务调度**：APScheduler
- **服务器**：Waitress WSGI服务器
- **安全认证**：Flask-Login、CSRF保护
- **邮件服务**：SMTP

## 2. 数据库设计

### 2.1 ER图
系统主要实体及其关系如下：
- User(用户) 1--N Permission(权限)
- FireStation(微型消防站物资) N--1 ResponsiblePerson(负责人)
- FireEquipment(消防器材) N--1 ResponsiblePerson(负责人)
- EquipmentExpiry(有效期规则) 1--N FireStation/FireEquipment(通过物品名称关联)
- MailLog(邮件日志) N--1 User(发送者)
- SchedulerConfig(调度配置) 1--N 定时任务(逻辑关联)

### 2.2 数据库表设计

#### 2.2.1 用户表(users)
| 字段名      | 数据类型    | 约束        | 说明                         |
|------------|------------|------------|------------------------------|
| id         | INTEGER    | PK         | 用户ID，自增                  |
| username   | VARCHAR(64)| NOT NULL   | 用户名，唯一                  |
| password_hash | VARCHAR(128) | NOT NULL | 密码哈希                   |
| email      | VARCHAR(120) |          | 电子邮箱                     |
| role       | VARCHAR(20) | NOT NULL  | 角色(admin/user)             |
| is_active  | BOOLEAN    | NOT NULL   | 是否激活                     |
| last_login | DATETIME   |            | 最后登录时间                  |

#### 2.2.2 权限表(permissions)
| 字段名       | 数据类型    | 约束       | 说明                         |
|-------------|------------|-----------|------------------------------|
| id          | INTEGER    | PK        | 权限ID，自增                  |
| user_id     | INTEGER    | FK        | 用户ID，外键关联users表       |
| operation_type | VARCHAR(50) | NOT NULL | 操作类型(微型消防站/灭火器和呼吸器) |
| area_id     | VARCHAR(50) | NOT NULL  | 区域ID                       |
| area_name   | VARCHAR(100) |         | 区域名称                     |
| can_view    | BOOLEAN    | NOT NULL  | 是否可查看                   |
| can_add     | BOOLEAN    | NOT NULL  | 是否可添加                   |
| can_edit    | BOOLEAN    | NOT NULL  | 是否可编辑                   |
| can_delete  | BOOLEAN    | NOT NULL  | 是否可删除                   |

#### 2.2.3 微型消防站物资表(fire_stations)
| 字段名         | 数据类型    | 约束       | 说明                      |
|---------------|------------|-----------|---------------------------|
| id            | INTEGER    | PK        | ID，自增                  |
| area_code     | INTEGER    | NOT NULL  | 区域编码                  |
| area_name     | VARCHAR(100) | NOT NULL | 区域名称                  |
| item_name     | VARCHAR(100) | NOT NULL | 物品名称                  |
| model         | VARCHAR(100) |         | 型号                      |
| quantity      | INTEGER    |           | 数量                      |
| production_date | DATE     |           | 生产日期                  |
| manufacturer  | VARCHAR(100) |         | 生产厂家                  |
| remark        | TEXT       |           | 备注                      |
| created_at    | DATETIME   | NOT NULL  | 创建时间                  |
| updated_at    | DATETIME   |           | 更新时间                  |

#### 2.2.4 消防器材表(fire_equipments)
| 字段名         | 数据类型    | 约束       | 说明                      |
|---------------|------------|-----------|---------------------------|
| id            | INTEGER    | PK        | ID，自增                  |
| area_code     | VARCHAR(20) | NOT NULL | 区域编码                  |
| area_name     | VARCHAR(100) | NOT NULL | 区域名称                  |
| equipment_type | VARCHAR(100) | NOT NULL | 设备类型                  |
| model         | VARCHAR(100) |         | 型号                      |
| serial_number | VARCHAR(100) |         | 序列号                    |
| production_date | DATE     |           | 生产日期                  |
| installation_date | DATE   |           | 安装日期                  |
| installation_location | VARCHAR(200) | | 安装位置                 |
| installation_floor | VARCHAR(50) |     | 安装楼层                  |
| manufacturer  | VARCHAR(100) |         | 生产厂家                  |
| remark        | TEXT       |           | 备注                      |
| created_at    | DATETIME   | NOT NULL  | 创建时间                  |
| updated_at    | DATETIME   |           | 更新时间                  |

#### 2.2.5 有效期规则表(equipment_expiries)
| 字段名         | 数据类型    | 约束       | 说明                      |
|---------------|------------|-----------|---------------------------|
| id            | INTEGER    | PK        | ID，自增                  |
| item_category | VARCHAR(50) | NOT NULL | 物品类别                  |
| item_name     | VARCHAR(100) | NOT NULL | 物品名称                  |
| normal_expiry | FLOAT      | NOT NULL  | 正常有效期(年)            |
| mandatory_expiry | FLOAT   |           | 强制有效期(年)            |
| description   | TEXT       |           | 说明                      |
| created_at    | DATETIME   | NOT NULL  | 创建时间                  |
| updated_at    | DATETIME   |           | 更新时间                  |

#### 2.2.6 负责人表(responsible_persons)
| 字段名         | 数据类型    | 约束       | 说明                      |
|---------------|------------|-----------|---------------------------|
| id            | INTEGER    | PK        | ID，自增                  |
| area_code     | INTEGER    | NOT NULL  | 区域编码，唯一             |
| area_name     | VARCHAR(100) | NOT NULL | 区域名称                  |
| person_name   | VARCHAR(50) | NOT NULL | 负责人姓名                |
| contact       | VARCHAR(50) | NOT NULL | 联系方式                  |
| email         | VARCHAR(100) |         | 电子邮箱                  |
| created_at    | DATETIME   | NOT NULL  | 创建时间                  |
| updated_at    | DATETIME   |           | 更新时间                  |

#### 2.2.7 邮件日志表(mail_logs)
| 字段名         | 数据类型    | 约束       | 说明                      |
|---------------|------------|-----------|---------------------------|
| id            | INTEGER    | PK        | ID，自增                  |
| send_time     | DATETIME   | NOT NULL  | 发送时间                  |
| sender        | VARCHAR(120) | NOT NULL | 发件人                    |
| recipient     | VARCHAR(120) | NOT NULL | 收件人                    |
| recipient_name | VARCHAR(50) |         | 收件人姓名                |
| subject       | VARCHAR(200) | NOT NULL | 邮件主题                  |
| content_summary | TEXT     |           | 内容摘要                  |
| status        | VARCHAR(20) | NOT NULL | 状态(success/failed)      |
| error_message | TEXT       |           | 错误信息                  |
| items_count   | INTEGER    |           | 邮件中的物品数量          |
| ip_address    | VARCHAR(50) |          | 发送IP地址                |
| user_id       | INTEGER    |           | 用户ID，外键关联users表   |
| username      | VARCHAR(64) |          | 用户名                    |

#### 2.2.8 调度配置表(scheduler_configs)
| 字段名         | 数据类型    | 约束       | 说明                      |
|---------------|------------|-----------|---------------------------|
| id            | INTEGER    | PK        | ID，自增                  |
| name          | VARCHAR(100) | NOT NULL | 任务名称                  |
| frequency_type | VARCHAR(20) | NOT NULL | 频率类型(daily/weekly/monthly) |
| day_of_week   | VARCHAR(20) |          | 每周几执行(weekly有效)    |
| day_of_month  | INTEGER    |           | 每月几号执行(monthly有效) |
| execution_time | VARCHAR(10) | NOT NULL | 执行时间(HH:MM格式)       |
| warning_levels | VARCHAR(100) |         | 预警级别(逗号分隔)        |
| recipient_filter | VARCHAR(200) |       | 收件人筛选条件            |
| enabled       | BOOLEAN    | NOT NULL  | 是否启用                  |
| created_at    | DATETIME   | NOT NULL  | 创建时间                  |
| updated_at    | DATETIME   |           | 更新时间                  |

### 2.3 索引设计
- users表：username列添加唯一索引
- permissions表：(user_id, operation_type, area_id)添加复合索引
- fire_stations表：area_code, item_name添加索引
- fire_equipments表：area_code, equipment_type添加索引
- equipment_expiries表：item_name添加索引
- responsible_persons表：area_code添加唯一索引
- mail_logs表：send_time, status添加索引

## 3. 模块设计

### 3.1 模块划分
系统划分为以下主要模块：

1. **用户认证模块**
   - 登录、登出功能
   - 密码管理
   - 会话管理

2. **用户管理模块**
   - 用户增删改查
   - 权限管理
   - 角色管理

3. **微型消防站物资管理模块**
   - 物资信息增删改查
   - 物资信息导入导出
   - 物资信息筛选查询

4. **消防器材管理模块**
   - 器材信息增删改查
   - 器材信息导入导出
   - 器材信息筛选查询

5. **有效期管理模块**
   - 有效期规则设置
   - 有效期计算
   - 预警查询与显示

6. **邮件通知模块**
   - 邮件发送
   - 邮件模板管理
   - 邮件日志记录

7. **定时任务模块**
   - 任务配置
   - 任务调度
   - 任务执行记录

8. **区域与负责人模块**
   - 区域管理
   - 负责人管理

9. **统计分析模块**
   - 数据统计
   - 图表展示

### 3.2 核心模块流程设计

#### 3.2.1 有效期预警流程
```
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ 获取物资数据  │───>│ 匹配有效期规则 │───>│ 计算剩余天数  │
└───────────────┘    └───────────────┘    └───────┬───────┘
                                                  │
                                                  ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ 发送预警邮件  │<───│ 筛选负责人    │<───│ 判断预警级别  │
└───────────────┘    └───────────────┘    └───────────────┘
```

#### 3.2.2 邮件发送流程
```
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ 确定收件人    │───>│ 生成邮件内容  │───>│ 连接SMTP服务器│
└───────────────┘    └───────────────┘    └───────┬───────┘
                                                  │
                                                  ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ 记录发送日志  │<───│ 发送邮件      │<───│ 邮件认证      │
└───────────────┘    └───────────────┘    └───────────────┘
```

#### 3.2.3 定时任务调度流程
```
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ 读取任务配置  │───>│ 初始化调度器  │───>│ 注册定时任务  │
└───────────────┘    └───────────────┘    └───────┬───────┘
                                                  │
                                                  ▼
┌───────────────┐                         ┌───────────────┐
│ 执行任务      │<────────────────────────│ 启动调度器    │
└───────────────┘                         └───────────────┘
```

### 3.3 权限设计
系统实现基于角色和区域的细粒度权限控制：

1. **角色级权限**：
   - 管理员：拥有系统全部权限
   - 普通用户：仅拥有被授权的区域和操作权限

2. **操作级权限**：
   - 查看权限(can_view)
   - 添加权限(can_add)
   - 编辑权限(can_edit)
   - 删除权限(can_delete)

3. **区域级权限**：
   - 基于区域划分权限
   - 可为用户分配特定区域的权限
   - 操作类型包括"微型消防站"和"灭火器和呼吸器"

## 4. 接口设计

### 4.1 内部接口

#### 4.1.1 用户认证接口
```python
# 用户登录
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # 处理登录请求，验证用户名和密码

# 用户登出
@auth_bp.route('/logout')
@login_required
def logout():
    # 处理登出请求，清除会话
```

#### 4.1.2 微型消防站物资接口
```python
# 获取物资列表
@station_bp.route('/')
@login_required
def index():
    # 返回微型消防站物资列表，支持分页和筛选

# 添加物资
@station_bp.route('/add', methods=['POST'])
@login_required
def add_station():
    # 处理添加物资请求
```

#### 4.1.3 有效期预警接口
```python
# 获取预警列表
@admin_bp.route('/expiry_alert')
@login_required
def expiry_alert():
    # 返回所有预警物资，支持分页和筛选

# 发送预警邮件
@admin_bp.route('/send_expiry_alert_emails', methods=['POST'])
@login_required
@admin_required
def send_expiry_alert_emails():
    # 处理发送预警邮件请求
```

### 4.2 外部接口

#### 4.2.1 数据导入导出接口
```python
# 导出数据为Excel
@station_bp.route('/export')
@login_required
def export_stations():
    # 导出微型消防站物资数据为Excel文件

# 导入数据
@station_bp.route('/import', methods=['POST'])
@login_required
def import_stations():
    # 从Excel文件导入微型消防站物资数据
```

#### 4.2.2 邮件服务接口
```python
def send_emails_to_responsibles(person_dict, app, config, recipient_filter=None):
    """向各个负责人发送预警邮件"""
    # 配置SMTP连接
    # 遍历收件人
    # 发送邮件
    # 记录日志
```

## 5. 前端设计

### 5.1 页面布局
系统采用响应式设计，主要页面布局包括：

1. **主布局**：
   - 顶部导航栏：包含系统名称、用户信息和注销按钮
   - 左侧侧边栏：包含系统各功能模块的导航菜单
   - 主内容区：显示当前操作的内容
   - 底部页脚：版权信息和系统版本

2. **登录页面**：
   - 用户名输入框
   - 密码输入框
   - 登录按钮
   - 系统标题和欢迎信息

### 5.2 关键界面原型

#### 5.2.1 微型消防站物资管理页面
- 顶部筛选区：区域选择、物资名称搜索
- 操作按钮区：添加、导入、导出
- 数据表格区：分页显示物资信息
- 每条记录操作区：编辑、删除按钮

#### 5.2.2 有效期预警页面
- 顶部统计区：显示各预警级别的物资数量
- 筛选区：预警级别、区域、物资类型筛选
- 预警表格区：分页显示预警信息，按紧急程度排序
- 邮件发送区：选择收件人和发送按钮

#### 5.2.3 用户管理页面
- 用户列表区：显示所有用户信息
- 添加用户按钮
- 用户权限管理区：为每个用户分配权限

## 6. 安全设计

### 6.1 身份认证
- 使用Flask-Login实现用户认证
- 密码使用Werkzeug的generate_password_hash和check_password_hash进行哈希处理和验证
- 会话使用服务器端会话管理，设置会话超时时间

### 6.2 权限控制
- 基于装饰器的访问控制：login_required和admin_required
- 细粒度的数据访问控制，确保用户只能访问有权限的区域数据
- 前端根据用户权限动态显示或隐藏操作按钮

### 6.3 CSRF保护
- 使用Flask-WTF的CSRFProtect进行跨站请求伪造保护
- 所有表单请求必须包含有效的CSRF令牌
- AJAX请求通过头部传递CSRF令牌

### 6.4 输入验证
- 前端表单验证：使用HTML5表单验证和JavaScript验证
- 后端数据验证：使用WTForms进行表单验证
- 数据库输入过滤：防止SQL注入攻击

### 6.5 错误处理
- 全局错误处理器捕获异常
- 针对不同类型的错误返回友好的错误页面
- 敏感错误信息只在开发环境显示，生产环境隐藏详细错误信息

## 7. 性能优化设计

### 7.1 数据库优化
- 合理设计索引，提高查询效率
- 使用懒加载模式，避免不必要的数据加载
- 分页查询，限制单次返回数据量

### 7.2 页面优化
- 静态资源缓存
- 使用缓存破坏技术(cache busting)更新静态资源
- 减少HTTP请求数量，合并CSS和JavaScript文件
- 压缩HTML、CSS和JavaScript文件

### 7.3 后端优化
- 异步处理耗时操作：邮件发送
- 使用APScheduler进行任务调度，避免阻塞主线程
- 合理配置Waitress服务器的工作线程数

## 8. 部署设计

### 8.1 部署架构
```
┌─────────────────┐      ┌─────────────────┐
│  Windows服务器  │      │    SMTP服务器   │
├─────────────────┤      └─────────────────┘
│  Python环境     │              ▲
│                 │              │
│  Waitress服务器 │◄─────────────┘
│                 │
│  Flask应用      │
│                 │
│  SQLite数据库   │
└─────────────────┘
```

### 8.2 部署步骤

1. **环境准备**：
   - 安装Python 3.9+
   - 创建并激活虚拟环境
   - 安装所需依赖包

2. **应用配置**：
   - 配置数据库连接
   - 配置邮件服务器参数
   - 配置日志记录

3. **数据库初始化**：
   - 创建数据库表结构
   - 导入初始数据
   - 创建管理员账户

4. **服务器配置**：
   - 配置Waitress服务器
   - 设置启动脚本
   - 配置开机自启动

### 8.3 升级策略
- 备份数据库文件
- 停止旧版本服务
- 部署新版本代码
- 运行数据库迁移脚本
- 启动新版本服务
- 验证系统功能

## 9. 测试计划

### 9.1 单元测试
- 使用pytest框架进行单元测试
- 测试覆盖核心业务逻辑函数
- 测试各个模块的独立功能

### 9.2 集成测试
- 测试模块间的交互
- 测试数据流通过完整业务流程
- 测试与外部系统(如邮件服务器)的集成

### 9.3 性能测试
- 测试在大数据量下的系统响应时间
- 测试并发用户访问时系统的稳定性
- 测试定时任务的准确性和资源消耗

### 9.4 安全测试
- 测试身份认证机制
- 测试权限控制机制
- 测试CSRF防护措施
- 测试输入验证和过滤

## 10. 附录

### 10.1 技术选型理由
- **Flask框架**：轻量级、灵活、易于扩展，适合中小型应用
- **SQLite数据库**：无需独立数据库服务器，便于部署和维护
- **Bootstrap框架**：提供响应式设计，简化前端开发
- **Waitress服务器**：纯Python实现，无需额外依赖，在Windows平台稳定可靠

### 10.2 系统限制
- SQLite数据库不适合高并发访问，最大支持约100个并发用户
- 单服务器部署，无法实现负载均衡和高可用
- 邮件发送为同步操作，可能影响系统响应时间

### 10.3 未来扩展计划
- 支持更多类型的消防设备管理
- 添加移动端适配，支持手机访问
- 引入OCR技术，支持通过扫描录入设备信息
- 升级为分布式架构，提高系统可扩展性
```

## 核心实现要点

1. **有效期计算与预警**：
   - 通过物品名称与有效期规则表匹配，支持模糊匹配
   - 基于生产日期和有效期年数计算到期日期
   - 按剩余天数分级(已过期、30天内、60天内、90天内)，优先显示紧急预警

2. **细粒度权限控制**：
   - 使用装饰器实现控制器级别权限检查
   - 查询时加入权限过滤条件，确保数据安全
   - 在视图渲染时根据权限动态显示操作按钮

3. **邮件通知系统**：
   - 支持个性化邮件内容，为每位负责人生成其负责物品的列表
   - 实现定时自动发送和手动触发发送
   - 完整的邮件日志记录，包括成功和失败情况

4. **调度系统**：
   - 基于APScheduler实现定时任务
   - 支持每日、每周、每月三种定时模式
   - 实现任务配置的Web界面管理

这个详细设计文档提供了系统的完整架构、数据库设计、模块划分、接口定义以及部署和测试计划，为开发团队提供了清晰的实现指导。

