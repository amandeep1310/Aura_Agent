import requests

BASE_URL = "http://localhost:8000"


def generate_content(topic):

    try:

        response = requests.post(

            f"{BASE_URL}/generate",

            json={
                "topic": topic
            }
        )

        return response.json()

    except Exception as e:

        return {
            "error": str(e)
        }


def revise_content(payload):

    ...