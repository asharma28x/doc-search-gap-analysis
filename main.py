import os
import glob
from datetime import datetime
from document_processor import create_vector_store, load_vector_store, get_embedding_model
from agents import SECMonitoringAgent, RegulationAnalystAgent, InternalPolicyAuditorAgent, ComplianceReportAgent
from sec_rule_downloader import SECRulemakingMonitor

# Variable Configs
INTERNAL_DOCS_PATH = "internal_docs/"
VECTOR_STORE_PATH = "vector_store/"
NEW_REGS_PATH = "sec_rules_data/"
REPORTS_PATH = "reports/"

def main():
    """Main function to orchestrate the agentic workflow."""
    
    # Create reports directory if it doesn't exist
    os.makedirs(REPORTS_PATH, exist_ok=True)
    
    # Initialize Embedding Model 
    embedding_model = get_embedding_model()

    # Setup Vector Store (One-time cost), deals with internal documents
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

    # STEP 1: Check for new SEC regulations using the monitoring system
    print("\n" + "="*80)
    print("STEP 1: Checking for New SEC Regulations")
    print("="*80)
    
    monitor = SECRulemakingMonitor(storage_path=NEW_REGS_PATH)
    new_rules = monitor.process_new_rules()
    
    if new_rules:
        print(f"\n✓ Downloaded {len(new_rules)} new regulation(s)")
    else:
        print("\nNo new regulations found via API.")
    
    # STEP 2: Process all regulations in the folder
    print("\n" + "="*80)
    print("STEP 2: Processing All Regulations")
    print("="*80)
    
    # Instantiate Agents 
    monitor_agent = SECMonitoringAgent()
    analyst_agent = RegulationAnalystAgent()
    auditor_agent = InternalPolicyAuditorAgent()
    report_agent = ComplianceReportAgent()

    # Find all regulation PDFs
    new_regulation_files = glob.glob(os.path.join(NEW_REGS_PATH, "*.pdf"))

    if not new_regulation_files:
        print(f"No regulation PDFs found in '{NEW_REGS_PATH}'.")
        return

    print(f"Found {len(new_regulation_files)} regulation(s) to analyze. Starting workflow...\n")

    # Track all processed regulations for consolidated report
    all_regulations_data = []
    processed_count = 0

    # Loop through each found regulation file
    for reg_file_path in new_regulation_files:
        file_name = os.path.basename(reg_file_path)
        
        # Add a clear separator in the console output for each file being processed
        print(f"\n\n{'='*80}\nProcessing Regulation: {file_name}\n{'='*80}")

        # Find metadata for this regulation if it was just downloaded
        regulation_metadata = None
        for rule in new_rules:
            if rule.get('pdf_path') == reg_file_path:
                regulation_metadata = rule
                break

        # Monitor for new regulations (read the PDF)
        regulation_text = monitor_agent.run(reg_file_path)
        if not regulation_text:
            print(f"Could not read text from {file_name}. Skipping.")
            continue

        # Analyze the regulation to extract mandates
        extracted_mandates = analyst_agent.run(regulation_text)
        print("\n=== Extracted Mandates ===")
        print(extracted_mandates[:500] + "..." if len(extracted_mandates) > 500 else extracted_mandates)

        # Audit internal policies against each mandate
        gap_analysis_findings = auditor_agent.run(extracted_mandates, index, chunks, embedding_model)
        print("\n=== Gap Analysis Findings ===")
        print(gap_analysis_findings[:500] + "..." if len(gap_analysis_findings) > 500 else gap_analysis_findings)

        # Collect regulation data for consolidated report
        if regulation_metadata:
            reg_title = regulation_metadata.get('title', file_name.replace('.pdf', '').replace('_', ' ').title())
            reg_url = regulation_metadata.get('url', 'URL not available')
            reg_date = regulation_metadata.get('date', 'Date not available')
        else:
            reg_title = file_name.replace('.pdf', '').replace('_', ' ').title()
            reg_url = "URL not available (processed from local file)"
            reg_date = "Date not available"
        
        all_regulations_data.append({
            'title': reg_title,
            'url': reg_url,
            'date': reg_date,
            'file_name': file_name,
            'mandates': extracted_mandates,
            'gap_analysis': gap_analysis_findings
        })
        
        processed_count += 1
        print(f"\n✓ Completed analysis for {file_name} ({processed_count}/{len(new_regulation_files)})")

    # STEP 3: Generate Consolidated Report
    if not all_regulations_data:
        print("\nNo regulations were successfully processed. Exiting.")
        return
    
    print("\n" + "="*80)
    print("STEP 3: Generating Consolidated Compliance Report")
    print("="*80)
    
    # Generate the consolidated final compliance report
    final_report = report_agent.run_consolidated(all_regulations_data)
    
    # Display Final Report preview
    print("\n" + "-"*80)
    print("          CONSOLIDATED COMPLIANCE REPORT PREVIEW")
    print("-"*80 + "\n")
    print(final_report[:2000] + "..." if len(final_report) > 2000 else final_report)
    
    # Save consolidated report as TEXT
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"consolidated_compliance_report_{timestamp}.txt"
    report_path = os.path.join(REPORTS_PATH, report_filename)
    
    report_agent.save_consolidated_report_as_text(
        final_report, 
        report_path,
        all_regulations_data,
        timestamp
    )
    
    print(f"\n{'='*80}")
    print(f"✓ Consolidated report saved to: {report_path}")
    print(f"✓ Total regulations analyzed: {len(all_regulations_data)}")
    print(f"✓ Report size: {os.path.getsize(report_path) / 1024:.2f} KB")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
