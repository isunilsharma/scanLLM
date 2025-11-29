"""
Enhanced Scanner v2 with ownership mapping, contract extraction, blast radius, and policy evaluation
"""
import re
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from models.scan import ScanJob, ScanStatus
from models.finding import Finding
from services.git_utils import GitUtils
from services.contract_extractor import extract_contracts
from services.ownership_mapper import OwnershipMapper
from services.policy_engine import PolicyEngine
from services.blast_radius import calculate_blast_radius, aggregate_blast_radius
from services.heatmap import aggregate_heatmap
from services.insights import (
    compute_frameworks_summary,
    compute_hotspots,
    compute_risk_flags,
    compute_recommended_actions
)
from core.config import config

logger = logging.getLogger(__name__)

class ScannerV2:
    def __init__(self, db: Session):
        self.db = db
        self.patterns = config.get_enabled_patterns()
        self.file_extensions = config.get_file_extensions()
        self.exclude_paths = config.get_exclude_paths()
        self.max_file_size = config.get_max_file_size()
        self.ownership_mapper = OwnershipMapper()
        self.policy_engine = PolicyEngine(config.policies.get('policies', {}))
    
    def scan_repository(self, scan_id: str, repo_url: str) -> Dict[str, Any]:
        """
        Main scanning logic with v2 enhancements
        """
        scan_job = self.db.query(ScanJob).filter(ScanJob.id == scan_id).first()
        if not scan_job:
            raise ValueError(f"Scan job {scan_id} not found")
        
        scan_job.status = ScanStatus.RUNNING
        self.db.commit()
        
        repo_path = None
        try:
            # Clone repository
            repo_path = GitUtils.clone_repo(
                repo_url,
                shallow=config.settings['git']['shallow_clone'],
                depth=config.settings['git']['depth']
            )
            
            if not repo_path:
                raise Exception("Failed to clone repository")
            
            # Scan files and extract contracts
            findings = self._scan_directory_v2(repo_path, scan_id, repo_url)
            
            # Store findings
            for finding_data in findings:
                finding = Finding(**finding_data)
                self.db.add(finding)
            
            self.db.commit()
            
            # Compute aggregations
            unique_files = list(set(f['file_path'] for f in findings))
            frameworks = list(set(f['framework'] for f in findings))
            
            # Build summary JSON with all v2 features
            summary_json = self._build_summary_json(findings, repo_path)
            
            # Evaluate policies
            policies_result = self.policy_engine.evaluate(findings, frameworks)
            
            # Compute risk flags (enhanced with blast radius)
            frameworks_summary = compute_frameworks_summary(findings)
            risk_flags = compute_risk_flags(findings, frameworks_summary)
            
            # Add blast radius risk if high-risk files exist
            high_blast_count = sum(1 for f in summary_json['files'].values() if f.get('blastRadius') == 'high')
            if high_blast_count > 0:
                risk_flags.append({
                    'id': 'high_blast_files_exist',
                    'label': f'High-impact files with AI usage ({high_blast_count} files)',
                    'severity': 'high',
                    'description': f'Found {high_blast_count} critical files (api/, service/, jobs/) with significant AI usage. Changes could have wide impact.'
                })
            
            # Update scan job with v2 fields
            scan_job.status = ScanStatus.SUCCESS
            scan_job.total_occurrences = len(findings)
            scan_job.files_count = len(unique_files)
            scan_job.total_matches = len(findings)
            scan_job.ai_files_count = len(unique_files)
            scan_job.frameworks_json = json.dumps({fw: findings.count(fw) for fw in frameworks})
            scan_job.risk_flags_json = json.dumps(risk_flags)
            scan_job.policies_result_json = json.dumps(policies_result)
            scan_job.summary_json = json.dumps(summary_json)
            
            self.db.commit()
            
            # Build response
            return self._build_response_v2(scan_job, findings)
            
        except Exception as e:
            logger.error(f"Scan failed: {str(e)}")
            scan_job.status = ScanStatus.FAILED
            scan_job.error_message = str(e)
            self.db.commit()
            raise
        
        finally:
            if repo_path:
                GitUtils.cleanup_repo(repo_path)
    
    def _scan_directory_v2(self, root_path: Path, scan_id: str, repo_url: str) -> List[Dict[str, Any]]:
        """
        Scan directory with v2 enhancements: contract extraction and ownership mapping
        """
        findings = []
        file_contents = {}  # Cache for blast radius calculation
        
        for file_path in root_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            # Check if file should be excluded
            if self._should_exclude(file_path, root_path):
                continue
            
            # Check file extension
            if file_path.suffix not in self.file_extensions:
                continue
            
            # Check file size
            try:
                if file_path.stat().st_size > self.max_file_size:
                    logger.debug(f"Skipping large file: {file_path}")
                    continue
            except OSError:
                continue
            
            # Scan file with v2 enhancements
            file_findings = self._scan_file_v2(file_path, root_path, scan_id, repo_url)
            findings.extend(file_findings)
            
            # Cache file content for blast radius
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_contents[str(file_path.relative_to(root_path))] = f.read()
            except Exception:
                pass
        
        return findings
    
    def _should_exclude(self, file_path: Path, root_path: Path) -> bool:
        """Check if file path contains any excluded directories"""
        relative_path = str(file_path.relative_to(root_path))
        for exclude in self.exclude_paths:
            if exclude in relative_path.split('/'):
                return True
        return False
    
    def _scan_file_v2(self, file_path: Path, root_path: Path, scan_id: str, repo_url: str) -> List[Dict[str, Any]]:
        """
        Scan file with v2 enhancements
        Ownership mapping is skipped to improve performance (gets rate-limited quickly)
        """
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            relative_path = str(file_path.relative_to(root_path))
            
            # Skip ownership mapping to improve scan speed
            # GitHub API rate limits at 60 requests/hour unauthenticated
            # For 100 files, this causes 10+ second delays
            ownership = {}  # Disabled for performance
            
            for line_num, line in enumerate(lines, start=1):
                for pattern_info in self.patterns:
                    pattern = pattern_info['regex']
                    if re.search(pattern, line):
                        # Extract snippet
                        snippet = self._extract_snippet(lines, line_num, pattern, line)
                        
                        # Extract contracts from snippet
                        contracts = extract_contracts(snippet)
                        
                        findings.append({
                            'scan_id': scan_id,
                            'file_path': relative_path,
                            'line_number': line_num,
                            'line_text': line.strip()[:500],
                            'framework': pattern_info['framework'],
                            'pattern_name': pattern_info['name'],
                            'pattern_category': pattern_info.get('category', 'misc'),
                            'pattern_severity': pattern_info.get('severity', 'low'),
                            'pattern_description': pattern_info.get('description', ''),
                            'snippet': snippet,
                            # Contract fields
                            'model_name': contracts.get('model_name'),
                            'temperature': contracts.get('temperature'),
                            'max_tokens': contracts.get('max_tokens'),
                            'is_streaming': contracts.get('is_streaming'),
                            'has_tools': contracts.get('has_tools'),
                            # Ownership fields (disabled for performance)
                            'owner_name': None,
                            'owner_email': None,
                            'owner_committed_at': None
                        })
        
        except Exception as e:
            logger.warning(f"Error scanning file {file_path}: {str(e)}")
        
        return findings
    
    def _extract_snippet(self, lines: List[str], match_line: int, pattern: str, matched_line: str) -> str:
        """Extract code snippet with context and highlighting"""
        start_idx = max(0, match_line - 4)
        end_idx = min(len(lines), match_line + 3)
        
        snippet_lines = []
        for i in range(start_idx, end_idx):
            if i == match_line - 1:
                highlighted = re.sub(pattern, r'[[[HIT]]]\g<0>[[[ENDHIT]]]', lines[i].rstrip())
                snippet_lines.append(highlighted)
            else:
                snippet_lines.append(lines[i].rstrip())
        
        return '\n'.join(snippet_lines)
    
    def _build_summary_json(self, findings: List[Dict[str, Any]], repo_path: Path) -> Dict[str, Any]:
        """
        Build comprehensive summary JSON for v2
        """
        # File-level aggregation with blast radius
        files_data = {}
        for finding in findings:
            file_path = finding['file_path']
            if file_path not in files_data:
                files_data[file_path] = {
                    'matchCount': 0,
                    'frameworks': set(),
                    'categories': set(),
                    'blastRadius': 'low'
                }
            
            files_data[file_path]['matchCount'] += 1
            files_data[file_path]['frameworks'].add(finding['framework'])
            if finding.get('pattern_category'):
                files_data[file_path]['categories'].add(finding['pattern_category'])
        
        # Calculate blast radius for each file
        for file_path, data in files_data.items():
            data['blastRadius'] = calculate_blast_radius(
                file_path,
                data['matchCount']
            )
            # Convert sets to lists for JSON serialization
            data['frameworks'] = list(data['frameworks'])
            data['categories'] = list(data['categories'])
        
        # Heatmap aggregation
        directories = aggregate_heatmap(findings)
        
        return {
            'files': files_data,
            'directories': directories
        }
    
    def _build_response_v2(self, scan_job: ScanJob, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build complete v2 API response
        """
        # Group findings by file
        files_map = {}
        for finding in findings:
            file_path = finding['file_path']
            if file_path not in files_map:
                files_map[file_path] = {
                    'file_path': file_path,
                    'frameworks': set(),
                    'occurrences': []
                }
            
            files_map[file_path]['frameworks'].add(finding['framework'])
            files_map[file_path]['occurrences'].append({
                'line_number': finding['line_number'],
                'line_text': finding['line_text'],
                'framework': finding['framework'],
                'pattern_name': finding['pattern_name'],
                'pattern_category': finding.get('pattern_category'),
                'pattern_severity': finding.get('pattern_severity'),
                'pattern_description': finding.get('pattern_description'),
                'snippet': finding.get('snippet'),
                'model_name': finding.get('model_name'),
                'temperature': finding.get('temperature'),
                'max_tokens': finding.get('max_tokens'),
                'is_streaming': finding.get('is_streaming'),
                'has_tools': finding.get('has_tools'),
                'owner_name': finding.get('owner_name'),
                'owner_email': finding.get('owner_email'),
                'owner_committed_at': finding.get('owner_committed_at')
            })
        
        files_list = []
        for file_data in files_map.values():
            file_data['frameworks'] = sorted(list(file_data['frameworks']))
            files_list.append(file_data)
        
        files_list.sort(key=lambda x: x['file_path'])
        
        # Parse stored JSON fields
        summary_json = json.loads(scan_job.summary_json) if scan_job.summary_json else {}
        risk_flags = json.loads(scan_job.risk_flags_json) if scan_job.risk_flags_json else []
        policies_result = json.loads(scan_job.policies_result_json) if scan_job.policies_result_json else {}
        frameworks_summary = compute_frameworks_summary(findings)
        hotspots = compute_hotspots(findings)
        recommended_actions = compute_recommended_actions(risk_flags, frameworks_summary)
        
        # Model & prompt contracts aggregation
        contracts = self._aggregate_contracts(findings)
        
        # Ownership aggregation
        ownership_summary = self._aggregate_ownership(findings)
        
        # Blast radius summary
        blast_radius_summary = aggregate_blast_radius(summary_json.get('files', {}))
        
        return {
            'scan_id': scan_job.id,
            'status': scan_job.status.value,
            'repo_url': scan_job.repo_url,
            'total_occurrences': scan_job.total_occurrences,
            'files_count': scan_job.files_count,
            'files': files_list,
            # v1 insights
            'frameworks_summary': frameworks_summary,
            'hotspots': hotspots,
            'risk_flags': risk_flags,
            'recommended_actions': recommended_actions,
            # v2 enhancements
            'policies_result': policies_result,
            'blast_radius_summary': blast_radius_summary,
            'contracts': contracts,
            'ownership_summary': ownership_summary,
            'heatmap': summary_json.get('directories', {})
        }
    
    def _aggregate_contracts(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate model and prompt contracts"""
        models = set()
        temperatures = []
        max_tokens_list = []
        streaming_count = 0
        tools_count = 0
        
        for finding in findings:
            if finding.get('model_name'):
                models.add(finding['model_name'])
            if finding.get('temperature') is not None:
                temperatures.append(finding['temperature'])
            if finding.get('max_tokens') is not None:
                max_tokens_list.append(finding['max_tokens'])
            if finding.get('is_streaming'):
                streaming_count += 1
            if finding.get('has_tools'):
                tools_count += 1
        
        return {
            'unique_models': sorted(list(models)),
            'temperature_range': {
                'min': min(temperatures) if temperatures else None,
                'max': max(temperatures) if temperatures else None,
                'avg': sum(temperatures) / len(temperatures) if temperatures else None
            },
            'max_tokens_range': {
                'min': min(max_tokens_list) if max_tokens_list else None,
                'max': max(max_tokens_list) if max_tokens_list else None,
                'avg': sum(max_tokens_list) / len(max_tokens_list) if max_tokens_list else None
            },
            'streaming_usage': streaming_count,
            'tools_usage': tools_count
        }
    
    def _aggregate_ownership(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate ownership by owner name"""
        from collections import defaultdict
        
        owner_data = defaultdict(lambda: {'files': set(), 'matches': 0})
        
        for finding in findings:
            if finding.get('owner_name'):
                owner_data[finding['owner_name']]['files'].add(finding['file_path'])
                owner_data[finding['owner_name']]['matches'] += 1
        
        ownership_list = []
        for owner, data in owner_data.items():
            ownership_list.append({
                'owner_name': owner,
                'ai_files_count': len(data['files']),
                'total_matches': data['matches']
            })
        
        return sorted(ownership_list, key=lambda x: -x['total_matches'])[:5]
