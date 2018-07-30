"""create azure iot mqtt table

Revision ID: 09a18d3d3b1e
Revises: d56db793263d
Create Date: 2017-12-05 13:30:03.219377

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '09a18d3d3b1e'
down_revision = 'd56db793263d'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'appif_azure_iot_mqtt',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False, unique=True),
        sa.Column('iothost', sa.String, nullable=False),
        sa.Column('keyname', sa.String, nullable=False),
        sa.Column('keyvalue', sa.String, nullable=False),
        sa.Column('created', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated', sa.DateTime(timezone=True), nullable=False),
    )

def downgrade():
    op.drop_table('appif_azure_iot_mqtt')

