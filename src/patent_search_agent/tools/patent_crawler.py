"""Patent crawler tool for extracting detailed patent information."""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import time
import re


def crawl_patent_details(patent_url: str) -> Dict[str, Any]:
    """
    Crawl detailed patent information from Google Patents URL.
    
    This is a template implementation that should be replaced with
    your existing patent crawling logic.
    
    Args:
        patent_url: URL of the patent on Google Patents
        
    Returns:
        Dictionary with detailed patent information
    """
    try:
        # Add delay to be respectful to the server
        time.sleep(1)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(patent_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract patent information
        patent_info = {
            "url": patent_url,
            "patent_number": _extract_patent_number(soup, patent_url),
            "title": _extract_title(soup),
            "abstract": _extract_abstract(soup),
            "description": _extract_description(soup),
            "claims": _extract_claims(soup),
            "inventors": _extract_inventors(soup),
            "assignee": _extract_assignee(soup),
            "publication_date": _extract_publication_date(soup),
            "application_date": _extract_application_date(soup),
            "ipc_codes": _extract_ipc_codes(soup),
            "cpc_codes": _extract_cpc_codes(soup),
            "references": _extract_references(soup),
            "cited_by": _extract_cited_by(soup),
            "family_patents": _extract_family_patents(soup)
        }
        
        return patent_info
        
    except Exception as e:
        print(f"Error crawling patent {patent_url}: {str(e)}")
        return _fallback_patent_info(patent_url)


def _extract_patent_number(soup: BeautifulSoup, url: str) -> str:
    """Extract patent number from the page."""
    try:
        # Try multiple selectors for patent number
        selectors = [
            '[data-proto="PATENT_NUMBER"]',
            '.patent-number',
            '[data-test="patent-number"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        # Fallback: extract from URL
        if "/patent/" in url:
            return url.split("/patent/")[-1].split("?")[0]
            
        return ""
        
    except Exception:
        return ""


def _extract_title(soup: BeautifulSoup) -> str:
    """Extract patent title."""
    try:
        selectors = [
            'h1[data-proto="TITLE"]',
            '.patent-title',
            'h1.title',
            'h1'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
                
        return ""
        
    except Exception:
        return ""


def _extract_abstract(soup: BeautifulSoup) -> str:
    """Extract patent abstract."""
    try:
        selectors = [
            '[data-proto="ABSTRACT"]',
            '.abstract',
            '.patent-abstract'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
                
        return ""
        
    except Exception:
        return ""


def _extract_description(soup: BeautifulSoup) -> str:
    """Extract patent description."""
    try:
        selectors = [
            '[data-proto="DESCRIPTION"]',
            '.description',
            '.patent-description'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # Get first 1000 characters to avoid too much text
                text = element.get_text(strip=True)
                return text[:1000] + "..." if len(text) > 1000 else text
                
        return ""
        
    except Exception:
        return ""


def _extract_claims(soup: BeautifulSoup) -> List[str]:
    """Extract patent claims."""
    try:
        claims = []
        
        # Look for claims section
        claims_section = soup.find(attrs={"data-proto": "CLAIMS"}) or soup.find(class_="claims")
        
        if claims_section:
            # Extract individual claims
            claim_elements = claims_section.find_all(["div", "p"], class_=re.compile("claim"))
            
            for claim in claim_elements:
                claim_text = claim.get_text(strip=True)
                if claim_text and len(claim_text) > 10:  # Filter out very short text
                    claims.append(claim_text)
        
        return claims[:10]  # Limit to first 10 claims
        
    except Exception:
        return []


def _extract_inventors(soup: BeautifulSoup) -> str:
    """Extract inventor names."""
    try:
        selectors = [
            '[data-proto="INVENTOR"]',
            '.inventors',
            '.patent-inventors'
        ]
        
        inventors = []
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                inventor = element.get_text(strip=True)
                if inventor:
                    inventors.append(inventor)
        
        return "; ".join(inventors) if inventors else ""
        
    except Exception:
        return ""


def _extract_assignee(soup: BeautifulSoup) -> str:
    """Extract assignee/company name."""
    try:
        selectors = [
            '[data-proto="ASSIGNEE"]',
            '.assignee',
            '.patent-assignee'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
                
        return ""
        
    except Exception:
        return ""


def _extract_publication_date(soup: BeautifulSoup) -> str:
    """Extract publication date."""
    try:
        selectors = [
            '[data-proto="PUBLICATION_DATE"]',
            '.publication-date',
            '.patent-date'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                date_text = element.get_text(strip=True)
                # Try to normalize date format
                return _normalize_date(date_text)
                
        return ""
        
    except Exception:
        return ""


def _extract_application_date(soup: BeautifulSoup) -> str:
    """Extract application date."""
    try:
        selectors = [
            '[data-proto="APPLICATION_DATE"]',
            '.application-date',
            '.filing-date'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                date_text = element.get_text(strip=True)
                return _normalize_date(date_text)
                
        return ""
        
    except Exception:
        return ""


def _extract_ipc_codes(soup: BeautifulSoup) -> List[str]:
    """Extract IPC classification codes."""
    try:
        codes = []
        
        # Look for IPC codes in various locations
        ipc_elements = soup.find_all(text=re.compile(r'[A-H]\d{2}[A-Z]'))
        
        for element in ipc_elements:
            # Extract IPC codes using regex
            ipc_matches = re.findall(r'[A-H]\d{2}[A-Z]\d*(?:/\d+)*', element)
            codes.extend(ipc_matches)
        
        return list(set(codes))  # Remove duplicates
        
    except Exception:
        return []


def _extract_cpc_codes(soup: BeautifulSoup) -> List[str]:
    """Extract CPC classification codes."""
    try:
        codes = []
        
        # Look for CPC codes (similar to IPC but with different pattern)
        cpc_elements = soup.find_all(text=re.compile(r'[A-H]\d{2}[A-Z]'))
        
        for element in cpc_elements:
            cpc_matches = re.findall(r'[A-H]\d{2}[A-Z]\d+/\d+', element)
            codes.extend(cpc_matches)
        
        return list(set(codes))
        
    except Exception:
        return []


def _extract_references(soup: BeautifulSoup) -> List[str]:
    """Extract cited references."""
    try:
        references = []
        
        # Look for references section
        refs_section = soup.find(attrs={"data-proto": "REFERENCES"}) or soup.find(class_="references")
        
        if refs_section:
            # Extract patent numbers from references
            ref_links = refs_section.find_all("a", href=re.compile(r"/patent/"))
            
            for link in ref_links:
                href = link.get("href", "")
                if "/patent/" in href:
                    patent_num = href.split("/patent/")[-1].split("?")[0]
                    references.append(patent_num)
        
        return references[:20]  # Limit to 20 references
        
    except Exception:
        return []


def _extract_cited_by(soup: BeautifulSoup) -> List[str]:
    """Extract patents that cite this patent."""
    try:
        # This would typically require additional API calls or parsing
        # For now, return empty list
        return []
        
    except Exception:
        return []


def _extract_family_patents(soup: BeautifulSoup) -> List[str]:
    """Extract patent family members."""
    try:
        family = []
        
        # Look for patent family section
        family_section = soup.find(attrs={"data-proto": "FAMILY"}) or soup.find(class_="family")
        
        if family_section:
            family_links = family_section.find_all("a", href=re.compile(r"/patent/"))
            
            for link in family_links:
                href = link.get("href", "")
                if "/patent/" in href:
                    patent_num = href.split("/patent/")[-1].split("?")[0]
                    family.append(patent_num)
        
        return family
        
    except Exception:
        return []


def _normalize_date(date_text: str) -> str:
    """Normalize date format."""
    try:
        # Remove common prefixes/suffixes
        date_text = re.sub(r'(Publication date|Filing date|Date):\s*', '', date_text, flags=re.IGNORECASE)
        
        # Extract date patterns
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
            r'\w+ \d{1,2}, \d{4}'  # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_text)
            if match:
                return match.group(0)
        
        return date_text.strip()
        
    except Exception:
        return date_text


def _fallback_patent_info(patent_url: str) -> Dict[str, Any]:
    """Return fallback patent info when crawling fails."""
    return {
        "url": patent_url,
        "patent_number": "",
        "title": "Unable to crawl patent details",
        "abstract": "Crawling failed - please check manually",
        "description": "",
        "claims": [],
        "inventors": "",
        "assignee": "",
        "publication_date": "",
        "application_date": "",
        "ipc_codes": [],
        "cpc_codes": [],
        "references": [],
        "cited_by": [],
        "family_patents": [],
        "crawl_error": True
    }
