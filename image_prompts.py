"""
Prompt templates used by api.py for image analysis and comparison.
"""

# Prompt for extracting structured fields from an image
IMAGE_ANALYSIS_PROMPT = """
Analyze the following image and extract the requested fields.
Return a JSON object ONLY with the following exact keys:
1. "confidence": An integer from 0 to 100 representing how confident you are in your analysis. Do NOT include a percent sign, just the number (e.g. 92).
2. "activity": What is happening/the main action in the image. Keep it brief (one sentence max).
3. "objects": A comma-separated list of key objects visible in the image.
4. "summary": A brief, one-sentence summary of the overall scene.

Do not write any paragraphs or extra conversational text (no theory). Output ONLY raw JSON.
"""

# Prompt template for comparing two structured image analyses
# Use .format(m1_activity=..., m1_objects=..., m1_summary=..., gt_activity=..., gt_objects=..., gt_summary=...)
COMPARISON_PROMPT_TEMPLATE = """
You are an expert image-analysis evaluator. Compare the following two structured image analyses and determine how closely they match in meaning, context, key details, objects, and activity.

Output a JSON object ONLY with EXACTLY these keys:
- "score": An integer from 0 to 100 representing the similarity/coincidence percentage. Be precise and objective.
- "reason": A short explanation (1-2 sentences) of why you assigned this score.

Analysis 1 (Model Output):
- Activity: {m1_activity}
- Objects: {m1_objects}
- Summary: {m1_summary}

Analysis 2 (Ground Truth):
- Activity: {gt_activity}
- Objects: {gt_objects}
- Summary: {gt_summary}

Scoring guidelines:
- 90-100: Nearly identical meaning, same objects and activity captured.
- 70-89: Same general scene, minor detail differences.
- 50-69: Partially overlapping, some key details missed.
- 0-49: Significantly different descriptions.

Provide your response in raw JSON format. Do not use markdown blocks.
"""

