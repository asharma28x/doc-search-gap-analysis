# Document Search Gap Analysis Agent

## Introduction

An AI-powered SEC compliance automation system that monitors new regulatory filings, extracts actionable mandates, and performs gap analysis against internal company policies. The system features both a command-line interface and a user-friendly Streamlit web application with intelligent model management and robust error handling.

**NOTE** This is a submission for the NTT Data Agentic AI Campaign.

## Key Features

- **Automated SEC Monitoring**: Scrapes SEC.gov for latest rulemaking activities and downloads regulation PDFs
- **Intelligent Mandate Extraction**: Uses LLM to identify actionable compliance requirements from regulatory text with enhanced validation
- **RAG-based Gap Analysis**: Searches internal policy documents using vector embeddings (FAISS + SentenceTransformers)
- **Multi-Agent Architecture**: Specialized AI agents for monitoring, analysis, auditing, and reporting
- **Executive Reporting**: Generates comprehensive compliance reports with risk prioritization and action plans
- **Web Interface**: Streamlit app for easy document upload and analysis
- **Smart Model Management**: Automatic model downloading with multiple fallback strategies
- **Robust Error Handling**: Enhanced LLM response validation and informative error messages

## Architecture

The system uses a 4-agent pipeline:

1. **SECMonitoringAgent**: Extracts text from PDF documents
2. **RegulationAnalystAgent**: Identifies and structures regulatory mandates using LLM with validation
3. **InternalPolicyAuditorAgent**: Performs semantic search against internal policies and conducts gap analysis
4. **ComplianceReportAgent**: Synthesizes findings into executive-level reports

### Technical Components

**Core Processing:**
- **Document Processor**: PDF chunking, embedding generation, FAISS vector store management
- **LLM Service**: Custom NTT AI API integration with configurable token limits
- **SEC Downloader**: Web scraping and PDF retrieval from SEC.gov

**Model Management:**
- **Automatic Model Download**: Checks for local models and downloads if needed
- **Multiple Download Strategies**: Hugging Face CLI, Git clone, Python library fallback
- **Offline Support**: Uses local models when available to reduce bandwidth and latency

## Prerequisites

