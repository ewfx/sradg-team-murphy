from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from workflow import run_workflow
from global_state import state

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "historical" not in request.files or "realtime" not in request.files:
            return "Both Historical and Real-Time CSV files are required!"

        historical_file = request.files["historical"]
        realtime_file = request.files["realtime"]

        if historical_file.filename == "" or realtime_file.filename == "":
            return "Please select both CSV files before submitting."

        # Read files into Pandas DataFrames (on-the-fly, no saving)
        historical_df = pd.read_csv(historical_file)
        realtime_df = pd.read_csv(realtime_file)

        # Trigger LangGraph workflow with both DataFrames
        results = run_workflow(historical_df, realtime_df)
        llm_response_str = str(results["llm_response"])

        # Check workflow decision and redirect accordingly
        if results["anomaly_decision"] == "Reconciler Intervention Page":
            return render_template("reconciler_review.html", llm_response=llm_response_str)
        elif results["anomaly_decision"] == "No Anomaly":
            return render_template("no_anomaly.html", message=results["message"])
        elif results["reviewer_action"] == "email_notification":
            return render_template("results.html", message=results["message"])
        elif results["reviewer_action"] == "raise_sr":
            return render_template("results.html", message=results["message"])

        return render_template("results.html", message=results["message"], predictions=llm_response_str)

    return render_template("upload.html")

@app.route("/reconciler_intervention_page", methods=["POST", "GET"])
def reconciler_intervention():
    # Displays a page for reconciler review.
    if request.method == "POST":
        data = request.get_json()
        return render_template("reconciler_review.html", llm_response=data["llm_response"])
    else:
        return render_template("reconciler_review.html", llm_response="Waiting for LLM response...")
    #return "Done"


@app.route("/reconciler_review_submit", methods=["POST"])
def reconciler_review_submit():
    selected_action = request.form.get("action")

    if not selected_action:
        return "No action selected. Please try again.", 400

    print(f"User selected action: {selected_action}")
    state.anomaly_decision = ""
    state.message = ""
    state.reviewer_action = selected_action

    if selected_action == "email_notification":
        state.message = "Email notification sent successfully!"
    elif selected_action == "raise_sr":
         state.message = "SR ticket raised successfully"
    elif selected_action == "source_target_system_adjustment":
        return render_template("source_target_system_adjustment.html", message=state.message,
                               predictions=state.llm_response)
    return render_template("results.html", message=state.message, predictions=state.llm_response)

@app.route("/reconciler_action_wait", methods=["GET"])
def reconciler_action_wait():
    # Reconciler wait
    return render_template("results.html", message=state.message)

@app.route("/no_anomaly", methods=["GET"])
def no_anomaly():
    # No anomaly page.
    return "No anomaly detected"

@app.route("/source_target_adjustment", methods=["GET"])
def source_target_adjustment():
    # Source target system adjustment page.
    data = request.get_json()
    return render_template("source_target_system_adjustment.html", llm_response=data["llm_response"])

@app.route("/email_notification", methods=["GET"])
def email_notification():
    """Email notification."""
    return "Email notification sent successfully!"

@app.route("/raise_sr", methods=["GET"])
def raise_sr():
    """Raise SR ticket."""
    return "SR ticket raised successfully"

if __name__ == "__main__":
    app.run(debug=True)
