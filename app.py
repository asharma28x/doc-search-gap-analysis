import streamlit as st
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import glob

from document_processor import create_vector_store, load_vector_store, get_embedding_model
from agents import SECMonitoringAgent, RegulationAnalystAgent, InternalPolicyAuditorAgent, ComplianceReportAgent
from sec_rule_downloader import SECRulemakingMonitor

# Configuration

# Helper: choose a writable directory. Try project-local path first, then fallback to system temp.
def _choose_writable_dir(preferred_name: str) -> str:
    from pathlib import Path
    import tempfile

    # Try project-local directory first
    try:
        candidate = Path.cwd() / preferred_name
        candidate.mkdir(parents=True, exist_ok=True)
        # verify write privileges by creating and removing a small file
        test_file = candidate / ".write_test"
        with open(test_file, "w") as f:
            f.write("ok")
        test_file.unlink()
        return str(candidate)
    except Exception:
        # Fallback to system temp directory (user should have write access)
        fallback = Path(tempfile.gettempdir()) / "doc_search_app" / preferred_name
        fallback.mkdir(parents=True, exist_ok=True)
        return str(fallback)


TEMP_INTERNAL_DOCS_PATH = _choose_writable_dir("temp_internal_docs")
TEMP_VECTOR_STORE_PATH = _choose_writable_dir("temp_vector_store")
SEC_RULES_PATH = _choose_writable_dir("sec_rules_data")
REPORTS_PATH = _choose_writable_dir("reports")

# Page configuration
st.set_page_config(
    page_title="SEC Compliance Analyzer",
    page_icon="📋",
    layout="wide"
)

st.title("📋 SEC Compliance Gap Analysis System")
st.markdown("---")

# Initialize session state
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'report_path' not in st.session_state:
    st.session_state.report_path = None
if 'regulations_analyzed' not in st.session_state:
    st.session_state.regulations_analyzed = 0

# Create necessary directories
os.makedirs(TEMP_INTERNAL_DOCS_PATH, exist_ok=True)
os.makedirs(TEMP_VECTOR_STORE_PATH, exist_ok=True)
os.makedirs(SEC_RULES_PATH, exist_ok=True)
os.makedirs(REPORTS_PATH, exist_ok=True)

# Sidebar for instructions
with st.sidebar:
    st.header("📖 How to Use")
    st.markdown("""
    **Step 1:** Upload your internal policy documents (PDFs)
    
    **Step 2:** Choose regulation source:
    - **Auto-fetch**: Download latest SEC regulations automatically
    - **Manual upload**: Upload specific regulation PDFs
    
    **Step 3:** Click "Run Compliance Analysis"
    
    **Step 4:** Download the generated compliance report
    """)
    
    st.markdown("---")
    st.markdown("**Supported Formats:** PDF only")
    st.markdown("**Max File Size:** 200MB per file")

# Main content area
col1, col2 = st.columns(2)

with col1:
    st.subheader("📁 Internal Company Documents")
    st.markdown("Upload your company's internal policies, procedures, and compliance documents.")
    
    internal_docs = st.file_uploader(
        "Upload Internal Policy PDFs",
        type=['pdf'],
        accept_multiple_files=True,
        key="internal_uploader",
        help="Upload all relevant internal policy documents for gap analysis"
    )
    
    if internal_docs:
        st.success(f"✓ {len(internal_docs)} internal document(s) uploaded")
        with st.expander("View uploaded files"):
            for idx, file in enumerate(internal_docs, 1):
                st.write(f"{idx}. {file.name} ({file.size / 1024:.2f} KB)")

with col2:
    st.subheader("📜 SEC Regulations")
    st.markdown("Choose how to source SEC regulations for analysis.")
    
    regulation_source = st.radio(
        "Regulation Source:",
        ["Auto-fetch from SEC.gov", "Manual Upload"],
        help="Auto-fetch downloads latest regulations automatically"
    )
    
    regulation_docs = None
    auto_fetch = False
    
    if regulation_source == "Manual Upload":
        regulation_docs = st.file_uploader(
            "Upload Regulation PDFs",
            type=['pdf'],
            accept_multiple_files=True,
            key="regulation_uploader",
            help="Upload specific SEC regulation documents"
        )
        
        if regulation_docs:
            st.success(f"✓ {len(regulation_docs)} regulation(s) uploaded")
            with st.expander("View uploaded files"):
                for idx, file in enumerate(regulation_docs, 1):
                    st.write(f"{idx}. {file.name} ({file.size / 1024:.2f} KB)")
    else:
        auto_fetch = True
        st.info("📡 Will auto-fetch latest regulations from SEC.gov")
        
        # Optional: Let user specify how many to fetch
        num_regulations = st.slider(
            "Number of latest regulations to analyze:",
            min_value=1,
            max_value=10,
            value=5,
            help="How many recent SEC regulations to download and analyze"
        )

