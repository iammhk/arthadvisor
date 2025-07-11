"""add profile_pic to user

Revision ID: bf206005532d
Revises: e84226b70864
Create Date: 2025-07-09 09:45:53.079125

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bf206005532d'
down_revision = 'e84226b70864'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('symbols')
    op.drop_table('finance_data')
    op.drop_table('timestamps')
    op.drop_table('ltp')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('profile_pic', sa.String(length=256), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('profile_pic')

    op.create_table('ltp',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('symbol', sa.VARCHAR(), nullable=False),
    sa.Column('ltp', sa.FLOAT(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('symbol')
    )
    op.create_table('timestamps',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('symbol', sa.VARCHAR(), nullable=False),
    sa.Column('timestamp', sa.DATETIME(), nullable=False),
    sa.Column('operation', sa.VARCHAR(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('finance_data',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('symbol', sa.VARCHAR(), nullable=True),
    sa.Column('date', sa.DATE(), nullable=True),
    sa.Column('open', sa.FLOAT(), nullable=True),
    sa.Column('high', sa.FLOAT(), nullable=True),
    sa.Column('low', sa.FLOAT(), nullable=True),
    sa.Column('close', sa.FLOAT(), nullable=True),
    sa.Column('volume', sa.FLOAT(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('symbol', 'date', name=op.f('_symbol_date_uc'))
    )
    op.create_table('symbols',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(), nullable=True),
    sa.Column('yahoo_symbol', sa.VARCHAR(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('yahoo_symbol', name=op.f('_yahoo_symbol_uc'))
    )
    # ### end Alembic commands ###
