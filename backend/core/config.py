import yaml
from pathlib import Path
from typing import Dict, List, Any

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"

class Config:
    def __init__(self):
        self.patterns = self._load_yaml(CONFIG_DIR / "patterns.yml")
        self.settings = self._load_yaml(CONFIG_DIR / "settings.yml")
        self.policies = self._load_yaml(CONFIG_DIR / "policies.yml")
    
    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_enabled_patterns(self) -> List[Dict[str, Any]]:
        """Get all enabled patterns from config with full metadata"""
        enabled = []
        for framework, data in self.patterns.get('frameworks', {}).items():
            for pattern in data.get('patterns', []):
                if pattern.get('enabled', True):
                    enabled.append({
                        'framework': framework,
                        'name': pattern['name'],
                        'regex': pattern['regex'],
                        'category': pattern.get('category', 'misc'),
                        'severity': pattern.get('severity', 'low'),
                        'description': pattern.get('description', ''),
                        'tags': pattern.get('tags', [])
                    })
        return enabled
    
    def get_file_extensions(self) -> List[str]:
        return self.settings.get('scan', {}).get('file_extensions', [])
    
    def get_exclude_paths(self) -> List[str]:
        return self.settings.get('scan', {}).get('exclude_paths', [])
    
    def get_max_file_size(self) -> int:
        return self.settings.get('scan', {}).get('max_file_size_bytes', 500000)

config = Config()
