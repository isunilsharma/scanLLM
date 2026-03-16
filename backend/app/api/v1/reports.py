"""
Report endpoints — /api/v1/scans/{scan_id}/report/*

PDF reports and AI-BOM (CycloneDX) exports.
"""
import sys
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, JSONResponse
from sqlalchemy.orm import Session

# Ensure backend root is importable
_backend_dir = str(Path(__file__).parent.parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from core.database import get_db
from models.scan import ScanJob, ScanStatus
from models.finding import Finding

import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["reports-v1"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_scan_or_404(scan_id: str, db: Session) -> ScanJob:
    scan_job = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan_job:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan_job


def _finding_to_dict(f: Finding) -> Dict[str, Any]:
    return {
        "file_path": f.file_path,
        "line_number": f.line_number,
        "line_text": f.line_text,
        "framework": f.framework,
        "pattern_name": f.pattern_name,
        "pattern_category": f.pattern_category,
        "pattern_severity": f.pattern_severity,
        "pattern_description": f.pattern_description,
        "snippet": f.snippet,
        "model_name": f.model_name,
        "temperature": f.temperature,
        "max_tokens": f.max_tokens,
        "is_streaming": f.is_streaming,
        "has_tools": f.has_tools,
        "owner_name": f.owner_name,
        "owner_email": f.owner_email,
        "owner_committed_at": (
            f.owner_committed_at.isoformat() if f.owner_committed_at else None
        ),
    }


def _get_scan_data(scan_id: str, db: Session) -> Dict[str, Any]:
    """Fetch scan + findings and build the full response dict."""
    scan_job = _get_scan_or_404(scan_id, db)

    if scan_job.status != ScanStatus.SUCCESS:
        raise HTTPException(
            status_code=400,
            detail="Scan has not completed successfully",
        )

    findings_objs = db.query(Finding).filter(Finding.scan_id == scan_id).all()
    findings = [_finding_to_dict(f) for f in findings_objs]

    from services.scanner_v2 import ScannerV2

    scanner = ScannerV2(db)
    return scanner._build_response_v2(scan_job, findings)


# ---------------------------------------------------------------------------
# PDF report
# ---------------------------------------------------------------------------

@router.get("/scans/{scan_id}/report/pdf")
async def download_pdf_report(scan_id: str, db: Session = Depends(get_db)):
    """Generate and download a PDF report for a scan."""
    scan_data = _get_scan_data(scan_id, db)

    try:
        from app.reports.pdf_generator import PDFGenerator

        generator = PDFGenerator()
        risk_score = scan_data.get("risk_score", {})
        owasp_data = scan_data.get("owasp", {})
        pdf_bytes = generator.generate_pdf(scan_data, risk_score, owasp_data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="scanllm-report-{scan_id[:8]}.pdf"'
            },
        )
    except ImportError:
        logger.warning("PDF generator dependencies not available (xhtml2pdf/jinja2)")
    except Exception as e:
        logger.error("PDF generation failed: %s", e)

    # Fallback: return JSON representation
    return JSONResponse(
        content={
            "message": "PDF generation failed. Returning JSON report.",
            "scan_id": scan_id,
            "repo_url": scan_data.get("repo_url"),
            "total_occurrences": scan_data.get("total_occurrences", 0),
            "files_count": scan_data.get("files_count", 0),
            "frameworks_summary": scan_data.get("frameworks_summary", []),
            "risk_flags": scan_data.get("risk_flags", []),
            "recommended_actions": scan_data.get("recommended_actions", []),
        },
        headers={
            "Content-Disposition": f'attachment; filename="scanllm-report-{scan_id[:8]}.json"'
        },
    )


# ---------------------------------------------------------------------------
# AI-BOM (CycloneDX) JSON
# ---------------------------------------------------------------------------

@router.get("/scans/{scan_id}/report/aibom")
async def download_aibom_json(scan_id: str, db: Session = Depends(get_db)):
    """Download AI Bill of Materials in CycloneDX JSON format."""
    scan_data = _get_scan_data(scan_id, db)

    try:
        from app.reports.aibom_generator import AIBOMGenerator

        generator = AIBOMGenerator()
        findings = scan_data.get("findings", [])
        bom = generator.generate(scan_data, findings)
        return Response(
            content=json.dumps(bom, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="scanllm-aibom-{scan_id[:8]}.json"'
            },
        )
    except ImportError:
        logger.warning("AI-BOM generator not available")
    except Exception as e:
        logger.error("AI-BOM JSON generation failed: %s", e)

    # Fallback: minimal CycloneDX-like stub
    bom_stub = _build_aibom_stub(scan_id, scan_data)
    return Response(
        content=json.dumps(bom_stub, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="scanllm-aibom-{scan_id[:8]}.json"'
        },
    )


# ---------------------------------------------------------------------------
# AI-BOM (CycloneDX) XML
# ---------------------------------------------------------------------------

@router.get("/scans/{scan_id}/report/aibom.xml")
async def download_aibom_xml(scan_id: str, db: Session = Depends(get_db)):
    """Download AI Bill of Materials in CycloneDX XML format."""
    scan_data = _get_scan_data(scan_id, db)

    try:
        from app.reports.aibom_generator import AIBOMGenerator

        generator = AIBOMGenerator()
        findings = scan_data.get("findings", [])
        xml_str = generator.generate_xml(scan_data, findings)
        return Response(
            content=xml_str,
            media_type="application/xml",
            headers={
                "Content-Disposition": f'attachment; filename="scanllm-aibom-{scan_id[:8]}.xml"'
            },
        )
    except ImportError:
        logger.warning("AI-BOM generator not available")
    except Exception as e:
        logger.error("AI-BOM XML generation failed: %s", e)

    # Fallback: minimal XML stub
    bom_stub = _build_aibom_stub(scan_id, scan_data)
    xml_str = _dict_to_minimal_xml(bom_stub)
    return Response(
        content=xml_str,
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="scanllm-aibom-{scan_id[:8]}.xml"'
        },
    )


