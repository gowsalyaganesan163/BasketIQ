import pandas as pd


def clean_dataset(df, mapping):
    data = df.copy()

    data = data.rename(columns={
        mapping["transaction"]: "transaction_id",
        mapping["product"]: "product",
    })

    if mapping.get("date"):
        data = data.rename(columns={
            mapping["date"]: "date"
        })

        data["date"] = pd.to_datetime(
            data["date"],
            errors="coerce"
        )

    if mapping.get("quantity"):
        data = data.rename(columns={
            mapping["quantity"]: "quantity"
        })
    else:
        data["quantity"] = 1

    data = data.dropna(
        subset=["transaction_id", "product"]
    )

    data["product"] = (
        data["product"]
        .astype(str)
        .str.strip()
    )

    data = data[data["product"] != ""]

    data["quantity"] = pd.to_numeric(
        data["quantity"],
        errors="coerce"
    )

    data = data.dropna(subset=["quantity"])

    # Remove zero and negative quantities
    data = data[data["quantity"] > 0]

    # Keep one row per transaction-product combination
    data = data.drop_duplicates(
        subset=["transaction_id", "product"]
    )

    data = data.reset_index(drop=True)

    return data