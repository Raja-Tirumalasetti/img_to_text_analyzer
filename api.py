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

def generate_text_from_image(image_bytes: bytes, model_name: str = "gemini-2.5-flash") -> dict:
    """Generate structured description details from an image."""
    if provider == "gemini":
        model = GenerativeModel(model_name)
        # Gemini expects raw bytes for the image data in the dictionary
        img_part = {
            "mime_type": "image/jpeg",
            "data": image_bytes,
        }
        
        prompt = """
Analyze the following image and extract the requested fields. 
Return a JSON object ONLY with the following exact keys:
1. "confidence": Estimate your confidence level as a percentage (e.g. "95%").
2. "activity": What is happening/the main action in the image. Keep it brief.
3. "objects": A comma-separated list of key objects visible in the image.
4. "summary": A brief, one-sentence summary of the overall scene.

Do not write any paragraphs or extra conversational text (no theory). Output ONLY raw JSON.
"""
        response = model.generate_content([prompt, img_part])
        content = response.text.strip()
        
        # Strip markdown code blocks if present
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
                "confidence": str(data.get("confidence", "N/A")),
                "activity": str(data.get("activity", "N/A")),
                "objects": str(data.get("objects", "N/A")),
                "summary": str(data.get("summary", "N/A"))
            }
        except Exception as e:
            return {
                "confidence": "N/A",
                "activity": "Error parsing response.",
                "objects": "N/A",
                "summary": content
            }
    else:
        raise RuntimeError("Unsupported provider configured.")

def compare_descriptions(desc1_dict: dict, desc2_dict: dict) -> dict:
    """Compare two structured description dicts and calculate a coincidence score (0-100%)."""
    model = GenerativeModel("gemini-2.5-flash")
    
    prompt = f"""
Compare the following two structured image analyses and determine how closely they match in meaning, context, key details, objects, and activity.
Output a JSON object ONLY, with the keys "score" (integer from 0 to 100 representing similarity/coincidence) and "reason" (a short explanation in English).

Analysis 1 (Model 1):
- Activity: {desc1_dict.get('activity')}
- Objects: {desc1_dict.get('objects')}
- Summary: {desc1_dict.get('summary')}

Analysis 2 (Ground Truth):
- Activity: {desc2_dict.get('activity')}
- Objects: {desc2_dict.get('objects')}
- Summary: {desc2_dict.get('summary')}

Provide your response in raw JSON format. Do not use markdown blocks.
"""
    response = model.generate_content(prompt)
    content = response.text.strip()
    
    # Strip markdown code blocks if the model generated them
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
