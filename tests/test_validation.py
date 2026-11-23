import pandas as pd

from modules.dataset_validator import validate_dataset


def sample_mapping():
    return {
        "transaction": "Invoice",
        "product": "Product",
        "date": "Date",
        "quantity": "Quantity"
    }


def test_valid_dataset():
    df = pd.DataFrame({
        "Invoice": ["T1", "T1", "T2", "T2"],
        "Product": ["Milk", "Bread", "Milk", "Eggs"],
        "Date": ["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-02"],
        "Quantity": [1, 2, 1, 1]
    })

    errors, warnings = validate_dataset(df, sample_mapping())

    assert errors == []
    assert warnings == []


def test_empty_dataset():
    df = pd.DataFrame()

    errors, warnings = validate_dataset(df, sample_mapping())

    assert "Dataset is empty." in errors


def test_missing_transaction_selection():
    df = pd.DataFrame({
        "Product": ["Milk", "Bread"]
    })

    mapping = {
        "transaction": None,
        "product": "Product"
    }

    errors, warnings = validate_dataset(df, mapping)

    assert "transaction column has not been selected." in errors


def test_missing_product_selection():
    df = pd.DataFrame({
        "Invoice": ["T1", "T2"]
    })

    mapping = {
        "transaction": "Invoice",
        "product": None
    }

    errors, warnings = validate_dataset(df, mapping)

    assert "product column has not been selected." in errors


def test_invalid_transaction_column():
    df = pd.DataFrame({
        "Invoice": ["T1", "T2"],
        "Product": ["Milk", "Bread"]
    })

    mapping = {
        "transaction": "WrongColumn",
        "product": "Product"
    }

    errors, warnings = validate_dataset(df, mapping)

    assert "Selected transaction column does not exist." in errors


def test_missing_transaction_ids_warning():
    df = pd.DataFrame({
        "Invoice": ["T1", None, "T2"],
        "Product": ["Milk", "Bread", "Eggs"]
    })

    mapping = {
        "transaction": "Invoice",
        "product": "Product"
    }

    errors, warnings = validate_dataset(df, mapping)

    assert "Missing transaction IDs detected." in warnings


def test_missing_products_warning():
    df = pd.DataFrame({
        "Invoice": ["T1", "T2", "T3"],
        "Product": ["Milk", None, "Eggs"]
    })

    mapping = {
        "transaction": "Invoice",
        "product": "Product"
    }

    errors, warnings = validate_dataset(df, mapping)

    assert "Missing product values detected." in warnings


def test_fewer_than_two_transactions_warning():
    df = pd.DataFrame({
        "Invoice": ["T1", "T1"],
        "Product": ["Milk", "Bread"]
    })

    mapping = {
        "transaction": "Invoice",
        "product": "Product"
    }

    errors, warnings = validate_dataset(df, mapping)

    assert "Dataset contains fewer than two transactions." in warnings