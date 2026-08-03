"""add special_status to financial_profiles

Revision ID: 2a3d67e97020
Revises: f773e7d4d8b6
Create Date: 2026-08-03 22:08:25.292513

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a3d67e97020'
down_revision: Union[str, None] = 'f773e7d4d8b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "financial_profiles",
        sa.Column("special_status", sa.ARRAY(sa.String()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("financial_profiles", "special_status")
