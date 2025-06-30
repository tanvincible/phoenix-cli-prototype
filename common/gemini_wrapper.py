import os
import requests
import json

class GeminiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    def generate_content(self, prompt: str) -> str:
        headers = {
            'Content-Type': 'application/json',
        }
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        try:
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                headers=headers,
                data=json.dumps(data)
            )
            response.raise_for_status() # Raise an exception for HTTP errors
            response_json = response.json()
            # Assuming the structure for text content
            if "candidates" in response_json and response_json["candidates"]:
                for part in response_json["candidates"][0]["content"]["parts"]:
                    if "text" in part:
                        return part["text"].strip()
            return "No content generated."
        except requests.exceptions.RequestException as e:
            print(f"Error calling Gemini API: {e}")
            return f"Error: {e}"
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            print(f"Raw response: {response.text}")
            return f"Error decoding JSON: {e}"

# Example usage (for testing):
if __name__ == "__main__":
    # Ensure you have GEMINI_API_KEY set as an environment variable
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY environment variable not set.")
    else:
        gemini_client = GeminiClient(GEMINI_API_KEY)
        prompt = "Explain the concept of multi-agent systems in one sentence."
        response_text = gemini_client.generate_content(prompt)
        print(f"Gemini Response: {response_text}")