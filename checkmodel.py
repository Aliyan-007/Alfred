import os
from dotenv import load_dotenv
from groq import Groq

print("Starting model check...")

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("ERROR: GROQ_API_KEY was not found.")
    raise SystemExit(1)

print("API key found.")
print("Connecting to Groq...")

client = Groq(api_key=api_key)

try:
    models = client.models.list()

    print("\nModels available to your API key:")
    print("=" * 50)

    if not models.data:
        print("NO MODELS WERE RETURNED.")

    for model in models.data:
        print(model.id)

    print("=" * 50)
    print(f"Total models: {len(models.data)}")

except Exception as error:
    print("\nERROR:")
    print(error)