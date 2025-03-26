from pydantic import BaseModel
from typing import Any

class WorkflowState(BaseModel):
    historical_df: Any = None
    realtime_df: Any = None
    historical_data: Any = None
    realtime_data: Any = None
    llm_response: Any = None
    anomaly_decision: str = ""
    reviewer_action: str = ""
    message: str = ""

# Create an instance of WorkflowState
state = WorkflowState()
