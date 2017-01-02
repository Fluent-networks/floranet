"""Change device deveui column unique

Revision ID: b664cccf21a2
Revises: ad38a9fad16b
Create Date: 2016-12-16 13:41:18.297672

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b664cccf21a2'
down_revision = 'ad38a9fad16b'
branch_labels = None
depends_on = None

def upgrade():
    # Applies a unique constraint on the devices table for the column deveui
    op.create_index('devices_deveui_unique', 'devices', ['deveui'], unique=True)

def downgrade():
    op.drop_index('devices_deveui_unique')
    
