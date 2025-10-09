"""
Security utilities for PII masking and connection string sanitization
"""

import polars as pl
import re
from typing import List


def mask_pii_columns(df: pl.DataFrame, custom_keywords: List[str] = None) -> pl.DataFrame:
    """
    Automatically mask columns that likely contain PII

    Args:
        df: DataFrame to mask
        custom_keywords: Additional PII keywords beyond defaults

    Returns:
        DataFrame with masked PII columns
    """
    pii_keywords = [
        'ssn', 'social', 'tax_id', 'national_id',
        'credit_card', 'card_number', 'cvv', 'card_holder',
        'password', 'passwd', 'secret', 'token', 'api_key',
        'email', 'e_mail', 'mail',
        'phone', 'mobile', 'cell', 'telephone',
        'address', 'street', 'zip', 'postal', 'zipcode',
        'passport', 'license', 'drivers',
        'account_number', 'routing',
        'dob', 'date_of_birth', 'birthdate',
        'salary', 'wage', 'income', 'compensation'
    ]

    if custom_keywords:
        pii_keywords.extend(custom_keywords)

    masked_cols = []
    for col in df.columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in pii_keywords):
            masked_cols.append(col)
            # Replace with masked value
            df = df.with_columns(
                pl.lit("***PII_MASKED***").alias(col)
            )

    if masked_cols:
        print(f"🔒 Masked PII columns: {', '.join(masked_cols)}\n")

    return df


def sanitize_connection_string(connection_string: str) -> str:
    """
    Sanitize connection string by removing password

    Args:
        connection_string: Database connection string

    Returns:
        Sanitized connection string with password removed
    """
    return re.sub(r':([^:@]+)@', ':***@', connection_string)
