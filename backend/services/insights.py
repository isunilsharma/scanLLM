"""
Insights generation for scan results.
Computes risk flags, recommendations, and aggregations.
"""
from typing import List, Dict, Any
from collections import defaultdict

def get_directory_path(file_path: str, depth: int = 2) -> str:
    """Extract directory path up to specified depth"""
    parts = file_path.split('/')
    if len(parts) <= depth:
        return '/'.join(parts[:-1]) + '/' if len(parts) > 1 else ''
    return '/'.join(parts[:depth]) + '/'

def compute_frameworks_summary(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate findings by framework and category"""
    framework_data = defaultdict(lambda: {
        'total_matches': 0,
        'files': set(),
        'categories': defaultdict(int)
    })
    
    for finding in findings:
        fw = finding['framework']
        framework_data[fw]['total_matches'] += 1
        framework_data[fw]['files'].add(finding['file_path'])
        if finding.get('pattern_category'):
            framework_data[fw]['categories'][finding['pattern_category']] += 1
    
    summary = []
    for fw, data in sorted(framework_data.items()):
        categories = [
            {'category': cat, 'count': count}
            for cat, count in sorted(data['categories'].items(), key=lambda x: -x[1])
        ]
        summary.append({
            'framework': fw,
            'total_matches': data['total_matches'],
            'files_count': len(data['files']),
            'categories': categories
        })
    
    return sorted(summary, key=lambda x: -x['total_matches'])

def compute_hotspots(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify directories with highest AI usage"""
    directory_data = defaultdict(lambda: {
        'files': set(),
        'matches': 0
    })
    
    for finding in findings:
        directory = get_directory_path(finding['file_path'])
        directory_data[directory]['files'].add(finding['file_path'])
        directory_data[directory]['matches'] += 1
    
    hotspots = []
    for directory, data in directory_data.items():
        hotspots.append({
            'directory': directory or '(root)',
            'files_with_ai': len(data['files']),
            'total_matches': data['matches']
        })
    
    return sorted(hotspots, key=lambda x: -x['total_matches'])[:5]

def compute_risk_flags(findings: List[Dict[str, Any]], frameworks_summary: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute risk flags based on findings"""
    flags = []
    
    # Check for multiple frameworks
    if len(frameworks_summary) > 1:
        flags.append({
            'id': 'multiple_frameworks',
            'label': f'Multiple frameworks detected ({len(frameworks_summary)})',
            'severity': 'medium',
            'description': f'This repository uses {len(frameworks_summary)} different AI frameworks, which may complicate standardization and maintenance.'
        })
    
    # Check for secrets
    secrets_count = sum(1 for f in findings if f.get('pattern_category') == 'secrets')
    if secrets_count > 0:
        flags.append({
            'id': 'secrets_detected',
            'label': f'Possible API keys detected ({secrets_count} occurrences)',
            'severity': 'high',
            'description': 'Potential hard-coded API keys or secrets found in code. These should be rotated and moved to a secrets manager.'
        })
    
    # Check for embeddings
    embeddings_count = sum(1 for f in findings if f.get('pattern_category') == 'embedding_call')
    if embeddings_count > 0:
        flags.append({
            'id': 'embeddings_present',
            'label': f'Embeddings API usage detected ({embeddings_count} calls)',
            'severity': 'low',
            'description': 'This repository uses embedding APIs, which may indicate vector search or RAG patterns.'
        })
    
    # Check for RAG patterns
    rag_count = sum(1 for f in findings if f.get('pattern_category') == 'rag_pattern')
    if rag_count > 0:
        flags.append({
            'id': 'rag_present',
            'label': f'RAG patterns detected ({rag_count} occurrences)',
            'severity': 'medium',
            'description': 'Retrieval-Augmented Generation patterns found. Review data governance and retrieval quality.'
        })
    
    # Check for LLM-only (no embeddings or RAG)
    has_llm = any(f.get('pattern_category') == 'llm_call' for f in findings)
    has_embeddings = embeddings_count > 0
    has_rag = rag_count > 0
    
    if has_llm and not has_embeddings and not has_rag:
        flags.append({
            'id': 'llm_only_no_rag',
            'label': 'Only direct LLM calls (no RAG)',
            'severity': 'low',
            'description': 'This repository uses LLM calls but no embeddings or RAG patterns. Migration is likely simpler.'
        })
    
    return flags

def compute_recommended_actions(risk_flags: List[Dict[str, Any]], frameworks_summary: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate recommended actions based on risk flags"""
    actions = []
    risk_ids = {flag['id'] for flag in risk_flags}
    
    # Multiple frameworks
    if 'multiple_frameworks' in risk_ids:
        actions.append({
            'id': 'standardize_framework',
            'title': 'Standardize LLM framework usage',
            'description': f'This repo uses {len(frameworks_summary)} different AI frameworks. Consider consolidating onto one preferred stack and routing calls through a common gateway.',
            'related_risk_flags': ['multiple_frameworks']
        })
    
    # Secrets detected
    if 'secrets_detected' in risk_ids:
        actions.append({
            'id': 'rotate_secrets',
            'title': 'Rotate possible hard-coded keys',
            'description': 'Potential API keys were detected in code. Rotate these credentials immediately and move them into a secrets manager like AWS Secrets Manager or HashiCorp Vault.',
            'related_risk_flags': ['secrets_detected']
        })
    
    # RAG patterns
    if 'rag_present' in risk_ids or 'embeddings_present' in risk_ids:
        actions.append({
            'id': 'review_rag_governance',
            'title': 'Review RAG data governance',
            'description': 'RAG and embedding usage detected. Review what data is being embedded, how it is stored, and who has access. Consider implementing data governance policies.',
            'related_risk_flags': ['rag_present', 'embeddings_present']
        })
    
    # LLM only (simple migration target)
    if 'llm_only_no_rag' in risk_ids:
        actions.append({
            'id': 'simple_migration_target',
            'title': 'Good candidate for model migration',
            'description': 'This repo uses direct LLM calls without complex RAG patterns, making it a simpler target for model upgrades or provider changes.',
            'related_risk_flags': ['llm_only_no_rag']
        })
    
    # General standardization if no specific actions
    if not actions:
        actions.append({
            'id': 'establish_monitoring',
            'title': 'Establish AI usage monitoring',
            'description': 'Consider adding observability around LLM calls: latency tracking, token usage monitoring, and error rate tracking.',
            'related_risk_flags': []
        })
    
    return actions
