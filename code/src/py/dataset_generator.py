import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta


# Function to generate month-end dates for the last 6 months
def generate_month_end_dates(months=7):
    today = datetime.now()
    month_end_dates = []
    for i in range(months, 0, -1):
        year = (today - timedelta(days=i * 30)).year
        month = (today - timedelta(days=i * 30)).month
        # Get the last day of the month
        last_day = (datetime(year, month + 1, 1) - timedelta(days=1)) if month < 12 else datetime(year, 12, 31)
        month_end_dates.append(last_day)
    return month_end_dates


# Function to generate historical data with month-end dates
def generate_historical_data(num_keys=10000, months=6):
    historical_data = []
    month_end_dates = generate_month_end_dates(months)
    key_ids = range(1, num_keys + 1)

    for key_id in key_ids:
        company = random.randint(1000, 9999)
        account = random.randint(1000000, 9999999)
        au = random.randint(1000, 9999)
        currency = random.choice(['USD', 'EUR', 'INR', 'JPY'])
        primary_account = random.choice(['LOANS', 'INTEREST', 'DEPOSITS', 'FEES'])
        secondary_account = random.choice(['PRINCIPAL', 'INTEREST', 'PENALTY'])

        for date in month_end_dates:
            gl_balance = round(random.uniform(1000, 50000), 2)
            ihub_balance = gl_balance + round(random.uniform(-5000, 5000), 2)  # Include large variations
            balance_diff = ihub_balance - gl_balance  # This will include negative values

            transaction = {
                'As of Date': date,
                'Company': company,
                'Account': account,
                'AU': au,
                'Currency': currency,
                'Primary Account': primary_account,
                'Secondary Account': secondary_account,
                'GL Balance': gl_balance,
                'IHub Balance': ihub_balance,
                'Balance Difference': balance_diff
            }
            historical_data.append(transaction)

    return pd.DataFrame(historical_data)


# Function to generate classification dataset with anomaly labeling
def generate_classification_data(historical_df_class):
    classification_data = []
    key_columns = ['Company', 'Account', 'AU', 'Currency', 'Primary Account', 'Secondary Account']

    # Group by key columns and calculate historical features
    grouped = historical_df_class.groupby(key_columns)
    for group_key, group_data in grouped:
        group_data = group_data.sort_values(by='As of Date')

        # Historical features for GL Balance
        historical_mean_gl = group_data['GL Balance'].expanding().mean().shift(2)
        historical_std_gl = group_data['GL Balance'].expanding().std().shift(2)
        historical_trend_gl = group_data['GL Balance'].shift(2).rolling(window=3).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 3 else np.nan
        )

        # Historical features for IHub Balance
        historical_mean_ihub = group_data['IHub Balance'].expanding().mean().shift(2)
        historical_std_ihub = group_data['IHub Balance'].expanding().std().shift(2)
        historical_trend_ihub = group_data['IHub Balance'].shift(1).rolling(window=3).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 3 else np.nan
        )

        # Historical features for Balance Difference
        historical_mean_diff = group_data['Balance Difference'].expanding().mean().shift(2)
        historical_std_diff = group_data['Balance Difference'].expanding().std().shift(2)
        historical_trend_diff = group_data['Balance Difference'].shift(2).rolling(window=3).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 3 else np.nan
        )

        # Use the last row as the current record
        current_transaction = group_data.iloc[-2].to_dict()
        current_transaction['Historical Mean GL Balance'] = historical_mean_gl.iloc[-1]
        current_transaction['Historical Std Dev GL Balance'] = historical_std_gl.iloc[-1]
        current_transaction['Historical Trend GL Balance'] = historical_trend_gl.iloc[-1]
        current_transaction['Historical Mean IHub Balance'] = historical_mean_ihub.iloc[-1]
        current_transaction['Historical Std Dev IHub Balance'] = historical_std_ihub.iloc[-1]
        current_transaction['Historical Trend IHub Balance'] = historical_trend_ihub.iloc[-1]
        current_transaction['Historical Mean Balance Difference'] = historical_mean_diff.iloc[-1]
        current_transaction['Historical Std Dev Balance Difference'] = historical_std_diff.iloc[-1]
        current_transaction['Historical Trend Balance Difference'] = historical_trend_diff.iloc[-1]

        # Add anomaly labels using historical trend
        balance_diff = abs(current_transaction['Balance Difference'])
        if balance_diff > 4000:  # Example anomaly condition
            current_transaction['Anomaly'] = 'Yes'
            current_transaction['Anomaly_Type'] = 'Huge Spike'
        # elif abs(historical_trend_diff.iloc[-1]) > 2000 or abs(historical_trend_ihub.iloc[-1]) > 2000 or abs(historical_trend_gl.iloc[-1]) > 2000: # Example threshold for trend anomaly
        #     current_transaction['Anomaly'] = 'Yes'
        #     current_transaction['Anomaly_Type'] = 'Trend Deviation'
        elif historical_std_diff.iloc[-1] > 10000 or historical_std_gl.iloc[-1] > 10000 or historical_std_ihub.iloc[
            -1] > 10000:
            current_transaction['Anomaly'] = 'Yes'
            current_transaction['Anomaly_Type'] = 'Inconsistent Variation'
        else:
            current_transaction['Anomaly'] = 'No'
            current_transaction['Anomaly_Type'] = 'No Anomaly'

        classification_data.append(current_transaction)

    return pd.DataFrame(classification_data)


def generate_prediction_df(historical_df_pred):
    pred_data = []
    key_columns = ['Company', 'Account', 'AU', 'Currency', 'Primary Account', 'Secondary Account']

    # Group by key columns and calculate historical features
    grouped = historical_df_pred.groupby(key_columns)
    for group_key, group_data in grouped:
        group_data = group_data.sort_values(by='As of Date')
        current_transaction = group_data.iloc[-1].to_dict()
        pred_data.append(current_transaction)

    return pd.DataFrame(pred_data)


# Generate datasets
historical_df = generate_historical_data(num_keys=10000, months=7)
classification_df = generate_classification_data(historical_df)
prediction_df = generate_prediction_df(historical_df)

# Save to CSV
historical_df.to_csv('historical_data.csv', index=False)
classification_df.to_csv('classification_data.csv', index=False)
prediction_df.to_csv('prediction_data.csv', index=False)

print("Datasets with Historical Trend Balance Difference incorporated in anomaly labeling created!")
