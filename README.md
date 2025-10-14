# doc-search-gap-analysis

To create a new branch in github, use the command in terminal after opening the project in GitHub CodeSpaces:

```bash
git checkout -b <Branch-Name>
```

where ```<Branch-Name>``` should be the name of the feature you're coding up and adding to the repo. Commit and publish the branch using the VSCode sidebar after.

# Introduction

An AI-powered SEC compliance automation system that monitors new regulatory filings, extracts actionable mandates, and performs gap analysis against internal company policies. The system features both a command-line interface and a user-friendly Streamlit web application.

## Key Features

- **Automated SEC Monitoring**: Scrapes SEC.gov for latest rulemaking activities and downloads regulation PDFs
- **Intelligent Mandate Extraction**: Uses LLM to identify actionable compliance requirements from regulatory text
- **RAG-based Gap Analysis**: Searches internal policy documents using vector embeddings (FAISS + SentenceTransformers)
- **Multi-Agent Architecture**: Specialized AI agents for monitoring, analysis, auditing, and reporting
- **Executive Reporting**: Generates comprehensive compliance reports with risk prioritization and action plans
- **Web Interface**: Streamlit app for easy document upload and analysis

## Architecture

The system uses a 4-agent pipeline:

1. **SECMonitoringAgent**: Extracts text from PDF documents
2. **RegulationAnalystAgent**: Identifies and structures regulatory mandates using LLM
3. **InternalPolicyAuditorAgent**: Performs semantic search against internal policies and conducts gap analysis
4. **ComplianceReportAgent**: Synthesizes findings into executive-level reports

## Prerequisites

- Python 3.8+
- NTT AI API credentials (contact your administrator for `auth.py` and `ntt_secrets.py`)

## Installation

1. Clone the repository and navigate to the project directory

2. Install required Python packages:

```bash
pip install -r requirements.txt
```

3. Set up authentication files (provided separately):
   - `auth.py` - Contains authentication function
   - `ntt_secrets.py` - Contains NTT_ID credential

4. Create required directories (auto-created on first run):

```bash
mkdir internal_docs sec_rules_data reports vector_store
```

## Usage

### Option 1: Streamlit Web Application (Recommended)

Launch the interactive web interface:

```bash
streamlit run app.py
```

Then:
1. **Upload Internal Documents**: Drag and drop your company's policy PDFs
2. **Select Regulation Source**:
   - **Auto-fetch**: Automatically download latest regulations from SEC.gov
   - **Manual Upload**: Upload specific regulation PDFs
3. **Run Analysis**: Click "Run Compliance Analysis" button
4. **Download Report**: View preview and download the generated compliance report

### Option 2: Command Line Interface

For automated/scheduled runs:

```bash
python main.py
```

This will:
1. Load or create vector store from PDFs in `internal_docs/`
2. Check for new SEC regulations (downloads to `sec_rules_data/`)
3. Analyze all regulations in `sec_rules_data/`
4. Generate consolidated report in `reports/`

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
├── internal_docs/              # Place your company policy PDFs here
├── sec_rules_data/             # Downloaded SEC regulation PDFs
├── vector_store/               # FAISS index and text chunks
├── temp_internal_docs/         # Temporary storage (Streamlit uploads)
├── temp_vector_store/          # Temporary vector stores (Streamlit)
└── reports/                    # Generated compliance reports
```

## Key Files Explained

### Core Application Files

- **`app.py`**: Streamlit web interface with file upload, progress tracking, and report download
- **`main.py`**: Command-line version that processes all documents in folders
- **`agents.py`**: Contains the 4 specialized AI agents (Monitoring, Analyst, Auditor, Report)

### Infrastructure Files

- **`document_processor.py`**: Handles PDF chunking, embedding generation, and FAISS vector store creation
- **`sec_rule_downloader.py`**: Scrapes SEC.gov rulemaking page and downloads regulation PDFs
- **`llm_service.py`**: Simple wrapper for LLM API calls with configurable token limits
- **`LLM.py`**: LangChain-compatible custom LLM implementation for NTT AI API

### Configuration Files

- **`auth.py`**: Authentication function (returns API token)
- **`ntt_secrets.py`**: Contains `NTT_ID` constant for API identification
- **`requirements.txt`**: Python package dependencies

## Configuration

### LLM Settings

Token limits and model settings can be adjusted in `llm_service.py`:

```python
def llm_chat(prompt, max_tokens=8000):
    # Adjust max_tokens as needed (up to 8000)
