from llm_service import llm_chat
from pypdf import PdfReader
import numpy as np

class SECMonitoringAgent:
    def run(self, regulation_pdf_path):
        """
        Simulated agent: Reads the text from a provided SEC regulation PDF.
        Gonna have to make integration with API after instead
        """
        print("=== Running SEC Monitoring Agent ===")
        try:
            reader = PdfReader(regulation_pdf_path)
            text = "".join(page.extract_text() for page in reader.pages)
            print(f"Successfully read {regulation_pdf_path}")
            return text
        except Exception as e:
            print(f"Error reading regulation PDF: {e}")
            return None

class RegulationAnalystAgent:
    def run(self, regulation_text):
        """
        Uses an LLM to analyze regulation text and extract actionable mandates.
        """
        print("=== Running Regulation Analyst Agent ===")
        prompt = f"""
        Analyze the following SEC regulation text and extract all actionable mandates required for a company to be compliant. Ignore the document's history, commentary, and non-binding suggestions; focus only on direct requirements.

        For each distinct mandate you identify, provide the following details in a structured format:

        **Mandate:** [A short, descriptive title for the mandate (e.g., 'Incident Disclosure Timeline')]
        **Requirement:** [A clear, one-sentence summary of what the company must do]
        **Source Text:** [The exact quote from the regulation that defines this mandate]

        Here is the regulation text:
        ---
        {regulation_text}
        ---
        """
        response = llm_chat(prompt)
        print("Mandates extracted.")
        return response

class InternalPolicyAuditorAgent:
    def run(self, mandates_text, vector_store, text_chunks, embedding_model):
        """
        Performs a gap analysis for each mandate against the internal documents.
        """
        print("=== Running Internal Policy Auditor Agent ===")
        findings = []
        # Simple parsing of mandates from the LLM's text response
        mandates = mandates_text.strip().split('**Mandate:**')
        
        for mandate_block in mandates:
            if not mandate_block.strip():
                continue

            mandate_title = mandate_block.split('**Requirement:**')[0].strip()
            print(f"Auditing mandate: {mandate_title}")

            # Use the mandate title and requirement for searching
            query_embedding = embedding_model.encode([mandate_block])
            
            # Search the vector store for top 3 relevant chunks
            k = 3
            distances, indices = vector_store.search(np.array(query_embedding, dtype=np.float32), k)
            
            relevant_chunks = [text_chunks[i] for i in indices[0]]
            context = "\n\n===\n\n".join(relevant_chunks)

            prompt = f"""
            You are an AI compliance auditor. Perform a gap analysis for a specific regulatory mandate against our internal company policies.

            **Regulatory Mandate to Analyze:**
            {mandate_block.strip()}

            **Relevant Sections from Our Internal Policies:**
            {context}

            **Your Task:**
            1. Compare our internal policy text with the specific requirement of the mandate.
            2. Determine if we are fully compliant, partially compliant, or have a major gap.
            3. Clearly state the impacted document and section (use the 'Source:' from the context).
            4. Explain *why* our current policy is insufficient or where the gap is.
            5. Provide a confidence score (from 0.0 to 1.0) on how certain you are about this gap.

            **Format your output concisely as follows:**
            **Gap Analysis:** [Your analysis explaining the gap]
            **Impacted Document:** [Document name and section]
            **Compliance Status:** [Fully Compliant / Partially Compliant / Major Gap]
            **Confidence Score:** [e.g., 0.95]
            """
            
            analysis_result = llm_chat(prompt)
            # Combine the mandate with its analysis for the final report
            full_finding = f"**Mandate:** {mandate_title}\n{analysis_result}"
            findings.append(full_finding)
            print(f"Analysis complete for: {mandate_title}")
            
        return "\n\n".join(findings)

class ComplianceReportAgent:
    def run(self, regulation_title, regulation_url, gap_analysis_results):
        """
        Synthesizes all findings into a final, professional report for the legal team.
        """
        print("=== Running Compliance Report Agent ===")
        prompt = f"""
        You are an AI assistant writing a report for our company's legal team. Your tone must be professional, clear, and actionable. Using the summary of the new regulation and the detailed gap analysis findings, generate a concise compliance report.

        The report must include the following sections and no other text before or after:

        **Executive Summary:**
        - Regulation Title: {regulation_title}
        - Regulation Source: {regulation_url}
        - High-Level Overview: Briefly summarize the key compliance gaps found based on the detailed findings below.

        **Detailed Findings:**
        [Present the detailed gap analysis findings provided below. Format them clearly and professionally.]

        **Recommended Stakeholders for Notification:**
        [Based on the findings, list which stakeholders should be notified (e.g., Legal, CISO, Board of Directors, HR).]
        
        **Disclaimer:**
        This is an AI-generated preliminary analysis and requires comprehensive review by human legal and compliance professionals before any action is taken.

        ---
        **GAP ANALYSIS FINDINGS TO INCLUDE IN THE REPORT:**
        {gap_analysis_results}
        ---
        """
        final_report = llm_chat(prompt)
        print("Compliance report generated.")
        return final_report
