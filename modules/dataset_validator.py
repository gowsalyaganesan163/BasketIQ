import pandas as pd


def validate_dataset(df, mapping):
    errors = []
    warnings = []

    if df is None or df.empty:
        errors.append("Dataset is empty.")
        return errors, warnings

    required_fields = ["transaction", "product"]

    for field in required_fields:
        column = mapping.get(field)

        if not column:
            errors.append(f"{field} column has not been selected.")

        elif column not in df.columns:
            errors.append(f"Selected {field} column does not exist.")

    date_column = mapping.get("date")

    if date_column and date_column not in df.columns:
        errors.append("Selected date column does not exist.")

    quantity_column = mapping.get("quantity")

    if quantity_column and quantity_column not in df.columns:
        errors.append("Selected quantity column does not exist.")

    if not errors:
        transaction_col = mapping["transaction"]
        product_col = mapping["product"]

        if df[transaction_col].isna().any():
            warnings.append("Missing transaction IDs detected.")

        if df[product_col].isna().any():
            warnings.append("Missing product values detected.")

        if df[transaction_col].nunique() < 2:
            warnings.append("Dataset contains fewer than two transactions.")

    return errors, warnings