st.markdown("---")

# Analysis section
st.subheader("🔍 Run Analysis")

col_analyze, col_status = st.columns([1, 2])

with col_analyze:
    # Validation logic
    can_analyze = False
    validation_messages = []
    
    if not internal_docs:
        validation_messages.append("⚠️ Please upload internal documents")
    else:
        validation_messages.append("✓ Internal documents ready")
    
    if regulation_source == "Manual Upload" and not regulation_docs:
        validation_messages.append("⚠️ Please upload regulation documents")
    elif regulation_source == "Manual Upload":
        validation_messages.append("✓ Regulation documents ready")
    else:
        validation_messages.append("✓ Auto-fetch mode enabled")
    
    can_analyze = len([m for m in validation_messages if "⚠️" in m]) == 0
    
    analyze_button = st.button(
        "🚀 Run Compliance Analysis",
        type="primary",
        disabled=not can_analyze,
        use_container_width=True
    )

with col_status:
    for msg in validation_messages:
        if "⚠️" in msg:
            st.warning(msg)
        else:
            st.success(msg)

# Run analysis when button is clicked
if analyze_button:
    st.session_state.analysis_complete = False
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # STEP 1: Save uploaded internal documents
        status_text.text("📥 Step 1/5: Processing internal documents...")
        progress_bar.progress(10)
        
        # Create per-run temp subdirectories to avoid deleting parent folders (which can fail
        # on OneDrive or managed locations). We use a timestamp to isolate runs.
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        RUN_INTERNAL_DIR = os.path.join(TEMP_INTERNAL_DOCS_PATH, run_id)
        os.makedirs(RUN_INTERNAL_DIR, exist_ok=True)

        internal_doc_paths = []
        for uploaded_file in internal_docs:
            file_path = os.path.join(RUN_INTERNAL_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            internal_doc_paths.append(file_path)
        
        st.info(f"✓ Saved {len(internal_doc_paths)} internal document(s)")
        progress_bar.progress(20)
        
        # STEP 2: Create vector store from internal documents
        status_text.text("🔨 Step 2/5: Building vector store from internal policies...")
        
        embedding_model = get_embedding_model()
        
        # Use a run-specific temp vector store path to avoid permission and concurrency issues
        import document_processor
        RUN_VECTOR_STORE = os.path.join(TEMP_VECTOR_STORE_PATH, f"vector_store_{run_id}")
        os.makedirs(RUN_VECTOR_STORE, exist_ok=True)
        document_processor.VECTOR_STORE_PATH = RUN_VECTOR_STORE
        document_processor.INDEX_FILE = os.path.join(RUN_VECTOR_STORE, "faiss_index.bin")
        document_processor.CHUNKS_FILE = os.path.join(RUN_VECTOR_STORE, "chunks.pkl")
        
        create_vector_store(internal_doc_paths, embedding_model)
        index, chunks = load_vector_store()
        
        if index is None:
            st.error("❌ Failed to create vector store. Please check your documents.")
            st.stop()
        
        st.info(f"✓ Vector store created with {len(chunks)} text chunks")
        progress_bar.progress(40)
        
        # STEP 3: Get regulations (auto-fetch or manual)
        status_text.text("📜 Step 3/5: Obtaining SEC regulations...")
        
        regulation_file_paths = []
        new_rules = []
        
        if auto_fetch:
            # Auto-fetch from SEC
            monitor = SECRulemakingMonitor(storage_path=SEC_RULES_PATH)
            new_rules = monitor.process_new_rules()
            
            if new_rules:
                regulation_file_paths = [rule['pdf_path'] for rule in new_rules]
                st.info(f"✓ Downloaded {len(new_rules)} new regulation(s) from SEC.gov")
            else:
                # If no new rules, check existing files
                existing_regs = glob.glob(os.path.join(SEC_RULES_PATH, "*.pdf"))
                if existing_regs:
                    regulation_file_paths = existing_regs[:num_regulations]
                    st.warning(f"⚠️ No new regulations found. Using {len(regulation_file_paths)} existing regulation(s).")
                else:
                    st.error("❌ No regulations found. Please try manual upload mode.")
                    st.stop()
        else:
            # Manual upload
            for uploaded_file in regulation_docs:
                file_path = os.path.join(SEC_RULES_PATH, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                regulation_file_paths.append(file_path)
            
            st.info(f"✓ Saved {len(regulation_file_paths)} regulation document(s)")
        
        progress_bar.progress(50)
        
        # STEP 4: Analyze regulations
        status_text.text("🔍 Step 4/5: Analyzing regulations and identifying gaps...")
        
        # Instantiate agents
        monitor_agent = SECMonitoringAgent()
        analyst_agent = RegulationAnalystAgent()
        auditor_agent = InternalPolicyAuditorAgent()
        report_agent = ComplianceReportAgent()
        
        all_regulations_data = []
        
        # Process each regulation
        for idx, reg_file_path in enumerate(regulation_file_paths, 1):
            file_name = os.path.basename(reg_file_path)
            
            sub_status = st.empty()
            sub_status.text(f"   Analyzing regulation {idx}/{len(regulation_file_paths)}: {file_name}")
            
            # Find metadata if auto-fetched
            regulation_metadata = None
            for rule in new_rules:
                if rule.get('pdf_path') == reg_file_path:
                    regulation_metadata = rule
                    break
            
            # Read regulation text
            regulation_text = monitor_agent.run(reg_file_path)
            if not regulation_text:
                st.warning(f"⚠️ Could not read {file_name}, skipping...")
                continue
            
            # Extract mandates
            extracted_mandates = analyst_agent.run(regulation_text)

            # DEBUG: Show extraction result
            if not extracted_mandates or "Error" in extracted_mandates:
                st.warning(f"⚠️ Mandate extraction issue for {file_name}")
                with st.expander(f"Debug: {file_name} extraction"):
                    st.text(f"Text length: {len(regulation_text)}")
                    st.text(f"First 500 chars: {regulation_text[:500]}")
                    st.text(f"Mandates result: {extracted_mandates[:500]}")
            else:
                st.success(f"✓ Extracted mandates from {file_name}")

            # Perform gap analysis
            gap_analysis_findings = auditor_agent.run(
                extracted_mandates, 
                index, 
                chunks, 
                embedding_model
            )
            
            # Store results
            if regulation_metadata:
                reg_title = regulation_metadata.get('title', file_name.replace('.pdf', '').replace('_', ' ').title())
                reg_url = regulation_metadata.get('url', 'URL not available')
                reg_date = regulation_metadata.get('date', 'Date not available')
            else:
                reg_title = file_name.replace('.pdf', '').replace('_', ' ').title()
                reg_url = "Manually uploaded"
                reg_date = datetime.now().strftime('%Y-%m-%d')
            
            all_regulations_data.append({
                'title': reg_title,
                'url': reg_url,
                'date': reg_date,
                'file_name': file_name,
                'mandates': extracted_mandates,
                'gap_analysis': gap_analysis_findings
            })
            
            # Update progress
            progress_bar.progress(50 + int(40 * idx / len(regulation_file_paths)))
        
        if not all_regulations_data:
            st.error("❌ No regulations were successfully analyzed.")
            st.stop()
        
        progress_bar.progress(90)
        
        # STEP 5: Generate consolidated report
        status_text.text("📊 Step 5/5: Generating consolidated compliance report...")
        
        final_report = report_agent.run_consolidated(all_regulations_data)
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"consolidated_compliance_report_{timestamp}.txt"
        report_path = os.path.join(REPORTS_PATH, report_filename)
        
        report_agent.save_consolidated_report_as_text(
            final_report,
            report_path,
            all_regulations_data,
            timestamp
        )
        
        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")
        
        # Update session state
        st.session_state.analysis_complete = True
        st.session_state.report_path = report_path
        st.session_state.regulations_analyzed = len(all_regulations_data)
        
        st.success(f"""
        ### ✅ Analysis Complete!
        
        - **Regulations Analyzed:** {len(all_regulations_data)}
        - **Internal Documents:** {len(internal_doc_paths)}
        - **Report Generated:** {report_filename}
        - **Report Size:** {os.path.getsize(report_path) / 1024:.2f} KB
        """)
        
    except Exception as e:
        st.error(f"❌ Error during analysis: {str(e)}")
        import traceback
        with st.expander("View error details"):
            st.code(traceback.format_exc())

# Display results if analysis is complete
if st.session_state.analysis_complete and st.session_state.report_path:
    st.markdown("---")
    st.subheader("📊 Analysis Results")
    
    col_download, col_preview = st.columns([1, 3])
    
    with col_download:
        # Download button
        with open(st.session_state.report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        st.download_button(
            label="📥 Download Full Report",
            data=report_content,
            file_name=os.path.basename(st.session_state.report_path),
            mime="text/plain",
            type="primary",
            use_container_width=True
        )
        
        st.metric("Regulations Analyzed", st.session_state.regulations_analyzed)
        st.metric("Report Size", f"{len(report_content) / 1024:.2f} KB")
    
    with col_preview:
        st.markdown("**Report Preview** (First 3000 characters)")
        preview_text = report_content[:3000]
        if len(report_content) > 3000:
            preview_text += "\n\n[... Report continues. Download for full content ...]"
        
        st.text_area(
            "Report Content",
            value=preview_text,
            height=400,
            label_visibility="collapsed"
        )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
    SEC Compliance Gap Analysis System v1.0 | Powered by AI
</div>
""", unsafe_allow_html=True)
