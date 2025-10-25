"""
CSV Parser Service

This service handles parsing CSV bank statement files from French banks.
Specifically designed for Crédit Agricole format but can be extended.
"""

import csv
import re
from io import StringIO
from typing import Any

from app.exceptions import CSVProcessingError
from app.logger import get_logger

logger = get_logger(__name__)


async def parse_csv(file_bytes: bytes) -> dict[str, Any]:
    """
    Parse a CSV bank statement file and extract structured data.

    Args:
        file_bytes: The CSV file content as bytes

    Returns:
        Dictionary with:
        - raw_csv: Original CSV content as string
        - metadata: Dict with account info (holder, account_number, balance, date_range)
        - transactions: List of transaction dicts with date, description, debit, credit

    Raises:
        CSVProcessingError: If the CSV cannot be parsed or is invalid

    How it works:
    1. Decode bytes to UTF-8 string (with fallback to latin-1 for French characters)
    2. Extract metadata from header lines
    3. Find the transaction table (starts with "Date;Libellé;...")
    4. Parse each transaction row into structured format
    5. Return both raw data and structured transactions
    """
    try:
        # Try UTF-8 first, fallback to latin-1 for French characters (é, è, etc.)
        try:
            csv_content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            csv_content = file_bytes.decode("latin-1")

        if not csv_content.strip():
            raise CSVProcessingError(
                "CSV file is empty",
                details={"file_size": len(file_bytes)},
            )

        logger.info(f"Decoded CSV file: {len(csv_content)} characters")

        # Extract metadata from header
        metadata = _extract_metadata(csv_content)

        # Parse transactions
        transactions = _parse_transactions(csv_content)

        if not transactions:
            raise CSVProcessingError(
                "No transactions found in CSV",
                details={"content_length": len(csv_content)},
            )

        logger.info(f"Successfully parsed {len(transactions)} transactions from CSV")

        return {
            "raw_csv": csv_content,
            "metadata": metadata,
            "transactions": transactions,
        }

    except CSVProcessingError:
        # Re-raise our own exceptions
        raise
    except Exception as e:
        # Catch any other unexpected errors
        raise CSVProcessingError(
            "Failed to process CSV file",
            details={"error": str(e), "type": type(e).__name__},
        ) from e


def _extract_metadata(csv_content: str) -> dict[str, str]:
    """
    Extract metadata from CSV header lines.

    Expected format (Crédit Agricole):
    - Line with account holder name (MONSIEUR/MADAME ...)
    - Line with account number (Compte de Dépôt carte n° ...)
    - Line with balance (Solde au DD/MM/YYYY ... €)
    - Line with date range (Liste des opérations ... entre le ... et le ...)
    """
    lines = csv_content.split("\n")
    metadata: dict[str, str] = {}

    for line in lines[:15]:  # Check first 15 lines for metadata
        # Account holder (MONSIEUR/MADAME)
        if "MONSIEUR" in line or "MADAME" in line:
            metadata["account_holder"] = line.strip().replace(";", "").strip()

        # Account number
        if "Compte" in line:
            # Extract number after "n°" (flexible pattern to handle encoding issues)
            match = re.search(r"n.?\s*(\d+)", line)
            if match:
                metadata["account_number"] = match.group(1)

        # Balance
        if "Solde au" in line:
            # Extract date and amount (flexible € pattern to handle encoding issues)
            match = re.search(r"Solde au (\d{2}/\d{2}/\d{4})\s*([\d\s,]+)", line)
            if match:
                metadata["balance_date"] = match.group(1)
                # Remove all whitespace (including non-breaking spaces)
                metadata["balance"] = (
                    match.group(2).replace(" ", "").replace("\xa0", "").strip()
                )

        # Date range
        if "Liste des opérations" in line and "entre le" in line:
            match = re.search(
                r"entre le (\d{2}/\d{2}/\d{4}) et le (\d{2}/\d{2}/\d{4})", line
            )
            if match:
                metadata["period_start"] = match.group(1)
                metadata["period_end"] = match.group(2)

    return metadata


def _parse_transactions(csv_content: str) -> list[dict[str, Any]]:
    """
    Parse transaction rows from CSV content.

    Expected format:
    Date;Libellé;Débit euros;Crédit euros;
    DD/MM/YYYY;"DESCRIPTION";amount;;  (for debit)
    DD/MM/YYYY;"DESCRIPTION";;amount;  (for credit)

    Descriptions can span multiple lines within quotes.
    """
    transactions: list[dict[str, Any]] = []

    # Find where transactions start (line with column headers)
    lines = csv_content.split("\n")
    transaction_start_idx = -1

    for idx, line in enumerate(lines):
        if "Date;Libellé;Débit" in line or "Date;Libell" in line:
            transaction_start_idx = idx + 1
            break

    if transaction_start_idx == -1:
        logger.warning("Could not find transaction header in CSV")
        return transactions

    # Parse transactions using CSV reader (handles multi-line fields)
    transaction_content = "\n".join(lines[transaction_start_idx:])
    csv_reader = csv.reader(StringIO(transaction_content), delimiter=";")

    for row in csv_reader:
        # Skip empty rows
        if not row or len(row) < 4:
            continue

        # Skip rows without a valid date
        date = row[0].strip()
        if not re.match(r"\d{2}/\d{2}/\d{4}", date):
            continue

        description = row[1].strip() if len(row) > 1 else ""
        debit_str = row[2].strip() if len(row) > 2 else ""
        credit_str = row[3].strip() if len(row) > 3 else ""

        # Convert amounts to float (handle French format: 1 234,56 → 1234.56)
        debit = _parse_amount(debit_str) if debit_str else None
        credit = _parse_amount(credit_str) if credit_str else None

        transactions.append(
            {
                "date": date,
                "description": description,
                "debit": debit,
                "credit": credit,
            }
        )

    return transactions


def _parse_amount(amount_str: str) -> float | None:
    """
    Parse French-formatted amount to float.

    Examples:
    - "15,00" → 15.0
    - "3 312,37" → 3312.37
    - "1 234,56" → 1234.56
    """
    try:
        # Remove all whitespace (including non-breaking spaces), replace comma with dot
        # Keep only digits, comma, and dot
        cleaned = "".join(c for c in amount_str if c.isdigit() or c in ".,")
        cleaned = cleaned.replace(",", ".")
        return float(cleaned)
    except ValueError:
        logger.warning(f"Could not parse amount: {amount_str}")
        return None
