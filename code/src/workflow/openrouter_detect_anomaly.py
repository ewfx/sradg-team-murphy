import requests

# OpenRouter API URL
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Replace with your OpenRouter API key
API_KEY = "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"

# Specify the model you want to use
MODEL_NAME = "mistralai/mistral-7b-instruct:free"  # Change to your preferred model

# Define the headers for authentication
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def query_openrouter(prompt, model=MODEL_NAME):
    """
    Sends a prompt to the OpenRouter API and returns the model's response.
    """
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": "You are an AI assistant."},
                     {"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 512
    }

    response = requests.post(API_URL, headers=HEADERS, json=payload)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error {response.status_code}: {response.text}"

if __name__ == "__main__":
    # Example usage
    prompt = f"""
        You are an AI model designed for anomaly detection in financial reconciliation data. Your task is to analyze the given data and compare it with historical trends to identify anomalies based on the balance columns and report if there is an anomaly and the category only
    
        Given data:
        As of Date,Company,Account,AU,Currency,Primary Account,Secondary Account,GL Balance,IHub Balance,Balance Difference,Match Status
        2025-03-27,83885,8100566,AU1,USD,ALL OTHER LOANS,DEFERRED COSTS,27020.76,18789.66,16231.1
    
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
    print(response)
