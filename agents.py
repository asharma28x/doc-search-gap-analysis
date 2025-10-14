from llm_service import llm_chat
from pypdf import PdfReader
import numpy as np
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from datetime import datetime
import re

class SECMonitoringAgent:
    def run(self, regulation_pdf_path):
        """
        Reads the text from a provided SEC regulation PDF.
        """
        print("=== Running SEC Monitoring Agent ===")
        try:
            reader = PdfReader(regulation_pdf_path)
            text = "".join(page.extract_text() for page in reader.pages)
            print(f"Successfully read {regulation_pdf_path} ({len(text)} characters)")
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
        
        # Check if regulation text is empty
        if not regulation_text or len(regulation_text.strip()) < 100:
            print("ERROR: Regulation text is too short or empty")
            return "Error: Regulation document appears to be empty or unreadable."
        
        # Increase truncation limit to 100k characters (adjust based on your needs)
        max_length = 100000
        if len(regulation_text) > max_length:
            print(f"Warning: Regulation text is {len(regulation_text)} chars, truncating to {max_length}")
            regulation_text = regulation_text[:max_length] + "\n\n[...Document truncated due to length...]"
        
        print(f"Processing regulation text: {len(regulation_text)} characters")
        
        prompt = f"""You are a regulatory compliance analyst specializing in SEC regulations. Your task is to extract ALL actionable mandates and requirements from the provided regulation text.

**IMPORTANT:** Even if this is a concept release or request for comments, identify any procedural requirements, deadlines, or obligations mentioned.

**Instructions:**
1. Identify ONLY direct requirements and obligations that companies must follow
2. Exclude: background information, legislative history, commentary, examples, and non-binding guidance
3. Focus on: "must", "shall", "required to", "obligated to", specific deadlines, and concrete actions
4. Group related requirements logically
5. If this is a concept release with no actionable mandates, state: "No actionable mandates - this is a concept release for public comment only."

**For each distinct mandate, provide:**

**Mandate:** [Short descriptive title, max 10 words]
**Category:** [Choose one: Disclosure, Reporting, Internal Controls, Timeline/Deadline, Governance, Documentation, Other]
**Requirement:** [Clear one-sentence summary of the obligation]
**Specifics:** [Key details: deadlines, thresholds, formats, who must comply]
**Source Reference:** [Exact section/paragraph number or first 50 words of the source text]

**Format your response as a numbered list with clear separation between mandates.**

---
REGULATION TEXT:
{regulation_text}
---

Begin your analysis:"""

        try:
            # Use increased token limit
            response = llm_chat(prompt, max_tokens=8000)
            
            # Check if response is valid
            if not response or len(response.strip()) < 50:
                print(f"WARNING: LLM returned short or empty response: '{response}'")
                return "Error: LLM did not provide a valid analysis. The document may be too complex or the API may have failed."
            
            if "Error" in response[:100]:
                print(f"ERROR in LLM response: {response[:200]}")
                return response
            
            print(f"Mandates extracted ({len(response)} characters)")
            return response
            
        except Exception as e:
            print(f"ERROR calling LLM: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Error analyzing regulation: {str(e)}"


class InternalPolicyAuditorAgent:
    def run(self, mandates_text, vector_store, text_chunks, embedding_model):
        """
        Performs a gap analysis for each mandate against the internal documents.
        """
        print("=== Running Internal Policy Auditor Agent ===")
        
        # Check if mandates_text is valid
        if not mandates_text or len(mandates_text.strip()) < 50:
            print("ERROR: No valid mandates text provided")
            return "Error: No mandates were extracted from the regulation."
        
        if "Error" in mandates_text[:100]:
            print("ERROR: Mandates text contains error message")
            return mandates_text  # Pass through the error
        
        if "No actionable mandates" in mandates_text:
            print("INFO: Regulation has no actionable mandates (concept release)")
            return mandates_text
        
        findings = []
        
        mandate_blocks = self._parse_mandates(mandates_text)
        
        if not mandate_blocks:
            print("Warning: Could not parse any mandates from the analyst output")
            print(f"First 500 chars of mandates_text: {mandates_text[:500]}")
            return "No mandates could be parsed for analysis. Raw output:\n\n" + mandates_text[:1000]
        
        print(f"Analyzing {len(mandate_blocks)} mandates...\n")
        
        for idx, mandate_block in enumerate(mandate_blocks, 1):
            mandate_title = mandate_block.get('title', f'Mandate {idx}')
            print(f"[{idx}/{len(mandate_blocks)}] Auditing: {mandate_title}")

            # Create a query from the mandate
            query_text = f"{mandate_block.get('title', '')} {mandate_block.get('requirement', '')} {mandate_block.get('specifics', '')}"
            
            # Search the vector store for top 5 relevant chunks
            k = 5
            try:
                query_embedding = embedding_model.encode([query_text])
                distances, indices = vector_store.search(np.array(query_embedding, dtype=np.float32), k)
                
                relevant_chunks = [text_chunks[i] for i in indices[0]]
                context = "\n\n===SECTION BREAK===\n\n".join(relevant_chunks)
            except Exception as e:
                print(f"Error searching vector store: {e}")
                context = "No relevant internal policies found."

            prompt = f"""You are an expert compliance auditor conducting a gap analysis between SEC regulatory requirements and internal company policies.

**REGULATORY MANDATE TO EVALUATE:**
Title: {mandate_block.get('title', 'N/A')}
Category: {mandate_block.get('category', 'N/A')}
Requirement: {mandate_block.get('requirement', 'N/A')}
Specifics: {mandate_block.get('specifics', 'N/A')}

**RELEVANT EXCERPTS FROM INTERNAL POLICIES:**
{context}

**YOUR TASK:**
Conduct a thorough gap analysis by answering these questions:

1. **Coverage Assessment**: Does any internal policy explicitly address this mandate?
2. **Adequacy Analysis**: If addressed, is the current policy sufficient to meet the regulatory requirement? Consider:
   - Scope and completeness
   - Specific deadlines or thresholds mentioned
   - Level of detail and clarity
   - Implementation mechanisms
3. **Gap Identification**: What specific elements are missing or insufficient?
4. **Risk Assessment**: What is the compliance risk if this gap is not addressed?

**OUTPUT FORMAT (be concise but thorough):**

**Compliance Status:** [Choose ONE: Fully Compliant | Partially Compliant | Non-Compliant | No Relevant Policy Found]

**Evidence Analysis:**
[2-3 sentences explaining what you found in internal policies and how it relates to the mandate]

**Gap Description:**
[Specific statement of what is missing or insufficient. Be concrete. If fully compliant, state "No gap identified."]

**Impacted Documents:**
[List specific document names and sections from the Source: tags in the context. If none, state "No directly relevant policy documents identified."]

**Recommended Action:**
[One concrete next step: e.g., "Draft new section in X policy addressing Y" or "No action required"]

**Confidence Score:** [0.0-1.0]
[How confident are you in this assessment? Consider clarity of both the mandate and internal policies]

**Risk Level:** [Low | Medium | High | Critical]"""

            try:
                analysis_result = llm_chat(prompt, max_tokens=8000)
                
                # Check for errors
                if not analysis_result or len(analysis_result.strip()) < 50:
                    analysis_result = "Error: LLM returned insufficient analysis."
                
                # Combine the mandate with its analysis for the final report
                full_finding = f"""
{'='*80}
MANDATE {idx}: {mandate_title}
{'='*80}

**Category:** {mandate_block.get('category', 'N/A')}

**Regulatory Requirement:**
{mandate_block.get('requirement', 'N/A')}

**Specifics:**
{mandate_block.get('specifics', 'N/A')}

**GAP ANALYSIS:**
{analysis_result}
"""
                findings.append(full_finding)
                print(f"  ✓ Analysis complete")
                
            except Exception as e:
                print(f"  ✗ Error analyzing mandate: {e}")
                findings.append(f"**Mandate {idx}:** {mandate_title}\n**Error:** Could not complete analysis - {str(e)}")
            
        return "\n\n".join(findings)
    
    def _parse_mandates(self, mandates_text):
        """
        Parse the structured mandate text into individual mandate dictionaries.
        Enhanced to handle various formatting styles.
        """
        mandates = []
        
        # Check for special cases first
        if "No actionable mandates" in mandates_text:
            return []
        
        # Try multiple splitting strategies
        # Strategy 1: Split by numbered items (1., 2., etc.)
        blocks = re.split(r'\n(?=\d+\.)', mandates_text)
        
        # Strategy 2: If that doesn't work, try splitting by "**Mandate:**"
        if len(blocks) <= 1:
            blocks = re.split(r'\n(?=\*\*Mandate:)', mandates_text)
        
        # Strategy 3: If still no luck, try splitting by "MANDATE" or "Mandate" headers
        if len(blocks) <= 1:
            blocks = re.split(r'\n(?=MANDATE|Mandate)', mandates_text, flags=re.IGNORECASE)
        
        for block in blocks:
            if not block.strip() or len(block.strip()) < 50:
                continue
            
            mandate = {}
            
            # Extract fields using regex with more flexible patterns
            title_match = re.search(r'\*\*Mandate:\*\*\s*(.+?)(?:\n|\*\*|$)', block, re.IGNORECASE)
            category_match = re.search(r'\*\*Category:\*\*\s*(.+?)(?:\n|\*\*|$)', block, re.IGNORECASE)
            requirement_match = re.search(r'\*\*Requirement:\*\*\s*(.+?)(?:\n\*\*|\n\n|$)', block, re.IGNORECASE | re.DOTALL)
            specifics_match = re.search(r'\*\*Specifics:\*\*\s*(.+?)(?:\n\*\*|\n\n|$)', block, re.IGNORECASE | re.DOTALL)
            
            # If structured format found, use it
            if title_match or requirement_match:
                mandate['title'] = title_match.group(1).strip() if title_match else block[:100].strip()
                mandate['category'] = category_match.group(1).strip() if category_match else 'Uncategorized'
                mandate['requirement'] = requirement_match.group(1).strip() if requirement_match else ''
                mandate['specifics'] = specifics_match.group(1).strip() if specifics_match else ''
                mandate['full_text'] = block.strip()
                mandates.append(mandate)
            else:
                # Fallback: treat entire block as a single mandate
                # Look for first sentence as title
                sentences = block.split('.')
                mandate['title'] = sentences[0][:100].strip() if sentences else block[:100].strip()
                mandate['category'] = 'Uncategorized'
                mandate['requirement'] = block.strip()
                mandate['specifics'] = ''
                mandate['full_text'] = block.strip()
                mandates.append(mandate)
        
        return mandates


class ComplianceReportAgent:
    def run_consolidated(self, all_regulations_data):
        """
        Generate a consolidated report covering multiple regulations.
        
        Args:
            all_regulations_data: List of dicts, each containing:
                - title, url, date, file_name, mandates, gap_analysis
        """
        print(f"=== Running Consolidated Compliance Report Agent ===")
        print(f"Processing {len(all_regulations_data)} regulation(s)...")
        
        # Build consolidated findings
        regulations_summary = []
        
        for idx, reg_data in enumerate(all_regulations_data, 1):
            reg_summary = f"""
{'='*80}
REGULATION {idx}: {reg_data['title']}
{'='*80}
Source: {reg_data['url']}
Date: {reg_data['date']}
File: {reg_data['file_name']}

EXTRACTED MANDATES:
{'-'*80}
{reg_data['mandates']}

GAP ANALYSIS FINDINGS:
{'-'*80}
{reg_data['gap_analysis']}
"""
            regulations_summary.append(reg_summary)
        
        consolidated_findings = "\n\n".join(regulations_summary)
        
        # Truncate if needed (but keep more content)
        max_findings_length = 150000
        if len(consolidated_findings) > max_findings_length:
            print(f"Warning: Consolidated findings too long ({len(consolidated_findings)} chars), truncating to {max_findings_length}")
            consolidated_findings = consolidated_findings[:max_findings_length] + "\n\n[...Additional findings truncated...]"
        
        prompt = f"""You are a Chief Compliance Officer preparing a comprehensive compliance report for executive leadership. This report consolidates the analysis of {len(all_regulations_data)} recent SEC regulations.

**ANALYSIS CONTEXT:**
- Number of Regulations Analyzed: {len(all_regulations_data)}
- Analysis Date: {datetime.now().strftime('%B %d, %Y')}
- Scope: Multi-regulation compliance gap analysis

**IMPORTANT:** Some regulations may be concept releases with no actionable mandates. Focus your report on regulations with actual compliance requirements.

**YOUR TASK:**
Create a comprehensive executive compliance report that synthesizes findings across all regulations. This is a strategic document for C-suite and Board review.

**REPORT STRUCTURE:**

================================================================================
EXECUTIVE SUMMARY
================================================================================

[Write 4-6 paragraphs covering:
1. Overview of the {len(all_regulations_data)} regulations analyzed and their strategic importance
2. Note which regulations are concept releases vs. final rules with mandates
3. Cross-cutting themes and patterns identified across regulations with mandates
4. Overall organizational compliance posture (aggregate statistics)
5. Top 3-5 most critical gaps requiring immediate executive attention
6. Strategic recommendations and resource implications
7. Estimated timeline and effort for full compliance]

================================================================================
REGULATIONS ANALYZED
================================================================================

[For each regulation, provide:
- Number and Title
- Type (Concept Release / Final Rule / Proposed Rule)
- Key focus areas (1-2 sentences)
- Number of mandates identified (0 if concept release)
- Overall compliance status if applicable]

================================================================================
CONSOLIDATED FINDINGS BY RISK LEVEL
================================================================================

**Note:** Only include findings from regulations with actionable mandates.

CRITICAL RISKS (Immediate Action Required)
{'-'*80}
[List all critical gaps across ALL regulations with mandates]

HIGH RISKS (30-Day Timeline)
{'-'*80}
[List all high-priority gaps]

MEDIUM RISKS (90-Day Timeline)
{'-'*80}
[Summary of medium-priority issues]

LOW RISKS & COMPLIANT ITEMS
{'-'*80}
[Brief summary]

================================================================================
RECOMMENDED ACTION PLAN
================================================================================

PHASE 1: IMMEDIATE (0-30 days)
{'-'*80}
[Specific actions for critical gaps]

PHASE 2: SHORT-TERM (1-3 months)
{'-'*80}
[Actions for high-priority items]

PHASE 3: LONG-TERM (3-6 months)
{'-'*80}
[Actions for medium-priority items]

================================================================================

**DETAILED FINDINGS TO SYNTHESIZE:**

{consolidated_findings}

================================================================================

Write the complete consolidated report now:"""

        try:
            final_report = llm_chat(prompt, max_tokens=8000)
            
            if not final_report or len(final_report.strip()) < 100:
                print("ERROR: LLM returned insufficient report")
                final_report = f"""ERROR: Could not generate comprehensive report.

Summary of regulations analyzed:
{chr(10).join([f"{i+1}. {reg['title']} - {reg['file_name']}" for i, reg in enumerate(all_regulations_data)])}

Please review the detailed findings in the appendices below."""
            
            print("✓ Consolidated compliance report generated")
            return final_report
            
        except Exception as e:
            print(f"ERROR generating report: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Error generating consolidated report: {str(e)}"
    
    
    def save_consolidated_report_as_text(self, report_text, output_path, all_regulations_data, timestamp):
        """
        Save the consolidated compliance report as a professionally formatted text file.
        """
        print(f"Generating consolidated text report: {output_path}")
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # Header
                f.write("="*80 + "\n")
                f.write("CONSOLIDATED COMPLIANCE GAP ANALYSIS REPORT\n")
                f.write("Multi-Regulation Assessment\n")
                f.write("="*80 + "\n\n")
                
                # Metadata
                f.write(f"Report Date:           {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")
                f.write(f"Regulations Analyzed:  {len(all_regulations_data)}\n")
                f.write(f"Analysis ID:           {timestamp}\n")
                f.write(f"Generated By:          AI Compliance Analysis System v1.0\n")
                f.write("\n" + "="*80 + "\n\n")
                
                # Regulations covered
                f.write("REGULATIONS COVERED IN THIS REPORT:\n")
                f.write("-"*80 + "\n")
                for idx, reg in enumerate(all_regulations_data, 1):
                    f.write(f"{idx}. {reg['title']}\n")
                    f.write(f"   File: {reg['file_name']}\n")
                    f.write(f"   Date: {reg['date']}\n")
                    f.write(f"   URL:  {reg['url']}\n\n")
                
                f.write("="*80 + "\n\n")
                
                # Main report content
                f.write(report_text)
                
                # Appendix: Detailed regulation-by-regulation findings
                f.write("\n\n" + "="*80 + "\n")
                f.write("APPENDIX: DETAILED FINDINGS BY REGULATION\n")
                f.write("="*80 + "\n\n")
                
                for idx, reg_data in enumerate(all_regulations_data, 1):
                    f.write(f"\n{'='*80}\n")
                    f.write(f"APPENDIX {idx}: {reg_data['title']}\n")
                    f.write(f"{'='*80}\n\n")
                    
                    f.write(f"Source:     {reg_data['url']}\n")
                    f.write(f"Date:       {reg_data['date']}\n")
                    f.write(f"File:       {reg_data['file_name']}\n\n")
                    
                    f.write(f"{'-'*80}\n")
                    f.write("EXTRACTED MANDATES:\n")
                    f.write(f"{'-'*80}\n\n")
                    f.write(reg_data['mandates'])
                    f.write("\n\n")
                    
                    f.write(f"{'-'*80}\n")
                    f.write("GAP ANALYSIS FINDINGS:\n")
                    f.write(f"{'-'*80}\n\n")
                    f.write(reg_data['gap_analysis'])
                    f.write("\n\n")
                
                # Footer
                f.write("\n" + "="*80 + "\n")
                f.write("END OF REPORT\n")
                f.write("="*80 + "\n")
            
            print(f"✓ Consolidated text report saved successfully")
            
        except Exception as e:
            print(f"✗ Error generating consolidated text report: {e}")
            import traceback
            traceback.print_exc()
            raise
