"""添加定时任务配置表

Revision ID: scheduler_table
Revises: <your_previous_revision>
Create Date: 2023-04-15 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# 修改为上一个迁移脚本的ID
revision = 'scheduler_table'
# 查找您系统中最后一个迁移脚本的ID并填入此处
down_revision = '实际的前一个迁移版本ID'
branch_labels = None
depends_on = None

def upgrade():
    # 创建定时任务配置表
    op.create_table('scheduler_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('enabled', sa.Boolean(), default=True),
        sa.Column('frequency_type', sa.String(length=20), nullable=False),
        sa.Column('execution_time', sa.String(length=10), nullable=False),
        sa.Column('day_of_week', sa.String(length=10)),
        sa.Column('day_of_month', sa.Integer()),
        sa.Column('warning_levels', sa.String(length=100)),
        sa.Column('recipient_filter', sa.String(length=200)),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.Integer()),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # 删除定时任务配置表
    op.drop_table('scheduler_configs')
