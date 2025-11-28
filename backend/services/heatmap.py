"""Heatmap aggregation for directory-level AI usage"""
from typing import Dict, Any, List
from collections import defaultdict

def aggregate_heatmap(findings: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """
    Aggregate AI usage by directory.
    Returns directory -> {files, matches}
    """
    directory_data = defaultdict(lambda: {
        'files': set(),
        'matches': 0
    })
    
    for finding in findings:
        file_path = finding.get('file_path', '')
        
        # Extract directory (up to 2 levels)
        parts = file_path.split('/')
        if len(parts) <= 1:
            directory = '(root)'
        elif len(parts) == 2:
            directory = parts[0] + '/'
        else:
            directory = '/'.join(parts[:2]) + '/'
        
        directory_data[directory]['files'].add(file_path)
        directory_data[directory]['matches'] += 1
    
    # Convert sets to counts
    result = {}
    for directory, data in directory_data.items():
        result[directory] = {
            'files': len(data['files']),
            'matches': data['matches']
        }
    
    # Sort by matches descending
    result = dict(sorted(result.items(), key=lambda x: -x[1]['matches']))
    
    return result
