
import os
import pandas as pd

from flask import Flask, render_template, request, redirect, url_for, flash

from modules.dataset_validator import validate_dataset
from modules.preprocessing import clean_dataset
from modules.transaction_builder import build_transactions, encode_transactions
from modules.association_mining import mine_associations
from modules.rule_evaluation import evaluate_rules, format_rules
from modules.temporal_analysis import analyze_periods
from modules.trend_detector import detect_trends
from modules.recommendation_engine import generate_recommendations
from modules.network_builder import build_association_network, get_network_data

from mlflow_tracking.tracker import log_analysis_run


app = Flask(__name__)

app.secret_key = "basketiq-development-key"
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024


# Temporary in-memory storage for V1 development
uploaded_data = None
analysis_results = None
dataset_name = None


# --------------------------------------------------
# HOME ROUTE
# --------------------------------------------------

@app.route("/")
def home():
    return render_template(
        "index.html",
        dataset_name=dataset_name,
        results=analysis_results
    )


# --------------------------------------------------
# DATASET UPLOAD ROUTE
# --------------------------------------------------

@app.route("/upload", methods=["POST"])
def upload_dataset():
    global uploaded_data, analysis_results, dataset_name

    file = request.files.get("dataset")

    if file is None or file.filename == "":
        flash("Please select a dataset.")
        return redirect(url_for("home"))

    filename = file.filename.lower()

    try:
        if filename.endswith(".csv"):
            uploaded_data = pd.read_csv(file)

        elif filename.endswith(".xlsx"):
            uploaded_data = pd.read_excel(file)

        else:
            flash("Only CSV and XLSX files are supported.")
            return redirect(url_for("home"))

    except Exception as error:
        uploaded_data = None
        flash(f"Could not read file: {error}")
        return redirect(url_for("home"))

    if uploaded_data.empty:
        flash("The uploaded dataset is empty.")
        return redirect(url_for("home"))

    dataset_name = file.filename
    analysis_results = None

    columns = uploaded_data.columns.tolist()

    return render_template(
        "index.html",
        dataset_name=dataset_name,
        columns=columns,
        preview=uploaded_data.head(10).to_html(
            classes="table table-striped",
            index=False
        ),
        results=None
    )


# --------------------------------------------------
# ANALYSIS ROUTE
# --------------------------------------------------

@app.route("/analyze", methods=["POST"])
def analyze():
    global uploaded_data, analysis_results

    if uploaded_data is None:
        flash("Upload a dataset first.")
        return redirect(url_for("home"))

    # ----------------------------------------------
    # 1. COLUMN MAPPING
    # ----------------------------------------------

    mapping = {
        "transaction": request.form.get("transaction"),
        "product": request.form.get("product"),
        "date": request.form.get("date") or None,
        "quantity": request.form.get("quantity") or None
    }

    # ----------------------------------------------
    # 2. DATASET VALIDATION
    # ----------------------------------------------

    errors, warnings = validate_dataset(uploaded_data, mapping)

    if errors:
        for error in errors:
            flash(error)

        return redirect(url_for("home"))

    # ----------------------------------------------
    # 3. PREPROCESSING
    # ----------------------------------------------

    cleaned_data = clean_dataset(uploaded_data, mapping)

    # ----------------------------------------------
    # 4. TRANSACTION BUILDING
    # ----------------------------------------------

    transactions = build_transactions(cleaned_data)

    # ----------------------------------------------
    # 5. TRANSACTION ENCODING
    # ----------------------------------------------

    encoded_data = encode_transactions(transactions)

    # ----------------------------------------------
    # 6. MINING PARAMETERS
    # ----------------------------------------------

    try:
        min_support = float(request.form.get("min_support", 0.02))
        min_confidence = float(request.form.get("min_confidence", 0.30))
        min_lift = float(request.form.get("min_lift", 1.0))

    except (TypeError, ValueError):
        flash("Invalid mining parameters.")
        return redirect(url_for("home"))

    if not (0 < min_support <= 1):
        flash("Minimum support must be greater than 0 and at most 1.")
        return redirect(url_for("home"))

    if not (0 <= min_confidence <= 1):
        flash("Minimum confidence must be between 0 and 1.")
        return redirect(url_for("home"))

    if min_lift < 0:
        flash("Minimum lift cannot be negative.")
        return redirect(url_for("home"))

    # ----------------------------------------------
    # 7. ASSOCIATION MINING
    # ----------------------------------------------

    itemsets, rules = mine_associations(
        encoded_data,
        min_support=min_support,
        min_confidence=min_confidence
    )

    # ----------------------------------------------
    # 8. RULE EVALUATION
    # ----------------------------------------------

    evaluated_rules = evaluate_rules(
        rules,
        min_confidence=min_confidence,
        min_lift=min_lift
    )

    formatted_rules = format_rules(evaluated_rules)

    # ----------------------------------------------
    # 9. TEMPORAL ANALYSIS
    # ----------------------------------------------

    trend_results = pd.DataFrame()
    temporal_results = None
    recommendations = []

    if mapping["date"] and "date" in cleaned_data.columns:

        try:
            temporal_results = analyze_periods(
                cleaned_data,
                min_support=min_support,
                min_confidence=min_confidence,
                min_lift=min_lift
            )

            trend_results = detect_trends(
                temporal_results["earlier_rules"],
                temporal_results["recent_rules"]
            )

            recommendations = generate_recommendations(trend_results)

        except ValueError as error:
            warnings.append(f"Temporal analysis skipped: {error}")

    # ----------------------------------------------
    # 10. MLFLOW EXPERIMENT TRACKING
    # ----------------------------------------------

    run_id = None

    try:
        run_id = log_analysis_run(
            min_support=min_support,
            min_confidence=min_confidence,
            min_lift=min_lift,
            total_transactions=len(transactions),
            unique_products=cleaned_data["product"].nunique(),
            frequent_itemsets_count=len(itemsets),
            rules_count=len(evaluated_rules),
            trends_count=len(trend_results)
        )

    except Exception as error:
        warnings.append(f"MLflow logging failed: {error}")

    # ----------------------------------------------
    # 11. ASSOCIATION NETWORK
    # ----------------------------------------------

    graph = build_association_network(evaluated_rules)

    network_data = get_network_data(graph)

    # ----------------------------------------------
    # 12. PREPARE RESULTS
    # ----------------------------------------------

    analysis_results = {
        "total_rows": len(cleaned_data),
        "total_transactions": len(transactions),
        "unique_products": cleaned_data["product"].nunique(),
        "frequent_itemsets": len(itemsets),
        "total_rules": len(evaluated_rules),

        "mlflow_run_id": run_id,

        "rules": formatted_rules.to_dict(orient="records"),
        "trends": trend_results.to_dict(orient="records"),
        "recommendations": recommendations,

        "network": network_data,
        "warnings": warnings
    }

    # ----------------------------------------------
    # 13. RENDER DASHBOARD
    # ----------------------------------------------

    return render_template(
        "index.html",
        dataset_name=dataset_name,
        results=analysis_results
    )


# --------------------------------------------------
# APPLICATION ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
