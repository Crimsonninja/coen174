"""empty message

Revision ID: b4d72c310e6d
Revises: 7d57f30187c0
Create Date: 2019-11-05 11:22:54.979570

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4d72c310e6d'
down_revision = '7d57f30187c0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('activities', sa.Column('status', sa.String(length=30), nullable=True))
    op.add_column('teams', sa.Column('approved', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('teams', 'approved')
    op.drop_column('activities', 'status')
    # ### end Alembic commands ###
