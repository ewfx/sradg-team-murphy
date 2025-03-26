import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Load historical training data
train_data = pd.read_csv("train_data.csv")  # Update path

# Define key columns and criteria columns
key_columns = ["company_number", "account", "AU", "currency", "primary_account", "secondary_account"]
criteria_columns = ["gl_balance", "ihb_balance"]

# Ensure classification column exists
if "match_status" not in train_data.columns:
    raise ValueError("Training data must have 'match_status' column (Match/Break).")

# Filter only "Break" cases for training
train_breaks = train_data[train_data["match_status"] == "break"].copy()

# Compute difference column
if "difference" not in train_breaks.columns:
    train_breaks["difference"] = train_breaks["gl_balance"] - train_breaks["ihb_balance"]

# Use historical break cases for model training
X_train = train_breaks[criteria_columns + ["difference"]]
y_train = np.ones(len(X_train))  # All historical "Break" cases are labeled as expected (1)

# Scale the features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

# Train Random Forest model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train_scaled, y_train)

# Load new dataset (only Break cases)
new_data = pd.read_csv("new_data.csv")  # Update path

# Ensure required columns exist
missing_cols = [col for col in criteria_columns if col not in new_data.columns]
if missing_cols:
    raise ValueError(f"New data is missing required columns: {missing_cols}")

# Compute difference column
if "difference" not in new_data.columns:
    new_data["difference"] = new_data["gl_balance"] - new_data["ihb_balance"]

# Extract feature columns
X_new = new_data[criteria_columns + ["difference"]]

# Scale using the same scaler
X_new_scaled = scaler.transform(X_new)

# Predict anomalies
predictions = model.predict(X_new_scaled)
print(predictions)
# Add predictions to new data
new_data["anomaly_detected"] = (predictions == 0)  # 1 = Expected Break, 0 = Anomaly

# Save results
new_data.to_csv("predicted_anomalies.csv", index=False)

print("Anomaly detection complete. Results saved in 'predicted_anomalies.csv'.")
