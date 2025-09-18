import os
import glob
from document_processor import create_vector_store, load_vector_store, get_embedding_model
from agents import SECMonitoringAgent, RegulationAnalystAgent, InternalPolicyAuditorAgent, ComplianceReportAgent

# Variable Configs
INTERNAL_DOCS_PATH = "internal_docs/"
VECTOR_STORE_PATH = "vector_store/"
NEW_REGS_PATH = "new_regulations/"

def main():
    """Main function to orchestrate the agentic workflow."""
    
    # Initialize Embedding Model 
    embedding_model = get_embedding_model()

    #Setup Vector Store (One-time cost), deals with internal documents
    index, chunks = load_vector_store()
    if index is None or chunks is None:
        print("Vector store not found. Creating a new one...")
        internal_doc_files = glob.glob(os.path.join(INTERNAL_DOCS_PATH, "*.pdf"))
        if not internal_doc_files:
            print(f"Error: No PDF files found in {INTERNAL_DOCS_PATH}. Please add your internal policy PDFs.")
            return
        create_vector_store(internal_doc_files, embedding_model)
        index, chunks = load_vector_store()
        if index is None:
            print("Failed to create or load the vector store. Exiting.")
            return

    # Instantiate Agents 
    monitor_agent = SECMonitoringAgent()
    analyst_agent = RegulationAnalystAgent()
    auditor_agent = InternalPolicyAuditorAgent()
    report_agent = ComplianceReportAgent()

    # Find and Process all new regulations
    new_regulation_files = glob.glob(os.path.join(NEW_REGS_PATH, "*.pdf"))

    if not new_regulation_files:
        print(f"No new regulation PDFs found in '{NEW_REGS_PATH}'. Please add a file to analyze.")
        return

    print(f"Found {len(new_regulation_files)} regulation(s) to analyze. Starting workflow...")

    # Loop through each found regulation file.
    for reg_file_path in new_regulation_files:
        file_name = os.path.basename(reg_file_path)
        
        # Add a clear separator in the console output for each file being processed.
        print(f"\n\n{'='*70}\nProcessing Regulation: {file_name}\n{'='*70}")

        # Monitor for new regulations (simulated by reading the current file in the loop)
        regulation_text = monitor_agent.run(reg_file_path)
        if not regulation_text:
            print(f"Could not read text from {file_name}. Skipping.")
            continue # Skip to the next file if this one is unreadable

        # Analyze the regulation to extract mandates
        extracted_mandates = analyst_agent.run(regulation_text)
        print("\n=== Extracted Mandates ===")
        print(extracted_mandates)

        # Audit internal policies against each mandate
        gap_analysis_findings = auditor_agent.run(extracted_mandates, index, chunks, embedding_model)
        print("\n=== Gap Analysis Findings ===")
        print(gap_analysis_findings)

        # Generate the final compliance report and Dynamically create a title from the filename.
        report_title = file_name.replace('.pdf', '').replace('_', ' ').title()
        report_url = "URL not available from PDF, placeholder used." # URL is a placeholder for when we create api link
        
        final_report = report_agent.run(report_title, report_url, gap_analysis_findings)
        
        # Display Final Report for the current file 
        print("\n" + "-"*50)
        print(f"          FINAL COMPLIANCE REPORT for {file_name}")
        print("-"*50 + "\n")
        print(final_report)


if __name__ == "__main__":
    main()
