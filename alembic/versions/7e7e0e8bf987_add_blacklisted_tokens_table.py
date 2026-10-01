"""add blacklisted_tokens table

Revision ID: 7e7e0e8bf987
Revises: fabfed50145d
Create Date: 2026-10-01 ...

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7e7e0e8bf987"
down_revision: Union[str, Sequence[str], None] = "fabfed50145d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "blacklisted_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("jti", sa.String(length=255), nullable=False),
        sa.Column("blacklisted_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_blacklisted_tokens_jti"), "blacklisted_tokens", ["jti"], unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_blacklisted_tokens_jti"), table_name="blacklisted_tokens")
    op.drop_table("blacklisted_tokens")
