"""Create device table

Revision ID: e7ff8a1b22fd
Revises: 
Create Date: 2016-10-10 19:32:50.611470

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e7ff8a1b22fd'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'devices',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('deveui', sa.Numeric, nullable=True),
        sa.Column('devaddr', sa.Integer, nullable=False),
        sa.Column('appeui', sa.Numeric, nullable=False),
        sa.Column('nwkskey', sa.Numeric, nullable=False),
        sa.Column('appskey', sa.Numeric, nullable=False),
        sa.Column('tx_chan', sa.Integer, nullable=True),
        sa.Column('tx_datr', sa.String, nullable=True),
        sa.Column('gw_addr', sa.String, nullable=True),
        sa.Column('fcntup', sa.Integer, server_default="0", nullable=False),
        sa.Column('fcntdown', sa.Integer, server_default="0", nullable=False),
        )

def downgrade():
    op.drop_table('devices')
