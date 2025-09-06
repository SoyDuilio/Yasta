"""Re-create role column
Revision ID: 29f6b6071791
Revises: 48eb359cad2a
Create Date: 2025-06-07 12:13:11.275466
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '29f6b6071791'
down_revision: Union[str, None] = '48eb359cad2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column(
        'role',
        postgresql.ENUM(
            'authenticated',
            'client_freemium',
            'client_paid',
            'staff_collaborator',
            'staff_manager',
            'staff_ceo',
            'admin',
            name='userrole',
            create_type=False
        ),
        server_default=sa.text("'authenticated'::userrole"),
        nullable=False
    ))

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'role')