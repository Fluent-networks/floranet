"""create appif reflector azure_iot_https

Revision ID: bdf0f3bcffc7
Revises: 5f0ed1bab7fa
Create Date: 2017-07-08 14:21:54.736175

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET

# revision identifiers, used by Alembic.
revision = 'bdf0f3bcffc7'
down_revision = '5f0ed1bab7fa'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'appif_reflector',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False, unique=True),
        sa.Column('created', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated', sa.DateTime(timezone=True), nullable=False),
        )
    op.create_table(
        'appif_azure_iot_https',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False, unique=True),
        sa.Column('iothost', sa.String, nullable=False),
        sa.Column('keyname', sa.String, nullable=False),
        sa.Column('keyvalue', sa.String, nullable=False),
        sa.Column('poll_interval', sa.Integer, nullable=False),
        sa.Column('created', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated', sa.DateTime(timezone=True), nullable=False),
        )

def downgrade():
    op.drop_table('appif_azure_iot_https')
    op.drop_table('appif_reflector')
    