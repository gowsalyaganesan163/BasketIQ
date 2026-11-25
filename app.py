import os
import logging
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


# --------------------------------------------------
# APP CONFIGURATION
# --------------------------------------------------

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "basketiq-development-key")

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Resource protection for Render Free
MAX_ANALYSIS_TRANSACTIONS = 5000
MAX_NETWORK_RULES = 150

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
# DATASET UPLOAD
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
            uploaded_data = pd.read_excel(file, engine="openpyxl")

        else:
            flash("Only CSV and XLSX files are supported.")
            return redirect(url_for("home"))

    except Exception:
        logger.exception("Dataset upload failed")

        uploaded_data = None
        flash("Could not read the uploaded file. Please check the file format.")
        return redirect(url_for("home"))

    if uploaded_data.empty:
        flash("The uploaded dataset is empty.")
        return redirect(url_for("home"))

    dataset_name = file.filename
    analysis_results = None

    columns = uploaded_data.columns.tolist()

    logger.info(
        "Dataset uploaded successfully: %s | Rows: %s | Columns: %s",
        dataset_name,
        len(uploaded_data),
        len(columns)
    )

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

    logger.info("Analysis request received")

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
    # 2. VALIDATE MINING PARAMETERS FIRST
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
    # 3. DATASET VALIDATION
    # ----------------------------------------------

    try:
        errors, warnings = validate_dataset(uploaded_data, mapping)

        if warnings is None:
            warnings = []

    except Exception:
        logger.exception("Dataset validation failed")
        flash("Dataset validation failed. Please check your column selections.")
        return redirect(url_for("home"))

    if errors:
        for error in errors:
            flash(error)

        return redirect(url_for("home"))

    # ----------------------------------------------
    # 4. RESOURCE-LIMITED DATA PREPARATION
    # ----------------------------------------------

    try:
        analysis_data = uploaded_data.copy()

        transaction_column = mapping["transaction"]

        unique_transactions = analysis_data[transaction_column].dropna().unique()

        original_transaction_count = len(unique_transactions)

        # Sample transactions if dataset is too large
        if original_transaction_count > MAX_ANALYSIS_TRANSACTIONS:

            logger.warning(
                "Dataset contains %s transactions. Sampling %s transactions.",
                original_transaction_count,
                MAX_ANALYSIS_TRANSACTIONS
            )

            sampled_transactions = pd.Series(unique_transactions).sample(
                n=MAX_ANALYSIS_TRANSACTIONS,
                random_state=42
            ).values

            analysis_data = analysis_data[
                analysis_data[transaction_column].isin(sampled_transactions)
            ].copy()

            warnings.append(
                f"Large dataset detected. Analysis uses a reproducible sample "
                f"of {MAX_ANALYSIS_TRANSACTIONS:,} transactions from "
                f"{original_transaction_count:,} transactions."
            )

        logger.info(
            "Preparing %s rows across %s transactions",
            len(analysis_data),
            analysis_data[transaction_column].nunique()
        )

        # ------------------------------------------
        # 5. PREPROCESSING
        # ------------------------------------------

        cleaned_data = clean_dataset(analysis_data, mapping)

        logger.info("Dataset cleaning completed")

        # ------------------------------------------
        # 6. TRANSACTION BUILDING
        # ------------------------------------------

        transactions = build_transactions(cleaned_data)

        logger.info(
            "Transaction building completed: %s transactions",
            len(transactions)
        )

        # ------------------------------------------
        # 7. TRANSACTION ENCODING
        # ------------------------------------------

        encoded_data = encode_transactions(transactions)

        logger.info("Transaction encoding completed")

        # ------------------------------------------
        # 8. ASSOCIATION MINING
        # ------------------------------------------

        itemsets, rules = mine_associations(
            encoded_data,
            min_support=min_support,
            min_confidence=min_confidence
        )

        logger.info(
            "Association mining completed: %s itemsets, %s rules",
            len(itemsets),
            len(rules)
        )

        # ------------------------------------------
        # 9. RULE EVALUATION
        # ------------------------------------------

        evaluated_rules = evaluate_rules(
            rules,
            min_confidence=min_confidence,
            min_lift=min_lift
        )

        formatted_rules = format_rules(evaluated_rules)

        logger.info(
            "Rule evaluation completed: %s rules",
            len(evaluated_rules)
        )

        # ------------------------------------------
        # 10. TEMPORAL ANALYSIS
        # ------------------------------------------

        trend_results = pd.DataFrame()
        temporal_results = None
        recommendations = []

        if mapping["date"] and "date" in cleaned_data.columns:

            try:
                logger.info("Starting temporal analysis")

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

                logger.info("Temporal analysis completed")

            except Exception:
                logger.exception("Temporal analysis failed")
                warnings.append(
                    "Temporal analysis was skipped because of a processing issue."
                )

        # ------------------------------------------
        # 11. MLFLOW TRACKING
        # ------------------------------------------

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

        except Exception:
            logger.exception("MLflow logging failed")
            warnings.append("MLflow tracking was unavailable for this run.")

        # ------------------------------------------
        # 12. NETWORK GENERATION
        # ------------------------------------------

        try:
            logger.info("Building association network")

            # Keep the network lightweight
            network_rules = evaluated_rules

            if len(network_rules) > MAX_NETWORK_RULES:
                network_rules = network_rules.head(MAX_NETWORK_RULES)

                warnings.append(
                    f"Network visualization limited to the top "
                    f"{MAX_NETWORK_RULES} rules for performance."
                )

            graph = build_association_network(network_rules)

            network_data = get_network_data(graph)

            logger.info("Association network completed")

        except Exception:
            logger.exception("Network generation failed")
            network_data = {
                "nodes": [],
                "edges": []
            }

            warnings.append(
                "Association network could not be generated for this analysis."
            )

        # ------------------------------------------
        # 13. PREPARE RESULTS
        # ------------------------------------------

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

        logger.info("Analysis finished successfully")

        # ------------------------------------------
        # 14. RENDER RESULTS
        # ------------------------------------------

        return render_template(
            "index.html",
            dataset_name=dataset_name,
            results=analysis_results
        )

    except Exception:
        logger.exception("ANALYSIS PIPELINE FAILED")

        flash(
            "Analysis could not be completed. "
            "Try a smaller dataset or increase the minimum support value."
        )

        return redirect(url_for("home"))


# --------------------------------------------------
# REQUEST SIZE ERROR
# --------------------------------------------------

@app.errorhandler(413)
def file_too_large(error):
    flash("File is too large. Please upload a smaller dataset.")
    return redirect(url_for("home"))


# --------------------------------------------------
# APPLICATION ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=False)
