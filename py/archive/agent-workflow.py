from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI

import sqlite3
import json
import smtplib
import requests

# ✅ 1. Define the State
class AnomalyState:
    def __init__(self, new_data):
        self.new_data = new_data
        self.historical_data = None
        self.prediction = None
        self.explanation = None
        self.action_taken = None

# ✅ 2. Load Historical Data from SQLite
def get_historical_data(state):
    conn = sqlite3.connect("anomaly_data.db")
    cursor = conn.cursor()

    query = """
    SELECT * FROM transactions 
    WHERE company_number = ? AND account = ? AND AU = ? AND currency = ?
    """
    
    params = (state.new_data["company_number"], state.new_data["account"], state.new_data["AU"], state.new_data["currency"])
    cursor.execute(query, params)
    
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        state.historical_data = [{"company_number": row[0], "account": row[1], "gl_balance": row[6], "ihb_balance": row[7], "difference": row[8], "match_status": row[9]} for row in rows]
    else:
        state.historical_data = []
    
    return state

# ✅ 3. Predict Anomaly using LLM
def predict_anomaly(state):
    llm = ChatOpenAI(model="gpt-4-turbo", api_key="your-api-key")

    prompt = f"""
    Given this historical transaction data: {json.dumps(state.historical_data, indent=2)}
    A new transaction has arrived: {json.dumps(state.new_data, indent=2)}

    Determine if the new transaction is an anomaly. Respond with:
    - "Anomaly" if it is unexpected.
    - "Not Anomaly" if it follows previous trends.
    - Provide an explanation.
    """
    
    response = llm.invoke(prompt)
    result = response.content.split("\n")[0]  # First line = classification
    explanation = "\n".join(response.content.split("\n")[1:])  # Rest = explanation
    
    state.prediction = result
    state.explanation = explanation
    return state

# ✅ 4. Send Email Notification
def send_email(state):
    if state.prediction != "Anomaly":
        return state  # No need to notify

    sender_email = "your-email@example.com"
    sender_password = "your-password"
    recipient_email = "finance-team@example.com"

    subject = "🚨 Anomaly Detected in Financial Data!"
    body = f"""
    Alert: Anomaly Detected!
    -----------------------------------------
    Company: {state.new_data['company_number']}
    Account: {state.new_data['account']}
    Anomaly Details: {state.explanation}
    Action Required: Please investigate.
    """

    msg = f"Subject: {subject}\n\n{body}"

    try:
        with smtplib.SMTP("smtp.example.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg)
        state.action_taken = "Email Sent"
    except Exception as e:
        state.action_taken = f"Email Failed: {str(e)}"
    
    return state

# ✅ 5. Create a Service Request (SR) if needed
def create_service_request(state):
    if state.prediction != "Anomaly":
        return state  # No need for an SR

    if abs(state.new_data["difference"]) < 50000:  # Example threshold
        return state  # Not critical

    JIRA_URL = "https://your-jira-instance.com/rest/api/2/issue"
    JIRA_AUTH = ("your-username", "your-api-token")

    data = {
        "fields": {
            "project": {"key": "SR"},
            "summary": f"Anomaly Detected: {state.new_data['company_number']} - {state.new_data['account']}",
            "description": f"An anomaly was detected:\n{state.explanation}",
            "issuetype": {"name": "Service Request"}
        }
    }

    response = requests.post(JIRA_URL, json=data, auth=JIRA_AUTH)

    if response.status_code == 201:
        state.action_taken = f"SR Created: {response.json()['key']}"
    else:
        state.action_taken = f"SR Failed: {response.text}"
    
    return state

# ✅ 6. Log Anomaly Detection Result
def log_result(state):
    conn = sqlite3.connect("anomaly_data.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO anomaly_results (company_number, account, gl_balance, ihb_balance, difference, prediction, explanation, action_taken)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        state.new_data["company_number"],
        state.new_data["account"],
        state.new_data["gl_balance"],
        state.new_data["ihb_balance"],
        state.new_data["difference"],
        state.prediction,
        state.explanation,
        state.action_taken
    ))

    conn.commit()
    conn.close()
    
    return state

# ✅ 7. Define the LangGraph Workflow
workflow = StateGraph(AnomalyState)

workflow.add_node("get_historical_data", get_historical_data)
workflow.add_node("predict_anomaly", predict_anomaly)
workflow.add_node("send_email", send_email)
workflow.add_node("create_service_request", create_service_request)
workflow.add_node("log_result", log_result)

workflow.add_edge("get_historical_data", "predict_anomaly")
workflow.add_edge("predict_anomaly", "send_email")
workflow.add_edge("send_email", "create_service_request")
workflow.add_edge("create_service_request", "log_result")

workflow.set_entry_point("get_historical_data")

# ✅ 8. Execute the Workflow with New Data
def run_anomaly_detection(new_data):
    state = AnomalyState(new_data)
    return workflow.invoke(state)

# Example: Incoming data
new_transaction = {
    "company_number": "1111",
    "account": "1634789",
    "AU": "6783",
    "currency": "EUR",
    "primary_account": "ALL OTHER LOANS",
    "secondary_account": "DEFERRED ORIGINATION FEES",
    "gl_balance": 20000,
    "ihb_balance": 0,
    "difference": 20000
}

result_state = run_anomaly_detection(new_transaction)
print("📌 Final Result:", result_state.prediction, "| Action Taken:", result_state.action_taken)
