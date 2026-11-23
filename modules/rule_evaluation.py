import pandas as pd


def evaluate_rules(
    rules,
    min_confidence=0.30,
    min_lift=1.0
):
    if rules is None or rules.empty:
        return pd.DataFrame()

    filtered = rules[
        (rules["confidence"] >= min_confidence) &
        (rules["lift"] >= min_lift)
    ].copy()

    filtered = filtered.sort_values(
        by=["lift", "confidence", "support"],
        ascending=False
    )

    return filtered.reset_index(drop=True)


def format_rules(rules):
    if rules is None or rules.empty:
        return pd.DataFrame()

    result = rules.copy()

    result["antecedents"] = result["antecedents"].apply(
        lambda x: ", ".join(sorted(list(x)))
    )

    result["consequents"] = result["consequents"].apply(
        lambda x: ", ".join(sorted(list(x)))
    )

    return result
