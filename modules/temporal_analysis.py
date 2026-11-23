import pandas as pd

from modules.transaction_builder import (
    build_transactions,
    encode_transactions
)

from modules.association_mining import (
    mine_associations
)

from modules.rule_evaluation import (
    evaluate_rules
)


def split_time_periods(df, split_date=None):
    if "date" not in df.columns:
        raise ValueError("Dataset has no date column.")

    data = df.dropna(subset=["date"]).copy()

    if data.empty:
        raise ValueError("No valid dates found.")

    if split_date is None:
        split_date = data["date"].median()

    split_date = pd.to_datetime(split_date)

    earlier = data[data["date"] <= split_date]
    recent = data[data["date"] > split_date]

    return earlier, recent, split_date


def mine_period(
    df,
    min_support=0.02,
    min_confidence=0.30,
    min_lift=1.0
):
    transactions = build_transactions(df)

    if len(transactions) < 2:
        return None

    encoded = encode_transactions(transactions)

    itemsets, rules = mine_associations(
        encoded,
        min_support=min_support,
        min_confidence=min_confidence
    )

    rules = evaluate_rules(
        rules,
        min_confidence=min_confidence,
        min_lift=min_lift
    )

    return rules


def analyze_periods(
    df,
    split_date=None,
    min_support=0.02,
    min_confidence=0.30,
    min_lift=1.0
):
    earlier, recent, split_date = split_time_periods(
        df,
        split_date
    )

    earlier_rules = mine_period(
        earlier,
        min_support,
        min_confidence,
        min_lift
    )

    recent_rules = mine_period(
        recent,
        min_support,
        min_confidence,
        min_lift
    )

    return {
        "earlier_rules": earlier_rules,
        "recent_rules": recent_rules,
        "split_date": split_date,
        "earlier_transactions": earlier["transaction_id"].nunique(),
        "recent_transactions": recent["transaction_id"].nunique()
    }