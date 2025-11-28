"""Policy evaluation engine"""
import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class PolicyEngine:
    def __init__(self, policy_config: Dict[str, Any]):
        self.forbid_frameworks = policy_config.get('forbid_frameworks', [])
        self.warn_models = policy_config.get('warn_models', [])
        self.require_env_keys = policy_config.get('require_env_keys', True)
    
    def evaluate(self, findings: List[Dict[str, Any]], frameworks: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Evaluate policies against scan findings.
        Returns errors, warnings, and passes.
        """
        errors = []
        warnings = []
        passes = []
        
        # Check forbidden frameworks
        for framework in frameworks:
            if framework in self.forbid_frameworks:
                errors.append({
                    'rule': 'forbid_frameworks',
                    'message': f'Forbidden framework detected: {framework}',
                    'severity': 'high'
                })
        
        if not any(f in self.forbid_frameworks for f in frameworks):
            passes.append({
                'rule': 'forbid_frameworks',
                'message': 'No forbidden frameworks detected'
            })
        
        # Check for warned models
        detected_models = set()
        for finding in findings:
            if finding.get('model_name'):
                detected_models.add(finding['model_name'])
        
        for model in detected_models:
            if model in self.warn_models:
                warnings.append({
                    'rule': 'warn_models',
                    'message': f'Deprecated or warned model in use: {model}',
                    'severity': 'medium'
                })
        
        # Check for hard-coded keys/secrets
        if self.require_env_keys:
            secrets_count = sum(1 for f in findings if f.get('pattern_category') == 'secrets')
            
            if secrets_count > 0:
                errors.append({
                    'rule': 'require_env_keys',
                    'message': f'Potential hard-coded API keys detected ({secrets_count} occurrences)',
                    'severity': 'critical'
                })
            else:
                passes.append({
                    'rule': 'require_env_keys',
                    'message': 'No hard-coded secrets detected'
                })
        
        return {
            'errors': errors,
            'warnings': warnings,
            'passes': passes
        }
