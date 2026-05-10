import os
from dotenv import load_dotenv

load_dotenv()


def ask_ai(prompt: str):
    provider = os.getenv("VIBE_PROVIDER", "auto").lower()

    if provider == "gemini":
        return ask_gemini(prompt)

    if provider == "groq":
        return ask_groq(prompt)

    # auto fallback
    gemini_response = ask_gemini(prompt)

    if gemini_response and not gemini_response.startswith("AI Error:"):
        return gemini_response

    groq_response = ask_groq(prompt)

    if groq_response and not groq_response.startswith("AI Error:"):
        return groq_response

    return gemini_response or groq_response


def ask_gemini(prompt: str):
    try:
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        if not api_key:
            return "AI Error: GEMINI_API_KEY is missing."

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=prompt,
        )

        return response.text

    except Exception as e:
        return f"AI Error: {e}"


def ask_groq(prompt: str):
    try:
        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            return "AI Error: GROQ_API_KEY is missing."

        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.2,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"AI Error: {e}"