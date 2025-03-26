from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel
from NoSqlUtil import TinyDBManager  # Import the existing TinyDBManager


# Define the lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the TinyDBManager
    app.state.db_manager = TinyDBManager()  # Ensure you use the correct database file
    print("✅ TinyDB Manager initialized")
    yield  # Continue running the app without closing the DB

# Initialize FastAPI with lifespan handler
app = FastAPI(lifespan=lifespan)

class RegisterSystemRequest(BaseModel):
    system_name: str
    key_columns: List[str]
    criteria_columns: List[str]

class UploadCSV(BaseModel):
    system_name: str
    file_path: str

class HistoricalDataRequest(BaseModel):
    system_name: str
    query_params: dict

@app.get("/")
def read_root():
    return {"message": "FastAPI is running with TinyDBManager!"}


@app.post("/register_system/")
def register_system(data: RegisterSystemRequest):
    """Register a new system and store its metadata"""
    try:
        app.state.db_manager.register_system(data.system_name, data.key_columns, data.criteria_columns)
        return {"message": f"System '{data.system_name}' registered successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/upload_csv/")
def upload_csv(data: UploadCSV):
    """Load data from CSV into the corresponding system's table"""
    try:
        app.state.db_manager.load_csv_to_system(data.system_name, data.file_path)
        return {"message": f"Data loaded successfully for system '{data.system_name}'."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/get_historical_data/")
def get_historical_data(data: HistoricalDataRequest):
    """Fetch historical data for a system based on query params"""
    print(data.system_name)
    print(data.query_params)
    try:
        data = app.state.db_manager.get_historical_data(data.system_name, data.query_params)
        return {"historical_data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
