"""add_storage_path_to_prompt_challenges

Revision ID: a8d8e9c0b1a2
Revises: 6b56a3ef6fe0
Create Date: 2026-07-05 02:08:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a8d8e9c0b1a2"
down_revision: Union[str, Sequence[str], None] = "b8556481fe05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "prompt_challenges",
        sa.Column("storage_path", sa.String(length=512), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("prompt_challenges", "storage_path")
