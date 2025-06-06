import json
import os
from api_handlers.product import search_products_by_keywords
from utils.fallback_llm import get_fallback_response
from utils.spell_corrector import correct_text
from utils.cms_responses import CMS_RESPONSES, CMS_SYNONYMS
from utils.intent_classifier import classify_intent
from utils.pincode_checker import check_pincode_serviceability
from utils.logger import log_conversation  # ⬅️ NEW

CONTEXT_FILE = "data/context_memory.json"

def load_context():
    if os.path.exists(CONTEXT_FILE):
        with open(CONTEXT_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                pass
    return {
        "last_product": None,
        "pending_ai_query": None,
        "last_product_options": [],
        "expecting_pincode": False
    }

def save_context(context):
    with open(CONTEXT_FILE, "w") as f:
        json.dump(context, f)

def extract_intent(query):
    q = query.lower()
    if "price" in q or "cost" in q or "how much" in q:
        return "our_price"
    elif "feature" in q:
        return "features"
    elif "why choose" in q or "why should i buy" in q:
        return "why_choose"
    elif "usage" in q or "how to use" in q:
        return "usage"
    elif q.strip() in ["yes", "yes please", "okay", "ask ai", "go ahead"]:
        return "ai_confirm"
    else:
        return "general"

def get_product_attribute(product, attribute):
    val = product.get(attribute, "")
    return val.strip() if val else None

def extract_product_keywords(q):
    for phrase in ["what is the", "price of", "cost of", "how much is", "show me", "i want", "tell me about"]:
        q = q.lower().replace(phrase, "")
    return q.strip()

def format_product_list(products):
    msg = "🔍 I found multiple matching products:\n\n"
    for i, p in enumerate(products[:5], 1):
        msg += f"{i}. **{p['name']}** – ₹{p['our_price']}\n\n"
    return msg.strip()

def handle_user_query(user_input):
    context = load_context()
    corrected_query = correct_text(user_input)
    print(f"🔎 Corrected Query: {corrected_query}")
    query_lower = corrected_query.lower()

    # Check for greeting or small talk
    intent_type = classify_intent(corrected_query)
    if intent_type == "greeting":
        response = (
            "👋 Namaste! I’m your Aarogyaa Bharat assistant.\n\n"
            "Ask me about:\n- 🏷️ Prices\n- 🚚 Delivery\n- 🛠️ Installation\n- 💬 Products"
        )
        log_conversation(user_input, response)
        return response
    elif intent_type == "small_talk":
        response = (
            "🤖 I’m your trusty bot, full of medical wisdom and witty puns.\n"
            "Try asking: *'Do you deliver in Pune?'* or *'Return policy?*"
        )
        log_conversation(user_input, response)
        return response

    # Handle pincode delivery flow
    if context.get("expecting_pincode") and user_input.strip().isdigit() and len(user_input.strip()) == 6:
        pin = user_input.strip()
        delivery_info = check_pincode_serviceability(pin)
        context["expecting_pincode"] = False
        save_context(context)

        if delivery_info["deliverable"]:
            response = (
                f"✅ Yes! We deliver to pincode {pin} in **{delivery_info['district']}**, **{delivery_info['state']}**."
            )
        else:
            response = (
                f"❌ Sorry, we don’t deliver to pincode {pin}"
                f"{f' in **{delivery_info['district']}**, **{delivery_info['state']}**' if delivery_info['district'] else ''}."
            )
        log_conversation(user_input, response)
        return response

    if "deliver" in query_lower or "ship to" in query_lower:
        context["expecting_pincode"] = True
        save_context(context)
        response = "🚚 We deliver across India. Please enter your *pincode* to confirm availability."
        log_conversation(user_input, response)
        return response

    # CMS / FAQ responses
    if query_lower.strip() in CMS_RESPONSES:
        response = CMS_RESPONSES[query_lower.strip()]
        log_conversation(user_input, response)
        return response

    for phrase, key in CMS_SYNONYMS.items():
        if phrase in query_lower and key in CMS_RESPONSES:
            response = CMS_RESPONSES[key]
            log_conversation(user_input, response)
            return response

    # Product selection by option number
    if user_input.lower().startswith("select option") or user_input.strip().isdigit():
        try:
            index = int(user_input.strip().split()[-1]) - 1
            selected = context.get("last_product_options", [])[index]
            context["last_product"] = selected["name"]
            context["last_product_options"] = []
            save_context(context)
            response = (
                f"**{selected['name']}**\n"
                f"Price: ₹{selected.get('our_price', 'N/A')}\n\n"
                f"**Features:** {selected.get('features', '')}\n\n"
                f"**Why Choose:** {selected.get('why_choose', '')}"
            )
            log_conversation(user_input, response)
            return response
        except:
            response = "⚠️ Invalid selection. Try `select option 2` or just type the number."
            log_conversation(user_input, response)
            return response

    # AI fallback confirmation
    if extract_intent(corrected_query) == "ai_confirm" and context.get("pending_ai_query"):
        ai_response = get_fallback_response(context["pending_ai_query"])
        context["pending_ai_query"] = None
        save_context(context)
        log_conversation(user_input, ai_response)
        return f"🤖 AI says:\n{ai_response}"

    # Product search
    intent = extract_intent(corrected_query)
    keywords = extract_product_keywords(corrected_query)
    matched = search_products_by_keywords(keywords)
    selected = None

    if matched:
        context["last_product"] = matched[0]["name"]
        context["pending_ai_query"] = None

        if len(matched) > 1 and intent in ["our_price", "general"]:
            context["last_product_options"] = matched
            save_context(context)
            response = format_product_list(matched)
            log_conversation(user_input, response)
            return response

        selected = matched[0]
        save_context(context)

    elif intent in ["our_price", "features", "why_choose", "usage"]:
        context["pending_ai_query"] = corrected_query
        save_context(context)
        response = "🧠 That’s beyond my training! Want me to ask my AI cousin?"
        log_conversation(user_input, response)
        return response

    elif context.get("last_product") and intent != "general":
        previous = search_products_by_keywords(context["last_product"])
        if previous:
            selected = previous[0]

    if selected:
        if intent != "general":
            value = get_product_attribute(selected, intent)
            if value:
                response = f"**{intent.replace('_', ' ').capitalize()} of {selected['name']}**:\n{value}"
                log_conversation(user_input, response)
                return response
            else:
                context["pending_ai_query"] = corrected_query
                save_context(context)
                response = f"Couldn't find {intent} info for **{selected['name']}**. Want me to ask AI?"
                log_conversation(user_input, response)
                return response

        response = f"**{selected['name']}**\nPrice: ₹{selected.get('our_price', 'N/A')}"
        log_conversation(user_input, response)
        return response

    context["pending_ai_query"] = corrected_query
    save_context(context)
    response = "🧠 That went over my head like a flying stethoscope. Want me to ask the AI?"
    log_conversation(user_input, response)
    return response
