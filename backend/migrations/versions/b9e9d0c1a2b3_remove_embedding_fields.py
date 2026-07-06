"""remove_embedding_fields_from_prompt_challenges

Revision ID: b9e9d0c1a2b3
Revises: a8d8e9c0b1a2
Create Date: 2026-07-05 02:35:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b9e9d0c1a2b3"
down_revision: Union[str, Sequence[str], None] = "a8d8e9c0b1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column("prompt_challenges", "target_embedding")
    op.drop_column("prompt_challenges", "embedding_model_name")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "prompt_challenges",
        sa.Column("target_embedding", sa.JSON(), nullable=True),
    )
    op.add_column(
        "prompt_challenges",
        sa.Column("embedding_model_name", sa.String(length=100), nullable=True),
    )
