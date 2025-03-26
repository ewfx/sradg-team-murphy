import json
from openai import OpenAI
from sqlUtil import SQLiteDB
from NoSqlUtil import TinyDBManager

# Initialize the in-memory database
db = SQLiteDB()

# Load historical data from a CSV file
db.load_csv_data("train_data_new.csv")

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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",
)

# historical_data = [
#     {"company_number": "1111", "account": "1634789", "AU": "6783", "currency": "EUR",
#      "gl_balance": 20000, "ihb_balance": 10000, "difference": 10000, "match_status": "break"},
# ]

# historical_data = [
#   {
#     "company_number": "1111",
#     "account": "1634789",
#     "AU": "6783",
#     "currency": "EUR",
#     "primary_account": "ALL OTHER LOANS",
#     "secondary_account": "DEFERRED ORIGINATION FEES",
#     "gl_balance": 20000,
#     "ihb_balance": 60000,
#     "difference": -40000,
#     "match_status": "break"
#   },
#   {
#     "company_number": "1111",
#     "account": "1634789",
#     "AU": "6783",
#     "currency": "EUR",
#     "primary_account": "ALL OTHER LOANS",
#     "secondary_account": "DEFERRED ORIGINATION FEES",
#     "gl_balance": 20000,
#     "ihb_balance": 40000,
#     "difference": -20000,
#     "match_status": "break"
#   },
#   {
#     "company_number": "1111",
#     "account": "1634789",
#     "AU": "6783",
#     "currency": "EUR",
#     "primary_account": "ALL OTHER LOANS",
#     "secondary_account": "DEFERRED ORIGINATION FEES",
#     "gl_balance": 20000,
#     "ihb_balance": 20000,
#     "difference": 0,
#     "match_status": "match"
#   },
#   {
#     "company_number": "1111",
#     "account": "1634789",
#     "AU": "6783",
#     "currency": "EUR",
#     "primary_account": "ALL OTHER LOANS",
#     "secondary_account": "DEFERRED ORIGINATION FEES",
#     "gl_balance": 20000.1,
#     "ihb_balance": 20000,
#     "difference": 0.1,
#     "match_status": "match"
#   },
#   {
#     "company_number": "1111",
#     "account": "1634789",
#     "AU": "6783",
#     "currency": "EUR",
#     "primary_account": "ALL OTHER LOANS",
#     "secondary_account": "DEFERRED ORIGINATION FEES",
#     "gl_balance": 10000,
#     "ihb_balance": 10000,
#     "difference": 0,
#     "match_status": "match"
#   },
#   {
#     "company_number": "1111",
#     "account": "1634789",
#     "AU": "6783",
#     "currency": "EUR",
#     "primary_account": "ALL OTHER LOANS",
#     "secondary_account": "DEFERRED ORIGINATION FEES",
#     "gl_balance": 10200,
#     "ihb_balance": 10000,
#     "difference": 200,
#     "match_status": "break"
#   }
# ]

######
new_data = {
    "company_number": "1111",
    "account": "1634789",
    "AU": "6783",
    "currency": "EUR",
    "primary_account": "ALL OTHER LOANS",
    "secondary_account": "DEFERRED ORIGINATION FEES",
    "gl_balance": 20000,
    "ihb_balance": 0,
    "difference": -20000,
    "match_status": "break"
}

# Query the historical database
historical_data = db.get_historical_data(new_data)
# if historical_data:
#     print("🔍 Matching historical records found:")
#     print(historical_data)
# else:
#     print("No matching historical data found.")

prompt = f"""
Given the historical financial data:
{json.dumps(historical_data, indent=2)}

Analyze the new record:
{json.dumps(new_data, indent=2)}

Is this new 'break' an anomaly based on past data? Answer 'Yes' or 'No' with an explanation and categorize it into the following categories:
- Inconsistent variations in outstanding balances
- Sudden drop in IHub balance
- Sudden increase in GL balance
- Huge spike in outstanding balances
- Others
Send the response with three labels: 'Anomaly', 'category', 'explanation' each separated by a pipe.
"""

completion = client.chat.completions.create(
  extra_headers={
    # "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
    # "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
  },
  extra_body={},
  model="meta-llama/llama-3.3-70b-instruct:free",
  messages=[
        {"role": "system", "content": "You are a financial anomaly detection assistant."},
        {"role": "user", "content": prompt}
    ],
    max_tokens=300
)

content = completion.choices[0].message.content

anomaly_result = content.split("|")[0].split(":")[1].strip()
category = content.split("|")[1].strip()
explanation = content.split("|")[2].strip()

print(explanation)

db.save_prediction(new_data, anomaly_result, category, explanation)

# Usage:
predictions = db.get_predictions()
for p in predictions:
    print(p)

################
# ✅ Example Usage
db_manager = TinyDBManager()

# 🔹 Save metadata
db_manager.save_metadata(
    system_name="AnomalyDetection",
    table_name="t_anomaly_detection",
    key_columns=["company_number", "account", "AU", "currency"],
    criteria_columns=["gl_balance", "ihb_balance"]
)

# 🔹 Load CSV into TinyDB (replace 'your_file.csv' with actual file path)
csv_file_path = "data_load_system2.csv"  # Change this to the actual CSV file path
db_manager.load_csv_to_collection("AnomalyDetection", "t_anomaly_detection", csv_file_path)

# 🔹 Retrieve metadata
metadata = db_manager.get_metadata("AnomalyDetection", "t_anomaly_detection")
print("Metadata:", metadata)

# 🔹 Retrieve all data from the table
data = db_manager.get_all_data("AnomalyDetection", "t_anomaly_detection")
print("Loaded Data:", data)



db.close()