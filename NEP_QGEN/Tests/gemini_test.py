import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def test_gemini_api():
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        print(f"API Key found: {api_key[:10]}..." if api_key else "No API key found")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        response = model.generate_content("Say 'Hello, API is working!'")
        print("✅ Success:", response.text)
        
    except Exception as e:
        print("❌ Error:", str(e))

if __name__ == "__main__":
    test_gemini_api()
