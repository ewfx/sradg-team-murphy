import os
from langgraph.graph import StateGraph
import graphviz
import requests
from global_state import WorkflowState, state
from openrouter_detect_anomaly import query_openrouter
#from anomaly_detector import predict_anomalies


VISUALIZATION_DIR = "workflow_visuals"
FLASK_SERVER_URL = "http://127.0.0.1:5000"


def load_data(_):
    state.historical_data = _.historical_df
    state.realtime_data = _.realtime_df
    return state


def invoke_llm(_):
    df_hist = state.historical_data
    #print(f"HISTORICAL DATA:", df_hist)
    df_real = state.realtime_data
    #print(f"REAL-TIME DATA:", df_real)
    prompt = f"""
        You are an AI model designed for anomaly detection in financial reconciliation data. Your task is to analyze the given data and compare it with historical trends to identify anomalies based on the balance columns and report if there is an anomaly and the category only

        Given data:
        As of Date,Company,Account,AU,Currency,Primary Account,Secondary Account,GL Balance,IHub Balance,Balance Difference,Match Status
        2025-03-27,83885,8100566,AU1,USD,ALL OTHER LOANS,DEFERRED COSTS,27020.76,18789.66,14231.1

        Historical data:
        As of Date,Company,Account,AU,Currency,Primary Account,Secondary Account,GL Balance,IHub Balance,Balance Difference,Match Status
        2024-09-05,83885,8100566,AU1,USD,ALL OTHER LOANS,DEFERRED COSTS,26020.76,17789.66,14231.1,Break,
        2024-07-04,83885,8100566,AU1,USD,ALL OTHER LOANS,DEFERRED COSTS,25020.76,16789.66,12231.1,Break,
        2023-10-29,83885,8100566,AU1,USD,ALL OTHER LOANS,DEFERRED COSTS,24020.76,15789.66,10231.1,Break,
        2023-01-23,83885,8100566,AU1,USD,ALL OTHER LOANS,DEFERRED COSTS,23020.76,14789.66,8231.1,Break,

        Categorize the anomaly into one of the following:
        1. Inconsistent variations in outstanding balances
        2. Huge spike in outstanding balances
        3. Outstanding balances are in line with previous months
        4. Consistent increase or decrease in outstanding balances
        5. Spike threshold is greater than 10000.

        if anomaly is not one of the above classify it as Other

        **Final Output:** 
            Anomaly: (Yes/No) and Comments: one of the predefined categories and explanation why you choose that category
            and reason for anomaly.

        Example Output:
            Anomaly: Yes, Category: Huge spike in outstanding balances

        **Do not include prompt or any context in the response.**
        """
    response = query_openrouter(prompt)
    #print("LLM Response: ", response)
    state.llm_response = response
    return state

def decision_logic_when_anomaly(_):
    """Determines whether human intervention is needed based on the LLM response."""
    response_text = state.llm_response.strip()

    if "Anomaly: Yes" in response_text:
        state.anomaly_decision = "Reconciler Intervention Page"
    else:
        state.anomaly_decision = "No Anomaly"

    print(f"Decision made: {state.anomaly_decision}")  # Debugging log
    return state


def reconciler_intervention_page(_):
    # Triggers a Flask endpoint to display a reconciler review page."""
    print("Sending case for reconciler Review...")
    requests.post(f"{FLASK_SERVER_URL}/reconciler_intervention_page", json={"llm_response": state.llm_response, "decision": state.anomaly_decision})
    state.reviewer_action = "reconciler_action_wait"
    return state

def reconciler_action_wait(_):
    print("Sending case for reconciler action wait...")
    requests.get(f"{FLASK_SERVER_URL}/reconciler_action_wait")
    #state.reviewer_action = "reconciler_action_wait"
    return state

def email_notification(_):
    """Calls Flask endpoint for email notification."""
    print(f"EMAIL NOTIFICATION IN WORKFLOW")
    response = requests.get(f"{FLASK_SERVER_URL}/email_notification")
    state.message = response.text
    return state

def raise_sr_ticket(_):
    """Calls Flask endpoint for raising an SR ticket."""
    print(f"RAISE SR IN WORKFLOW")
    response = requests.get(f"{FLASK_SERVER_URL}/raise_sr")
    state.message = response.text
    state.reviewer_action = "raise_sr"
    return state

