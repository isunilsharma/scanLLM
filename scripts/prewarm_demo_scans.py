#!/usr/bin/env python3
"""
Prewarm demo scans for sample repositories
Runs scans for all sample repos and caches results
"""

import sys
sys.path.insert(0, '/app/backend')

import asyncio
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from core.database import SessionLocal, init_db
from core.constants import SAMPLE_REPOS, SCAN_VERSION, CACHE_TTL_DAYS
from models.scan import ScanJob, ScanStatus
from models.demo_scan_cache import DemoScanCache
from services.scanner_v2 import ScannerV2

def prewarm_demo_scans():
    print("="*70)
    print("Demo Scan Prewarm - Caching Sample Repository Scans")
    print("="*70)
    print(f"Scan Version: {SCAN_VERSION}")
    print(f"Sample Repos: {len(SAMPLE_REPOS)}")
    print(f"Cache TTL: {CACHE_TTL_DAYS} days")
    print("")
    
    db = SessionLocal()
    
    try:
        for repo_url in SAMPLE_REPOS:
            repo_parts = repo_url.replace('https://github.com/', '').split('/')
            repo_owner = repo_parts[0] if len(repo_parts) > 0 else 'unknown'
            repo_name = repo_parts[1] if len(repo_parts) > 1 else 'unknown'
            
            print(f"\nProcessing: {repo_owner}/{repo_name}")
            print("-" * 50)
            
            # Process both scan modes
            for scan_mode, full_scan in [('journal', False), ('full', True)]:
                print(f"  Scan mode: {scan_mode}")
                
                # Check if cache exists and is fresh
                existing_cache = db.query(DemoScanCache).filter(
                    DemoScanCache.repo_url == repo_url,
                    DemoScanCache.scan_mode == scan_mode,
                    DemoScanCache.scan_version == SCAN_VERSION
                ).first()
                
                if existing_cache:
                    # Handle timezone-aware comparison
                    expires_at = existing_cache.expires_at
                    
                    # Check if cache never expires (None) or is still valid
                    if expires_at is None:
                        print("    ✓ Cache valid (never expires)")
                        continue
                    
                    # Handle timezone for expiring cache
                    if expires_at.tzinfo is None:
                        from datetime import timezone as tz
                        expires_at = expires_at.replace(tzinfo=tz.utc)
                    
                    if expires_at > datetime.now(timezone.utc):
                        print(f"    ✓ Cache valid (expires {expires_at})")
                        continue
                
                print("    Running scan...")
                
                try:
                    # Create scan job
                    scan_job = ScanJob(
                        repo_url=repo_url,
                        status=ScanStatus.PENDING,
                        repo_owner=repo_owner,
                        repo_name=repo_name,
                        source='demo_precomputed'
                    )
                    db.add(scan_job)
                    db.commit()
                    db.refresh(scan_job)
                    
                    # Run scan
                    scanner = ScannerV2(db)
                    result = scanner.scan_repository(scan_job.id, repo_url, full_scan)
                    
                    # Store in cache
                    if existing_cache:
                        db.delete(existing_cache)
                    
                    cache_entry = DemoScanCache(
                        repo_url=repo_url,
                        repo_owner=repo_owner,
                        repo_name=repo_name,
                        scan_mode=scan_mode,
                        scan_version=SCAN_VERSION,
                        status='COMPLETE',
                        scan_id=scan_job.id,
                        result_payload_json=json.dumps(result),
                        expires_at=None if CACHE_TTL_DAYS is None else datetime.now(timezone.utc) + timedelta(days=CACHE_TTL_DAYS)
                    )
                    db.add(cache_entry)
                    db.commit()
                    
                    print(f"    ✓ Cached (scan_id: {scan_job.id})")
                    print(f"      Files: {result.get('files_count', 0)}, Matches: {result.get('total_occurrences', 0)}")
                    
                except Exception as e:
                    print(f"    ✗ Failed: {str(e)}")
                    # Store error in cache
                    if existing_cache:
                        db.delete(existing_cache)
                    
                    error_cache = DemoScanCache(
                        repo_url=repo_url,
                        repo_owner=repo_owner,
                        repo_name=repo_name,
                        scan_mode=scan_mode,
                        scan_version=SCAN_VERSION,
                        status='ERROR',
                        scan_id='',
                        result_payload_json=json.dumps({'error': str(e)}),
                        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)  # Shorter TTL for errors
                    )
                    db.add(error_cache)
                    db.commit()
    
    finally:
        db.close()
    
    print("\n" + "="*70)
    print("✅ Prewarm complete!")
    print("="*70)

if __name__ == '__main__':
    init_db()
    prewarm_demo_scans()
