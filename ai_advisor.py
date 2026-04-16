import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import anthropic

load_dotenv()

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/pawpal_advisor.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)

AI_LOG_PATH = "logs/pawpal_ai_log.jsonl"


def _log_interaction(pet_context: dict, user_message: str, response: str, success: bool) -> None:
    """Append one AI interaction to the JSONL log file."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "pet_context": pet_context,
        "user_message": user_message,
        "response": response,
        "success": success,
    }
    with open(AI_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Core advisor function
# ---------------------------------------------------------------------------

def get_ai_advice(
    user_message: str,
    pet_name: str,
    species: str,
    current_tasks: list[str],
) -> str:
    """
    Send a message to Claude with the pet's profile and current schedule as
    context. Returns the AI's response as a string.
    """
    pet_context = {
        "pet_name": pet_name,
        "species": species,
        "current_tasks": current_tasks,
    }

    system_prompt = f"""You are PawPal AI, a knowledgeable and friendly pet care advisor.
You are helping the owner of a {species} named {pet_name}.
Their current scheduled tasks are: {', '.join(current_tasks) if current_tasks else 'none yet'}.

Your job is to:
- Suggest specific, practical pet care tasks the owner should add to their schedule
- Answer questions about {species} care clearly and concisely
- When suggesting tasks, always include: task name, how long it takes (in minutes), and priority (HIGH/MEDIUM/LOW)

Keep responses concise and actionable. Format task suggestions clearly like:
Task: [name] | Duration: [X] mins | Priority: [HIGH/MEDIUM/LOW]"""

    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": user_message}
            ],
            system=system_prompt,
        )
        response_text = message.content[0].text
        _log_interaction(pet_context, user_message, response_text, success=True)
        logging.info(f"AI advice requested for {pet_name} ({species}) — success")
        return response_text

    except Exception as e:
        error_msg = f"AI advisor unavailable: {str(e)}"
        _log_interaction(pet_context, user_message, error_msg, success=False)
        logging.error(f"AI advisor error: {str(e)}")
        return error_msg