- Python 3.8+
- NTT AI API credentials (contact your administrator for `auth.py` and `ntt_secrets.py`)
- Internet connection (for initial model download and SEC.gov access)
- 2GB+ free disk space (for embedding models and vector stores)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/asharma28x/doc-search-gap-analysis/
cd doc-search-gap-analysis
```

### 2. Install Required Packages

```bash
pip install -r requirements.txt
```

**Required packages include:**
- `streamlit` - Web interface
- `pypdf` - PDF processing
- `beautifulsoup4` - Web scraping
- `sentence-transformers` - Text embeddings
- `faiss-cpu` - Vector similarity search
- `numpy` - Numerical operations
- `requests` - HTTP requests
- `langchain` and `langchain-core` - LLM framework

### 3. Set Up Authentication

Place these files in the project root (provided separately):

**`auth.py`** - Contains authentication function that returns API token

**`ntt_secrets.py`** - Contains credentials:
- `NTT_ID` - Your NTT AI ID
- `NTT_SECRET` - Your NTT AI secret key

⚠️ **Security Note**: Never commit these files to version control!

### 4. Initial Setup

On first run, the system will:
- Create necessary directories automatically
- Download the embedding model (`all-MiniLM-L6-v2`) to `./models/`
- This is a one-time ~100MB download

**Directories created:**
```
internal_docs/              # Your company policy PDFs
sec_rules_data/            # Downloaded SEC regulations
reports/                   # Generated compliance reports
vector_store/              # FAISS indices
models/                    # Embedding models
temp_internal_docs/        # Streamlit upload staging
temp_vector_store/         # Temporary vector stores
```

## Usage

### Option 1: Streamlit Web Application (Recommended)

Launch the interactive web interface:

```bash
streamlit run app.py
```

**Workflow:**

1. **Upload Internal Documents** 
   - Drag and drop your company's policy PDFs
   - Supports multiple files (max 200MB per file)
   - System creates vector embeddings automatically

2. **Select Regulation Source**
   - **Auto-fetch Mode**: 
     - Downloads latest regulations from SEC.gov
     - Use slider to select how many (1-10 regulations)
     - System tracks already-processed rules to avoid duplicates
   - **Manual Upload Mode**: 
     - Upload specific regulation PDFs
     - Useful for analyzing historical or specific regulations

3. **Run Analysis**
   - Click "Run Compliance Analysis" button
   - Progress bar shows real-time status:
     - Step 1: Processing internal documents
     - Step 2: Building vector store
     - Step 3: Obtaining regulations
     - Step 4: Analyzing and identifying gaps
     - Step 5: Generating consolidated report

4. **Review Results**
   - Preview report in the interface
   - Download full report as text file
   - Metrics show regulations analyzed and report size

**Features:**
- ✅ Real-time progress tracking
- ✅ Input validation with helpful messages
- ✅ Report preview and download
- ✅ Error messages with debugging details
- ✅ Support for concept releases vs. actionable rules

### Option 2: Command Line Interface

For automated/scheduled runs:

```bash
python main.py
```

**Process:**
1. Loads existing vector store or creates from `internal_docs/`
2. Checks SEC.gov for new regulations
3. Downloads new PDFs to `sec_rules_data/`
4. Analyzes all regulations in the folder
5. Generates consolidated report in `reports/`

**Use cases:**
- Scheduled cron jobs
- Batch processing
- Integration with CI/CD pipelines
- Automated compliance monitoring

## Project Structure

```
doc-search-gap-analysis/
├── app.py                      # Streamlit web interface
├── main.py                     # CLI orchestration pipeline
├── agents.py                   # AI agent implementations
├── document_processor.py       # Vector store and RAG logic
├── sec_rule_downloader.py      # SEC website scraper
├── llm_service.py              # LLM API wrapper
├── LLM.py                      # Custom LangChain LLM class
├── auth.py                     # Authentication (not in repo)
├── ntt_secrets.py              # API credentials (not in repo)
├── requirements.txt            # Python dependencies
│
├── utils/
│   └── model_downloader.py     # Model download management
│
├── models/                     # Downloaded embedding models
├── internal_docs/              # Company policy PDFs
├── sec_rules_data/             # Downloaded SEC regulation PDFs
├── vector_store/               # FAISS index and text chunks
├── temp_internal_docs/         # Temporary storage (Streamlit)
├── temp_vector_store/          # Temporary vector stores
└── reports/                    # Generated compliance reports
```

## Key Files Explained

### Core Application Files

**`app.py`** - Streamlit Web Interface
- File upload handling for internal docs and regulations
- Auto-fetch integration with SEC downloader
- Progress tracking and status updates
- Report preview and download
- Temporary file management with unique run IDs
- Writable directory detection for OneDrive/managed systems

**`main.py`** - Command-Line Interface
- Batch processing of all regulations
- Vector store management
- Consolidated report generation
- Integration with SEC monitoring

**`agents.py`** - AI Agent Implementations
- `SECMonitoringAgent`: PDF text extraction
- `RegulationAnalystAgent`: Mandate extraction with validation
- `InternalPolicyAuditorAgent`: Gap analysis with context search
- `ComplianceReportAgent`: Executive report generation
- Enhanced mandate parsing with multiple strategies
- Concept release detection

### Infrastructure Files

**`document_processor.py`** - Document Processing
- PDF loading and text chunking
- FAISS vector store creation and loading
- Integration with model downloader
- Configurable embedding model

**`sec_rule_downloader.py`** - SEC.gov Integration
- Web scraping of rulemaking activity page
- PDF link extraction from rule detail pages
- Rule tracking to avoid duplicates (stored in `processed_rules.json`)
- Metadata preservation (title, date, URL)

**`llm_service.py`** - LLM API Wrapper
- Simple interface for LLM calls
- Configurable token limits (default 4000, up to 8000)
- Model selection (GPT-4o-mini, Gemini 2.5 Flash, GPT-4o)

**`LLM.py`** - LangChain LLM Implementation
- Custom LLM wrapper for NTT AI API
- Enhanced response parsing with multiple strategies
- Error handling and timeout management
- Support for various response formats

**`utils/model_downloader.py`** - Model Management
- Checks for local model existence
- Three download strategies:
  1. Hugging Face CLI (preferred)
  2. Git clone (fallback)
  3. Python library (last resort)
- Automatic installation of dependencies
- Graceful fallback to online downloads

## Configuration

### LLM Settings

**Token Limits** (in `llm_service.py`):
```python
def llm_chat(prompt, max_tokens=4000):
    # Adjust max_tokens (up to 8000 supported)
```

**Model Selection** (in `llm_service.py`):
```python
model_id="a4022a51-2f02-4ba7-8a31-d33c7456b58e"  # Gemini 2.5 Flash (default)
# model_id="cc5bab32-9ccf-472b-9d76-91fc2ec5b047"  # GPT-4o-mini
# model_id="6c26a584-a988-4fed-92ea-f6501429fab9"  # GPT-4o
```

**Character Limits** (in `agents.py`):
```python
# RegulationAnalystAgent.run()
max_length = 100000  # Regulation text truncation

