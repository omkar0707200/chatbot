from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

from chains.core_chain import handle_user_query
from utils.fallback_llm import get_fallback_response  # make sure this exists

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

@app.route("/")
def home():
    return "🤖 Aarogyaa Bharat Chatbot is running!"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "Missing or empty 'query'"}), 400

    # Check if fallback should be used
    if data.get("old_query") and query.lower() in [
        "yes", "yes please", "okay", "ask ai", "go ahead"
    ]:
        askai = data.get("old_query")
        response = get_fallback_response(askai)
    else:
        response = handle_user_query(query)

    return jsonify({"response": response})

# Run app if needed locally
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
