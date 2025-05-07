import re

INTENT_KEYWORDS = {
    "greeting": [
        r"\b(hi|hello|hey|howdy|yo|greetings)\b",
        r"\bgood (morning|afternoon|evening|day|night)\b",
        r"\bhow (are|r) (you|u)\b",
        r"\bsup\b",
        r"\bwhat('?s| is) up\b"
    ],
    "small_talk": [
        r"\bare you a (bot|robot)\b",
        r"\bwhat('?s| is) your name\b",
        r"\bcan i talk to (a )?(human|agent)\b",
        r"\bwho (are|r) you\b",
        r"\bhow old are you\b",
        r"\bdo you speak\b"
    ],
    # Add more categories if needed
}

def classify_intent(text):
    text = text.lower().strip()

    for intent, patterns in INTENT_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return intent

    return "unknown"
