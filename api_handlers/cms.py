import requests

def get_page_content(slug):
    try:
        response = requests.get("http://aarogyaabharat.com/api/page-content", params={"slug": slug})
        return response.json()
    except Exception as e:
        return {"error": str(e)}
