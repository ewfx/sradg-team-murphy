from flask import Flask, request, jsonify
import pandas as pd
import os
import queue

app = Flask(__name__)

# In-memory storage for reconciliation systems
reconciliation_systems = {}


# Load systems from CSV (mock initial data loader)
def load_system_data():
    # Example CSV structure for each reconciliation system
    systems = [
        {"name": "System A", "key_columns": "Company,Account", "criteria_columns": "GL Balance,IHub Balance"},
        {"name": "System B", "key_columns": "Currency,AU", "criteria_columns": "Balance Difference"}
    ]
    for system in systems:
        reconciliation_systems[system["name"]] = {
            "info": {
                "key_columns": system["key_columns"],
                "criteria_columns": system["criteria_columns"],
            },
            "history": pd.DataFrame(),
            "predictions": pd.DataFrame()
        }


load_system_data()


# API: Get all reconciliation systems
@app.route('/api/get-reconciliation-systems', methods=['GET'])
def get_reconciliation_systems():
    systems = [
        {
            "name": name,
            "keyColumns": system["info"]["key_columns"],
            "criteriaColumns": system["info"]["criteria_columns"]
        }
        for name, system in reconciliation_systems.items()
    ]
    return jsonify(systems)


# API: Add new reconciliation system
@app.route('/api/add-reconciliation-system', methods=['POST'])
def add_reconciliation_system():
    name = request.form.get('name')
    key_columns = request.form.get('keyColumns')
    criteria_columns = request.form.get('criteriaColumns')
    file = request.files.get('historicalFile')

    if not name or not key_columns or not criteria_columns or not file:
        return jsonify({"error": "Missing fields"}), 400

    # Load historical data from the uploaded file
    try:
        historical_data = pd.read_csv(file)
        reconciliation_systems[name] = {
            "info": {
                "key_columns": key_columns,
                "criteria_columns": criteria_columns,
            },
            "history": historical_data,
            "predictions": pd.DataFrame()
        }
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"message": "Reconciliation system added successfully"}), 201


# API: Upload history data
@app.route('/api/upload-history', methods=['POST'])
def upload_history():
    system_name = request.form.get('system_name')
    file = request.files.get('historyFile')

    if not system_name or system_name not in reconciliation_systems or not file:
        return jsonify({"error": "Invalid system or file"}), 400

    try:
        history_data = pd.read_csv(file)
        reconciliation_systems[system_name]["history"] = history_data
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"message": "History uploaded successfully"}), 200


# API: Upload file for anomaly prediction
@app.route('/api/upload-and-predict', methods=['POST'])
def upload_and_predict():
    system_name = request.form.get('system_name')
    file = request.files.get('predictionFile')

    if not system_name or system_name not in reconciliation_systems or not file:
        return jsonify({"error": "Invalid system or file"}), 400

    try:
        prediction_data = pd.read_csv(file)
        # Mock prediction process
        prediction_data["Anomaly"] = ["Yes" if x % 2 == 0 else "No" for x in range(len(prediction_data))]
        reconciliation_systems[system_name]["predictions"] = prediction_data
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"message": "Prediction file uploaded and processed successfully"}), 200


# API: Get prediction results
@app.route('/api/get-prediction-results', methods=['GET'])
def get_prediction_results():
    system_name = request.args.get('system_name')

    if not system_name or system_name not in reconciliation_systems:
        return jsonify({"error": "Invalid system"}), 400

    prediction_data = reconciliation_systems[system_name]["predictions"]
    return prediction_data.to_json(orient="records")


# In-memory queue for predictions
prediction_queue = queue.Queue()

# Mock data for systems
mock_transactions_a1 = [
    {"transaction_id": 1, "key": "A1-001", "amount": 5000},
    {"transaction_id": 2, "key": "A1-002", "amount": 10000}
]

mock_transactions_a2 = [
    {"transaction_id": 1, "key": "A2-001", "amount": 7000},
    {"transaction_id": 2, "key": "A2-002", "amount": 15000}
]


# API: Get transactions from System A1
@app.route('/api/system-a1/transactions', methods=['GET'])
def get_transactions_a1():
    return jsonify(mock_transactions_a1)


# API: Get transactions from System A2
@app.route('/api/system-a2/transactions', methods=['GET'])
def get_transactions_a2():
    return jsonify(mock_transactions_a2)


# API: Push data to the prediction queue
@app.route('/api/push-to-queue', methods=['POST'])
def push_to_queue():
    data = request.json
    prediction_queue.put(data)
    return jsonify({"message": "Data pushed to prediction queue", "data": data})


# API: Update System A1
@app.route('/api/system-a1/update', methods=['POST'])
def update_system_a1():
    data = request.json
    return jsonify({"message": "System A1 updated successfully", "data": data})


# API: Update System A2
@app.route('/api/system-a2/update', methods=['POST'])
def update_system_a2():
    data = request.json
    return jsonify({"message": "System A2 updated successfully", "data": data})


# API: Mimic ticket creation
@app.route('/api/create-ticket', methods=['POST'])
def create_ticket():
    data = request.json
    return jsonify({"message": "Ticket created successfully", "ticket": data})


# API: Mimic sending notification email
@app.route('/api/send-email', methods=['POST'])
def send_email():
    data = request.json
    return jsonify({"message": "Notification email sent successfully", "email_details": data})


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
