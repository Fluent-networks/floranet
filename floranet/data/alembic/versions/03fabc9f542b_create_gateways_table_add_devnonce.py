"""create gateways table add device nonce array

Revision ID: 03fabc9f542b
Revises: b664cccf21a2
Create Date: 2017-02-04 11:24:46.937314

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET

# revision identifiers, used by Alembic.
revision = '03fabc9f542b'
down_revision = 'b664cccf21a2'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'gateways',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('host', INET, nullable=False, unique=True),
        sa.Column('name', sa.String, nullable=True),
        sa.Column('enabled', sa.Boolean, nullable=False, default=True),
        sa.Column('eui', sa.Numeric, nullable=False, unique=True),
        sa.Column('power', sa.Integer, nullable=False),
        sa.Column('port', sa.String, nullable=True),
        sa.Column('latitude', sa.Float, nullable=True),
        sa.Column('longitude', sa.Float, nullable=True),
        sa.Column('created', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated', sa.DateTime(timezone=True), nullable=False),
        )
    op.add_column('devices',
        sa.Column('devnonce', sa.dialects.postgresql.ARRAY(sa.Integer())))


def downgrade():
    op.drop_table('gateways')
    op.drop_column('devices', 'devnonce')