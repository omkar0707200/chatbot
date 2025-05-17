import json
import os
from api_handlers.product import search_products_by_keywords
from utils.fallback_llm import get_fallback_response
from utils.spell_corrector import correct_text
from utils.cms_responses import CMS_RESPONSES, CMS_SYNONYMS
from utils.intent_classifier import classify_intent
from utils.pincode_checker import check_pincode_serviceability  # NEW

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
        "last_product_options": [],
        "expecting_pincode": False
    }

def save_context(context):
    with open(CONTEXT_FILE, "w") as f:
        json.dump(context, f)

def extract_intent(query):
    query = query.lower()
    if "price" in query or "cost" in query or "how much" in query:
        return "our_price"
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
        message += f"{i}. **{p['name']}** – ₹{p['our_price']}\n\n"
    return message.strip()

def handle_user_query(query):
    context = load_context()
    corrected_query = correct_text(query)
    print(f"🔎 Corrected Query: {corrected_query}")
    query_lower = corrected_query.lower()

    # 1. INTENT CLASSIFIER
    intent_type = classify_intent(corrected_query)
    if intent_type == "greeting":
        return (
            "👋 Namaste! I’m your Aarogyaa Bharat assistant.\n\n"
            "You can ask me about:\n"
            "- 🏷️ Product prices\n"
            "- 🚚 Delivery & return policy\n"
            "- 🛠️ Installation & warranty\n"
            "- 💬 Any medical equipment query\n\n"
            "What would you like to know?"
        )
    elif intent_type == "small_talk":
        return (
            "🤖 I’m your trusty bot, full of medical wisdom and witty puns.\n"
            "Try me with a question like: *'Do you deliver in Pune?'* or *'Tell me about your refund policy'*!"
        )

    # 2. HANDLE EXPECTING PINCODE
    if context.get("expecting_pincode") and query.strip().isdigit() and len(query.strip()) == 6:
        pin = query.strip()
        delivery_info = check_pincode_serviceability(pin)
        context["expecting_pincode"] = False
        save_context(context)

        if delivery_info["deliverable"]:
            return (
                f"✅ Yes! We deliver to pincode {pin} in **{delivery_info['district']}**, **{delivery_info['state']}**.\n"
                f"🛒 You can continue shopping with confidence!"
            )
        else:
            return (
                f"❌ Sorry, we currently do not deliver to pincode {pin}"
               f" in **{delivery_info['district']}**, **{delivery_info['state']}**"
                if delivery_info['district']
                else ''
                f" 💬 Please contact our support team for alternative options."
            )

    # 3. CHECK FOR DELIVERY-RELATED QUERY
    if "deliver" in query_lower or "available in" in query_lower or "ship to" in query_lower:
        context["expecting_pincode"] = True
        save_context(context)
        return "🚚 We deliver to most cities across India. Please share your *pincode* so I can check for you."

    # 4. CHECK CMS/FAQ EXACT & SYNONYM
    if query_lower.strip() in CMS_RESPONSES:
        return CMS_RESPONSES[query_lower.strip()]

    for phrase, key in CMS_SYNONYMS.items():
        if phrase in query_lower and key in CMS_RESPONSES:
            return CMS_RESPONSES[key]

    # 5. PRODUCT SELECTION
    if query.lower().startswith("select option") or query.strip().isdigit():
        try:
            index = int(query.strip().split()[-1]) - 1
            selected = context.get("last_product_options", [])[index]
            context["last_product"] = selected["name"]
            context["last_product_options"] = []
            save_context(context)
            return (
                f"**{selected['name']}**\n"
                f"Price: ₹{selected.get('our_price', 'N/A')}\n\n"
                f"**Features:** {selected.get('features', '')}\n\n"
                f"**Why Choose:** {selected.get('why_choose', '')}"
            )
        except:
            return "⚠️ Invalid selection. Try `select option 1` or just type the number."

    # 6. AI FALLBACK CONFIRMATION
    if extract_intent(corrected_query) == "ai_confirm" and context.get("pending_ai_query"):
        ai_response = get_fallback_response(context["pending_ai_query"])
        context["pending_ai_query"] = None
        save_context(context)
        return f"🤖 AI says:\n{ai_response}"

    # 7. PRODUCT SEARCH
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
            return format_product_list(matched)

        selected = matched[0]
        save_context(context)

    elif intent in ["our_price", "features", "why_choose", "usage"]:
        context["pending_ai_query"] = corrected_query
        save_context(context)
        return "🧠 That’s beyond my training! Want me to ask my AI cousin?"

    elif context.get("last_product") and intent != "general":
        previous = search_products_by_keywords(context["last_product"])
        if previous:
            selected = previous[0]

    if selected:
        if intent != "general":
            value = get_product_attribute(selected, intent)
            if value:
                context["pending_ai_query"] = None
                save_context(context)
                return f"**{intent.replace('_', ' ').capitalize()} of {selected['name']}**:\n{value}"
            else:
                context["pending_ai_query"] = corrected_query
                save_context(context)
                return f"Couldn't find {intent} info for **{selected['name']}**. Want me to ask AI?"

        return (
            f"**{selected['name']}**\n"
            f"Price: ₹{selected.get('our_price', 'N/A')}"
        )

    context["pending_ai_query"] = corrected_query
    save_context(context)
    return "🧠 That went over my head like a flying stethoscope. Want me to ask the AI?"
