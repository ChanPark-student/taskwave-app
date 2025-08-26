
"""init tables

Revision ID: 0001_init
Revises: 
Create Date: 2025-08-26 00:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('school', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table('subjects',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
    )
    op.create_index('ix_subjects_user_id', 'subjects', ['user_id'], unique=False)

    op.create_table('weeks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('subject_id', sa.Integer(), sa.ForeignKey('subjects.id', ondelete="CASCADE"), nullable=False),
        sa.Column('week_index', sa.Integer(), nullable=False),
    )

    op.create_table('sessions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('week_id', sa.Integer(), sa.ForeignKey('weeks.id', ondelete="CASCADE"), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
    )

    op.create_table('materials',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('subject_id', sa.Integer(), sa.ForeignKey('subjects.id', ondelete="CASCADE"), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('storage_path', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_materials_subject_id', 'materials', ['subject_id'], unique=False)

    op.create_table('uploads',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=True),
        sa.Column('storage_path', sa.String(), nullable=False),
        sa.Column('size', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_uploads_user_id', 'uploads', ['user_id'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_uploads_user_id', table_name='uploads')
    op.drop_table('uploads')
    op.drop_index('ix_materials_subject_id', table_name='materials')
    op.drop_table('materials')
    op.drop_table('sessions')
    op.drop_table('weeks')
    op.drop_index('ix_subjects_user_id', table_name='subjects')
    op.drop_table('subjects')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
