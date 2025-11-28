"""Blast radius calculation"""
from typing import Dict, Any, List
import re

def calculate_blast_radius(file_path: str, match_count: int, file_content: str = None) -> str:
    """
    Calculate blast radius for a file based on:
    - Number of AI matches
    - Whether it's a critical path (/api/, /service/, /jobs/)
    - Import complexity
    """
    # Check if critical path
    critical_patterns = ['/api/', '/service/', '/jobs/', '/core/', '/lib/']
    is_critical = any(pattern in file_path.lower() for pattern in critical_patterns)
    
    # Count imports if content available
    import_count = 0
    if file_content:
        import_lines = re.findall(r'^\s*(import |from )', file_content, re.MULTILINE)
        import_count = len(import_lines)
    
    # Calculate blast radius
    if is_critical and match_count > 5:
        return "high"
    elif is_critical and match_count > 2:
        return "medium"
    elif match_count > 10:
        return "high"
    elif match_count > 2:
        return "medium"
    else:
        return "low"

def aggregate_blast_radius(files_data: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    """
    Aggregate blast radius counts.
    Returns counts of high/medium/low risk files.
    """
    counts = {'high': 0, 'medium': 0, 'low': 0}
    
    for file_data in files_data.values():
        blast_radius = file_data.get('blastRadius', 'low')
        counts[blast_radius] = counts.get(blast_radius, 0) + 1
    
    return counts
