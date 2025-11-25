import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from models.scan import ScanJob, ScanStatus
from models.finding import Finding
from services.git_utils import GitUtils
from core.config import config

logger = logging.getLogger(__name__)

class Scanner:
    def __init__(self, db: Session):
        self.db = db
        self.patterns = config.get_enabled_patterns()
        self.file_extensions = config.get_file_extensions()
        self.exclude_paths = config.get_exclude_paths()
        self.max_file_size = config.get_max_file_size()
    
    def scan_repository(self, scan_id: str, repo_url: str) -> Dict[str, Any]:
        """
        Main scanning logic: clone repo, scan files, store findings.
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
            
            # Scan files
            findings = self._scan_directory(repo_path, scan_id)
            
            # Store findings
            for finding_data in findings:
                finding = Finding(**finding_data)
                self.db.add(finding)
            
            # Update scan job
            unique_files = set(f['file_path'] for f in findings)
            scan_job.status = ScanStatus.SUCCESS
            scan_job.total_occurrences = len(findings)
            scan_job.files_count = len(unique_files)
            self.db.commit()
            
            # Build response
            return self._build_response(scan_job, findings)
            
        except Exception as e:
            logger.error(f"Scan failed: {str(e)}")
            scan_job.status = ScanStatus.FAILED
            scan_job.error_message = str(e)
            self.db.commit()
            raise
        
        finally:
            if repo_path:
                GitUtils.cleanup_repo(repo_path)
    
    def _scan_directory(self, root_path: Path, scan_id: str) -> List[Dict[str, Any]]:
        """
        Recursively scan directory for pattern matches.
        """
        findings = []
        
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
            
            # Scan file
            file_findings = self._scan_file(file_path, root_path, scan_id)
            findings.extend(file_findings)
        
        return findings
    
    def _should_exclude(self, file_path: Path, root_path: Path) -> bool:
        """
        Check if file path contains any excluded directories.
        """
        relative_path = str(file_path.relative_to(root_path))
        for exclude in self.exclude_paths:
            if exclude in relative_path.split('/'):
                return True
        return False
    
    def _scan_file(self, file_path: Path, root_path: Path, scan_id: str) -> List[Dict[str, Any]]:
        """
        Scan a single file for pattern matches.
        """
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            relative_path = str(file_path.relative_to(root_path))
            
            for line_num, line in enumerate(lines, start=1):
                for pattern_info in self.patterns:
                    pattern = pattern_info['regex']
                    if re.search(pattern, line):
                        findings.append({
                            'scan_id': scan_id,
                            'file_path': relative_path,
                            'line_number': line_num,
                            'line_text': line.strip()[:500],  # Truncate to 500 chars
                            'framework': pattern_info['framework'],
                            'pattern_name': pattern_info['name']
                        })
        
        except Exception as e:
            logger.warning(f"Error scanning file {file_path}: {str(e)}")
        
        return findings
    
    def _build_response(self, scan_job: ScanJob, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build API response with aggregated findings.
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
                'pattern_name': finding['pattern_name']
            })
        
        # Convert to list and sort
        files_list = []
        for file_data in files_map.values():
            file_data['frameworks'] = sorted(list(file_data['frameworks']))
            files_list.append(file_data)
        
        files_list.sort(key=lambda x: x['file_path'])
        
        return {
            'scan_id': scan_job.id,
            'status': scan_job.status.value,
            'repo_url': scan_job.repo_url,
            'total_occurrences': scan_job.total_occurrences,
            'files_count': scan_job.files_count,
            'files': files_list
        }
