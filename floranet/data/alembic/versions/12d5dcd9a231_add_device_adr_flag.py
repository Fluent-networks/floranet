"""Add device ADR flag

Revision ID: 12d5dcd9a231
Revises: 996580ba7f6c
Create Date: 2017-08-12 13:11:07.474645

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '12d5dcd9a231'
down_revision = '996580ba7f6c'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('devices',
        sa.Column('adr', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    op.drop_column('devices', 'adr')
