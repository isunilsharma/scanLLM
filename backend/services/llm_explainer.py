"""
LLM-powered scan explanation service
"""
import logging
import json
from typing import Dict, Any
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

async def explain_scan(scan_data: Dict[str, Any]) -> str:
    """
    Generate an LLM-powered narrative explanation of the scan results.
    Uses only aggregated data, not raw code.
    """
    try:
        # Build context from scan data
        context = _build_scan_context(scan_data)

        system_message = "You are an AI engineering consultant analyzing code scan results. Provide clear, actionable insights for engineering leaders about their AI/LLM usage."

        prompt = f"""Analyze this AI dependency scan and provide a clear executive summary:

REPOSITORY: {scan_data.get('repo_url')}
SCAN RESULTS:
- Total AI Matches: {scan_data.get('total_occurrences', 0)}
- Files with AI: {scan_data.get('files_count', 0)}
- Frameworks: {', '.join([f['framework'] for f in scan_data.get('frameworks_summary', [])])}

USAGE BREAKDOWN:
{context['usage_breakdown']}

RISK FLAGS:
{context['risk_flags']}

POLICY EVALUATION:
{context['policies']}

BLAST RADIUS:
- High-risk files: {scan_data.get('blast_radius_summary', {}).get('high', 0)}
- Medium-risk files: {scan_data.get('blast_radius_summary', {}).get('medium', 0)}
- Low-risk files: {scan_data.get('blast_radius_summary', {}).get('low', 0)}

AI HOTSPOTS:
{context['hotspots']}

Please provide:
1. A 2-3 sentence high-level summary
2. Key risks to be aware of (2-3 points)
3. Migration concerns (if any)
4. Top 2-3 recommended actions

Keep it concise and actionable for engineering leadership."""

        # Try Anthropic first, then fall back to OpenAI
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        openai_key = os.getenv('OPENAI_API_KEY')

        if anthropic_key:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=anthropic_key)
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=system_message,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        elif openai_key:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=openai_key)
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        else:
            raise ValueError("No LLM API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in environment.")
        
    except Exception as e:
        logger.error(f"Failed to generate LLM explanation: {str(e)}")
        return f"Unable to generate AI explanation: {str(e)}"

def _build_scan_context(scan_data: Dict[str, Any]) -> Dict[str, str]:
    """Build formatted context sections from scan data"""
    
    # Usage breakdown
    usage_lines = []
    for fw in scan_data.get('frameworks_summary', []):
        categories = ', '.join([f"{c['category']}: {c['count']}" for c in fw.get('categories', [])])
        usage_lines.append(f"- {fw['framework']}: {fw['total_matches']} matches ({categories})")
    
    # Risk flags
    risk_lines = []
    for flag in scan_data.get('risk_flags', []):
        risk_lines.append(f"- [{flag.get('severity', 'low').upper()}] {flag.get('label', 'Unknown')}")
    
    # Policies
    policies = scan_data.get('policies_result', {})
    policy_lines = []
    policy_lines.append(f"Errors: {len(policies.get('errors', []))}")
    policy_lines.append(f"Warnings: {len(policies.get('warnings', []))}")
    policy_lines.append(f"Passes: {len(policies.get('passes', []))}")
    
    # Hotspots
    hotspot_lines = []
    for hotspot in scan_data.get('hotspots', [])[:3]:
        hotspot_lines.append(f"- {hotspot.get('directory', 'unknown')}: {hotspot.get('total_matches', 0)} matches in {hotspot.get('files_with_ai', 0)} files")
    
    return {
        'usage_breakdown': '\n'.join(usage_lines) if usage_lines else 'No usage detected',
        'risk_flags': '\n'.join(risk_lines) if risk_lines else 'No risk flags',
        'policies': '\n'.join(policy_lines),
        'hotspots': '\n'.join(hotspot_lines) if hotspot_lines else 'No hotspots'
    }
