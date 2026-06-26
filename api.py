import os
import json
from dotenv import load_dotenv

# Load environment variables from .env in project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

if os.getenv("GEMINI_API_KEY"):
    from google.generativeai import configure, GenerativeModel
    configure(api_key=os.getenv("GEMINI_API_KEY"))
    provider = "gemini"
else:
    raise RuntimeError("GEMINI_API_KEY not found in .env. Please set it to use the Gemini Vision API.")

def generate_text_from_image(image_bytes: bytes, model_name: str = "gemini-2.5-flash") -> str:
    """Generate a description from an image using the specified Gemini model."""
    if provider == "gemini":
        model = GenerativeModel(model_name)
        # Gemini expects raw bytes for the image data in the dictionary
        img_part = {
            "mime_type": "image/jpeg",
            "data": image_bytes,
        }
        response = model.generate_content([
            "Describe the image in detail.",
            img_part,
        ])
        return response.text.strip()
    else:
        raise RuntimeError("Unsupported provider configured.")

def compare_descriptions(desc1: str, desc2: str) -> dict:
    """Compare two descriptions using Gemini and calculate a coincidence score (0-100%)."""
    model = GenerativeModel("gemini-2.5-flash")
    prompt = f"""
Compare the following two image descriptions and determine how closely they match in meaning, context, and key details.
Output a JSON object ONLY, with the keys "score" (integer from 0 to 100 representing similarity/coincidence) and "reason" (a short explanation in English).

Description 1:
"{desc1}"

Description 2:
"{desc2}"

Example output:
{{"score": 85, "reason": "Both capture the red car, but Description 2 missed the mountain background."}}

Provide your response in raw JSON format. Do not use markdown blocks.
"""
    response = model.generate_content(prompt)
    content = response.text.strip()
    
    # Strip markdown code blocks if the model generated them despite instructions
    if content.startswith("```"):
        lines = content.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()
        
    try:
        data = json.loads(content)
        return {
            "score": int(data.get("score", 0)),
            "reason": data.get("reason", "No reason provided.")
        }
    except Exception as e:
        return {
            "score": 0,
            "reason": f"Failed to parse comparison response: {content}"
        }
