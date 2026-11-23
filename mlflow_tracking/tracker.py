
import os
from pathlib import Path

import mlflow


def initialize_mlflow():
    """Initialize local MLflow tracking."""

    tracking_dir = os.path.abspath(
        os.path.join("mlflow_tracking", "runs_store")
    )

    os.makedirs(tracking_dir, exist_ok=True)

    tracking_uri = Path(tracking_dir).as_uri()
    mlflow.set_tracking_uri(tracking_uri)

    mlflow.set_experiment("BasketIQ_Association_Mining")


def log_analysis_run(
    min_support,
    min_confidence,
    min_lift,
    total_transactions,
    unique_products,
    frequent_itemsets_count,
    rules_count,
    trends_count
):
    """Log parameters and metrics for one BasketIQ analysis."""

    initialize_mlflow()

    with mlflow.start_run(run_name="BasketIQ_Analysis"):

        # Analysis parameters
        mlflow.log_params({
            "min_support": min_support,
            "min_confidence": min_confidence,
            "min_lift": min_lift
        })

        # Dataset and analysis metrics
        mlflow.log_metrics({
            "total_transactions": total_transactions,
            "unique_products": unique_products,
            "frequent_itemsets": frequent_itemsets_count,
            "association_rules": rules_count,
            "detected_trends": trends_count
        })

        run_id = mlflow.active_run().info.run_id

    return run_id
