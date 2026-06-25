import requests

BASE_URL = "http://localhost:8000"


def generate_content(topic, objective):

    try:

        response = requests.post(

    f"{BASE_URL}/campaigns/create",

    json={
        "topic": topic,
        "objective": objective
    }
)

        if response.status_code not in [200, 202]:
            return {
                "error": response.text
            }

        return response.json()

    except Exception as e:

        return {
            "error": str(e)
        }


def revise_content(payload):
    pass

def get_campaign(campaign_id):

    try:

        response = requests.get(
            f"{BASE_URL}/campaigns/{campaign_id}"
        )

        return response.json()

    except Exception as e:

        return {
            "error": str(e)
        }