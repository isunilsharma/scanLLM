"""Contract extraction from code snippets"""
import re
from typing import Dict, Any, Optional

def extract_contracts(snippet: str) -> Dict[str, Any]:
    """
    Extract model contracts from code snippet.
    Looks for model=, temperature=, max_tokens=, stream=, tools=
    """
    contracts = {
        'model_name': None,
        'temperature': None,
        'max_tokens': None,
        'is_streaming': False,
        'has_tools': False
    }
    
    if not snippet:
        return contracts
    
    # Extract model name
    model_patterns = [
        r'model\s*=\s*["\']([^"\'
]+)["\']',
        r'"model"\s*:\s*"([^"]+)"',
        r"'model'\s*:\s*'([^']+)'"
    ]
    for pattern in model_patterns:
        match = re.search(pattern, snippet)
        if match:
            contracts['model_name'] = match.group(1)
            break
    
    # Extract temperature
    temp_patterns = [
        r'temperature\s*=\s*([0-9.]+)',
        r'"temperature"\s*:\s*([0-9.]+)',
        r"'temperature'\s*:\s*([0-9.]+)"
    ]
    for pattern in temp_patterns:
        match = re.search(pattern, snippet)
        if match:
            try:
                contracts['temperature'] = float(match.group(1))
                break
            except ValueError:
                pass
    
    # Extract max_tokens
    tokens_patterns = [
        r'max_tokens\s*=\s*([0-9]+)',
        r'"max_tokens"\s*:\s*([0-9]+)',
        r"'max_tokens'\s*:\s*([0-9]+)"
    ]
    for pattern in tokens_patterns:
        match = re.search(pattern, snippet)
        if match:
            try:
                contracts['max_tokens'] = int(match.group(1))
                break
            except ValueError:
                pass
    
    # Check for streaming
    if re.search(r'stream\s*=\s*True', snippet, re.IGNORECASE) or \
       re.search(r'"stream"\s*:\s*true', snippet, re.IGNORECASE):
        contracts['is_streaming'] = True
    
    # Check for tools
    if re.search(r'tools\s*=\s*\[', snippet) or \
       re.search(r'"tools"\s*:\s*\[', snippet) or \
       re.search(r'functions\s*=\s*\[', snippet):
        contracts['has_tools'] = True
    
    return contracts
