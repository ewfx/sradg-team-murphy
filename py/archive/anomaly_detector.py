import json
from openai import OpenAI
import pandas as pd
from sqlUtil import SQLiteDB

# Initialize the in-memory database
db = SQLiteDB()

# 1️⃣ Load Configuration
with open("anomaly_config.json", "r") as config_file:
    config = json.load(config_file)

# Load historical data from a CSV file
db.load_csv_data(config["historical_data_file"])


client = OpenAI(
  base_url=config["base_url"],
  api_key=config["api_key"]
)

def load_new_data_from_csv(csv_path):
    df = pd.read_csv(csv_path)
    json_data = df.to_dict(orient="records")
    return json_data

def find_anomalies():

    new_data = load_new_data_from_csv(config["new_data_case1"])
    print(new_data[0])

    # Query the historical database
    historical_data = db.get_historical_data(new_data[0])
    if historical_data:
        print("🔍 Matching historical records found:")
        print(historical_data)
    else:
        print("No matching historical data found.")

    prompt_template = config["prompt_template"]
    prompt = prompt_template.format(
            historical_data=json.dumps(historical_data, indent=2),
            new_data=json.dumps(new_data, indent=2)
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

    anomaly_result = content.split("|")[0].split(":")[1].strip()
    category = content.split("|")[1].strip()
    explanation = content.split("|")[2].strip()

    print('anomaly: ' + anomaly_result)
    print('explanation: ' + explanation)
    print('category: '+ category)


    db.save_prediction(new_data[0], anomaly_result, category, explanation)

    #save the predictions for audit and retraining purposes
    predictions = db.get_predictions()
    for p in predictions:
        print(p)

db.close()