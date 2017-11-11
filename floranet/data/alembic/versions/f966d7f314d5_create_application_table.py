"""create application table

Revision ID: f966d7f314d5
Revises: 56e7e493cad7
Create Date: 2017-03-20 13:27:04.791521

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f966d7f314d5'
down_revision = '56e7e493cad7'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'applications',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('appeui', sa.Numeric, nullable=False, unique=True),
        sa.Column('name', sa.String, nullable=True),
        sa.Column('domain', sa.String, nullable=True),
        sa.Column('appnonce', sa.Integer, nullable=False),
        sa.Column('appkey', sa.Numeric, nullable=False),
        sa.Column('fport', sa.Integer, nullable=False),        
        sa.Column('modname', sa.String, nullable=False),
        sa.Column('proto', sa.String, nullable=False),
        sa.Column('listen', sa.String, nullable=False),
        sa.Column('port', sa.Integer, nullable=False),
        sa.Column('created', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated', sa.DateTime(timezone=True), nullable=False),
        )

def downgrade():
    op.drop_table('applications')
