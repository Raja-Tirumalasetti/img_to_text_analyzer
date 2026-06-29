import streamlit as st
import pandas as pd
import io
import os
from api import generate_text_from_image
from batchrunner import parse_ground_truth_excel, run_batch_comparison, results_to_excel

# Set Page Config
st.set_page_config(
    page_title="Image-to-Text Analyzer",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Global Custom CSS Styling
st.markdown("""
<style>
    /* Main Background & Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header styling */
    .main-title {
        font-size: 42px;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 5px;
    }
    .sub-title {
        color: #64748b;
        font-size: 16px;
        margin-bottom: 25px;
    }
    
    /* Glassmorphic Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }
    
    /* Object Badges / Tags */
    .object-badge {
        display: inline-block;
        background: rgba(99, 102, 241, 0.15);
        color: #818cf8;
        border: 1px solid rgba(99, 102, 241, 0.3);
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 12px;
        margin-right: 6px;
        margin-bottom: 6px;
        font-weight: 500;
    }
    
    /* Custom Metric Display */
    .metric-container {
        background: linear-gradient(135deg, #4f46e5 0%, #8b5cf6 50%, #ec4899 100%);
        border-radius: 16px;
        padding: 30px;
        text-align: center;
        color: white;
        box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.4);
        margin-bottom: 25px;
    }
    .metric-value {
        font-size: 72px;
        font-weight: 800;
        margin: 0;
        letter-spacing: -2px;
        line-height: 1;
    }
    .metric-label {
        font-size: 14px;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
        margin-top: 10px;
    }
    
    /* Sidebar styling */
    .sidebar-header {
        font-size: 20px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 15px;
    }
    
    /* Status indicators */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        text-align: center;
    }
    .status-connected {
        background-color: #d1fae5;
        color: #065f46;
    }
    .status-missing {
        background-color: #fee2e2;
        color: #991b1b;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">⚙️ Configuration</div>', unsafe_allow_html=True)
    
    # Key Connection Status Check
    api_key_set = os.getenv("GEMINI_API_KEY") is not None
    if api_key_set:
        st.markdown('<span class="status-badge status-connected">🟢 Gemini API Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-missing">🔴 Gemini API Key Missing</span>', unsafe_allow_html=True)
        st.warning("Please configure GEMINI_API_KEY in your .env file.")
        
    st.write("---")
    
    # Workflow Mode Selection
    st.markdown("### Evaluation Mode")
    app_mode = st.radio(
        "Choose Mode:",
        ["🖼️ Image-based Evaluation", "📊 Direct Excel Comparison"],
        index=0,
        help="Choose whether to upload & analyze raw images or upload two populated Excel sheets directly."
    )
    
    st.write("---")
    
    # Model Configurations
    st.markdown("### Model Selection")
    model1_name = st.selectbox(
        "Image Analysis Model",
        ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-3.5-flash"],
        index=0,
        help="Model used to analyze raw images in Step 1."
    )
    
    st.write("---")
    st.markdown("""
    ### About
    **Image-to-Text Studio** is a high-performance visual-analysis automation framework. 
    It parses multiple images, builds structured content schemas, and compares datasets with advanced semantic evaluators.
    """)

# --- MAIN PAGE HEADER ---
st.markdown('<div class="main-title">🖼️ Image-to-Text Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">A premium, automated visual analytics and dataset evaluation dashboard</div>', unsafe_allow_html=True)

# Initialize Session State variables
if "model1_results" not in st.session_state:
    st.session_state.model1_results = {}
if "uploaded_images" not in st.session_state:
    st.session_state.uploaded_images = []
if "ground_truth" not in st.session_state:
    st.session_state.ground_truth = {}
if "comparison_results" not in st.session_state:
    st.session_state.comparison_results = []

if "excel_model_results" not in st.session_state:
    st.session_state.excel_model_results = {}
if "excel_gt_results" not in st.session_state:
    st.session_state.excel_gt_results = {}
if "excel_comparison_results" not in st.session_state:
    st.session_state.excel_comparison_results = []


# ═══════════════════════════════════════════════════════════════════
# MODE 1: IMAGE-BASED EVALUATION
# ═══════════════════════════════════════════════════════════════════
if app_mode == "🖼️ Image-based Evaluation":
    tab1, tab2 = st.tabs([
        "📤 Step 1: Upload & Process", 
        "⚖️ Step 2: Compare & Evaluate"
    ])

    # --- TAB 1: UPLOAD & PROCESS ---
    with tab1:
        st.header("Bulk Image Upload & Analysis")
        st.write("Upload a batch of images to extract structured features: Confidence, Activity, Objects, and Summary.")

        uploaded_files = st.file_uploader(
            "Drag and drop image files here", 
            type=["png", "jpg", "jpeg"], 
            accept_multiple_files=True,
            key="file_uploader_main"
        )
        
        if uploaded_files:
            st.session_state.uploaded_images = []
            for file in uploaded_files:
                file_bytes = file.read()
                st.session_state.uploaded_images.append({
                    "name": file.name,
                    "bytes": file_bytes
                })
                
        # Gallery Preview
        if st.session_state.uploaded_images:
            st.subheader("Uploaded Gallery Preview")
            cols = st.columns(min(len(st.session_state.uploaded_images), 6))
            for idx, img in enumerate(st.session_state.uploaded_images):
                with cols[idx % 6]:
                    st.image(img["bytes"], caption=img["name"], use_container_width=True)
                    
            # Run Button
            if st.button("🚀 Analyze Images with Model 1", key="btn_run_model1"):
                st.session_state.model1_results = {}
                progress_bar = st.progress(0)
                
                for idx, img in enumerate(st.session_state.uploaded_images):
                    img_name = img["name"]
                    img_bytes = img["bytes"]
                    
                    with st.spinner(f"Analyzing {img_name}..."):
                        try:
                            res = generate_text_from_image(img_bytes, model_name=model1_name)
                            st.session_state.model1_results[img_name] = res
                        except Exception as e:
                            st.session_state.model1_results[img_name] = {
                                "confidence": "N/A",
                                "activity": f"Error: {e}",
                                "objects": "N/A",
                                "summary": "N/A"
                            }
                    progress_bar.progress((idx + 1) / len(st.session_state.uploaded_images))
                st.success("Analysis complete!")

        # Display Structured Results
        if st.session_state.model1_results:
            st.write("---")
            st.subheader("Structured Model 1 Profiles")
            
            # Display Cards for each processed image
            for name, res in st.session_state.model1_results.items():
                col_img, col_info = st.columns([1, 4])
                
                # Find the corresponding image bytes for thumbnail
                img_bytes = next((x["bytes"] for x in st.session_state.uploaded_images if x["name"] == name), None)
                
                with col_img:
                    if img_bytes:
                        st.image(img_bytes, use_container_width=True)
                    else:
                        st.write("🖼️")
                        
                with col_info:
                    st.markdown(f"""
                    <div class="glass-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <span style="font-size: 18px; font-weight: 700; color: #1e293b;">{name}</span>
                            <span style="background: #e0e7ff; color: #4338ca; padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: 600;">
                                Confidence: {res.get('confidence', 'N/A')}%
                            </span>
                        </div>
                        <div style="margin-bottom: 8px;"><strong>Activity:</strong> {res.get('activity', 'N/A')}</div>
                        <div style="margin-bottom: 8px;"><strong>Summary:</strong> {res.get('summary', 'N/A')}</div>
                        <div style="margin-top: 12px;">
                            {''.join([f'<span class="object-badge">{obj.strip()}</span>' for obj in res.get('objects', 'N/A').split(',') if obj.strip()])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Overview Table
            st.subheader("Model 1 Grid Overview")
            df_model1 = pd.DataFrame([
                {
                    "Image Name": name,
                    "Confidence": res.get("confidence", "N/A"),
                    "Activity": res.get("activity", "N/A"),
                    "Objects": res.get("objects", "N/A"),
                    "Summary": res.get("summary", "N/A")
                }
                for name, res in st.session_state.model1_results.items()
            ])
            st.dataframe(df_model1, use_container_width=True)
            
            # Download Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_model1.to_excel(writer, index=False, sheet_name='Model 1 Results')
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 Download Model 1 Excel Sheet",
                data=excel_data,
                file_name="model1_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # --- TAB 2: COMPARE & EVALUATE ---
    with tab2:
        st.header("Semantic Coincidence Audit")
        st.write("Upload a Ground Truth Excel sheet, then run the LLM evaluator to compare Model 1 output against it.")

        if not st.session_state.model1_results:
            st.warning("Complete Step 1 first — analyze your images before running a comparison.")
        else:
            # --- Ground Truth Upload Section ---
            st.subheader("📂 Upload Ground Truth Data")
            uploaded_gt_file = st.file_uploader(
                "Upload Ground Truth Excel (must include image names matching Step 1)",
                type=["xlsx", "xls"],
                key="gt_uploader_step2"
            )

            if uploaded_gt_file:
                try:
                    gt_bytes = uploaded_gt_file.read()
                    st.session_state.ground_truth = parse_ground_truth_excel(gt_bytes)
                    st.success(f"Ground Truth loaded: {len(st.session_state.ground_truth)} entries parsed.")
                except Exception as e:
                    st.error(f"Error parsing Ground Truth Excel: {e}")

            # Show loaded ground truth summary
            if st.session_state.ground_truth:
                with st.expander("📋 Preview Ground Truth Data", expanded=False):
                    df_gt_preview = pd.DataFrame([
                        {
                            "Image Name": name,
                            "Confidence": res.get("confidence", "N/A"),
                            "Activity": res.get("activity", "N/A"),
                            "Objects": res.get("objects", "N/A"),
                            "Summary": res.get("summary", "N/A")
                        }
                        for name, res in st.session_state.ground_truth.items()
                    ])
                    st.dataframe(df_gt_preview, use_container_width=True)

            st.write("---")

            # --- Run Comparison Section ---
            st.subheader("⚖️ Run LLM Comparison")

            if not st.session_state.ground_truth:
                st.info("Upload a Ground Truth Excel file above to enable the comparison.")
            else:
                # Model Selection for Evaluation/Comparison
                comparison_model_name = st.selectbox(
                    "Select Model for Semantic Comparison",
                    ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-3.5-flash"],
                    index=0,
                    help="Model used to perform the semantic evaluation/coincidence audit.",
                    key="img_comp_model"
                )

                if st.button("🚀 Run Semantic Coincidence Audit", key="btn_run_comparison"):
                    progress_bar_comp = st.progress(0)

                    def update_progress(current, total):
                        progress_bar_comp.progress(current / total)

                    with st.spinner("Running batch comparison via LLM evaluator..."):
                        st.session_state.comparison_results = run_batch_comparison(
                            st.session_state.model1_results,
                            st.session_state.ground_truth,
                            model_name=comparison_model_name,
                            progress_callback=update_progress
                        )
                    st.success("Semantic audit complete!")

        # ── Display Comparison Dashboard ──
        if st.session_state.comparison_results:
            df_comp = pd.DataFrame(st.session_state.comparison_results)
            avg_score = df_comp["Coincidence Score (%)"].mean()
            
            # Display Metric Card
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">{avg_score:.1f}%</div>
                <div class="metric-label">Average Coincidence Value</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.subheader("Side-by-Side Verification Cards")
            for item in st.session_state.comparison_results:
                name = item["Image Name"]
                score = item["Coincidence Score (%)"]
                score_color = "#10b981" if score >= 80 else ("#f59e0b" if score >= 50 else "#ef4444")
                
                # Find corresponding image thumbnail bytes
                img_bytes = next((x["bytes"] for x in st.session_state.uploaded_images if x["name"] == name), None)
                
                col_th, col_card = st.columns([1, 4])
                with col_th:
                    if img_bytes:
                        st.image(img_bytes, use_container_width=True)
                    else:
                        st.write("🖼️")
                        
                with col_card:
                    st.markdown(f"""
                    <div class="glass-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 1px solid rgba(0, 0, 0, 0.08); padding-bottom: 10px;">
                            <span style="font-size: 18px; font-weight: 700; color: #1e293b;">{name}</span>
                            <span style="background: {score_color}15; color: {score_color}; border: 1px solid {score_color}30; padding: 4px 12px; border-radius: 8px; font-size: 14px; font-weight: 700;">
                                Match: {score}%
                            </span>
                        </div>
                        
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                            <div style="background: rgba(0, 0, 0, 0.02); padding: 12px; border-radius: 8px; border-left: 3px solid #6366f1;">
                                <div style="font-size: 12px; font-weight: 600; color: #6366f1; text-transform: uppercase;">Model 1 Output</div>
                                <div style="margin-top: 5px; font-size: 14px;"><strong>Confidence:</strong> {item.get("Model 1 Confidence", "N/A")}%</div>
                                <div style="margin-top: 3px; font-size: 14px;"><strong>Activity:</strong> {item["Model 1 Activity"]}</div>
                                <div style="margin-top: 3px; font-size: 14px;"><strong>Summary:</strong> {item["Model 1 Summary"]}</div>
                                <div style="margin-top: 5px;">
                                    {''.join([f'<span class="object-badge" style="background: rgba(99,102,241,0.08);">{obj.strip()}</span>' for obj in item["Model 1 Objects"].split(',') if obj.strip()])}
                                </div>
                            </div>
                            
                            <div style="background: rgba(0, 0, 0, 0.02); padding: 12px; border-radius: 8px; border-left: 3px solid #14b8a6;">
                                <div style="font-size: 12px; font-weight: 600; color: #14b8a6; text-transform: uppercase;">Ground Truth</div>
                                <div style="margin-top: 5px; font-size: 14px;"><strong>Confidence:</strong> {item.get("Ground Truth Confidence", "N/A")}%</div>
                                <div style="margin-top: 3px; font-size: 14px;"><strong>Activity:</strong> {item["Ground Truth Activity"]}</div>
                                <div style="margin-top: 3px; font-size: 14px;"><strong>Summary:</strong> {item["Ground Truth Summary"]}</div>
                                <div style="margin-top: 5px;">
                                    {''.join([f'<span class="object-badge" style="background: rgba(20,184,166,0.08); color: #0d9488; border-color: rgba(20,184,166,0.2);">{obj.strip()}</span>' for obj in item["Ground Truth Objects"].split(',') if obj.strip()])}
                                </div>
                            </div>
                        </div>
                        
                        <div style="background: rgba(0,0,0,0.01); padding: 10px; border-radius: 6px; font-size: 13px; color: #4b5563;">
                            <strong>Audit Verdict:</strong> {item["Reason"]}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            st.subheader("Detailed Audit Grid")
            def color_score(val):
                if val >= 80:
                    color = '#D1FAE5'
                elif val >= 50:
                    color = '#FEF3C7'
                else:
                    color = '#FEE2E2'
                return f'background-color: {color}'

            styled_df = df_comp.style.map(color_score, subset=["Coincidence Score (%)"])
            st.dataframe(styled_df, use_container_width=True)
            
            # Download Comparison Excel report
            excel_comp_data = results_to_excel(st.session_state.comparison_results)
            st.download_button(
                label="📥 Download Comparison Audit Excel Report",
                data=excel_comp_data,
                file_name="comparison_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# ═══════════════════════════════════════════════════════════════════
# MODE 2: DIRECT EXCEL-TO-EXCEL COMPARISON
# ═══════════════════════════════════════════════════════════════════
else:
    st.header("Excel-to-Excel Semantic Comparison")
    st.write("Upload two completed Excel files directly (Model Output and Ground Truth) to execute semantic auditing and download the comparison report.")

    col_excel1, col_excel2 = st.columns(2)

    with col_excel1:
        st.subheader("📂 Upload Model 1 Output Excel")
        uploaded_model_file = st.file_uploader(
            "Upload Model 1 Excel Results",
            type=["xlsx", "xls"],
            key="excel_model_file_uploader"
        )
        if uploaded_model_file:
            try:
                model_bytes = uploaded_model_file.read()
                st.session_state.excel_model_results = parse_ground_truth_excel(model_bytes)
                st.success(f"Model Output Excel loaded: {len(st.session_state.excel_model_results)} records parsed.")
            except Exception as e:
                st.error(f"Error parsing Model Output Excel: {e}")

    with col_excel2:
        st.subheader("📂 Upload Ground Truth Excel")
        uploaded_gt_file = st.file_uploader(
            "Upload Ground Truth Benchmark Excel",
            type=["xlsx", "xls"],
            key="excel_gt_file_uploader"
        )
        if uploaded_gt_file:
            try:
                gt_bytes = uploaded_gt_file.read()
                st.session_state.excel_gt_results = parse_ground_truth_excel(gt_bytes)
                st.success(f"Ground Truth Excel loaded: {len(st.session_state.excel_gt_results)} records parsed.")
            except Exception as e:
                st.error(f"Error parsing Ground Truth Excel: {e}")

    # Display Previews if uploaded
    if st.session_state.excel_model_results or st.session_state.excel_gt_results:
        col_preview1, col_preview2 = st.columns(2)
        with col_preview1:
            if st.session_state.excel_model_results:
                with st.expander("🔍 Preview Model Output Excel Data"):
                    df_m_preview = pd.DataFrame([
                        {
                            "Image Name": name,
                            "Confidence": res.get("confidence", "N/A"),
                            "Activity": res.get("activity", "N/A"),
                            "Objects": res.get("objects", "N/A"),
                            "Summary": res.get("summary", "N/A")
                        }
                        for name, res in st.session_state.excel_model_results.items()
                    ])
                    st.dataframe(df_m_preview, use_container_width=True)
        with col_preview2:
            if st.session_state.excel_gt_results:
                with st.expander("🔍 Preview Ground Truth Excel Data"):
                    df_g_preview = pd.DataFrame([
                        {
                            "Image Name": name,
                            "Confidence": res.get("confidence", "N/A"),
                            "Activity": res.get("activity", "N/A"),
                            "Objects": res.get("objects", "N/A"),
                            "Summary": res.get("summary", "N/A")
                        }
                        for name, res in st.session_state.excel_gt_results.items()
                    ])
                    st.dataframe(df_g_preview, use_container_width=True)

    # --- Run Excel Comparison ---
    if st.session_state.excel_model_results and st.session_state.excel_gt_results:
        st.write("---")
        st.subheader("⚖️ Run Direct Sheet Comparison")

        excel_comp_model = st.selectbox(
            "Select Model for Semantic Comparison",
            ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-3.5-flash"],
            index=0,
            help="Model used to perform the semantic evaluation/coincidence audit.",
            key="direct_excel_comp_model"
        )

        if st.button("🚀 Run Semantic Coincidence Audit", key="btn_run_excel_comparison"):
            progress_bar_excel = st.progress(0)

            def update_progress_excel(current, total):
                progress_bar_excel.progress(current / total)

            with st.spinner("Running batch comparison on Excel data via LLM evaluator..."):
                st.session_state.excel_comparison_results = run_batch_comparison(
                    st.session_state.excel_model_results,
                    st.session_state.excel_gt_results,
                    model_name=excel_comp_model,
                    progress_callback=update_progress_excel
                )
            st.success("Excel audit complete!")

    # ── Display Excel Comparison Dashboard ──
    if st.session_state.excel_comparison_results:
        df_comp = pd.DataFrame(st.session_state.excel_comparison_results)
        avg_score = df_comp["Coincidence Score (%)"].mean()
        
        # Display Metric Card
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{avg_score:.1f}%</div>
            <div class="metric-label">Average Coincidence Value</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("Side-by-Side Verification Cards")
        for item in st.session_state.excel_comparison_results:
            name = item["Image Name"]
            score = item["Coincidence Score (%)"]
            score_color = "#10b981" if score >= 80 else ("#f59e0b" if score >= 50 else "#ef4444")
            
            st.markdown(f"""
            <div class="glass-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 1px solid rgba(0, 0, 0, 0.08); padding-bottom: 10px;">
                    <span style="font-size: 18px; font-weight: 700; color: #1e293b;">{name}</span>
                    <span style="background: {score_color}15; color: {score_color}; border: 1px solid {score_color}30; padding: 4px 12px; border-radius: 8px; font-size: 14px; font-weight: 700;">
                        Match: {score}%
                    </span>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                    <div style="background: rgba(0, 0, 0, 0.02); padding: 12px; border-radius: 8px; border-left: 3px solid #6366f1;">
                        <div style="font-size: 12px; font-weight: 600; color: #6366f1; text-transform: uppercase;">Model Output</div>
                        <div style="margin-top: 5px; font-size: 14px;"><strong>Confidence:</strong> {item.get("Model 1 Confidence", "N/A")}%</div>
                        <div style="margin-top: 3px; font-size: 14px;"><strong>Activity:</strong> {item["Model 1 Activity"]}</div>
                        <div style="margin-top: 3px; font-size: 14px;"><strong>Summary:</strong> {item["Model 1 Summary"]}</div>
                        <div style="margin-top: 5px;">
                            {''.join([f'<span class="object-badge" style="background: rgba(99,102,241,0.08);">{obj.strip()}</span>' for obj in item["Model 1 Objects"].split(',') if obj.strip()])}
                        </div>
                    </div>
                    
                    <div style="background: rgba(0, 0, 0, 0.02); padding: 12px; border-radius: 8px; border-left: 3px solid #14b8a6;">
                        <div style="font-size: 12px; font-weight: 600; color: #14b8a6; text-transform: uppercase;">Ground Truth</div>
                        <div style="margin-top: 5px; font-size: 14px;"><strong>Confidence:</strong> {item.get("Ground Truth Confidence", "N/A")}%</div>
                        <div style="margin-top: 3px; font-size: 14px;"><strong>Activity:</strong> {item["Ground Truth Activity"]}</div>
                        <div style="margin-top: 3px; font-size: 14px;"><strong>Summary:</strong> {item["Ground Truth Summary"]}</div>
                        <div style="margin-top: 5px;">
                            {''.join([f'<span class="object-badge" style="background: rgba(20,184,166,0.08); color: #0d9488; border-color: rgba(20,184,166,0.2);">{obj.strip()}</span>' for obj in item["Ground Truth Objects"].split(',') if obj.strip()])}
                        </div>
                    </div>
                </div>
                
                <div style="background: rgba(0,0,0,0.01); padding: 10px; border-radius: 6px; font-size: 13px; color: #4b5563;">
                    <strong>Audit Verdict:</strong> {item["Reason"]}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.subheader("Detailed Audit Grid")
        def color_score(val):
            if val >= 80:
                color = '#D1FAE5'
            elif val >= 50:
                color = '#FEF3C7'
            else:
                color = '#FEE2E2'
            return f'background-color: {color}'

        styled_df = df_comp.style.map(color_score, subset=["Coincidence Score (%)"])
        st.dataframe(styled_df, use_container_width=True)
        
        # Download Comparison Excel report
        excel_comp_data = results_to_excel(st.session_state.excel_comparison_results)
        st.download_button(
            label="📥 Download Comparison Audit Excel Report",
            data=excel_comp_data,
            file_name="comparison_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
