"""create application app interfaces relationship

Revision ID: 66bc8df33d36
Revises: bdf0f3bcffc7
Create Date: 2017-07-08 18:28:26.093817

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '66bc8df33d36'
down_revision = 'bdf0f3bcffc7'
branch_labels = None
depends_on = None

# Create a polymorphic relationship between Applicaiton and
# the relevant application interface classe. The columns
# interfaceclass_id and interfaceclass_type are used to identify
# the id and type of the other class.

# Remove columns here that should be owned by the applicaiton
# interface class

def upgrade():
    op.create_table(
        'appinterfaces',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('interfaces_id', sa.Integer),
        sa.Column('interfaces_type', sa.String),
        )
    op.drop_column('applications', 'modname')
    op.drop_column('applications', 'proto')
    op.drop_column('applications', 'listen')
    op.drop_column('applications', 'port')
    op.add_column('applications',
                  sa.Column('appinterface_id', sa.Integer, nullable=True))
    
def downgrade():
    op.drop_table('appinterfaces')
    op.drop_column('applications', 'appinterface_id')
