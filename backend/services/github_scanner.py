import re
import logging
import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from models.scan import ScanJob, ScanStatus
from models.finding import Finding
from services.github_api import GitHubAPI
from services.contract_extractor import extract_contracts
from services.policy_engine import PolicyEngine
from services.blast_radius import calculate_blast_radius, aggregate_blast_radius
from services.heatmap import aggregate_heatmap
from services.insights import compute_frameworks_summary, compute_hotspots, compute_risk_flags, compute_recommended_actions
from core.config import config

logger = logging.getLogger(__name__)

class GitHubScanner:
    def __init__(self, db: Session, access_token: str):
        self.db = db
        self.github_api = GitHubAPI(access_token)
        self.patterns = config.get_enabled_patterns()
        self.file_extensions = config.get_file_extensions()
        self.skip_paths = config.settings.get('scan', {}).get('skip_paths', [])
        self.priority_paths = config.settings.get('scan', {}).get('priority_paths', [])
        self.default_file_limit = config.settings.get('scan', {}).get('default_file_limit', 1000)
        self.parallel_workers = config.settings.get('scan', {}).get('parallel_workers', 10)
        self.policy_engine = PolicyEngine(config.policies.get('policies', {}))
        self.db_lock = threading.Lock()
    
    def scan_repo(self, scan_id: str, owner: str, repo: str, branch: str = 'main', full_scan: bool = False) -> Dict[str, Any]:
        scan_job = self.db.query(ScanJob).filter(ScanJob.id == scan_id).first()
        if not scan_job:
            raise ValueError(f"Scan job {scan_id} not found")
        
        scan_job.status = ScanStatus.RUNNING
        self.db.commit()
        
        try:
            logger.info(f"Fetching file tree for {owner}/{repo}@{branch}")
            tree = self.github_api.get_file_tree(owner, repo, branch)
            files_to_scan = self._filter_files(tree, full_scan)
            logger.info(f"Scanning {len(files_to_scan)} files with {self.parallel_workers} workers")
            
            findings = self._scan_files_parallel(files_to_scan, owner, repo, branch, scan_id)
            
            with self.db_lock:
                for finding_data in findings:
                    finding = Finding(**finding_data)
                    self.db.add(finding)
                self.db.commit()
            
            unique_files = list(set(f['file_path'] for f in findings))
            frameworks = list(set(f['framework'] for f in findings))
            
            summary_json = self._build_summary_json(findings)
            policies_result = self.policy_engine.evaluate(findings, frameworks)
            frameworks_summary = compute_frameworks_summary(findings)
            risk_flags = compute_risk_flags(findings, frameworks_summary)
            
            scan_job.status = ScanStatus.SUCCESS
            scan_job.total_occurrences = len(findings)
            scan_job.files_count = len(unique_files)
            scan_job.total_matches = len(findings)
            scan_job.ai_files_count = len(unique_files)
            scan_job.frameworks_json = json.dumps({fw: sum(1 for f in findings if f['framework'] == fw) for fw in frameworks})
            scan_job.risk_flags_json = json.dumps(risk_flags)
            scan_job.policies_result_json = json.dumps(policies_result)
            scan_job.summary_json = json.dumps(summary_json)
            self.db.commit()
            
            from services.scanner_v2 import ScannerV2
            scanner = ScannerV2(self.db)
            return scanner._build_response_v2(scan_job, findings)
            
        except Exception as e:
            logger.error(f"GitHub scan failed: {str(e)}")
            scan_job.status = ScanStatus.FAILED
            scan_job.error_message = str(e)
            self.db.commit()
            raise
    
    def _filter_files(self, tree: List[Dict], full_scan: bool) -> List[Dict]:
        priority_files = []
        other_files = []
        
        # Only apply skip_paths if repo has > 200 files (avoid over-filtering small repos)
        total_files = len([item for item in tree if item['type'] == 'blob'])
        apply_skip = total_files > 200
        
        for item in tree:
            if item['type'] != 'blob':
                continue
            path = item['path']
            if not any(path.endswith(ext) for ext in self.file_extensions):
                continue
            if not full_scan and apply_skip and self._should_skip(path):
                continue
            if item.get('size', 0) > 500000:
                continue
            
            if self._is_priority_file(path):
                priority_files.append(item)
            else:
                other_files.append(item)
        
        all_files = priority_files + other_files
        if not full_scan and len(all_files) > self.default_file_limit:
            return all_files[:self.default_file_limit]
        return all_files
    
    def _should_skip(self, path: str) -> bool:
        path_parts = path.lower().split('/')
        return any(skip in path_parts for skip in self.skip_paths)
    
    def _is_priority_file(self, path: str) -> bool:
        path_parts = path.lower().split('/')
        return any(priority in path_parts for priority in self.priority_paths)
    
    def _scan_files_parallel(self, files: List[Dict], owner: str, repo: str, branch: str, scan_id: str) -> List[Dict[str, Any]]:
        all_findings = []
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = {executor.submit(self._scan_single_file, f, owner, repo, branch, scan_id): f for f in files}
            for future in as_completed(futures):
                try:
                    all_findings.extend(future.result())
                except:
                    pass
        return all_findings
    
    def _scan_single_file(self, file_item: Dict, owner: str, repo: str, branch: str, scan_id: str) -> List[Dict[str, Any]]:
        findings = []
        file_path = file_item['path']
        
        try:
            content = self.github_api.get_file_content(owner, repo, file_path, branch)
            if not content:
                return findings
            
            lines = content.split('\\n')
            
            for line_num, line in enumerate(lines, start=1):
                for pattern_info in self.patterns:
                    if re.search(pattern_info['regex'], line):
                        snippet = self._extract_snippet(lines, line_num, pattern_info['regex'])
                        contracts = extract_contracts(snippet)
                        
                        findings.append({
                            'scan_id': scan_id,
                            'file_path': file_path,
                            'line_number': line_num,
                            'line_text': line.strip()[:500],
                            'framework': pattern_info['framework'],
                            'pattern_name': pattern_info['name'],
                            'pattern_category': pattern_info.get('category', 'misc'),
                            'pattern_severity': pattern_info.get('severity', 'low'),
                            'pattern_description': pattern_info.get('description', ''),
                            'snippet': snippet,
                            'model_name': contracts.get('model_name'),
                            'temperature': contracts.get('temperature'),
                            'max_tokens': contracts.get('max_tokens'),
                            'is_streaming': contracts.get('is_streaming'),
                            'has_tools': contracts.get('has_tools'),
                            'owner_name': None,
                            'owner_email': None,
                            'owner_committed_at': None
                        })
        except:
            pass
        return findings
    
    def _extract_snippet(self, lines: List[str], match_line: int, pattern: str) -> str:
        start_idx = max(0, match_line - 4)
        end_idx = min(len(lines), match_line + 3)
        snippet_lines = []
        for i in range(start_idx, end_idx):
            if i == match_line - 1 and i < len(lines):
                highlighted = re.sub(pattern, r'[[[HIT]]]\g<0>[[[ENDHIT]]]', lines[i].rstrip())
                snippet_lines.append(highlighted)
            elif i < len(lines):
                snippet_lines.append(lines[i].rstrip())
        return '\\n'.join(snippet_lines)
    
    def _build_summary_json(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        files_data = {}
        for finding in findings:
            file_path = finding['file_path']
            if file_path not in files_data:
                files_data[file_path] = {'matchCount': 0, 'frameworks': set(), 'categories': set(), 'blastRadius': 'low'}
            files_data[file_path]['matchCount'] += 1
            files_data[file_path]['frameworks'].add(finding['framework'])
            if finding.get('pattern_category'):
                files_data[file_path]['categories'].add(finding['pattern_category'])
        
        for file_path, data in files_data.items():
            data['blastRadius'] = calculate_blast_radius(file_path, data['matchCount'])
            data['frameworks'] = list(data['frameworks'])
            data['categories'] = list(data['categories'])
        
        directories = aggregate_heatmap(findings)
        return {'files': files_data, 'directories': directories}
