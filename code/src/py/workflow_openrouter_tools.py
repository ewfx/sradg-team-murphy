import json
import os
from openai import OpenAI
from langgraph.graph import StateGraph, END
from langchain.tools import tool
from typing import Dict, Any, List
import graphviz
from pydantic import BaseModel
from sqlUtil import SQLiteDB

# ------------------ OpenRouter Configuration ------------------

with open("anomaly_config.json", "r") as config_file:
    config = json.load(config_file)

OPENROUTER_API_KEY = config["api_key"]
GEMINE_API_KEY = config["gemini_api_key"]
MISTRAL_API_KEY = config["mistral_key"]
OPENAI_BASE_URL = config["base_url"]

client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENAI_BASE_URL)
gemini_client = OpenAI(api_key=GEMINE_API_KEY, base_url=OPENAI_BASE_URL)
mistral_client = OpenAI(api_key=MISTRAL_API_KEY, base_url=OPENAI_BASE_URL)

db = SQLiteDB()
# Load historical data from a CSV file
db.load_csv_data(config["historical_data_file"])

# ------------------ Define Tools for External APIs ------------------

@tool
def fetch_data_from_system_GL(query: str) -> Dict[str, Any]:
    """Fetch additional data from System A"""
    return {"system_a_data": f"Additional data for {query} from System GL"}


@tool
def fetch_data_from_system_IHB(query: str) -> Dict[str, Any]:
    """Fetch additional data from System B"""
    return {"system_b_data": f"Additional data for {query} from System IHB"}

tools = [
    {
        "type": "function",
        "function": {
            "name": "fetch_data_from_system_GL",
            "description": "Fetch data from System GL based on input parameters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Query to fetch data from System A"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_data_from_system_IHB",
            "description": "Fetch data from System IHB based on input parameters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Query to fetch data from System B"}
                },
                "required": ["query"]
            }
        }
    }
]

functions=[
    {
        "name": "fetch_data_from_system_GL",
        "description": "Fetch additional data from System GL",
        "parameters": {
            "type": "object",
            "properties": {
                "record": {"type": "object"}
            }
        }
    },
    {
        "name": "fetch_data_from_system_IHB",
        "description": "Fetch additional data from System IHB",
        "parameters": {
            "type": "object",
            "properties": {
                "record": {"type": "object"}
            }
        }
    }
]

available_tools = {
    "fetch_data_from_system_GL": fetch_data_from_system_GL,
    "fetch_data_from_system_IHB": fetch_data_from_system_IHB
}
# ------------------ Define LangGraph Workflow ------------------

class WorkflowState(BaseModel):
    record: Dict[str, Any] = {}
    history_data: Dict[str, Any] = {}
    anomaly_detected: bool = False
    anomaly_reason: str = ""
    final_action: str = ""


graph = StateGraph(state_schema=WorkflowState)


# Step 1: Fetch record from queue
def fetch_record(state: WorkflowState) -> WorkflowState:
    state.record = {
        "company_number": "1111",
        "account": "1634789",
        "AU": "6783",
        "currency": "EUR",
        "primary_account" : "ALL OTHER LOANS",
        "secondary_account": "DEFERRED ORIGINATION FEES",
        "gl_balance": 20000,
        "ihb_balance": 0,
        "difference": 20000,
        "match_status": "break"
    }
    return state


graph.add_node("fetch_record", fetch_record)


# Step 2: Fetch history data
def fetch_history(state: WorkflowState) -> WorkflowState:
    state.history_data = db.get_historical_data(state.record)
    return state


graph.add_node("fetch_history", fetch_history)
graph.add_edge("fetch_record", "fetch_history")


