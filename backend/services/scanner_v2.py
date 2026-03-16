"""Enhanced Scanner v2 with parallel processing and smart filtering"""
import re
import logging
import json
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from models.scan import ScanJob, ScanStatus
from models.finding import Finding
from services.git_utils import GitUtils
from services.contract_extractor import extract_contracts
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
        self.policy_engine = PolicyEngine(config.policies.get('policies', {}))
        
        # Smart filtering
        self.skip_paths = config.settings.get('scan', {}).get('skip_paths', [])
        self.priority_paths = config.settings.get('scan', {}).get('priority_paths', [])
        self.default_file_limit = config.settings.get('scan', {}).get('default_file_limit', 1000)
        self.parallel_workers = config.settings.get('scan', {}).get('parallel_workers', 10)
        
        self.db_lock = threading.Lock()
    
    def scan_repository(self, scan_id: str, repo_url: str, full_scan: bool = False) -> Dict[str, Any]:
        """Main scanning with parallel processing"""
        scan_job = self.db.query(ScanJob).filter(ScanJob.id == scan_id).first()
        if not scan_job:
            raise ValueError(f"Scan job {scan_id} not found")
        
        scan_job.status = ScanStatus.RUNNING
        self.db.commit()
        
        repo_path = None
        try:
            repo_path = GitUtils.clone_repo(
                repo_url,
                shallow=config.settings['git']['shallow_clone'],
                depth=config.settings['git']['depth']
            )
            
            if not repo_path:
                raise Exception("Failed to clone repository")
            
            # Parallel scan
            findings = self._scan_directory_parallel(repo_path, scan_id, full_scan)
            
            # Batch insert
            with self.db_lock:
                for finding_data in findings:
                    finding = Finding(**finding_data)
                    self.db.add(finding)
                self.db.commit()
            
            # Aggregations
            unique_files = list(set(f['file_path'] for f in findings))
            frameworks = list(set(f['framework'] for f in findings))
            
            summary_json = self._build_summary_json(findings)
            policies_result = self.policy_engine.evaluate(findings, frameworks)
            frameworks_summary = compute_frameworks_summary(findings)
            risk_flags = compute_risk_flags(findings, frameworks_summary)
            
            high_blast_count = sum(1 for f in summary_json['files'].values() if f.get('blastRadius') == 'high')
            if high_blast_count > 0:
                risk_flags.append({
                    'id': 'high_blast_files_exist',
                    'label': f'High-impact files ({high_blast_count})',
                    'severity': 'high',
                    'description': f'Found {high_blast_count} critical files with AI usage.'
                })
            
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
    
    def _scan_directory_parallel(self, root_path: Path, scan_id: str, full_scan: bool) -> List[Dict[str, Any]]:
        """Parallel file scanning"""
        files_to_scan = self._collect_files_smart(root_path, full_scan)
        logger.info(f"Scanning {len(files_to_scan)} files with {self.parallel_workers} workers")
        
        all_findings = []
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = {executor.submit(self._scan_single_file, fp, root_path, scan_id): fp for fp in files_to_scan}
            
            for future in as_completed(futures):
                try:
                    all_findings.extend(future.result())
                except Exception as e:
                    logger.debug(f"Error: {str(e)}")
        
        return all_findings
    
    def _collect_files_smart(self, root_path: Path, full_scan: bool) -> List[Path]:
        """Smart file collection"""
        priority_files = []
        other_files = []
        
        for file_path in root_path.rglob('*'):
            if not file_path.is_file():
                continue
            if self._should_exclude(file_path, root_path):
                continue
            if file_path.suffix not in self.file_extensions:
                continue
            
            try:
                if file_path.stat().st_size > self.max_file_size:
                    continue
            except OSError:
                continue
            
            relative_path = str(file_path.relative_to(root_path))
            if not full_scan and self._should_skip(relative_path):
                continue
            
            if self._is_priority_file(relative_path):
                priority_files.append(file_path)
            else:
                other_files.append(file_path)
        
        all_files = priority_files + other_files
        
        if not full_scan and len(all_files) > self.default_file_limit:
            return all_files[:self.default_file_limit]
        
        return all_files
    
    def _should_exclude(self, file_path: Path, root_path: Path) -> bool:
        relative_path = str(file_path.relative_to(root_path))
        return any(exclude in relative_path.split('/') for exclude in self.exclude_paths)
    
    def _should_skip(self, relative_path: str) -> bool:
        path_parts = relative_path.lower().split('/')
        return any(skip in path_parts for skip in self.skip_paths)
    
    def _is_priority_file(self, relative_path: str) -> bool:
        path_parts = relative_path.lower().split('/')
        return any(priority in path_parts for priority in self.priority_paths)
    
    def _scan_single_file(self, file_path: Path, root_path: Path, scan_id: str) -> List[Dict[str, Any]]:
        """Scan single file"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            relative_path = str(file_path.relative_to(root_path))
            
            for line_num, line in enumerate(lines, start=1):
                for pattern_info in self.patterns:
                    if re.search(pattern_info['regex'], line):
                        snippet = self._extract_snippet(lines, line_num, pattern_info['regex'])
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
                            'model_name': contracts.get('model_name'),
                            'temperature': contracts.get('temperature'),
                            'max_tokens': contracts.get('max_tokens'),
                            'is_streaming': contracts.get('is_streaming'),
                            'has_tools': contracts.get('has_tools'),
                            'owner_name': None,
                            'owner_email': None,
                            'owner_committed_at': None
                        })
        except Exception:
            pass
        
        return findings
    
    def _extract_snippet(self, lines: List[str], match_line: int, pattern: str) -> str:
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

    # Maps framework names to component_type and provider for graph building
    _FRAMEWORK_META: Dict[str, Dict[str, str]] = {
        'openai': {'component_type': 'llm_provider', 'provider': 'OpenAI'},
        'anthropic': {'component_type': 'llm_provider', 'provider': 'Anthropic'},
        'google_genai': {'component_type': 'llm_provider', 'provider': 'Google'},
        'google_vertexai': {'component_type': 'llm_provider', 'provider': 'Google'},
        'cohere': {'component_type': 'llm_provider', 'provider': 'Cohere'},
        'mistral': {'component_type': 'llm_provider', 'provider': 'Mistral'},
        'groq': {'component_type': 'llm_provider', 'provider': 'Groq'},
        'together': {'component_type': 'llm_provider', 'provider': 'Together AI'},
        'replicate': {'component_type': 'llm_provider', 'provider': 'Replicate'},
        'huggingface': {'component_type': 'llm_provider', 'provider': 'Hugging Face'},
        'aws_bedrock': {'component_type': 'llm_provider', 'provider': 'AWS Bedrock'},
        'azure_openai': {'component_type': 'llm_provider', 'provider': 'Azure OpenAI'},
        'langchain': {'component_type': 'orchestration_framework', 'provider': 'LangChain'},
        'langgraph': {'component_type': 'orchestration_framework', 'provider': 'LangGraph'},
        'llamaindex': {'component_type': 'orchestration_framework', 'provider': 'LlamaIndex'},
        'crewai': {'component_type': 'agent_tool', 'provider': 'CrewAI'},
        'autogen': {'component_type': 'agent_tool', 'provider': 'AutoGen'},
        'dspy': {'component_type': 'orchestration_framework', 'provider': 'DSPy'},
        'haystack': {'component_type': 'orchestration_framework', 'provider': 'Haystack'},
        'chromadb': {'component_type': 'vector_db', 'provider': 'ChromaDB'},
        'pinecone': {'component_type': 'vector_db', 'provider': 'Pinecone'},
        'qdrant': {'component_type': 'vector_db', 'provider': 'Qdrant'},
        'weaviate': {'component_type': 'vector_db', 'provider': 'Weaviate'},
        'milvus': {'component_type': 'vector_db', 'provider': 'Milvus'},
        'faiss': {'component_type': 'vector_db', 'provider': 'FAISS'},
        'pgvector': {'component_type': 'vector_db', 'provider': 'pgvector'},
        'mcp': {'component_type': 'mcp_server', 'provider': 'MCP'},
        'vercel_ai': {'component_type': 'orchestration_framework', 'provider': 'Vercel AI'},
        'ollama': {'component_type': 'inference_server', 'provider': 'Ollama'},
        'vllm': {'component_type': 'inference_server', 'provider': 'vLLM'},
    }

    def _enrich_findings_for_graph(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add component_type and provider fields to findings for graph building."""
        for finding in findings:
            framework = finding.get('framework', '').lower()
            meta = self._FRAMEWORK_META.get(framework, {})
            finding['component_type'] = meta.get('component_type', 'ai_package')
            finding['provider'] = meta.get('provider', finding.get('framework', 'Unknown'))
            # Map category to severity for risk scoring
            if 'severity' not in finding:
                finding['severity'] = finding.get('pattern_severity', 'low')
        return findings

    def _build_response_v2(self, scan_job: ScanJob, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        files_map = {}
        for finding in findings:
            file_path = finding['file_path']
            if file_path not in files_map:
                files_map[file_path] = {'file_path': file_path, 'frameworks': set(), 'occurrences': []}

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

        summary_json = json.loads(scan_job.summary_json) if scan_job.summary_json else {}
        risk_flags = json.loads(scan_job.risk_flags_json) if scan_job.risk_flags_json else []
        policies_result = json.loads(scan_job.policies_result_json) if scan_job.policies_result_json else {}
        frameworks_summary = compute_frameworks_summary(findings)
        hotspots = compute_hotspots(findings)
        recommended_actions = compute_recommended_actions(risk_flags, frameworks_summary)
        contracts = self._aggregate_contracts(findings)
        blast_radius_summary = aggregate_blast_radius(summary_json.get('files', {}))

        # Enrich findings with component_type/provider for graph + risk + OWASP
        enriched = self._enrich_findings_for_graph(findings)

        # Risk scoring
        risk_score = None
        try:
            from app.scoring.risk_engine import RiskEngine
            engine = RiskEngine()
            risk_score = engine.score(enriched)
            # Add 'score' alias so frontend can read either .score or .overall_score
            risk_score['score'] = risk_score.get('overall_score', 0)
            # Store on scan job
            scan_job.risk_score_json = json.dumps(risk_score)
            self.db.commit()
        except Exception as exc:
            logger.warning("Risk scoring failed: %s", exc)

        # OWASP mapping
        owasp_data = None
        try:
            from app.scoring.owasp_mapper import OwaspMapper
            mapper = OwaspMapper()
            owasp_data = mapper.map_findings(enriched)
        except Exception as exc:
            logger.warning("OWASP mapping failed: %s", exc)

        # Dependency graph
        graph_data = None
        try:
            from app.graph.builder import GraphBuilder
            from app.graph.serializer import GraphSerializer
            builder = GraphBuilder()
            graph = builder.build(enriched)
            serializer = GraphSerializer()
            graph_data = serializer.to_react_flow(graph)
        except Exception as exc:
            logger.warning("Graph generation failed: %s", exc)

        return {
            'scan_id': scan_job.id,
            'status': scan_job.status.value,
            'repo_url': scan_job.repo_url,
            'total_occurrences': scan_job.total_occurrences,
            'files_count': scan_job.files_count,
            'files': files_list,
            'frameworks_summary': frameworks_summary,
            'hotspots': hotspots,
            'risk_flags': risk_flags,
            'recommended_actions': recommended_actions,
            'policies_result': policies_result,
            'blast_radius_summary': blast_radius_summary,
            'contracts': contracts,
            'ownership_summary': [],
            'heatmap': summary_json.get('directories', {}),
            'risk_score': risk_score,
            'owasp_data': owasp_data,
            'dependency_graph': graph_data,
        }
    
    def _aggregate_contracts(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
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
