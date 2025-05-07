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
    Normalize input query by:
    - Lowercasing
    - Removing filler words
    - Singularizing plural nouns
    """
    query = query.lower()
    query = re.sub(r'\bof\b', '', query)  # remove "of"
    query = re.sub(r'\s+', ' ', query).strip()  # normalize spaces

    words = query.split()
    singular_words = [p.singular_noun(w) if p.singular_noun(w) else w for w in words]
    return " ".join(singular_words)

def fuzzy_match_score(product, query):
    """
    Returns the best fuzzy score among name, title, and partial description.
    """
    name = product.get("name", "")
    title = product.get("title", "")
    description = product.get("description", "")

    name_score = fuzz.token_set_ratio(query, name)
    title_score = fuzz.token_set_ratio(query, title)
    desc_score = fuzz.partial_ratio(query, description)

    return max(name_score, title_score, desc_score)

def search_products_by_keywords(query, threshold=70, top_n=5):
    query = normalize_query(query)
    query_words = set(query.split())
    products = fetch_products()
    strong_matches = []

    for product in products:
        name = product.get("name", "").lower()
        title = product.get("title", "").lower()
        name_title = f"{name} {title}"

        score = fuzzy_match_score(product, query)

        # Only allow fuzzy match if it's in name/title
        valid_fuzzy = score >= threshold and any(word in name_title for word in query_words)

        # All query words match name/title directly
        keyword_exact = all(word in name_title for word in query_words)

        if valid_fuzzy or keyword_exact:
            strong_matches.append((score, product))

    strong_matches.sort(key=lambda x: x[0], reverse=True)

    seen_titles = set()
    final = []
    for score, prod in strong_matches:
        title = prod.get("title", "")
        if title not in seen_titles:
            final.append(prod)
            seen_titles.add(title)
        if len(final) >= top_n:
            break

    return final
