
#Summerizes the log input from the 'logger' of the party,
#uses python requests to connect to Ollama's UI 


#Includes the prompt given to Llama, tried to keep it simple since it's a lower parameter model

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"


def summarize_session(session_notes):
    prompt = f"""
You are a Dungeons & Dragons session chronicler.

Summarize the following session notes into a clear recap for the players.

Include:
- Important story events
- Combat encounters and their outcomes
- Important NPC interactions
- Discoveries, items, and rewards
- Unresolved quests or mysteries

Rules:
- Only use information from the provided notes.
- Do not invent characters, events, or outcomes.
- Keep the recap organized by date entered.
- If a category was not mentioned, omit it.
- Simplify the log
- Stay consitent between log sessions.
- Use third-person narration.

SESSION NOTES:
{session_notes}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3
            }
        },
        timeout=180
    )

    response.raise_for_status()

    summary = response.json().get("response", "").strip()

    if not summary:
        raise ValueError("Llama returned an empty summary.")

    return summary
