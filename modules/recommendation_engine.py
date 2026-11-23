def generate_recommendations(trends_df):
    recommendations = []

    if trends_df is None or trends_df.empty:
        return recommendations

    for _, row in trends_df.iterrows():
        products_a = ", ".join(row["antecedents"])
        products_b = ", ".join(row["consequents"])
        status = row["status"]

        if status == "Emerging":
            message = (
                f"Explore a bundle or product placement for "
                f"{products_a} and {products_b} "
                f"because this association is newly detected."
            )

        elif status == "Growing":
            message = (
                f"Consider testing a cross-promotion for "
                f"{products_a} and {products_b} "
                f"because their association is strengthening."
            )

        elif status == "Declining":
            message = (
                f"Review the placement or promotion strategy "
                f"for {products_a} and {products_b} "
                f"because their association is weakening."
            )

        else:
            message = (
                f"The association between {products_a} and "
                f"{products_b} is relatively stable. "
                f"Consider maintaining the current strategy."
            )

        recommendations.append({
            "products": f"{products_a} → {products_b}",
            "status": status,
            "suggestion": message
        })

    return recommendations