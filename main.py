from chains.core_chain import handle_user_query
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS
import os

load_dotenv()

app = Flask(__name__)
CORS(app)
@app.route("/")
def home():
    return "🤖 Aarogyaa Bharat Chatbot is running!"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    query = data.get("query")
    if( data.get("old_query") != None and (query=='yes' or query=='yes please' or query=='okay' or query=='ask ai' or query=='go ahead')):
        askai = data.get("old_query")
    else:
        askai = 'no'

    if not query:
        return jsonify({"error": "Missing 'query' in request"}), 400
    if(askai == 'no'):
        response = handle_user_query(query)
    else:
        response = get_fallback_response(askai)
    return jsonify({"response": response})
