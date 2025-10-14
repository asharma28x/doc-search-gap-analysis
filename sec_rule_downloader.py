import requests
from bs4 import BeautifulSoup
import pypdf
import io
import json
import time
from datetime import datetime
from pathlib import Path

class SECRulemakingMonitor:
    """
    Monitor SEC rulemaking activities and download new regulations.
    
    How it works:
    1. Scrapes the SEC rulemaking activity page
    2. Extracts the latest rulemakings
    3. Downloads PDFs of new rules
    4. Tracks which rules have been processed
    """
    
    def __init__(self, storage_path="sec_rules"):
        self.base_url = "https://www.sec.gov"
        self.rulemaking_url = f"{self.base_url}/rules-regulations/rulemaking-activity"
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.processed_rules_file = self.storage_path / "processed_rules.json"
        self.headers = {
            'User-Agent': 'Regulations ComplianceBot/1.0 (aditya28.sharma@nttdata.com)'
        }
        self.processed_rules = self._load_processed_rules()
    
    def _load_processed_rules(self):
        """Load list of already processed rules"""
        if self.processed_rules_file.exists():
            with open(self.processed_rules_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_processed_rules(self):
        """Save list of processed rules"""
        with open(self.processed_rules_file, 'w') as f:
            json.dump(self.processed_rules, f, indent=2)
    
    def get_latest_rulemakings(self, limit=10):
        """
        Scrape the rulemaking activity page for latest rules.
        
        Returns list of dicts with: title, url, date, release_number
        """
        print(f"Fetching rulemaking activity from {self.rulemaking_url}")
        
        response = requests.get(self.rulemaking_url, headers=self.headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all rulemaking entries
        # The structure may vary, so we look for links in the main content
        rulemakings = []
        
        # Look for articles or list items containing rule information
        # SEC typically uses specific CSS classes or structures
        content_area = soup.find('div', class_='view-content') or soup.find('main')
        
        if content_area:
            # Find all links that look like rule pages
            rule_links = content_area.find_all('a', href=lambda x: x and '/rules-regulations/20' in x)
            
            for link in rule_links[:limit]:
                href = link.get('href')
                if not href.startswith('http'):
                    href = self.base_url + href
                
                # Extract title
                title = link.get_text(strip=True)
                
                # Try to extract date from URL or surrounding text
                date_str = None
                parent = link.find_parent(['div', 'article', 'li'])
                if parent:
                    date_elem = parent.find('time') or parent.find(class_='date')
                    if date_elem:
                        date_str = date_elem.get_text(strip=True)
                
                rulemakings.append({
                    'title': title,
                    'url': href,
                    'date': date_str,
                    'fetched_at': datetime.now().isoformat()
                })
        
        print(f"Found {len(rulemakings)} rulemakings")
        return rulemakings
    
    def extract_pdf_link(self, rule_page_url):
        """
        Extract PDF download link from a rule's detail page.
        
        Example: https://www.sec.gov/rules-regulations/2025/09/...
        Returns: https://www.sec.gov/files/rules/final/2024/34-99679.pdf
        """
        print(f"Extracting PDF link from {rule_page_url}")
        
        response = requests.get(rule_page_url, headers=self.headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for PDF links - SEC typically labels them clearly
        pdf_links = []
        
        # Strategy 1: Find links with "pdf" in href
        for link in soup.find_all('a', href=lambda x: x and '.pdf' in x.lower()):
            href = link.get('href')
            if not href.startswith('http'):
                href = self.base_url + href
            
            link_text = link.get_text(strip=True).lower()
            
            # Prioritize "final rule" or "full document" links
            priority = 0
            if 'final' in link_text or 'full' in link_text or 'complete' in link_text:
                priority = 2
            elif 'rule' in link_text or 'document' in link_text:
                priority = 1
            
            pdf_links.append((priority, href, link_text))
        
        # Strategy 2: Look in the page metadata for release numbers
        release_num = None
        if '#' in rule_page_url:
            release_num = rule_page_url.split('#')[-1]
        
        # Sort by priority and return the best match
        if pdf_links:
            pdf_links.sort(reverse=True)
            return pdf_links[0][1]
        
        return None
    
    def download_pdf(self, pdf_url, filename=None):
        """Download PDF and return content"""
        print(f"Downloading PDF from {pdf_url}")
        
        response = requests.get(pdf_url, headers=self.headers)
        response.raise_for_status()
        
        # Save to file
        if filename is None:
            filename = pdf_url.split('/')[-1]
        
        filepath = self.storage_path / filename
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"Saved PDF to {filepath}")
        return response.content, filepath
    
    def extract_first_paragraph(self, pdf_content):
        """Extract and return first paragraph from PDF"""
        pdf_file = io.BytesIO(pdf_content)
        
        try:
            pdf_reader = pypdf.PdfReader(pdf_file)
            
            # Extract text from first few pages
            text = ""
            for page_num in range(min(3, len(pdf_reader.pages))):
                text += pdf_reader.pages[page_num].extract_text()
            
            # Find first substantial paragraph
            paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 100]
            
            if paragraphs:
                return paragraphs[0]
            else:
                # Fallback: return first 500 characters
                return text[:500].strip()
                
        except Exception as e:
            print(f"Error extracting text: {e}")
            return None
    
    def process_new_rules(self):
        """
        Main method: Check for new rules and process them.
        Returns list of newly processed rules with their data.
        """
        new_rules_processed = []
        
        # Get latest rulemakings
        rulemakings = self.get_latest_rulemakings(limit=5)
        
        for rule in rulemakings:
            rule_id = rule['url']
            
            # Skip if already processed
            if rule_id in self.processed_rules:
                print(f"Already processed: {rule['title'][:50]}...")
                continue
            
            print(f"\n{'='*80}")
            print(f"NEW RULE FOUND: {rule['title']}")
            print(f"URL: {rule['url']}")
            print(f"{'='*80}\n")
            
            try:
                # Extract PDF link
                pdf_url = self.extract_pdf_link(rule['url'])
                
                if not pdf_url:
                    print("Could not find PDF link, skipping...")
                    continue
                
                # Download PDF
                pdf_content, filepath = self.download_pdf(pdf_url)
                
                # Extract first paragraph
                first_paragraph = self.extract_first_paragraph(pdf_content)
                
                if first_paragraph:
                    print("\n--- FIRST PARAGRAPH ---")
                    print(first_paragraph)
                    print("\n" + "-"*80 + "\n")
                
                # Store rule information
                rule_data = {
                    **rule,
                    'pdf_url': pdf_url,
                    'pdf_path': str(filepath),
                    'first_paragraph': first_paragraph,
                    'processed_at': datetime.now().isoformat()
                }
                
                new_rules_processed.append(rule_data)
                
                # Mark as processed
                self.processed_rules.append(rule_id)
                self._save_processed_rules()
                
                
                print(f"✓ Successfully processed rule")
                
            except Exception as e:
                print(f"Error processing rule: {e}")
                continue
            
            # Be respectful to SEC servers
            time.sleep(2)
        
        return new_rules_processed