# Step 3: Anomaly detection using OpenRouter
def detect_anomaly(state: WorkflowState) -> WorkflowState:
    """Uses OpenRouter LLM to detect anomalies based on historical trends"""
    prompt_template = config["prompt_template"]
    prompt = prompt_template.format(
            historical_data=json.dumps(state.history_data, indent=2),
            new_data=json.dumps(state.record, indent=2)
        )

    completion = client.chat.completions.create(
    extra_headers={

    },
    extra_body={},
    model=config["llm_model"],
    messages=[
            {"role": "system", "content": "You are a financial anomaly detection assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300
    )

    content = completion.choices[0].message.content
    print(content)

    anomaly_result = content.split("|")[0].split(":")[1].strip()
    category = content.split("|")[1].strip()
    explanation = content.split("|")[2].strip()

    print('anomaly: ' + anomaly_result)
    print('explanation: ' + explanation)
    print('category: '+ category)

    # result = json.loads(response.choices[0].message.content)

    state.anomaly_detected = anomaly_result.strip() == "Yes"
    state.anomaly_reason = explanation

    print(f"Anomaly Detected: {state.anomaly_detected} - {state.anomaly_reason}")

    return state


graph.add_node("detect_anomaly", detect_anomaly)
graph.add_edge("fetch_history", "detect_anomaly")


# Step 4: Decision Making with Function Calling
def decide_action(state: WorkflowState) -> WorkflowState:

    if not state.anomaly_detected:
        state.final_action = "No Action Needed"
        return state

    prompt = f"""
    An anomaly was detected: {state.anomaly_reason}.
    Decide any one of the following appropriate action from:
    - "Update System A"
    - "Update System B"
    - "Send Email"
    - "Create SR Ticket"

    Use the supplied tools to fetch additional data.
    """

    print(f"action Prompt: {prompt}")

    response = mistral_client.chat.completions.create(
    model="mistralai/mistral-small-3.1-24b-instruct:free",
    messages=[
            {"role": "system", "content": "You are an AI agent responsible for deciding actions based on anomalies."},
            {"role": "user", "content": prompt}
        ],
        tools=tools,
        tool_choice='auto',
        temperature=0,
        max_tokens=300
    )

    print(response)

    # Check if function calling was triggered
    if response.choices[0].finish_reason == "tool_calls":
        tool_call = response.choices[0].message.tool_calls[0]
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        # Call the appropriate function
        print(f"Calling tool: {tool_name} with args: {tool_args}")
        additional_data = available_tools[tool_name](**tool_args)

        # Re-run LLM with new data
        prompt += f"\nAdditional data received: {json.dumps(additional_data, indent=2)}"
        ### Based on the above data, LLM will be invoked to decide the action ###
        ### Additionally RAG can be adopted to send the reconciler's feedback, back to LLM ###
        response = client.chat.completions.create(
            model=config["llm_model"],
            messages=[
                {"role": "system",
                 "content": "You are an AI agent responsible for deciding actions based on anomalies."},
                {"role": "user", "content": prompt},
            ],
            temperature=0
        )

    state.final_action = response.choices[0].message.content.strip()
    return state


graph.add_node("decide_action", decide_action)
graph.add_edge("detect_anomaly", "decide_action")


# Step 5: Execute Action
def execute_action(state: WorkflowState) -> WorkflowState:
    """Executes the LLM's suggested action"""
    action_mapping = {
        "Update System A": lambda r: f"System A updated for Account: {r['Account']}",
        "Update System B": lambda r: f"System B updated for Account: {r['Account']}",
        "Send Email": lambda r: f"Email sent regarding Account: {r['Account']}",
        "Create SR Ticket": lambda r: f"SR Ticket created for Account: {r['Account']}"
    }

    action_func = action_mapping.get(state.final_action, lambda x: "No Action Taken")
    result = action_func(state.record)

    print(f"✅ Action Executed: {result}")
    return state


graph.add_node("execute_action", execute_action)
graph.add_edge("decide_action", "execute_action")

# Define start and end points
graph.set_entry_point("fetch_record")
graph.set_finish_point("execute_action")

# ------------------ visualize the Workflow ------------------

# def visualize_graph():
#     dot = graphviz.Digraph(format="png")

#     # Define nodes
#     dot.node("fetch_record", "Fetch Record")
#     dot.node("fetch_history", "Fetch History")
#     dot.node("detect_anomaly", "Detect Anomaly")
#     dot.node("decide_action", "Decide Action")
#     dot.node("execute_action", "Execute Action")

#     # Define edges
#     dot.edge("fetch_record", "fetch_history")
#     dot.edge("fetch_history", "detect_anomaly")
#     dot.edge("detect_anomaly", "decide_action")
#     dot.edge("decide_action", "execute_action")

#     # Save and render
#     graph_path = os.path.join("workflow", "workflow-tools")
#     dot.render(graph_path)
#     print("✅ Graph saved as langgraph_workflow.png")

# # Generate Graph
# visualize_graph()

# ------------------ Run the Workflow ------------------

workflow = graph.compile()
workflow.invoke({})