def source_target_adjustment(_):
    # Handles source/target system adjustment (renders new HTML page).
    print(f"Calling s/t adjustment in workflow")
    state.message = "Redirecting to source/target system adjustment..."

    return state

def no_anomaly_page(_):
    # Calls another API in Flask to process the no anomaly page.
    print("Calling no anomaly page...")
    response = requests.get(f"{FLASK_SERVER_URL}/no_anomaly")
    state.message = response.text
    return state

# Define LangGraph Workflow
workflow = StateGraph(state_schema=WorkflowState)

workflow.add_node("Load Data", load_data)
workflow.add_node("Invoke LLM", invoke_llm)
workflow.add_node("Decision Logic When Anomaly", decision_logic_when_anomaly)
workflow.add_node("Reconciler Intervention Page", reconciler_intervention_page)
workflow.add_node("No Anomaly", no_anomaly_page)
workflow.add_node("Reconciler Action Wait", reconciler_action_wait)
workflow.add_node("Email Notification", email_notification)
workflow.add_node("Raise SR Ticket", raise_sr_ticket)
workflow.add_node("Source Target System Adjustment", source_target_adjustment)

# Define Graph Edges (Task Execution Flow)
workflow.add_edge("Load Data", "Invoke LLM")
workflow.add_edge("Invoke LLM", "Decision Logic When Anomaly")
workflow.add_conditional_edges("Decision Logic When Anomaly", lambda state: state.anomaly_decision, {
    "Reconciler Intervention Page": "Reconciler Intervention Page",
    "No Anomaly": "No Anomaly"
})
workflow.add_conditional_edges(
    "Reconciler Intervention Page",
    lambda state: state.reviewer_action,
    {
        "reconciler_action_wait": "Reconciler Action Wait",
        "email_notification": "Email Notification",
        "raise_sr": "Raise SR Ticket",
        "source_target_adjustment": "Source Target System Adjustment"
    }
)


# **Set Start Node**
workflow.set_entry_point("Load Data")


# Function to Run Workflow from UI
def run_workflow(historical_df=None, realtime_df=None):
    """Triggers the LangGraph workflow only when user has provided reviewer_action."""

    graph = workflow.compile()

    initial_state = WorkflowState(
        historical_df=historical_df,
        realtime_df=realtime_df
    )

    final_state = graph.invoke(initial_state.dict())
    visualize_workflow()
    print("✅ Workflow visualization saved as 'workflow.png'")
    return final_state




def visualize_workflow():
    """Generates and saves a visualization of the LangGraph workflow using Graphviz."""
    dot = graphviz.Digraph(format="png")

    # Define Nodes

    dot.node("Load Data", "Load Data")
    dot.node("Invoke LLM", "Invoke LLM")
    dot.node("Decision Logic When Anomaly", "Decision Logic When Anomaly")
    dot.node("Reconciler Intervention Page", "Reconciler Intervention Page")
    dot.node("No Anomaly", "No Anomaly")
    dot.node("Reconciler Action Wait", "Reconciler Action Wait")
    dot.node("Email Notification", "Email Notification")
    dot.node("Raise SR Ticket", "Raise SR Ticket")
    dot.node("Source Target System Adjustment", "Source Target System Adjustment")

    # Define Edges (Workflow Connections)
    dot.edge("Load Data", "Invoke LLM")
    dot.edge("Invoke LLM", "Decision Logic When Anomaly")
    dot.edge("Decision Logic When Anomaly", "Reconciler Intervention Page", label="Anomaly Detected")
    dot.edge("Decision Logic When Anomaly", "No Anomaly", label="No Anomaly")
    dot.edge("Reconciler Intervention Page", "Reconciler Action Wait")
    dot.edge("Reconciler Intervention Page", "Email Notification", label="Email Notification")
    dot.edge("Reconciler Intervention Page", "Raise SR Ticket", label="Raise SR Ticket")
    dot.edge("Reconciler Intervention Page", "Source Target System Adjustment", label="System Adjustment")

    # Save Graph as Image
    graph_path = os.path.join(VISUALIZATION_DIR, "workflow")
    dot.render(graph_path)
