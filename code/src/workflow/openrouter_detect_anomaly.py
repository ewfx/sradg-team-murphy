import requests

# OpenRouter API URL
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Replace with your OpenRouter API key
API_KEY = "#YOUR_TOKEN"

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
