"""Add data_properties table

Revision ID: d56db793263d
Revises: 12d5dcd9a231
Create Date: 2017-08-20 14:42:53.285592

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd56db793263d'
down_revision = '12d5dcd9a231'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'app_properties',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('application_id', sa.Integer()),
            sa.Column('port', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('type', sa.String(), nullable=False),
            sa.Column('created', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated', sa.DateTime(timezone=True), nullable=False),
            )

def downgrade():
    op.drop_table('app_properties')
