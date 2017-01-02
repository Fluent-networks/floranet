"""Add device ADR tracking, creation, update and fcnterror columns

Revision ID: ad38a9fad16b
Revises: e7ff8a1b22fd
Create Date: 2016-12-15 22:25:48.605782

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ad38a9fad16b'
down_revision = 'e7ff8a1b22fd'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('devices',
        sa.Column('adr_datr', sa.String(), nullable=True))
    op.add_column('devices',
        sa.Column('snr_pointer', sa.Integer(), nullable=True))
    op.add_column('devices',
        sa.Column('snr_average', sa.Float, nullable=True))    
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
    op.add_column('devices',
        sa.Column('fcnterror', sa.Boolean(), nullable=False, default=False))
    op.add_column('devices',
        sa.Column('created', sa.DateTime(timezone=True)))
    op.add_column('devices',
        sa.Column('updated', sa.DateTime(timezone=True)))

def downgrade():
    op.drop_column('devices', 'adr_datr')
    op.drop_column('devices', 'snr_pointer')
    op.drop_column('devices', 'snr_average')
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
    op.drop_column('devices', 'fcnterror')  
    op.drop_column('devices', 'created')
    op.drop_column('devices', 'updated')
