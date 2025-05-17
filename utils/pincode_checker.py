import requests

def check_pincode_serviceability(pincode):
    """
    Checks if the pincode is serviceable and returns delivery status along with district/state.
    """
    result = {
        "deliverable": False,
        "district": None,
        "state": None
    }

    try:
        response = requests.get(
            "https://aarogyaabharat.com/api/check-pincode",
            params={"pincode": pincode}
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                for entry in data:
                    if str(entry.get("pin")) == str(pincode):
                        result["district"] = entry.get("district")
                        result["state"] = entry.get("state")
                        result["deliverable"] = entry.get("delivery", "").lower() == "delivery"
                        return result
    except Exception as e:
        print("Delivery check error:", e)

    return result
