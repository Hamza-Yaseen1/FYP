import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
resp = requests.get(
    'https://api.groq.com/openai/v1/models',
    headers={'Authorization': f'Bearer {api_key}'}
)

if resp.status_code == 200:
    models = resp.json()['data']
    print(f"Available models ({len(models)}):")
    for m in models:
        print(f"  - {m['id']}")
else:
    print(f"Error: {resp.status_code} - {resp.text}")
