import os
import json
from dotenv import load_dotenv
from image_prompts import IMAGE_ANALYSIS_PROMPT, COMPARISON_PROMPT_TEMPLATE

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
        
        prompt = IMAGE_ANALYSIS_PROMPT
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

def compare_descriptions(desc1_dict: dict, desc2_dict: dict, model_name: str = "gemini-2.5-flash") -> dict:
    """Compare two structured description dicts and calculate a coincidence score (0-100%)."""
    model = GenerativeModel(model_name)
    
    prompt = COMPARISON_PROMPT_TEMPLATE.format(
        m1_activity=desc1_dict.get('activity'),
        m1_objects=desc1_dict.get('objects'),
        m1_summary=desc1_dict.get('summary'),
        gt_activity=desc2_dict.get('activity'),
        gt_objects=desc2_dict.get('objects'),
        gt_summary=desc2_dict.get('summary')
    )
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