# ---------------------------------------------------------------------------
# Stub helpers
# ---------------------------------------------------------------------------

def _build_aibom_stub(scan_id: str, scan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build a minimal CycloneDX-shaped BOM from scan data."""
    components: List[Dict[str, Any]] = []
    for fw in scan_data.get("frameworks_summary", []):
        components.append(
            {
                "type": "machine-learning",
                "name": fw.get("name", "unknown"),
                "version": "",
                "bom-ref": fw.get("name", "unknown"),
                "properties": [
                    {"name": "scanllm:category", "value": fw.get("category", "")},
                    {
                        "name": "scanllm:occurrences",
                        "value": str(fw.get("count", 0)),
                    },
                ],
            }
        )

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "metadata": {
            "tools": [{"name": "ScanLLM", "version": "0.1.0"}],
            "component": {
                "type": "application",
                "name": scan_data.get("repo_url", "unknown"),
            },
        },
        "components": components,
        "serialNumber": f"urn:uuid:{scan_id}",
    }


def _dict_to_minimal_xml(d: Dict[str, Any], root_tag: str = "bom") -> str:
    """Very simple dict-to-XML for the stub (no external deps)."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append(f'<{root_tag} xmlns="http://cyclonedx.org/schema/bom/1.6">')
    lines.append(f"  <bomFormat>{d.get('bomFormat', '')}</bomFormat>")
    lines.append(f"  <specVersion>{d.get('specVersion', '')}</specVersion>")
    lines.append(f"  <serialNumber>{d.get('serialNumber', '')}</serialNumber>")
    lines.append("  <components>")
    for comp in d.get("components", []):
        lines.append("    <component>")
        lines.append(f"      <type>{comp.get('type', '')}</type>")
        lines.append(f"      <name>{comp.get('name', '')}</name>")
        lines.append("    </component>")
    lines.append("  </components>")
    lines.append(f"</{root_tag}>")
    return "\n".join(lines)
