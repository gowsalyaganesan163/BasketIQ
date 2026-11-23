import pandas as pd


def rule_key(row):
    return (
        frozenset(row["antecedents"]),
        frozenset(row["consequents"])
    )


def detect_trends(
    earlier_rules,
    recent_rules,
    lift_change_threshold=0.10
):
    if earlier_rules is None:
        earlier_rules = pd.DataFrame()

    if recent_rules is None:
        recent_rules = pd.DataFrame()

    earlier_map = {}
    recent_map = {}

    for _, row in earlier_rules.iterrows():
        earlier_map[rule_key(row)] = row

    for _, row in recent_rules.iterrows():
        recent_map[rule_key(row)] = row

    all_keys = set(earlier_map) | set(recent_map)

    results = []

    for key in all_keys:
        old = earlier_map.get(key)
        new = recent_map.get(key)

        if old is None:
            status = "Emerging"
            old_lift = 0
            new_lift = new["lift"]

        elif new is None:
            status = "Declining"
            old_lift = old["lift"]
            new_lift = 0

        else:
            old_lift = old["lift"]
            new_lift = new["lift"]

            difference = new_lift - old_lift

            if difference > lift_change_threshold:
                status = "Growing"

            elif difference < -lift_change_threshold:
                status = "Declining"

            else:
                status = "Stable"

        results.append({
            "antecedents": list(key[0]),
            "consequents": list(key[1]),
            "earlier_lift": old_lift,
            "recent_lift": new_lift,
            "lift_change": new_lift - old_lift,
            "status": status
        })

    return pd.DataFrame(results)