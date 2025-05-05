import json
import os
from api_handlers.product import search_products_by_keywords
from utils.fallback_llm import get_fallback_response
from utils.spell_corrector import correct_text
from utils.cms_responses import CMS_RESPONSES
from utils.cms_responses import CMS_SYNONYMS


CONTEXT_FILE = "data/context_memory.json"

def load_context():
    try:
        if os.path.exists(CONTEXT_FILE):
            with open(CONTEXT_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
    except Exception as e:
        print("Error loading context:", e)

    return {
        "last_product": None,
        "pending_ai_query": None,
        "last_product_options": []
    }

def save_context(context):
    with open(CONTEXT_FILE, "w") as f:
        json.dump(context, f)

def extract_intent(query):
    query = query.lower()
    if "price" in query or "cost" in query or "how much" in query:
        return "price"
    elif "feature" in query:
        return "features"
    elif "why choose" in query or "why should i buy" in query:
        return "why_choose"
    elif "usage" in query or "how to use" in query:
        return "usage"
    elif query.strip() in ["yes", "yes please", "okay", "ask ai", "go ahead"]:
        return "ai_confirm"
    else:
        return "general"

def get_product_attribute(product, attribute):
    value = product.get(attribute, "")
    return value.strip() if value else None

def extract_product_keywords(corrected_query):
    noisy_phrases = [
        "what is the", "price of", "cost of", "how much is",
        "show me", "i want", "tell me about"
    ]
    cleaned = corrected_query.lower()
    for phrase in noisy_phrases:
        cleaned = cleaned.replace(phrase, "")
    return cleaned.strip()

def format_product_list(products):
    message = "🔍 I found multiple matching products:\n\n"
    for i, p in enumerate(products[:5], 1):
        message += (
            f"{i}. **{p['name']}** – ₹{p['our_price']}\n"
            f"   {p['description'][:90]}...\n\n"
        )
    return message.strip()

def handle_user_query(query):
    context = load_context()
    intent = extract_intent(query)

    # Handle: "select option 2" or just "2"
    if query.lower().startswith("select option") or query.strip().isdigit():
        try:
            option_number = int(query.strip().split()[-1])
            selected = context.get("last_product_options", [])[option_number - 1]
            context["last_product"] = selected["name"]
            context["last_product_options"] = []
            save_context(context)
            return (
                f"**{selected['name']}**\n"
                f"Price: ₹{selected.get('our_price', 'N/A')}\n\n"
                f"**Description:** {selected.get('description', '')}\n\n"
                f"**Features:** {selected.get('features', '')}\n\n"
                f"**Why Choose:** {selected.get('why_choose', '')}"
            )
        except:
            return "❌ Invalid selection. Try `select option 2` or just type the number."

    # Handle AI confirmation
    if intent == "ai_confirm" and context.get("pending_ai_query"):
        ai_response = get_fallback_response(context["pending_ai_query"])
        context["pending_ai_query"] = None
        save_context(context)
        return f"🤖 AI says:\n{ai_response}"

    corrected_query = correct_text(query)
    print(f"🔎 Corrected Query: {corrected_query}")

    # ✅ Check for predefined CMS responses
    # ✅ Synonym-based CMS intent detection
    cms_query = corrected_query.lower()
    for phrase, key in CMS_SYNONYMS.items():
        if phrase in cms_query and key in CMS_RESPONSES:
            return CMS_RESPONSES[key]


    keywords_only = extract_product_keywords(corrected_query)
    matched_products = search_products_by_keywords(keywords_only)

    selected_product = None

    if matched_products:
        context["last_product"] = matched_products[0]["name"]
        context["pending_ai_query"] = None

        # Save product options for selection
        if len(matched_products) > 1 and intent in ["price", "general"]:
            context["last_product_options"] = matched_products
            save_context(context)
            return format_product_list(matched_products)

        if len(matched_products) == 1:
            selected_product = matched_products[0]

        save_context(context)

    elif intent in ["price", "features", "why_choose", "usage"]:
        context["pending_ai_query"] = corrected_query
        save_context(context)
        return "I couldn’t find a matching product. Would you like me to ask the AI assistant for help?"

    else:
        if context.get("last_product") and intent != "general":
            memory_match = search_products_by_keywords(context["last_product"])
            if memory_match:
                selected_product = memory_match[0]

    if not matched_products and selected_product is None:
        context["pending_ai_query"] = corrected_query
        save_context(context)
        return "I couldn’t find a matching product. Would you like me to ask the AI assistant for help?"

    if intent != "general" and selected_product:
        value = get_product_attribute(selected_product, intent)
        if value:
            context["pending_ai_query"] = None
            save_context(context)
            return f"**{intent.capitalize()} of {selected_product['name']}**:\n{value}"
        else:
            context["pending_ai_query"] = corrected_query
            save_context(context)
            return f"I couldn’t find {intent} information for **{selected_product['name']}**. Want me to ask my AI assistant?"

    if selected_product:
        return (
            f"**{selected_product['name']}**\n"
            f"Price: ₹{selected_product.get('our_price', 'N/A')}\n"
            f"Description: {selected_product.get('description', '')[:150]}...\n"
        )

    return "I couldn’t find a matching product. Would you like me to ask the AI assistant for help?"
