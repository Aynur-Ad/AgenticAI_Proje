import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("GOOGLE_API_KEY bulunamadi")

genai.configure(api_key=api_key)

def get_llm():
    model = genai.GenerativeModel("gemini-2.5-flash-lite")

    def llm_call(prompt: str) -> str:
        response = model.generate_content(prompt)
        return response.text

    return llm_call