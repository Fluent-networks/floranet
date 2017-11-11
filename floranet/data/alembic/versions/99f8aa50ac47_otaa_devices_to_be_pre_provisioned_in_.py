"""OTAA devices to be pre-provisioned in the database.
Make columns devaddr nwkskey appskey nullable; deveui non-nullable.

Revision ID: 99f8aa50ac47
Revises: 282e6b269222
Create Date: 2017-02-20 10:01:14.549853

"""
from alembic import op
from sqlalchemy.sql import table, column
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '99f8aa50ac47'
down_revision = '282e6b269222'
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column('devices', 'devaddr', nullable=True)
    op.alter_column('devices', 'nwkskey', nullable=True)
    op.alter_column('devices', 'appskey', nullable=True)
    op.alter_column('devices', 'deveui', nullable=False)

def update_null_values(c):
    t = table('devices', column(c))
    op.execute(t.update().values(**{c: 0}))       
    
def downgrade():
    update_null_values('devaddr')
    op.alter_column('devices', 'devaddr', nullable=False)
    update_null_values('nwkskey')
    op.alter_column('devices', 'nwkskey', nullable=False)
    update_null_values('appskey')
    op.alter_column('devices', 'appskey', nullable=False)
    op.alter_column('devices', 'deveui', nullable=True)       
