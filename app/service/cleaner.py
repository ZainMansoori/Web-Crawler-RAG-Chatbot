import json
import os
from google import genai
from google.genai import errors
from loguru import logger

PROMPT = """
Extract ONLY the main readable content from this HTML.
Do NOT summarize or paraphrase.
Remove navigation, ads, scripts.
Return JSON ONLY with:
- title
- paragraphs (ordered list of strings)
HTML:
"""


def _load_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
    raise ValueError("Model did not return valid JSON")


def clean_html(html: str) -> dict:
    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY env var is required")
    client = genai.Client()
    model_name = os.getenv("GEMINI_MODEL")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=PROMPT + html,
        )
    except Exception as e:
        logger.error(f"Error cleaning HTML: {e}")
        raise e
    text = response.text or ""
    if not text and getattr(response, "candidates", None):
        parts = response.candidates[0].content.parts
        text = "".join(part.text for part in parts if getattr(part, "text", None))
    return _load_json(text)