# ComplianceReportAgent.run_consolidated()
max_findings_length = 150000  # Consolidated findings truncation
```

### Document Processing

**Embedding Model** (in `document_processor.py`):
```python
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODELS_DIR = "./models"
```

**Vector Search** (in `agents.py`):
```python
k = 5  # Number of relevant chunks to retrieve per mandate
```

### SEC Monitoring

**Number of Regulations** (in `sec_rule_downloader.py`):
```python
def get_latest_rulemakings(self, limit=10):  # Adjust limit
```

**Rate Limiting** (in `sec_rule_downloader.py`):
```python
time.sleep(2)  # Seconds between SEC requests
```

## Output

### Report Format

The system generates comprehensive text reports with:

**1. Executive Summary**
- Cross-regulation patterns and themes
- Overall compliance posture
- Critical gaps requiring immediate attention
- Strategic recommendations and resource implications
- Timeline and effort estimates

**2. Regulations Analyzed**
- Regulation type (Concept Release / Final Rule / Proposed Rule)
- Key focus areas
- Number of mandates identified
- Overall compliance status

**3. Consolidated Findings by Risk Level**
- **Critical Risks**: Immediate action required
- **High Risks**: 30-day timeline
- **Medium Risks**: 90-day timeline
- **Low Risks & Compliant Items**: Summary

**4. Impacted Documents**
- List of internal policies requiring updates
- Specific sections referenced
- Evidence from policy text

**5. Recommended Action Plan**
- **Phase 1 (0-30 days)**: Critical gaps
- **Phase 2 (1-3 months)**: High-priority items
- **Phase 3 (3-6 months)**: Medium-priority items

**6. Appendices**
- Detailed mandate-by-mandate analysis for each regulation
- Full gap analysis findings
- Source references and evidence

### Sample Report Structure

```
================================================================================
CONSOLIDATED COMPLIANCE GAP ANALYSIS REPORT
Multi-Regulation Assessment
================================================================================

Report Date:           January 15, 2025 at 02:30 PM
Regulations Analyzed:  5
Analysis ID:           20250115_143000
Generated By:          AI Compliance Analysis System v1.0

================================================================================

REGULATIONS COVERED IN THIS REPORT:
--------------------------------------------------------------------------------
1. Enhanced Disclosure Requirements for Investment Advisers
   File: sec-rule-34-99123.pdf
   Date: 2025-01-10
   URL:  https://www.sec.gov/rules/...

[... Additional regulations ...]

================================================================================
EXECUTIVE SUMMARY
================================================================================

[4-6 paragraphs of strategic analysis]

================================================================================
CONSOLIDATED FINDINGS BY RISK LEVEL
================================================================================

CRITICAL RISKS (Immediate Action Required)
--------------------------------------------------------------------------------
[Specific gaps with high compliance risk]

[... Additional sections ...]

================================================================================
APPENDIX: DETAILED FINDINGS BY REGULATION
================================================================================

[Mandate-by-mandate analysis with evidence]
```

### File Naming

**Reports:**
```
reports/consolidated_compliance_report_YYYYMMDD_HHMMSS.txt
```

**Downloaded Regulations:**
```
sec_rules_data/sec-rule-34-99123.pdf
```

**Processed Rules Tracking:**
```
sec_rules_data/processed_rules.json
```

## Technical Stack

**AI/ML:**
- **LLM**: NTT AI API (Gemini 2.5 Flash / GPT-4o-mini / GPT-4o)
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- **Vector Store**: FAISS (Facebook AI Similarity Search)
- **Framework**: LangChain for LLM orchestration

**Document Processing:**
- **PDF Parsing**: pypdf
- **Text Processing**: NumPy for embeddings

**Web:**
- **Interface**: Streamlit
- **Scraping**: BeautifulSoup4
- **HTTP**: Requests library

**Storage:**
- **Vector Store**: FAISS binary indices + pickled text chunks
- **Tracking**: JSON files for processed rules
- **Reports**: Plain text files

## Security Notes

### Credentials Management

**Never commit sensitive files:**
```bash
# Add to .gitignore
auth.py
ntt_secrets.py
*.env
*.key
```

**Rotate API tokens periodically** - Update `ntt_secrets.py` every 90 days

### Report Handling

**Before sharing reports:**
1. Review for sensitive internal information
2. Redact proprietary policy details if needed
3. Check for personally identifiable information (PII)
4. Verify compliance with data handling policies

**Access Control:**
```bash
# Set restrictive permissions on reports
chmod 600 reports/*.txt
```

### API Security Best Practices

1. Use environment variables for production:
```python
import os
NTT_ID = os.getenv('NTT_ID')
NTT_SECRET = os.getenv('NTT_SECRET')
```

2. Monitor API usage and set up alerts
3. Review API logs regularly for anomalies

## Support

For issues or questions:
- Review the relevant file documentation in the "Key Files Explained" section
- Check console output for error messages and debugging information
- Contact your team administrator for API access issues
- Review the configuration section for customization options

## Contributors

This is a submission for the Agentic AI Campaign with NTT Data. The contributors for this are: Aditya Sharma, Aparna Sajith, Arun Mantripragada, Ben Head, Victoria Foo, Colin Hatt, Ismail Yigit, Bharath Chandran, Nitesh Chilakala, and Vinothkumar Sivabalan
