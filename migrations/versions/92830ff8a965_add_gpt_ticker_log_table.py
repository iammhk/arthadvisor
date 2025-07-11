"""add gpt_ticker_log table

Revision ID: 92830ff8a965
Revises: c5038092c1d4
Create Date: 2025-07-08 23:57:38.539974

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '92830ff8a965'
down_revision = 'c5038092c1d4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ltp')
    op.drop_table('symbols')
    op.drop_table('finance_data')
    op.drop_table('timestamps')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
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
    op.create_table('ltp',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('symbol', sa.VARCHAR(), nullable=False),
    sa.Column('ltp', sa.FLOAT(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('symbol')
    )
    # ### end Alembic commands ###
