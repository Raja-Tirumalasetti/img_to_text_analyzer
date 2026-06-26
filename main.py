import streamlit as st
import pandas as pd
import io
import os
from api import generate_text_from_image, compare_descriptions

# Set Page Config
st.set_page_config(
    page_title="Image-to-Text Studio",
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
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
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
    
    # Model Configurations
    st.markdown("### Model Choices")
    model1_name = st.selectbox(
        "Model 1 (Main Describer)",
        ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-3.5-flash"],
        index=0,
        help="Model used to analyze images in Step 1."
    )
    
    model2_name = st.selectbox(
        "Model 2 (Ground Truth Simulator)",
        ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-3.5-flash"],
        index=0,
        help="Model used to generate ground truth if you don't upload a file in Step 2."
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

# Initialize Session State
if "model1_results" not in st.session_state:
    st.session_state.model1_results = {}
if "uploaded_images" not in st.session_state:
    st.session_state.uploaded_images = []
if "ground_truth" not in st.session_state:
    st.session_state.ground_truth = {}
if "comparison_results" not in st.session_state:
    st.session_state.comparison_results = []

# Core Steps Tabs
tab1, tab2, tab3 = st.tabs([
    "📤 Step 1: Upload & Process", 
    "🎯 Step 2: Establish Ground Truth", 
    "⚖️ Step 3: Compare & Evaluate"
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
                            Confidence: {res.get('confidence', 'N/A')}
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


# --- TAB 2: ESTABLISH GROUND TRUTH ---
with tab2:
    st.header("Define Baseline Ground Truth")
    st.write("Compare Model 1 against a designated Ground Truth dataset. Upload a pre-existing sheet or generate it automatically.")
    
    col_upload, col_auto = st.columns(2)
    
    with col_upload:
        st.subheader("Option A: Upload Ground Truth Excel")
        uploaded_gt_file = st.file_uploader(
            "Upload Ground Truth spreadsheet", 
            type=["xlsx", "xls"],
            key="gt_uploader_main"
        )
        
        if uploaded_gt_file:
            try:
                df_gt = pd.read_excel(uploaded_gt_file)
                cols = {c.lower().strip(): c for c in df_gt.columns}
                
                # Auto-detect key columns
                img_col = next((cols[p] for p in ["image name", "image", "file name", "filename", "name"] if p in cols), df_gt.columns[0])
                act_col = next((cols[p] for p in ["activity", "action"] if p in cols), None)
                obj_col = next((cols[p] for p in ["objects", "key objects", "tags"] if p in cols), None)
                sum_col = next((cols[p] for p in ["summary", "description", "desc", "ground truth description", "ground truth"] if p in cols), None)
                conf_col = next((cols[p] for p in ["confidence", "conf"] if p in cols), None)
                
                # Parse to state
                st.session_state.ground_truth = {}
                for _, row in df_gt.iterrows():
                    name = str(row[img_col]).strip()
                    activity = str(row[act_col]).strip() if act_col else "N/A"
                    objects = str(row[obj_col]).strip() if obj_col else "N/A"
                    confidence = str(row[conf_col]).strip() if conf_col else "N/A"
                    
                    if sum_col:
                        summary = str(row[sum_col]).strip()
                    elif len(df_gt.columns) > 1:
                        non_img = [c for c in df_gt.columns if c != img_col]
                        summary = str(row[non_img[0]]).strip()
                    else:
                        summary = "N/A"
                        
                    st.session_state.ground_truth[name] = {
                        "confidence": confidence,
                        "activity": activity,
                        "objects": objects,
                        "summary": summary
                    }
                st.success("Ground Truth dataset aligned successfully!")
            except Exception as e:
                st.error(f"Error parsing ground truth Excel: {e}")
                
    with col_auto:
        st.subheader("Option B: Auto-generate via Model 2")
        if not st.session_state.uploaded_images:
            st.info("Upload images in Step 1 to allow auto-generation of Ground Truth.")
        else:
            if st.button("🤖 Generate Baseline Ground Truth", key="btn_run_model2"):
                st.session_state.ground_truth = {}
                progress_bar_gt = st.progress(0)
                
                for idx, img in enumerate(st.session_state.uploaded_images):
                    img_name = img["name"]
                    img_bytes = img["bytes"]
                    
                    with st.spinner(f"Generating benchmark for {img_name}..."):
                        try:
                            res = generate_text_from_image(img_bytes, model_name=model2_name)
                            st.session_state.ground_truth[img_name] = res
                        except Exception as e:
                            st.session_state.ground_truth[img_name] = {
                                "confidence": "N/A",
                                "activity": f"Error: {e}",
                                "objects": "N/A",
                                "summary": "N/A"
                            }
                    progress_bar_gt.progress((idx + 1) / len(st.session_state.uploaded_images))
                st.success("Ground Truth benchmarks set successfully!")

    # Display Ground Truth Dataset
    if st.session_state.ground_truth:
        st.write("---")
        st.subheader("Current Ground Truth Dataset")
        df_gt_display = pd.DataFrame([
            {
                "Image Name": name,
                "Confidence": res.get("confidence", "N/A"),
                "Activity": res.get("activity", "N/A"),
                "Objects": res.get("objects", "N/A"),
                "Summary": res.get("summary", "N/A")
            }
            for name, res in st.session_state.ground_truth.items()
        ])
        st.dataframe(df_gt_display, use_container_width=True)
        
        output_gt = io.BytesIO()
        with pd.ExcelWriter(output_gt, engine='openpyxl') as writer:
            df_gt_display.to_excel(writer, index=False, sheet_name='Ground Truth')
        excel_gt_data = output_gt.getvalue()
        
        st.download_button(
            label="📥 Download Ground Truth Excel Sheet",
            data=excel_gt_data,
            file_name="ground_truth.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# --- TAB 3: COMPARE & EVALUATE ---
with tab3:
    st.header("Semantic Coincidence Audit")
    
    if not st.session_state.model1_results or not st.session_state.ground_truth:
        st.warning("Ensure Step 1 (Model 1 Results) and Step 2 (Ground Truth Dataset) are complete before starting the evaluation.")
    else:
        if st.button("⚖️ Run Semantic Coincidence Audit", key="btn_run_comparison"):
            st.session_state.comparison_results = []
            progress_bar_comp = st.progress(0)
            img_names = list(st.session_state.model1_results.keys())
            
            for idx, name in enumerate(img_names):
                desc1 = st.session_state.model1_results.get(name, {})
                desc2 = st.session_state.ground_truth.get(name, {})
                
                # Standardize to dict if string
                if not isinstance(desc1, dict):
                    desc1 = {"confidence": "N/A", "activity": "N/A", "objects": "N/A", "summary": desc1}
                if not isinstance(desc2, dict):
                    desc2 = {"confidence": "N/A", "activity": "N/A", "objects": "N/A", "summary": desc2}
                    
                with st.spinner(f"Auditing {name}..."):
                    try:
                        eval_res = compare_descriptions(desc1, desc2)
                        st.session_state.comparison_results.append({
                            "Image Name": name,
                            "Model 1 Activity": desc1.get("activity", "N/A"),
                            "Model 1 Objects": desc1.get("objects", "N/A"),
                            "Model 1 Summary": desc1.get("summary", "N/A"),
                            "Ground Truth Activity": desc2.get("activity", "N/A"),
                            "Ground Truth Objects": desc2.get("objects", "N/A"),
                            "Ground Truth Summary": desc2.get("summary", "N/A"),
                            "Coincidence Score (%)": eval_res.get("score", 0),
                            "Reason": eval_res.get("reason", "N/A")
                        })
                    except Exception as e:
                        st.session_state.comparison_results.append({
                            "Image Name": name,
                            "Model 1 Activity": desc1.get("activity", "N/A"),
                            "Model 1 Objects": desc1.get("objects", "N/A"),
                            "Model 1 Summary": desc1.get("summary", "N/A"),
                            "Ground Truth Activity": desc2.get("activity", "N/A"),
                            "Ground Truth Objects": desc2.get("objects", "N/A"),
                            "Ground Truth Summary": desc2.get("summary", "N/A"),
                            "Coincidence Score (%)": 0,
                            "Reason": f"Audit Error: {e}"
                        })
                progress_bar_comp.progress((idx + 1) / len(img_names))
            st.success("Semantic audit complete!")

    # Display comparison audit dashboard
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
            
            # Choose color based on score
            score_color = "#10b981" if score >= 80 else ("#f59e0b" if score >= 50 else "#ef4444")
            
            # Find the corresponding image bytes for thumbnail
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
                            <div style="margin-top: 5px; font-size: 14px;"><strong>Activity:</strong> {item["Model 1 Activity"]}</div>
                            <div style="margin-top: 3px; font-size: 14px;"><strong>Summary:</strong> {item["Model 1 Summary"]}</div>
                            <div style="margin-top: 5px;">
                                {''.join([f'<span class="object-badge" style="background: rgba(99,102,241,0.08);">{obj.strip()}</span>' for obj in item["Model 1 Objects"].split(',') if obj.strip()])}
                            </div>
                        </div>
                        
                        <div style="background: rgba(0, 0, 0, 0.02); padding: 12px; border-radius: 8px; border-left: 3px solid #14b8a6;">
                            <div style="font-size: 12px; font-weight: 600; color: #14b8a6; text-transform: uppercase;">Ground Truth</div>
                            <div style="margin-top: 5px; font-size: 14px;"><strong>Activity:</strong> {item["Ground Truth Activity"]}</div>
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
        
        # Color coding for data frame rendering
        def color_score(val):
            if val >= 80:
                color = '#D1FAE5'  # light green
            elif val >= 50:
                color = '#FEF3C7'  # light yellow
            else:
                color = '#FEE2E2'  # light red
            return f'background-color: {color}'

        styled_df = df_comp.style.map(color_score, subset=["Coincidence Score (%)"])
        st.dataframe(styled_df, use_container_width=True)
        
        output_comp = io.BytesIO()
        with pd.ExcelWriter(output_comp, engine='openpyxl') as writer:
            df_comp.to_excel(writer, index=False, sheet_name='Comparison Results')
        excel_comp_data = output_comp.getvalue()
        
        st.download_button(
            label="📥 Download Comparison Audit Excel Report",
            data=excel_comp_data,
            file_name="comparison_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
