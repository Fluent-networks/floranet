"""create appif file text store

Revision ID: d5ed30f62f76
Revises: 09a18d3d3b1e
Create Date: 2018-07-30 18:47:12.417385

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd5ed30f62f76'
down_revision = '09a18d3d3b1e'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'appif_file_text_store',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False, unique=True),
        sa.Column('file', sa.String, nullable=False, unique=True),
        sa.Column('created', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated', sa.DateTime(timezone=True), nullable=False),
        )

def downgrade():
    op.drop_table('appif_file_text_store')
