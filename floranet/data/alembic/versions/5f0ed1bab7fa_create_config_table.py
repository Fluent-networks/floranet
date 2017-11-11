"""create config table

Revision ID: 5f0ed1bab7fa
Revises: f966d7f314d5
Create Date: 2017-05-16 16:04:05.229611

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET

# revision identifiers, used by Alembic.
revision = '5f0ed1bab7fa'
down_revision = 'f966d7f314d5'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'config',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('listen', INET, nullable=False),
        sa.Column('port', sa.Integer, nullable=False),
        sa.Column('webport', sa.Integer, nullable=False),
        sa.Column('apitoken', sa.String, nullable=False),
        sa.Column('freqband', sa.String, nullable=False),
        sa.Column('netid', sa.Integer, nullable=False),
        sa.Column('duplicateperiod', sa.Integer, nullable=False),
        sa.Column('fcrelaxed', sa.Boolean, nullable=False),
        sa.Column('otaastart', sa.Integer, nullable=False),
        sa.Column('otaaend', sa.Integer, nullable=False),
        sa.Column('macqueueing', sa.Boolean, nullable=False),
        sa.Column('macqueuelimit', sa.Integer, nullable=False),
        sa.Column('adrenable', sa.Boolean, nullable=False),
        sa.Column('adrmargin', sa.Float, nullable=False),
        sa.Column('adrcycletime', sa.Integer, nullable=False),
        sa.Column('adrmessagetime', sa.Integer, nullable=False),
        sa.Column('created', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated', sa.DateTime(timezone=True), nullable=False),
        )

def downgrade():
    op.drop_table('config')
