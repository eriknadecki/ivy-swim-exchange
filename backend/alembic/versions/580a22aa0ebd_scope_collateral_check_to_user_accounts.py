"""scope collateral check to user accounts

Revision ID: 580a22aa0ebd
Revises: a258f13ccb3c
Create Date: 2026-07-21 20:06:17.524006

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '580a22aa0ebd'
down_revision: Union[str, Sequence[str], None] = 'a258f13ccb3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("ck_accounts_cash_covers_held", "accounts", type_="check")
    op.create_check_constraint(
        "ck_accounts_cash_covers_held",
        "accounts",
        "owner_type != 'user' OR cash_balance_cents >= held_collateral_cents",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_accounts_cash_covers_held", "accounts", type_="check")
    op.create_check_constraint(
        "ck_accounts_cash_covers_held",
        "accounts",
        "cash_balance_cents >= held_collateral_cents",
    )
