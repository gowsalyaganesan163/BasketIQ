import pandas as pd

from modules.temporal_analysis import split_time_periods, mine_period, analyze_periods
from modules.trend_detector import detect_trends
from modules.recommendation_engine import generate_recommendations


def sample_temporal_data():
    return pd.DataFrame({
        "transaction_id": [
            "T1", "T1", "T2", "T2",
            "T3", "T3", "T4", "T4",
            "T5", "T5", "T6", "T6"
        ],
        "product": [
            "Milk", "Bread",
            "Milk", "Bread",
            "Milk", "Eggs",
            "Bread", "Eggs",
            "Milk", "Bread",
            "Milk", "Bread"
        ],
        "date": pd.to_datetime([
            "2024-01-01", "2024-01-01",
            "2024-01-02", "2024-01-02",
            "2024-02-01", "2024-02-01",
            "2024-02-02", "2024-02-02",
            "2024-03-01", "2024-03-01",
            "2024-03-02", "2024-03-02"
        ]),
        "quantity": [1] * 12
    })


def test_split_time_periods():
    df = sample_temporal_data()

    earlier, recent, split_date = split_time_periods(df)

    assert not earlier.empty
    assert not recent.empty
    assert split_date is not None
    assert earlier["date"].max() <= split_date
    assert recent["date"].min() > split_date


def test_split_time_periods_custom_date():
    df = sample_temporal_data()

    earlier, recent, split_date = split_time_periods(
        df,
        split_date="2024-02-01"
    )

    assert earlier["date"].max() <= pd.Timestamp("2024-02-01")
    assert recent["date"].min() > pd.Timestamp("2024-02-01")


def test_split_time_periods_without_date():
    df = pd.DataFrame({
        "transaction_id": ["T1", "T2"],
        "product": ["Milk", "Bread"]
    })

    try:
        split_time_periods(df)
        assert False, "Expected ValueError"
    except ValueError:
        assert True


def test_mine_period():
    df = sample_temporal_data()

    rules = mine_period(
        df,
        min_support=0.20,
        min_confidence=0.30,
        min_lift=0.50
    )

    assert rules is not None
    assert isinstance(rules, pd.DataFrame)


def test_analyze_periods():
    df = sample_temporal_data()

    result = analyze_periods(
        df,
        min_support=0.20,
        min_confidence=0.30,
        min_lift=0.50
    )

    assert "earlier_rules" in result
    assert "recent_rules" in result
    assert "split_date" in result
    assert "earlier_transactions" in result
    assert "recent_transactions" in result


def test_detect_trends():
    earlier_rules = pd.DataFrame([
        {
            "antecedents": frozenset(["Milk"]),
            "consequents": frozenset(["Bread"]),
            "lift": 1.20
        },
        {
            "antecedents": frozenset(["Eggs"]),
            "consequents": frozenset(["Bread"]),
            "lift": 1.50
        }
    ])

    recent_rules = pd.DataFrame([
        {
            "antecedents": frozenset(["Milk"]),
            "consequents": frozenset(["Bread"]),
            "lift": 1.50
        },
        {
            "antecedents": frozenset(["Bread"]),
            "consequents": frozenset(["Eggs"]),
            "lift": 1.40
        }
    ])

    trends = detect_trends(
        earlier_rules,
        recent_rules,
        lift_change_threshold=0.10
    )

    assert not trends.empty
    assert "status" in trends.columns

    milk_bread = trends[
        (trends["antecedents"].apply(lambda x: "Milk" in x)) &
        (trends["consequents"].apply(lambda x: "Bread" in x))
    ]

    assert milk_bread.iloc[0]["status"] == "Growing"


def test_generate_recommendations():
    trends = pd.DataFrame([
        {
            "antecedents": ["Milk"],
            "consequents": ["Bread"],
            "status": "Growing"
        },
        {
            "antecedents": ["Eggs"],
            "consequents": ["Bread"],
            "status": "Emerging"
        },
        {
            "antecedents": ["Tea"],
            "consequents": ["Biscuits"],
            "status": "Declining"
        },
        {
            "antecedents": ["Coffee"],
            "consequents": ["Sugar"],
            "status": "Stable"
        }
    ])

    recommendations = generate_recommendations(trends)

    assert len(recommendations) == 4
    assert all("suggestion" in item for item in recommendations)
    assert all("status" in item for item in recommendations)


def test_empty_trends_recommendations():
    trends = pd.DataFrame()

    recommendations = generate_recommendations(trends)

    assert recommendations == []