import requests

def log_conversation(user_input, bot_response):
    try:
        payload = {
            "input": user_input,
            "response": bot_response
        }
        # Adjust port and headers as needed
        res = requests.post("https://aarogyaabharat.com/api/chatbot", json=payload)
        if res.status_code != 200:
            print("⚠️ Failed to log conversation:", res.text)
    except Exception as e:
        print("⚠️ Logging error:", e)