```

### Document Processing

Character limits for regulation text can be modified in `agents.py`:

```python
# In RegulationAnalystAgent.run()
max_length = 100000  # Adjust as needed
```

### SEC Monitoring

Number of regulations to fetch in `sec_rule_downloader.py`:

```python
def get_latest_rulemakings(self, limit=10):  # Adjust limit
```

## Output

### Report Format

The system generates comprehensive text reports containing:

1. **Executive Summary**: Cross-regulation patterns, compliance posture, critical gaps
2. **Regulations Analyzed**: Overview of each regulation and mandate count
3. **Consolidated Findings**: Gaps organized by risk level (Critical/High/Medium/Low)
4. **Impacted Documents**: List of internal policies requiring updates
5. **Action Plan**: Phased recommendations with timelines (0-30, 1-3, 3-6 months)
6. **Appendices**: Detailed mandate-by-mandate analysis for each regulation

### Sample Report Location

Reports are saved to `reports/consolidated_compliance_report_YYYYMMDD_HHMMSS.txt`

## Technical Stack

- **LLM**: Custom NTT AI API (via LangChain wrapper)
- **Embeddings**: `sentence-transformers/static-retrieval-mrl-en-v1`
- **Vector Store**: FAISS (Facebook AI Similarity Search)
- **PDF Processing**: pypdf
- **Web Scraping**: BeautifulSoup4
- **Web Interface**: Streamlit
- **Data Processing**: NumPy, Pandas

## Troubleshooting

### Empty Mandate Extraction

If mandates aren't being extracted:
- Check that PDFs contain readable text (not scanned images)
- Increase `max_tokens` in `llm_service.py` if responses are truncated
- Verify API credentials in `auth.py` and `ntt_secrets.py`
- Check console output for LLM API error messages

### Vector Store Issues

If vector store creation fails:
- Ensure PDFs in `internal_docs/` contain extractable text
- Check available disk space (FAISS indices can be large)
- Delete `vector_store/` folder and recreate

### SEC Download Failures

If regulation downloads fail:
- Check internet connection
- Verify SEC.gov is accessible (may have rate limiting)
- Review `sec_rule_downloader.py` User-Agent string
- Try manual upload mode in Streamlit app

### Performance Issues

For large document sets:
- Reduce number of regulations analyzed
- Decrease vector store search parameter `k` (currently 5)
- Process documents in smaller batches
- Use shorter regulation PDFs for initial testing

## Development

### Adding New Agents

Create new agent classes in `agents.py` following the pattern:

```python
class NewAgent:
    def run(self, input_data):
        # Agent logic here
        return output_data
```

### Customizing Prompts

All LLM prompts are in `agents.py`. Modify the `prompt` variables in:
- `RegulationAnalystAgent.run()` - Mandate extraction
- `InternalPolicyAuditorAgent.run()` - Gap analysis
- `ComplianceReportAgent.run_consolidated()` - Report generation

### Changing Vector Store

To use a different embedding model, update `document_processor.py`:

```python
EMBEDDING_MODEL = "your-model-name"  # Must be compatible with sentence-transformers
```

## Security Notes

- **Never commit** `auth.py` or `ntt_secrets.py` to version control
- Add these files to `.gitignore`
- API tokens should be rotated periodically
- Ensure compliance reports don't contain sensitive internal information before sharing

## Contributing

1. Create a feature branch: `git checkout -b feature-name`
2. Make changes and test thoroughly
3. Commit with descriptive messages
4. Push branch and create pull request
5. Request review from team members


## Support

For issues or questions:
- Check the Troubleshooting section above
- Review console output for error messages
- Contact your team administrator for API access issues
