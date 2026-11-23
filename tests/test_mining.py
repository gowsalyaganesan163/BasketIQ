import pandas as pd

from modules.preprocessing import clean_dataset
from modules.transaction_builder import build_transactions, encode_transactions
from modules.association_mining import mine_associations
from modules.rule_evaluation import evaluate_rules, format_rules


def sample_data():
    return pd.DataFrame({
        "Invoice": ["T1", "T1", "T2", "T2", "T3", "T3", "T4", "T4", "T5"],
        "Product": ["Milk", "Bread", "Milk", "Bread", "Milk", "Eggs", "Bread", "Eggs", "Milk"],
        "Quantity": [1, 2, 1, 1, 1, 2, 1, 1, 1],
        "Date": [
            "2024-01-01", "2024-01-01",
            "2024-01-02", "2024-01-02",
            "2024-01-03", "2024-01-03",
            "2024-01-04", "2024-01-04",
            "2024-01-05"
        ]
    })


def sample_mapping():
    return {
        "transaction": "Invoice",
        "product": "Product",
        "date": "Date",
        "quantity": "Quantity"
    }


def test_clean_dataset():
    df = sample_data()

    cleaned = clean_dataset(df, sample_mapping())

    assert "transaction_id" in cleaned.columns
    assert "product" in cleaned.columns
    assert "quantity" in cleaned.columns
    assert cleaned["product"].isna().sum() == 0


def test_clean_dataset_removes_invalid_rows():
    df = pd.DataFrame({
        "Invoice": ["T1", "T2", "T3", "T4"],
        "Product": ["Milk", None, "Bread", "Eggs"],
        "Quantity": [2, 1, 0, -1]
    })

    mapping = {
        "transaction": "Invoice",
        "product": "Product",
        "quantity": "Quantity"
    }

    cleaned = clean_dataset(df, mapping)

    assert len(cleaned) == 1
    assert cleaned.iloc[0]["product"] == "Milk"


def test_build_transactions():
    df = sample_data()

    cleaned = clean_dataset(df, sample_mapping())
    transactions = build_transactions(cleaned)

    assert len(transactions) == 5
    assert all(isinstance(transaction, list) for transaction in transactions)


def test_encode_transactions():
    transactions = [
        ["Milk", "Bread"],
        ["Milk", "Eggs"],
        ["Bread", "Eggs"]
    ]

    encoded = encode_transactions(transactions)

    assert set(encoded.columns) == {"Milk", "Bread", "Eggs"}
    assert len(encoded) == 3


def test_mine_associations():
    transactions = [
        ["Milk", "Bread"],
        ["Milk", "Bread"],
        ["Milk", "Bread"],
        ["Milk", "Eggs"],
        ["Bread", "Eggs"],
        ["Milk", "Bread"]
    ]

    encoded = encode_transactions(transactions)

    itemsets, rules = mine_associations(
        encoded,
        min_support=0.30,
        min_confidence=0.50
    )

    assert not itemsets.empty
    assert not rules.empty
    assert "support" in itemsets.columns
    assert "confidence" in rules.columns
    assert "lift" in rules.columns

def test_evaluate_rules():
    transactions = [
        ["Milk", "Bread"],
        ["Milk", "Bread"],
        ["Milk", "Bread"],
        ["Milk", "Bread"],
        ["Milk"],
        ["Eggs"]
    ]

    encoded = encode_transactions(transactions)

    itemsets, rules = mine_associations(
        encoded,
        min_support=0.30,
        min_confidence=0.50
    )

    evaluated = evaluate_rules(
        rules,
        min_confidence=0.50,
        min_lift=1.0
    )

    assert not evaluated.empty
    assert (evaluated["confidence"] >= 0.50).all()
    assert (evaluated["lift"] >= 1.0).all()



def test_format_rules():
    transactions = [
        ["Milk", "Bread"],
        ["Milk", "Bread"],
        ["Milk", "Bread"],
        ["Milk", "Bread"],
        ["Milk"],
        ["Eggs"]
    ]

    encoded = encode_transactions(transactions)

    itemsets, rules = mine_associations(
        encoded,
        min_support=0.30,
        min_confidence=0.50
    )

    evaluated = evaluate_rules(
        rules,
        min_confidence=0.50,
        min_lift=1.0
    )

    formatted = format_rules(evaluated)

    assert not formatted.empty
    assert isinstance(formatted.iloc[0]["antecedents"], str)
    assert isinstance(formatted.iloc[0]["consequents"], str)