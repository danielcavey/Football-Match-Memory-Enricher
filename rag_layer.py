import pandas as pd
import os
from dotenv import load_dotenv
import requests
import json

# Read in dataset from articles dataset
df = pd.read_csv("articles.csv")

# Function to extracts the text from the relevant articles in the dataset for a match

def get_match_articles(match_id):
    return df[df["match_id"]==match_id]

# Funtion that joins the text from all the different articles together

def build_context(match_articles):
    texts = match_articles["text"].tolist()
    return "\n\n".join(texts)

# Function that builds the query that will be fed into the LLM
# Edit OUTPUT FORMAT when a decision has been made about what summary date we want

def build_query(context):
    return f"""
    You are a strict information extraction system.

    TASK:
    Extract structured football match events from the text.

    RULES:
    - Use ONLY information explicitly stated in the text
    - Do NOT guess or infer missing data
    - Do NOT add commentary
    - Do NOT repeat or duplicate events
    - If minute is not explicitly stated, leave it as empty string
    - Return ONLY the valid JSON (no markdown, no backticks, no explanation, no prose prior to the JSON output)

    OUTPUT FORMAT (must match exactly):
    {{
        "goals": [
            {{
                "minute": "",
                "player": "",
                "team": ""
            }}
            ],
        "red cards": [
            {{
                "minute": "",
                "player": "",
                "team": ""
            }}
            ],
        "home manager": "",
        "away manager": "",
        "man of the match": "",
        "stadium": ""
    }}

    TEXT:
    {context}
    """.strip()

# Get API key for OpenRouter from .env file

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

# Python function that interacts with the LLM

# Reasons why OpenRouter was chosen as an API
# Access to multiple models (OpenAI, Google, HuggingFace) using one API
#       Flexibility identified as important at early stage of project
#       Avoids vendor lock in
# Inexpensive

# Reasons why LLama 3 was chosen as AI Model
# Relaible: Widely supported across different APIs (crucial for early stages of project when archeticeture can change)
# Good size (8B --> 8 billion paramters)
# Inexpensive: Works on cheap API tiers
# Fast enough for real time use (could get away with slower times since pipeline will only run infrequently)
# Instruct tuning: Trained specifically to follow user instructions

def extract_match_info(query):
    response = requests.post(                                       # Send data to server
        url="https://openrouter.ai/api/v1/chat/completions",        # URL where OpenRouter recieves and sends responses
        headers={
            "Authorization": f"Bearer {API_KEY}",                   # Communicates API Key
            "Content-Type": "application/json"                      # Telling API we sending json data
        },
        
        #The actual body of the request
        json={
            "model": "meta-llama/llama-3-8b-instruct",              # The AI model we want to use
            "messages": [
                {"role": "user", "content": query}                # Role being user tells us this is the input. Context is the input text we are giving the AI.
            ]
        }
    )

    data = response.json()                                          # Converts response to a dictionary

    if "choices" in data:
        return data["choices"][0]["message"]["content"]             # Prints output given by the AI. Defaults to the first response if the AI suggests multiple models
    else:
        return f"Error: {data}"
    
# Composes the preceeding functions to generate required summary for the sample match

match_id = 2
match_articles = get_match_articles(match_id)
context = build_context(match_articles)
query = build_query(context)
output = extract_match_info(query)
print(output)

# Saves output from LLM query into a json file

new_data = json.loads(output)
with open("match.json","w") as f:
    json.dump(new_data,f,indent=4)          # indent=4 means each indentation level in the json file is presented with 4 spaces for readibility