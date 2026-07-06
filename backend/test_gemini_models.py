import asyncio
import os

from dotenv import load_dotenv
from google import genai

# Load env variables from .env file
load_dotenv()


async def main():
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        print("[ERROR] AI_API_KEY is not defined in your backend/.env file.")
        return

    print(f"Using API Key: {api_key[:10]}...{api_key[-5:] if len(api_key) > 10 else ''}")
    client = genai.Client(api_key=api_key)

    # 1. Test gemini-2.5-flash
    try:
        print("\n[INFO] Testing model 'gemini-2.5-flash'...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents='Respond with exactly: "Gemini 2.5 Flash is working!"',
        )
        print(f"[OK] Response: {response.text.strip()}")
    except Exception as e:
        print(f"[ERROR] gemini-2.5-flash failed: {e}")

    # 2. Test gemini-1.5-flash
    try:
        print("\n[INFO] Testing model 'gemini-1.5-flash'...")
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents='Respond with exactly: "Gemini 1.5 Flash is working!"',
        )
        print(f"[OK] Response: {response.text.strip()}")
    except Exception as e:
        print(f"[ERROR] gemini-1.5-flash failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
