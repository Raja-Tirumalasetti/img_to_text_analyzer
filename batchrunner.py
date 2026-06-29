"""
batchrunner.py — Batch comparison engine for Model 1 output vs Ground Truth data.
Handles Excel parsing, LLM-based semantic comparison, and result aggregation.
"""

import pandas as pd
import io
from api import compare_descriptions


def parse_ground_truth_excel(file_bytes) -> dict:
    """Parse a ground truth Excel file and return a dict keyed by image name.

    Attempts to auto-detect columns for:
      Image Name, Activity, Objects, Summary, Confidence

    Returns:
        dict[str, dict]: {image_name: {confidence, activity, objects, summary}}
    """
    df = pd.read_excel(io.BytesIO(file_bytes) if isinstance(file_bytes, bytes) else file_bytes)
    cols = {c.lower().strip(): c for c in df.columns}

    # Auto-detect image name column
    img_col = next(
        (cols[p] for p in ["image name", "image", "file name", "filename", "name"] if p in cols),
        df.columns[0],
    )
    act_col = next((cols[p] for p in ["activity", "action"] if p in cols), None)
    obj_col = next((cols[p] for p in ["objects", "key objects", "tags"] if p in cols), None)
    sum_col = next(
        (cols[p] for p in ["summary", "description", "desc", "ground truth description", "ground truth"] if p in cols),
        None,
    )
    conf_col = next((cols[p] for p in ["confidence", "conf"] if p in cols), None)

    ground_truth = {}
    for _, row in df.iterrows():
        name = str(row[img_col]).strip()
        activity = str(row[act_col]).strip() if act_col else "N/A"
        objects = str(row[obj_col]).strip() if obj_col else "N/A"
        confidence = str(row[conf_col]).strip() if conf_col else "N/A"

        if sum_col:
            summary = str(row[sum_col]).strip()
        elif len(df.columns) > 1:
            non_img = [c for c in df.columns if c != img_col]
            summary = str(row[non_img[0]]).strip()
        else:
            summary = "N/A"

        ground_truth[name] = {
            "confidence": confidence,
            "activity": activity,
            "objects": objects,
            "summary": summary,
        }
    return ground_truth


def run_batch_comparison(model1_results: dict, ground_truth: dict, model_name: str = "gemini-2.5-flash", progress_callback=None) -> list:
    """Compare Model 1 results against Ground Truth using the LLM evaluator.

    Args:
        model1_results: dict[str, dict] — keyed by image name, value is structured dict.
        ground_truth:   dict[str, dict] — keyed by image name, value is structured dict.
        model_name:     str — Gemini model to use for comparison evaluation.
        progress_callback: Optional callable(current_index, total) for UI progress updates.

    Returns:
        list[dict]: One row per image with Model 1 fields, Ground Truth fields,
                    Coincidence Score (%), and Reason.
    """
    comparison_results = []
    img_names = list(model1_results.keys())
    total = len(img_names)

    for idx, name in enumerate(img_names):
        desc1 = model1_results.get(name, {})
        desc2 = ground_truth.get(name, {})

        # Standardize to dict if string
        if not isinstance(desc1, dict):
            desc1 = {"confidence": "N/A", "activity": "N/A", "objects": "N/A", "summary": desc1}
        if not isinstance(desc2, dict):
            desc2 = {"confidence": "N/A", "activity": "N/A", "objects": "N/A", "summary": desc2}

        try:
            eval_res = compare_descriptions(desc1, desc2, model_name=model_name)
            comparison_results.append({
                "Image Name": name,
                "Model 1 Confidence": desc1.get("confidence", "N/A"),
                "Model 1 Activity": desc1.get("activity", "N/A"),
                "Model 1 Objects": desc1.get("objects", "N/A"),
                "Model 1 Summary": desc1.get("summary", "N/A"),
                "Ground Truth Confidence": desc2.get("confidence", "N/A"),
                "Ground Truth Activity": desc2.get("activity", "N/A"),
                "Ground Truth Objects": desc2.get("objects", "N/A"),
                "Ground Truth Summary": desc2.get("summary", "N/A"),
                "Coincidence Score (%)": eval_res.get("score", 0),
                "Reason": eval_res.get("reason", "N/A"),
            })
        except Exception as e:
            comparison_results.append({
                "Image Name": name,
                "Model 1 Confidence": desc1.get("confidence", "N/A"),
                "Model 1 Activity": desc1.get("activity", "N/A"),
                "Model 1 Objects": desc1.get("objects", "N/A"),
                "Model 1 Summary": desc1.get("summary", "N/A"),
                "Ground Truth Confidence": desc2.get("confidence", "N/A"),
                "Ground Truth Activity": desc2.get("activity", "N/A"),
                "Ground Truth Objects": desc2.get("objects", "N/A"),
                "Ground Truth Summary": desc2.get("summary", "N/A"),
                "Coincidence Score (%)": 0,
                "Reason": f"Audit Error: {e}",
            })

        if progress_callback:
            progress_callback(idx + 1, total)

    return comparison_results


def results_to_excel(comparison_results: list) -> bytes:
    """Convert comparison results list to an in-memory Excel file (bytes)."""
    df = pd.DataFrame(comparison_results)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Comparison Results")
    return output.getvalue()
