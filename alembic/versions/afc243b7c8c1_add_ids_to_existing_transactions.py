"""add_ids_to_existing_transactions

Revision ID: afc243b7c8c1
Revises: 79dc7c44b520
Create Date: 2025-10-25 22:17:18.284382

"""

import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "afc243b7c8c1"
down_revision: Union[str, None] = "79dc7c44b520"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add sequential IDs to all transactions in existing statements.

    This data migration updates the transactions JSONB column to add
    an 'id' field (1-based) to each transaction object.

    Before: {"date": "...", "description": "...", ...}
    After:  {"id": 1, "date": "...", "description": "...", ...}
    """
    # Get database connection
    conn = op.get_bind()

    # Find all statements where transactions don't have IDs
    # Check if first transaction has 'id' key
    result = conn.execute(
        text("""
            SELECT id, transactions
            FROM statements
            WHERE NOT (transactions::jsonb->0 ? 'id')
        """)
    )

    statements_updated = 0

    # Process each statement
    for row in result:
        statement_id = row[0]
        transactions_json = row[1]

        # Parse JSON (it's stored as JSON/JSONB)
        transactions = (
            json.loads(transactions_json)
            if isinstance(transactions_json, str)
            else transactions_json
        )

        # Add sequential IDs to each transaction
        for idx, transaction in enumerate(transactions, start=1):
            transaction["id"] = idx

        # Update the statement with modified transactions
        conn.execute(
            text("UPDATE statements SET transactions = :transactions WHERE id = :id"),
            {"transactions": json.dumps(transactions), "id": statement_id},
        )

        statements_updated += 1

    print(f"✅ Added transaction IDs to {statements_updated} statements")


def downgrade() -> None:
    """
    Remove IDs from all transactions.

    This reverses the migration by removing the 'id' field from
    all transaction objects.
    """
    # Get database connection
    conn = op.get_bind()

    # Get all statements
    result = conn.execute(text("SELECT id, transactions FROM statements"))

    statements_updated = 0

    # Process each statement
    for row in result:
        statement_id = row[0]
        transactions_json = row[1]

        # Parse JSON
        transactions = (
            json.loads(transactions_json)
            if isinstance(transactions_json, str)
            else transactions_json
        )

        # Remove 'id' field from each transaction if it exists
        for transaction in transactions:
            transaction.pop("id", None)

        # Update the statement
        conn.execute(
            text("UPDATE statements SET transactions = :transactions WHERE id = :id"),
            {"transactions": json.dumps(transactions), "id": statement_id},
        )

        statements_updated += 1

    print(f"✅ Removed transaction IDs from {statements_updated} statements")
