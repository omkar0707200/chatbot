import os
import requests

from dotenv import load_dotenv
load_dotenv()


HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
if not HUGGINGFACE_API_KEY:
    raise EnvironmentError("HUGGINGFACE_API_KEY is not loaded. Check your .env and load_dotenv() call.")

API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

def get_fallback_response(prompt):
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.7,
            "return_full_text": False
        }
    }
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, list):
            return result[0]['generated_text']
        else:
            return result.get("generated_text", "Sorry, I couldn't understand that.")
    except Exception as e:
        if '401' in str(e):
            return "⚠️ Unauthorized API access. Please check your HuggingFace token."
    # print("Fallback LLM error:", e)
    return "I'm having trouble accessing my knowledge. Please try again later."

