import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

def mine_frequent_itemsets(
    encoded_df,
    min_support=0.02
):
    itemsets = apriori(
        encoded_df,
        min_support=min_support,
        use_colnames=True
    )

    return itemsets


def generate_rules(itemsets, min_confidence=0.30):
    if itemsets is None or len(itemsets) < 2:
        return pd.DataFrame()

    rules = association_rules(
        itemsets,
        metric="confidence",
        min_threshold=min_confidence
    )

    return rules


def mine_associations(
    encoded_df,
    min_support=0.02,
    min_confidence=0.30
):
    itemsets = mine_frequent_itemsets(
        encoded_df,
        min_support
    )

    rules = generate_rules(
        itemsets,
        min_confidence
    )

    return itemsets, rules