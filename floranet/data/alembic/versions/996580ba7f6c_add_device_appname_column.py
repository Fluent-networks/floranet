"""add device appname column

Revision ID: 996580ba7f6c
Revises: 66bc8df33d36
Create Date: 2017-07-12 16:19:12.192935

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '996580ba7f6c'
down_revision = '66bc8df33d36'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('devices',
        sa.Column('appname', sa.String(), nullable=True))


def downgrade():
    op.drop_column('devices', 'appname')
