"""create device name lat long enabled and otaa columns

Revision ID: 282e6b269222
Revises: 03fabc9f542b
Create Date: 2017-02-04 17:28:33.947208

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '282e6b269222'
down_revision = '03fabc9f542b'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('devices',
        sa.Column('name', sa.String(), nullable=False, server_default='device'))
    op.add_column('devices',
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('devices',
        sa.Column('otaa', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('devices',
        sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('devices',
        sa.Column('longitude', sa.Float(), nullable=True))


def downgrade():
    op.drop_column('devices', 'name')
    op.drop_column('devices', 'enabled')
    op.drop_column('devices', 'otaa')
    op.drop_column('devices', 'latitude')
    op.drop_column('devices', 'longitude')
