"""empty message

Revision ID: 46b6084fd26d
Revises: 50416b05c63e
Create Date: 2015-03-05 22:44:08.076228

"""

# revision identifiers, used by Alembic.
revision = '46b6084fd26d'
down_revision = '50416b05c63e'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.alter_column(
      table_name='datapoints', 
      column_name='created_at', 
      type_=postgresql.TIMESTAMP(), 
      autoincrement=False, 
      nullable=True)
    op.alter_column(
      table_name='datapoints', 
      column_name='timestamp', 
      type_=postgresql.TIMESTAMP(), 
      autoincrement=False, 
      nullable=True)
    op.alter_column(
      table_name='notes', 
      column_name='created_at', 
      type_=postgresql.TIMESTAMP(), 
      autoincrement=False, 
      nullable=True)


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    pass
    ### end Alembic commands ###
