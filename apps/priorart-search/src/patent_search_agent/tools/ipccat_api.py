"""IPCCAT API tool for automatic IPC classification."""

import os
import xml.etree.ElementTree as ET
import requests
from typing import List, Dict, Any
import html


def escape_xml_text(text: str) -> str:
    """
    Escape special XML characters in text.
    
    Args:
        text: Text to escape
        
    Returns:
        XML-safe text
    """
    if not text:
        return ""
    
    # Use html.escape for basic escaping, then handle additional XML entities
    escaped = html.escape(text, quote=True)
    return escaped


def format_ipc_code(raw_code: str) -> str:
    """
    Format raw IPC code into standard format.
    
    Args:
        raw_code: Raw IPC code string
        
    Returns:
        Formatted IPC code
    """
    if not raw_code or len(raw_code) < 4:
        return raw_code
    
    # Remove any whitespace and make uppercase
    raw_code = raw_code.strip().upper()
    
    section = raw_code[0]
    class_ = raw_code[1:3]
    subclass = raw_code[3]
    
    # Handle cases where raw_code might be shorter
    if len(raw_code) >= 8:
        main_group = raw_code[4:8].lstrip('0') or '0'
        subgroup = raw_code[8:10] + raw_code[10:].rstrip('0') if len(raw_code) > 8 else '00'
        return f"{section}{class_}{subclass}{main_group}/{subgroup}"
    else:
        return f"{section}{class_}{subclass}"


def parse_predictions(xml_string: str) -> List[Dict[str, Any]]:
    """
    Parse XML response from IPC classification API.
    
    Args:
        xml_string: XML response string
        
    Returns:
        List of prediction dictionaries with rank, category, and score
    """
    try:
        root = ET.fromstring(xml_string)
        predictions = []
        
        for pred in root.findall('prediction'):
            rank = pred.find('rank').text if pred.find('rank') is not None else None
            category = pred.find('category').text if pred.find('category') is not None else None
            score = pred.find('score').text if pred.find('score') is not None else None
            
            predictions.append({
                "rank": int(rank) if rank is not None else None,
                "category": format_ipc_code(category) if category else None,
                "score": int(score) if score is not None else None
            })
        
        return predictions
    except Exception as e:
        print(f"Error parsing XML predictions: {str(e)}")
        return []


def get_ipc_classification(patent_summary: str) -> List[str]:
    """
    Get IPC classification codes using IPCCAT API.
    
    Args:
        patent_summary: Comprehensive patent summary text
        
    Returns:
        List of IPC classification codes
    """
    try:
        ipccat_api_url = os.getenv("IPCCAT_API_URL", "https://ipccat-data.epo.org/ipccat")
        
        if not ipccat_api_url:
            print("Warning: IPCCAT API URL not configured, using fallback classification")
            return _fallback_ipc_classification(patent_summary)
        
        # Prepare XML request as per WIPO IPC API format
        predictions_count = int(os.getenv("IPC_PREDICTIONS_COUNT", "5"))
        hierarchic_level = os.getenv("IPC_HIERARCHIC_LEVEL", "SUBGROUP")
        
        # Escape XML special characters in patent_summary
        escaped_summary = escape_xml_text(patent_summary)
        
        xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
<request>
  <lang>en</lang>
  <text>{escaped_summary}</text>
  <numberofpredictions>{predictions_count}</numberofpredictions>
  <hierarchiclevel>{hierarchic_level}</hierarchiclevel>
</request>"""
        
        headers = {
            'Content-Type': 'application/xml',
            'Accept': 'application/xml'
        }
        
        headers = {
            'Content-Type': 'application/xml'
        }
        
        response = requests.post(
            url=ipccat_api_url,
            data=xml_data,
            headers=headers,
        )

        print(f"IPC API Status: {response.status_code}")
        
        # Parse XML response
        predictions = parse_predictions(response.text)
        
        # Extract IPC codes from predictions
        ipc_codes = []
        for pred in predictions:
            if pred.get("category") and pred.get("score", 0) >= 500:  # Minimum score threshold
                code = pred["category"]
                ipc_codes.append(code)
        
        if ipc_codes:
            return list(set(ipc_codes))  # Remove duplicates
        else:
            return _fallback_ipc_classification(patent_summary)
            
    except Exception as e:
        print(f"Error calling IPCCAT API: {str(e)}")
        return _fallback_ipc_classification(patent_summary)

def _fallback_ipc_classification(patent_summary: str) -> List[str]:
    """
    Fallback IPC classification based on keyword analysis.
    
    Args:
        patent_summary: Patent summary text
        
    Returns:
        List of fallback IPC codes
    """
    summary_lower = patent_summary.lower()
    
    # Technology area mappings
    classifications = {
        # Computing and Information Technology
        "G06F": ["computer", "software", "data", "algorithm", "digital", "processing", "cpu"],
        "G06N": ["artificial intelligence", "machine learning", "neural network", "ai"],
        "G06Q": ["business", "commerce", "payment", "transaction", "e-commerce"],
        
        # Telecommunications
        "H04W": ["wireless", "cellular", "wifi", "bluetooth", "radio", "mobile"],
        "H04L": ["network", "internet", "protocol", "communication", "transmission"],
        "H04N": ["video", "audio", "multimedia", "broadcasting", "streaming"],
        
        # Measuring and Testing
        "G01D": ["measure", "sensor", "detect", "monitor", "gauge", "meter"],
        "G01C": ["navigation", "gps", "location", "positioning", "compass"],
        "G01N": ["analysis", "test", "examine", "spectroscopy", "chromatography"],
        
        # Healthcare and Medical
        "A61B": ["medical", "diagnosis", "surgery", "patient", "health", "clinical"],
        "A61K": ["medicine", "drug", "pharmaceutical", "therapy", "treatment"],
        "A61M": ["medical device", "infusion", "injection", "catheter"],
        
        # Control Systems
        "G05B": ["control", "regulate", "automatic", "system", "feedback"],
        "G05D": ["regulate", "automatic control", "servo", "motor control"],
        
        # Optics and Photography
        "G02B": ["optical", "lens", "mirror", "prism", "light", "photonic"],
        "H01S": ["laser", "maser", "optical amplifier", "light source"],
        
        # Transportation
        "B60W": ["vehicle", "automobile", "car", "driving", "automotive"],
        "B64C": ["aircraft", "airplane", "drone", "aviation", "flight"],
        
        # Energy and Power
        "H02J": ["power", "energy", "battery", "charging", "electrical grid"],
        "H01M": ["battery", "fuel cell", "electrochemical", "energy storage"],
        
        # User Interfaces
        "G06F3": ["interface", "input", "display", "touch", "keyboard", "mouse"],
        "G09G": ["display", "screen", "monitor", "graphics", "visual"],
        
        # Security and Cryptography
        "H04L9": ["security", "encryption", "cryptography", "authentication", "secure"],
        "G07C": ["access control", "identification", "security system", "lock"]
    }
    
    # Score each classification
    scores = {}
    for ipc_code, keywords in classifications.items():
        score = sum(1 for keyword in keywords if keyword in summary_lower)
        if score > 0:
            scores[ipc_code] = score
    
    # Return top scoring classifications
    sorted_codes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    result_codes = [code for code, score in sorted_codes[:5]]

    # Ensure at least one code
    if not result_codes:
        result_codes = ["G06F"]  # Default to general computing
    
    return result_codes
