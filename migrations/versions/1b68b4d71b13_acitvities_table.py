"""Acitvities Table

Revision ID: 1b68b4d71b13
Revises: 51b3871e0eb6
Create Date: 2020-02-02 12:43:04.034839

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1b68b4d71b13'
down_revision = '51b3871e0eb6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('activity',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('title', sa.String(length=64), nullable=True),
    sa.Column('activity_type', sa.String(length=64), nullable=True),
    sa.Column('distance', sa.Float(), nullable=True),
    sa.Column('duration', sa.Float(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_activity_type'), 'activity', ['activity_type'], unique=False)
    op.create_index(op.f('ix_activity_timestamp'), 'activity', ['timestamp'], unique=False)
    op.create_index(op.f('ix_activity_title'), 'activity', ['title'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_activity_title'), table_name='activity')
    op.drop_index(op.f('ix_activity_timestamp'), table_name='activity')
    op.drop_index(op.f('ix_activity_activity_type'), table_name='activity')
    op.drop_table('activity')
    # ### end Alembic commands ###
