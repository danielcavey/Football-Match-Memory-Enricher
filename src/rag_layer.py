import pandas as pd
import os
from dotenv import load_dotenv
import requests
import json

# Read in dataset from articles dataset
articles_df = pd.read_csv("../data/articles.csv")

# Function to extracts the text from the relevant articles in the dataset for a match

def get_match_articles(match_id):
    return articles_df[articles_df["match_id"]==match_id]

# Funtion that joins the text from all the different articles together

def build_context(match_articles):
    texts = match_articles["text"].tolist()
    return "\n\n".join(texts)

matches_df = pd.read_csv("../data/clean_matches.csv")
matches_df = matches_df.iloc[42:44]

# Funtion that estabishes known information in place of the LLM

def get_known_facts(match_id):
    row = matches_df[matches_df["match_id"] == match_id]
    row = row.iloc[0]
 
    return {
        "home_team": row["home team"],
        "away_team": row["away team"],
        "score": f'{row["home score"]}-{row["away score"]}',
        "ground": row["ground"],
        "known_goalscorers": row["goalscorer(s)"]
    }

# Function that builds the query that will be fed into the LLM
# Edit OUTPUT FORMAT when a decision has been made about what summary date we want

def build_query(context):
    return f"""
    You are a strict information extraction system operating on football match reports.
 
    KNOWN FACTS (already verified from the attendee's own records — do not re-derive these,
    use them only to disambiguate which match/players the text is referring to):
    - Home team: {known_facts['home_team']}
    - Away team: {known_facts['away_team']}
    - Final score: {known_facts['score']}
    - Ground: {known_facts['ground']}
    - Known goalscorers: {', '.join(known_facts['known_goalscorers']) or 'none recorded'}
 
    TASK:
    Extract ONLY the following, which are NOT already known:
    - The minute and scoring team for each goal
    - Any red cards
    - Home and away managers
    - Man of the match
    - Any stadium detail that adds to or conflicts with the known ground
 
    RULES:
    - Use ONLY information explicitly stated in the TEXT below.
    - Do NOT guess or infer missing data. If a field is not stated, leave it as an empty
      string or empty list.
    - Do NOT invent players, minutes, or names that are not present in the text.
    - Do NOT repeat or duplicate events.
    - Every fact you return MUST include a short verbatim quote (<=25 words, copied exactly
      from the TEXT) as its "evidence". If you cannot find a supporting quote, omit the fact.
 
    TEXT:
    {context}
    """.strip()

# Get API key for OpenRouter from .env file

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

# JSON format that we want output to take

RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "match_extraction",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "Home team": {"type": "string"},
                "Away team": {"type": "string"},
                "Final score": {"type": "string"},
                "Ground": {"type": "string"},
                "goals": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "minute": {"type": "string"},
                            "player": {"type": "string"},
                            "team": {"type": "string"},
                            "evidence": {"type": "string"},
                        },
                        "required": ["minute", "player", "team", "evidence"],
                        "additionalProperties": False,
                    },
                },
                "red_cards": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "minute": {"type": "string"},
                            "player": {"type": "string"},
                            "team": {"type": "string"},
                            "evidence": {"type": "string"},
                        },
                        "required": ["minute", "player", "team", "evidence"],
                        "additionalProperties": False,
                    },
                },
                "home_manager": {"type": "string"},
                "home_manager_evidence": {"type": "string"},
                "away_manager": {"type": "string"},
                "away_manager_evidence": {"type": "string"},
                "man_of_the_match": {"type": "string"},
                "man_of_the_match_evidence": {"type": "string"},
            },
            "required": [
                "Home team", "Away team", "Final score",
                "Ground", "goals", "red_cards",
                "home_manager", "home_manager_evidence",
                "away_manager", "away_manager_evidence",
                "man_of_the_match", "man_of_the_match_evidence",
            ],
            "additionalProperties": False,
        },
    },
}

# Python function that interacts with the LLM

# Reasons why OpenRouter was chosen as an API
# Access to multiple models (OpenAI, Google, HuggingFace) using one API
#       Flexibility identified as important at early stage of project
#       Avoids vendor lock in
# Inexpensive

# Reasons why openai/gpt-4o-mini was chosen as AI Model.
# Relaible: Widely supported across different APIs (crucial for early stages of project when archeticeture can change)
# Excellent for following strict output formats and JSON schema adherance
# Strong for long context reasoning
# Inexpensive: Works on cheap API tiers
# Fast enough for real time use (could get away with slower times since pipeline will only run infrequently)
# Note: not open source unlike Llama 3

import requests

def call_llm(query, retries=2):
    for attempt in range(retries + 1):
        response = requests.post(                                       # Send data to server
            url="https://openrouter.ai/api/v1/chat/completions",        # URL where OpenRouter recieves and sends responses
            headers={
                "Authorization": f"Bearer {API_KEY}",                   # Communicates API Key
                "Content-Type": "application/json",                     # Telling API we sending json data
            },
            json={
                "model": "openai/gpt-4o-mini",                          # The AI model we want to use
                "temperature": 0,                                       # temperature parameter determines the randomness of the models selection. Setting to 0 makes it as deterministic as possible. Recommended for consistent data extraction
                "max_tokens": 1200,                                     # Restricts the length of the response.... REQUIRED?
                "response_format": RESPONSE_SCHEMA,                     # Structure for the output enforced by the API
                "messages": [
                    {"role": "user", "content": query}
                ],
            },
            timeout=30,                                                 # Dictates the length of time the code will wait for the API to respond...... REQUIRED? TOO SHORT?
        )
        data = response.json()
 
        if "choices" not in data:
            if attempt == retries:
                return None, f"API error: {data}"
            time.sleep(1.5 * (attempt + 1))
            continue
 
        content = data["choices"][0]["message"]["content"]              #Output given by the AI. Defaults to the first response if the AI suggests multiple models
        try:
            return json.loads(content), None
        except json.JSONDecodeError as e:
            if attempt == retries:
                return None, f"JSON parse failed after {retries + 1} attempts: {e}"
            time.sleep(1)
 
    return None, "Unknown failure"

# TO DO: ADD ERROR PROCESSING DOWNSTREAM
    
# Composes the preceeding functions to generate required summary for the sample match

output = []
for match_id,group in articles_df.groupby("match_id"):
    known_facts = get_known_facts(match_id)
    match_articles = get_match_articles(match_id)
    context = build_context(match_articles)
    query = build_query(context)
    LLM_ouput = call_llm(query)[0]
    output.append(LLM_ouput)

# Saves output from LLM query into a json file

with open("../data/match.json","w") as f:
    json.dump(output,f,indent=4)          # indent=4 means each indentation level in the json file is presented with 4 spaces for readibility