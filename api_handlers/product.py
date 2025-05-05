import requests
from fuzzywuzzy import fuzz
import re
import inflect

p = inflect.engine()

def fetch_products():
    try:
        response = requests.get("https://aarogyaabharat.com/api/product-info")
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'products' in data:
            return data['products']
        else:
            print("Unexpected response format:", data)
            return []
    except Exception as e:
        print("Error fetching products:", e)
        return []

def normalize_query(query):
    """
    Normalize input to handle plural → singular and remove filler words.
    """
    query = query.lower()
    query = re.sub(r'\bof\b', '', query)  # remove "of"
    query = re.sub(r'\s+', ' ', query).strip()  # remove extra spaces

    # Singularize each word (e.g., diapers → diaper)
    words = query.split()
    singular_words = [p.singular_noun(w) if p.singular_noun(w) else w for w in words]
    return " ".join(singular_words)

def fuzzy_match_score(product, query):
    name = product.get("name", "")
    title = product.get("title", "")
    description = product.get("description", "")

    name_score = fuzz.token_set_ratio(query, name)
    title_score = fuzz.token_set_ratio(query, title)
    desc_score = fuzz.partial_ratio(query, description)

    return max(name_score, title_score, desc_score)

def search_products_by_keywords(query, threshold=60, score_margin=10, top_n=5):
    query = normalize_query(query)
    products = fetch_products()
    fuzzy_scored = []
    keyword_hits = []

    query_words = set(query.split())

    for product in products:
        score = fuzzy_match_score(product, query)

        # Combine fuzzy score + keyword inclusion
        text_blob = (
            f"{product.get('name', '')} {product.get('title', '')} "
            f"{product.get('description', '')} {product.get('features', '')}"
        ).lower()

        keyword_match = any(word in text_blob for word in query_words)

        # Add if fuzzy score is high OR keyword present
        if score >= threshold or keyword_match:
            fuzzy_scored.append((score, product))

    if not fuzzy_scored:
        return []

    # Sort by score descending
    fuzzy_scored.sort(key=lambda x: x[0], reverse=True)

    # Return top N matching products (de-duped by title)
    seen = set()
    result = []
    for score, prod in fuzzy_scored:
        title = prod.get("title", "")
        if title not in seen:
            result.append(prod)
            seen.add(title)
        if len(result) >= top_n:
            break

    return result
