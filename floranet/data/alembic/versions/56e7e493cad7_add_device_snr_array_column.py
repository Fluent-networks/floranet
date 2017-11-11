"""Add device snr array column

Revision ID: 56e7e493cad7
Revises: 99f8aa50ac47
Create Date: 2017-03-01 20:00:55.501494

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '56e7e493cad7'
down_revision = '99f8aa50ac47'
branch_labels = None
depends_on = None

# Replace multiple snr columns with a snr array column
def upgrade():
    op.drop_column('devices', 'snr1')
    op.drop_column('devices', 'snr2')
    op.drop_column('devices', 'snr3')
    op.drop_column('devices', 'snr4')
    op.drop_column('devices', 'snr5')
    op.drop_column('devices', 'snr6')
    op.drop_column('devices', 'snr7')
    op.drop_column('devices', 'snr8')
    op.drop_column('devices', 'snr9')
    op.drop_column('devices', 'snr10')
    op.drop_column('devices', 'snr11')
    op.add_column('devices',
        sa.Column('snr', sa.dialects.postgresql.ARRAY(sa.Float())))

def downgrade():
    op.add_column('devices',
        sa.Column('snr1', sa.Float(), nullable=True))
    op.add_column('devices',
        sa.Column('snr2', sa.Float(), nullable=True))
    op.add_column('devices',
        sa.Column('snr3', sa.Float(), nullable=True))
    op.add_column('devices',
        sa.Column('snr4', sa.Float(), nullable=True))
    op.add_column('devices',
        sa.Column('snr5', sa.Float(), nullable=True))
    op.add_column('devices',
        sa.Column('snr6', sa.Float(), nullable=True))
    op.add_column('devices',
        sa.Column('snr7', sa.Float(), nullable=True))
    op.add_column('devices',
        sa.Column('snr8', sa.Float(), nullable=True))
    op.add_column('devices',
        sa.Column('snr9', sa.Float(), nullable=True))
    op.add_column('devices',
        sa.Column('snr10', sa.Float(), nullable=True))
    op.add_column('devices',
        sa.Column('snr11', sa.Float(), nullable=True))
    op.drop_column('devices', 'snr')
