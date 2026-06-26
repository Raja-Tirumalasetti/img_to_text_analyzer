import streamlit as st
import pandas as pd
import io
import os
from api import generate_text_from_image, compare_descriptions

st.set_page_config(page_title="Image-to-Text Automation & Comparison", layout="wide")

# Custom Premium Styling
st.markdown("""
<style>
    .reportview-container {
        background: #f5f7f8;
    }
    .metric-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        border-top: 4px solid #4F46E5;
    }
    .metric-value {
        font-size: 36px;
        font-weight: bold;
        color: #4F46E5;
    }
    .metric-label {
        font-size: 14px;
        color: #6B7280;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Image-to-Text Automation & Sheet Evaluator")
st.write("Upload a batch of images, generate descriptions using Gemini, and compare them with Ground Truth data using an Evaluation LLM.")

# Initialize session state variables
if "model1_results" not in st.session_state:
    st.session_state.model1_results = {}
if "uploaded_images" not in st.session_state:
    st.session_state.uploaded_images = []
if "ground_truth" not in st.session_state:
    st.session_state.ground_truth = {}
if "comparison_results" not in st.session_state:
    st.session_state.comparison_results = []

# Tabs for structured workflow
tab1, tab2, tab3 = st.tabs([
    "📤 Step 1: Upload & Model 1", 
    "🎯 Step 2: Ground Truth", 
    "⚖️ Step 3: Compare & Evaluate"
])

# --- TAB 1: UPLOAD & MODEL 1 ---
with tab1:
    st.header("Upload Images & Run Model 1")
    
    # Model Selection
    model1_name = st.selectbox(
        "Select Model 1 (Main describer)",
        ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-3.5-flash"],
        index=0,
        help="Recommended: gemini-2.5-flash for speed and cost efficiency."
    )
    
    uploaded_files = st.file_uploader(
        "Upload multiple images", 
        type=["png", "jpg", "jpeg"], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.session_state.uploaded_images = []
        for file in uploaded_files:
            file_bytes = file.read()
            st.session_state.uploaded_images.append({
                "name": file.name,
                "bytes": file_bytes
            })
        st.success(f"Successfully loaded {len(uploaded_files)} images!")

    if st.session_state.uploaded_images:
        if st.button("🚀 Run Model 1 on all images", key="run_model_1"):
            st.session_state.model1_results = {}
            progress_bar = st.progress(0)
            
            for i, img in enumerate(st.session_state.uploaded_images):
                img_name = img["name"]
                img_bytes = img["bytes"]
                
                with st.spinner(f"Processing {img_name}..."):
                    try:
                        desc = generate_text_from_image(img_bytes, model_name=model1_name)
                        st.session_state.model1_results[img_name] = desc
                    except Exception as e:
                        st.session_state.model1_results[img_name] = f"Error: {e}"
                
                progress_bar.progress((i + 1) / len(st.session_state.uploaded_images))
            st.success("Model 1 processing complete!")
            
    # Display results and provide Excel export
    if st.session_state.model1_results:
        st.subheader("Model 1 Results")
        
        # Convert dictionary to DataFrame for display
        df_model1 = pd.DataFrame([
            {"Image Name": name, "Model 1 Description": desc} 
            for name, desc in st.session_state.model1_results.items()
        ])
        st.dataframe(df_model1, use_container_width=True)
        
        # Export Model 1 to Excel in memory
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


# --- TAB 2: GROUND TRUTH ---
with tab2:
    st.header("Define Ground Truth Data")
    st.write("You can either upload an existing Ground Truth Excel sheet or generate one using another LLM (Model 2) for testing purposes.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Option A: Upload Ground Truth Excel")
        uploaded_gt_file = st.file_uploader(
            "Upload Excel file (should contain columns for image/file name & ground truth text)", 
            type=["xlsx", "xls"],
            key="gt_uploader"
        )
        
        if uploaded_gt_file:
            try:
                df_gt = pd.read_excel(uploaded_gt_file)
                # Standardize columns
                cols = {c.lower().strip(): c for c in df_gt.columns}
                
                # Auto-detect image name column
                img_col = None
                for possible in ["image name", "image", "file name", "filename", "name"]:
                    if possible in cols:
                        img_col = cols[possible]
                        break
                if not img_col:
                    img_col = df_gt.columns[0]
                    
                # Auto-detect description column
                desc_col = None
                for possible in ["ground truth description", "ground truth", "description", "desc", "true description", "text"]:
                    if possible in cols:
                        desc_col = cols[possible]
                        break
                if not desc_col:
                    desc_col = df_gt.columns[1] if len(df_gt.columns) > 1 else df_gt.columns[0]
                
                # Parse to session state
                st.session_state.ground_truth = {}
                for _, row in df_gt.iterrows():
                    name = str(row[img_col]).strip()
                    desc = str(row[desc_col]).strip()
                    st.session_state.ground_truth[name] = desc
                    
                st.success("Ground Truth loaded successfully from Excel!")
            except Exception as e:
                st.error(f"Error parsing ground truth Excel: {e}")
                
    with col2:
        st.subheader("Option B: Auto-generate Ground Truth using Model 2")
        model2_name = st.selectbox(
            "Select Model 2 (Simulating Ground Truth)",
            ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-3.5-flash"],
            index=0,
            help="Using a more powerful model like gemini-2.5-pro can serve as a ground-truth simulator."
        )
        
        if not st.session_state.uploaded_images:
            st.info("Please upload images in Step 1 first to generate Ground Truth.")
        else:
            if st.button("🤖 Run Model 2 (Generate Ground Truth)", key="run_model_2"):
                st.session_state.ground_truth = {}
                progress_bar_gt = st.progress(0)
                
                for i, img in enumerate(st.session_state.uploaded_images):
                    img_name = img["name"]
                    img_bytes = img["bytes"]
                    
                    with st.spinner(f"Generating ground truth for {img_name}..."):
                        try:
                            desc = generate_text_from_image(img_bytes, model_name=model2_name)
                            st.session_state.ground_truth[img_name] = desc
                        except Exception as e:
                            st.session_state.ground_truth[img_name] = f"Error: {e}"
                    
                    progress_bar_gt.progress((i + 1) / len(st.session_state.uploaded_images))
                st.success("Ground Truth generation complete!")
                
    # Display loaded Ground Truth
    if st.session_state.ground_truth:
        st.subheader("Loaded Ground Truth Data")
        df_gt_display = pd.DataFrame([
            {"Image Name": name, "Ground Truth Description": desc}
            for name, desc in st.session_state.ground_truth.items()
        ])
        st.dataframe(df_gt_display, use_container_width=True)
        
        # Export Ground Truth to Excel in memory for download
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
    st.header("Compare Results & Calculate Coincidence")
    
    if not st.session_state.model1_results or not st.session_state.ground_truth:
        st.warning("Please make sure you have generated Model 1 results (Step 1) and defined Ground Truth (Step 2) before running the comparison.")
    else:
        if st.button("⚖️ Run LLM Sheet Comparison", key="run_comparison"):
            st.session_state.comparison_results = []
            progress_bar_comp = st.progress(0)
            
            # Align image descriptions
            img_names = list(st.session_state.model1_results.keys())
            
            for i, name in enumerate(img_names):
                desc1 = st.session_state.model1_results.get(name, "")
                desc2 = st.session_state.ground_truth.get(name, "")
                
                if not desc1 or not desc2:
                    continue
                    
                with st.spinner(f"Evaluating {name}..."):
                    try:
                        eval_res = compare_descriptions(desc1, desc2)
                        st.session_state.comparison_results.append({
                            "Image Name": name,
                            "Model 1 Description": desc1,
                            "Ground Truth Description": desc2,
                            "Coincidence Score (%)": eval_res.get("score", 0),
                            "Reason": eval_res.get("reason", "N/A")
                        })
                    except Exception as e:
                        st.session_state.comparison_results.append({
                            "Image Name": name,
                            "Model 1 Description": desc1,
                            "Ground Truth Description": desc2,
                            "Coincidence Score (%)": 0,
                            "Reason": f"Evaluation error: {e}"
                        })
                        
                progress_bar_comp.progress((i + 1) / len(img_names))
            st.success("Comparison evaluation complete!")

    if st.session_state.comparison_results:
        df_comp = pd.DataFrame(st.session_state.comparison_results)
        
        # Calculate metric summary
        avg_score = df_comp["Coincidence Score (%)"].mean()
        
        st.subheader("Performance Metric")
        col_metric, _ = st.columns([1, 3])
        with col_metric:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{avg_score:.1f}%</div>
                <div class="metric-label">Average Coincidence Value</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("")
        st.subheader("Comparison Table")
        
        # Render styled dataframe
        def color_score(val):
            if val >= 80:
                color = '#D1FAE5'  # green
            elif val >= 50:
                color = '#FEF3C7'  # yellow
            else:
                color = '#FEE2E2'  # red
            return f'background-color: {color}'

        styled_df = df_comp.style.map(color_score, subset=["Coincidence Score (%)"])
        st.dataframe(styled_df, use_container_width=True)
        
        # Export Comparison Results to Excel in memory
        output_comp = io.BytesIO()
        with pd.ExcelWriter(output_comp, engine='openpyxl') as writer:
            df_comp.to_excel(writer, index=False, sheet_name='Comparison Results')
        excel_comp_data = output_comp.getvalue()
        
        st.download_button(
            label="📥 Download Comparison Results Excel Sheet",
            data=excel_comp_data,
            file_name="comparison_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
