import pandas as pd
from mlxtend.preprocessing import TransactionEncoder


def build_transactions(df):
    transactions = (
        df.groupby("transaction_id")["product"]
        .apply(lambda products: list(set(products)))
        .tolist()
    )

    return transactions


def encode_transactions(transactions):
    encoder = TransactionEncoder()

    encoded_array = encoder.fit(
        transactions
    ).transform(transactions)

    encoded_df = pd.DataFrame(
        encoded_array,
        columns=encoder.columns_
    )

    return encoded_df