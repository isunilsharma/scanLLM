"""Local web server for `scanllm ui` — serves the React dashboard and scan data APIs."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# HTML fallback when the built frontend is not available
_FALLBACK_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>ScanLLM Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#0a0a0a;color:#e4e4e7;min-height:100vh}
a{color:#22d3ee}
.tab-bar{display:flex;gap:2px;background:#18181b;padding:8px 16px;border-bottom:1px solid #27272a;overflow-x:auto;position:sticky;top:0;z-index:10}
.tab-btn{background:none;border:none;color:#71717a;padding:8px 16px;cursor:pointer;font-size:.875rem;border-radius:6px;white-space:nowrap;font-family:inherit}
.tab-btn:hover{color:#e4e4e7;background:#27272a}
.tab-btn.active{color:#22d3ee;background:#27272a;font-weight:600}
#tab-content{max-width:1100px;margin:0 auto;padding:24px 16px}
.card{background:#18181b;border:1px solid #27272a;border-radius:12px;padding:20px;margin-bottom:16px}
.card h2{font-size:1.1rem;margin-bottom:12px;color:#e4e4e7}
.grid{display:grid;gap:16px}
.grid-2{grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}
.grid-3{grid-template-columns:repeat(auto-fit,minmax(180px,1fr))}
.grid-4{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}
.metric{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #27272a}
.metric:last-child{border-bottom:none}
.ml{color:#a1a1aa;font-size:.875rem}
.mv{font-weight:600}
.badge{display:inline-block;padding:2px 10px;border-radius:9999px;font-size:.75rem;font-weight:600}
.b-crit{background:#7f1d1d;color:#fca5a5}.b-high{background:#78350f;color:#fbbf24}
.b-med{background:#713f12;color:#fcd34d}.b-low{background:#14532d;color:#86efac}
.b-info{background:#1e3a5f;color:#93c5fd}
.b-pass{background:#14532d;color:#86efac}.b-fail{background:#7f1d1d;color:#fca5a5}
.grade-A,.grade-B{color:#4ade80}.grade-C{color:#facc15}.grade-D,.grade-F{color:#f87171}
.gauge-wrap{display:flex;align-items:center;gap:24px;margin-bottom:16px}
.gauge{width:120px;height:120px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.5rem;font-weight:700}
.gauge-inner{width:90px;height:90px;border-radius:50%;background:#0a0a0a;display:flex;align-items:center;justify-content:center;flex-direction:column}
.gauge-score{font-size:1.5rem;font-weight:700;line-height:1}
.gauge-label{font-size:.7rem;color:#71717a;margin-top:2px}
.bar-row{display:flex;align-items:center;gap:8px;margin-bottom:8px;font-size:.85rem}
.bar-track{flex:1;height:8px;background:#27272a;border-radius:4px;overflow:hidden}
.bar-fill{height:100%;border-radius:4px}
.chip{display:inline-block;background:#27272a;padding:4px 10px;border-radius:6px;font-size:.8rem;margin:2px}
table{width:100%;border-collapse:collapse;font-size:.85rem}
th{text-align:left;padding:8px;border-bottom:2px solid #27272a;color:#a1a1aa;font-weight:600;position:sticky;top:0;background:#18181b}
td{padding:8px;border-bottom:1px solid #27272a}
tr:hover td{background:#1c1c1f}
.empty{text-align:center;color:#71717a;padding:40px 20px}
.btn{background:#22d3ee;color:#0a0a0a;border:none;padding:8px 20px;border-radius:8px;cursor:pointer;font-weight:600;font-size:.875rem;font-family:inherit}
.btn:hover{opacity:.85}
.btn-outline{background:none;border:1px solid #27272a;color:#e4e4e7}
.btn-outline:hover{background:#27272a}
.feedback-btn{position:fixed;bottom:20px;right:20px;background:#22d3ee;color:#0a0a0a;border:none;width:48px;height:48px;border-radius:50%;font-size:1.3rem;cursor:pointer;z-index:9999;box-shadow:0 4px 12px rgba(0,0,0,.5);pointer-events:auto;transition:transform .15s,opacity .15s}
.feedback-btn:hover{opacity:.85;transform:scale(1.1)}
.sev-bar{display:flex;height:10px;border-radius:5px;overflow:hidden;margin-top:6px}
.filter-bar{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}
.filter-btn{background:#27272a;border:1px solid #3f3f46;color:#a1a1aa;padding:4px 12px;border-radius:6px;cursor:pointer;font-size:.8rem;font-family:inherit}
.filter-btn.active{border-color:#22d3ee;color:#22d3ee}
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.7);display:none;align-items:center;justify-content:center;z-index:200}
.modal-overlay.open{display:flex}
.modal{background:#18181b;border:1px solid #27272a;border-radius:12px;padding:24px;max-width:440px;width:90%}
.modal h3{margin-bottom:12px}
.modal textarea{width:100%;background:#27272a;border:1px solid #3f3f46;color:#e4e4e7;border-radius:8px;padding:10px;font-family:inherit;font-size:.875rem;resize:vertical;min-height:80px}
.modal select,.modal input{width:100%;background:#27272a;border:1px solid #3f3f46;color:#e4e4e7;border-radius:8px;padding:8px;font-family:inherit;margin-bottom:10px}
.stars{display:flex;gap:4px;margin-bottom:10px}
.star{font-size:1.5rem;cursor:pointer;color:#3f3f46}
.star.on{color:#facc15}
</style>
</head>
<body>
<div class="tab-bar">
  <button class="tab-btn active" onclick="switchTab('overview',this)">Overview</button>
  <button class="tab-btn" onclick="switchTab('findings',this)">Findings</button>
  <button class="tab-btn" onclick="switchTab('risk',this)">Risk</button>
  <button class="tab-btn" onclick="switchTab('owasp',this)">OWASP</button>
  <button class="tab-btn" onclick="switchTab('graph',this)">Graph</button>
  <button class="tab-btn" onclick="switchTab('policies',this)">Policies</button>
  <button class="tab-btn" onclick="switchTab('history',this)">History</button>
  <button class="tab-btn" onclick="switchTab('export',this)">Export</button>
</div>
<div id="tab-content"><p class="empty">Loading...</p></div>
<button class="feedback-btn" onclick="openFeedback()" title="Send feedback">&#9993;</button>
<div id="fb-modal" class="modal-overlay">
  <div class="modal">
    <h3>Send Feedback</h3>
    <div class="stars" id="fb-stars"></div>
    <select id="fb-cat"><option value="bug">Bug Report</option><option value="feature">Feature Request</option><option value="general">General</option></select>
    <textarea id="fb-msg" placeholder="Your feedback..."></textarea>
    <div style="display:flex;gap:8px;margin-top:12px">
      <button class="btn" onclick="submitFeedback()">Submit</button>
      <button class="btn btn-outline" onclick="closeFeedback()">Cancel</button>
    </div>
    <p id="fb-status" style="margin-top:8px;font-size:.8rem;color:#71717a"></p>
  </div>
</div>
<script>
var _cache={};var _fbRating=0;
function esc(s){if(s==null)return'';return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
function switchTab(name,btn){
  document.querySelectorAll('.tab-btn').forEach(function(b){b.classList.remove('active')});
  if(btn)btn.classList.add('active');
  loadTab(name);
}
function fetchAPI(url){
  if(_cache[url])return Promise.resolve(_cache[url]);
  return fetch(url).then(function(r){return r.json()}).then(function(d){_cache[url]=d;return d});
}
function loadTab(name){
  var el=document.getElementById('tab-content');
  el.innerHTML='<p class="empty">Loading...</p>';
  var routes={overview:['/api/scan/latest',renderOverview],findings:['/api/scan/latest',renderFindings],
    risk:['/api/risk',renderRisk],owasp:['/api/owasp',renderOwasp],graph:['/api/graph',renderGraph],
    policies:['/api/policy',renderPolicies],history:['/api/scan/history',renderHistory],
    export:['/api/scan/latest',renderExport]};
  var r=routes[name];
  if(!r){el.innerHTML='<p class="empty">Unknown tab</p>';return}
  fetchAPI(r[0]).then(function(d){r[1](d,el)}).catch(function(e){el.innerHTML='<p class="empty" style="color:#f87171">Failed to load data: '+esc(e.message)+'</p>'});
}
function sevColor(s){var m={critical:'#ef4444',high:'#f59e0b',medium:'#eab308',low:'#22c55e',info:'#3b82f6'};return m[(s||'').toLowerCase()]||'#71717a'}
function sevBadge(s){var m={critical:'b-crit',high:'b-high',medium:'b-med',low:'b-low',info:'b-info'};return '<span class="badge '+(m[(s||'').toLowerCase()]||'b-info')+'">'+esc(s)+'</span>'}
function gradeColor(g){if(g==='A'||g==='B')return '#4ade80';if(g==='C')return '#facc15';return '#f87171'}
function renderOverview(data,el){
  if(!data||data.error){el.innerHTML='<div class="empty"><p>No scan data found.</p><p style="margin-top:8px;color:#a1a1aa">Run <code style="background:#27272a;padding:2px 6px;border-radius:4px">scanllm scan . --save</code> first.</p></div>';return}
  var s=data.summary||{};var r=data.risk||{};var grade=r.grade||'?';var score=r.overall_score||0;
  var pct=Math.min(score,100);var gc=gradeColor(grade);
  var h='<div class="gauge-wrap"><div class="gauge" style="background:conic-gradient('+gc+' 0 '+pct+'%,#27272a '+pct+'% 100%)"><div class="gauge-inner"><span class="gauge-score" style="color:'+gc+'">'+score+'</span><span class="gauge-label">/ 100</span></div></div>';
  h+='<div><div style="font-size:2rem;font-weight:700" class="grade-'+grade+'">Grade '+esc(grade)+'</div>';
  h+='<div class="ml">Risk Assessment</div></div></div>';
  h+='<div class="grid grid-4">';
  h+='<div class="card"><div class="ml">Findings</div><div style="font-size:1.5rem;font-weight:700">'+(s.total_findings||0)+'</div></div>';
  h+='<div class="card"><div class="ml">Files Scanned</div><div style="font-size:1.5rem;font-weight:700">'+(s.files_scanned||0)+'</div></div>';
  h+='<div class="card"><div class="ml">AI Files</div><div style="font-size:1.5rem;font-weight:700">'+(s.ai_files_count||0)+'</div></div>';
  h+='<div class="card"><div class="ml">Providers</div><div style="font-size:1.5rem;font-weight:700">'+Object.keys(s.providers||{}).length+'</div></div></div>';
  var sevs=s.severities||{};var total=Object.values(sevs).reduce(function(a,b){return a+b},0)||1;
  h+='<div class="card"><h2>Severity Breakdown</h2><div class="sev-bar">';
  ['critical','high','medium','low','info'].forEach(function(k){var v=sevs[k]||0;if(v>0)h+='<div style="width:'+((v/total)*100)+'%;background:'+sevColor(k)+'" title="'+esc(k)+': '+v+'"></div>'});
  h+='</div><div style="display:flex;gap:12px;margin-top:8px;flex-wrap:wrap">';
  ['critical','high','medium','low','info'].forEach(function(k){var v=sevs[k]||0;if(v>0)h+='<span class="ml"><span style="color:'+sevColor(k)+'">&#9679;</span> '+esc(k)+': '+v+'</span>'});
  h+='</div></div>';
  var provs=Object.keys(s.providers||{});
  if(provs.length){h+='<div class="card"><h2>Providers</h2><div>';provs.forEach(function(p){h+='<span class="chip">'+esc(p)+'</span>'});h+='</div></div>'}
  el.innerHTML=h;
}
function renderFindings(data,el){
  if(!data||data.error||!data.findings||!data.findings.length){el.innerHTML='<div class="empty">No findings. Run a scan first.</div>';return}
  var findings=data.findings;var show=findings.slice(0,200);
  var h='<div class="card"><h2>Findings ('+findings.length+')</h2>';
  if(findings.length>200)h+='<p class="ml" style="margin-bottom:8px">Showing first 200 of '+findings.length+'</p>';
  h+='<div class="filter-bar"><button class="filter-btn active" onclick="filterFindings(this,\'all\')">All</button>';
  ['critical','high','medium','low','info'].forEach(function(s){h+='<button class="filter-btn" onclick="filterFindings(this,\''+s+'\')">'+s.charAt(0).toUpperCase()+s.slice(1)+'</button>'});
  h+='</div><div style="overflow-x:auto"><table><thead><tr><th>Severity</th><th>Type</th><th>File</th><th>Line</th><th>Description</th></tr></thead><tbody id="findings-body">';
  show.forEach(function(f){
    var sev=(f.severity||'info').toLowerCase();
    h+='<tr data-sev="'+esc(sev)+'"><td>'+sevBadge(sev)+'</td><td>'+esc(f.type||f.component_type||'-')+'</td><td style="max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="'+esc(f.file||'')+'">'+esc(f.file||'-')+'</td><td>'+(f.line||'-')+'</td><td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="'+esc(f.description||f.message||'')+'">'+esc(f.description||f.message||'-')+'</td></tr>'});
  h+='</tbody></table></div></div>';
  el.innerHTML=h;
}
function filterFindings(btn,sev){
  document.querySelectorAll('.filter-btn').forEach(function(b){b.classList.remove('active')});
  btn.classList.add('active');
  document.querySelectorAll('#findings-body tr').forEach(function(tr){
    tr.style.display=(sev==='all'||tr.getAttribute('data-sev')===sev)?'':'none';
  });
}
function renderRisk(data,el){
  var score=data.overall_score||0;var grade=data.grade||'?';var gc=gradeColor(grade);var pct=Math.min(score,100);
  var h='<div class="card"><div class="gauge-wrap"><div class="gauge" style="background:conic-gradient('+gc+' 0 '+pct+'%,#27272a '+pct+'% 100%)"><div class="gauge-inner"><span class="gauge-score" style="color:'+gc+'">'+score+'</span><span class="gauge-label">/ 100</span></div></div>';
  h+='<div><div style="font-size:2.5rem;font-weight:700" class="grade-'+grade+'">Grade '+esc(grade)+'</div>';
  h+='<div class="ml">Overall Risk Score</div></div></div></div>';
  var cats=data.categories||data.breakdown||{};var keys=Object.keys(cats);
  if(keys.length){
    h+='<div class="card"><h2>Risk Breakdown</h2>';
    keys.forEach(function(k){
      var v=cats[k];var val=typeof v==='object'?(v.score||v.value||0):v;var maxv=typeof v==='object'?(v.max||v.weight||25):25;
      var pctBar=maxv>0?Math.min((val/maxv)*100,100):0;var label=k.replace(/_/g,' ').replace(/\b\w/g,function(c){return c.toUpperCase()});
      h+='<div class="bar-row"><span style="min-width:180px" class="ml">'+esc(label)+'</span><div class="bar-track"><div class="bar-fill" style="width:'+pctBar+'%;background:'+gc+'"></div></div><span class="mv" style="min-width:50px;text-align:right">'+val+'</span></div>';
    });
    h+='</div>';
  }
  var recs=data.recommendations||[];
  if(recs.length){
    h+='<div class="card"><h2>Recommendations</h2><ul style="list-style:none;padding:0">';
    recs.forEach(function(r){h+='<li style="padding:6px 0;border-bottom:1px solid #27272a;font-size:.875rem">&#8226; '+esc(typeof r==='string'?r:r.message||r.text||JSON.stringify(r))+'</li>'});
    h+='</ul></div>';
  }
  el.innerHTML=h;
}
function renderOwasp(data,el){
  var cats=data.categories||[];var cov=data.coverage||{};
  var total=10;var covered=cats.filter(function(c){return(c.findings_count||c.count||0)>0}).length;
  var covPct=Math.round((covered/total)*100);
  var h='<div class="card"><h2>OWASP LLM Top 10 Coverage</h2>';
  h+='<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px"><div class="bar-track" style="flex:1;height:12px"><div class="bar-fill" style="width:'+covPct+'%;background:#22d3ee"></div></div><span class="mv">'+covPct+'%</span></div>';
  h+='<p class="ml">'+covered+' of '+total+' categories have findings</p></div>';
  var owaspNames={LLM01:'Prompt Injection',LLM02:'Sensitive Info Disclosure',LLM03:'Supply Chain',LLM04:'Data and Model Poisoning',LLM05:'Improper Output Handling',LLM06:'Excessive Agency',LLM07:'System Prompt Leakage',LLM08:'Vector/Embedding Weaknesses',LLM09:'Misinformation',LLM10:'Unbounded Consumption'};
  if(cats.length){
    h+='<div class="grid grid-2">';
    cats.forEach(function(c){
      var id=c.id||c.owasp_id||'';var name=c.name||owaspNames[id]||id;var count=c.findings_count||c.count||0;
      var detected=count>0;var borderCol=detected?'#22d3ee':'#3f3f46';
      h+='<div class="card" style="border-color:'+borderCol+'"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px"><span style="font-weight:600;color:'+(detected?'#22d3ee':'#71717a')+'">'+esc(id)+'</span>';
      h+=detected?'<span class="badge b-high">'+count+' found</span>':'<span class="badge" style="background:#27272a;color:#71717a">Clear</span>';
      h+='</div><div style="font-size:.85rem;color:#a1a1aa">'+esc(name)+'</div>';
      if(c.description)h+='<div style="font-size:.78rem;color:#52525b;margin-top:4px">'+esc(c.description)+'</div>';
      h+='</div>'});
    h+='</div>';
  } else {
    h+='<div class="grid grid-2">';
    Object.keys(owaspNames).forEach(function(id){
      h+='<div class="card" style="border-color:#3f3f46"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px"><span style="font-weight:600;color:#71717a">'+id+'</span><span class="badge" style="background:#27272a;color:#71717a">No data</span></div><div style="font-size:.85rem;color:#a1a1aa">'+owaspNames[id]+'</div></div>'});
    h+='</div>';
  }
  el.innerHTML=h;
}
function renderGraph(data,el){
  var nodes=data.nodes||[];var edges=data.edges||[];
  if(!nodes.length){el.innerHTML='<div class="empty">No graph data. Run a scan first.</div>';return}
  var typeColors={llm_provider:'#22d3ee',vector_db:'#a78bfa',orchestration_framework:'#f59e0b',agent_tool:'#ef4444',ai_package:'#22c55e',secret:'#f87171',config_reference:'#71717a',mcp_server:'#ec4899',embedding_service:'#6366f1',inference_server:'#14b8a6'};
  var W=1060;var H=Math.max(500,nodes.length*18);var cx=W/2;var cy=H/2;var radius=Math.min(cx,cy)-60;
  var h='<div class="card"><h2>Dependency Graph ('+nodes.length+' nodes, '+edges.length+' edges)</h2>';
  h+='<div style="overflow:auto;max-height:600px"><svg width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'">';
  var posMap={};
  nodes.forEach(function(n,i){
    var a=(2*Math.PI*i)/nodes.length - Math.PI/2;
    var x=cx+radius*Math.cos(a);var y=cy+radius*Math.sin(a);
    posMap[n.id]={x:x,y:y};
  });
  edges.forEach(function(e){
    var src=e.source;var tgt=e.target;if(typeof src==='object')src=src.id||src;if(typeof tgt==='object')tgt=tgt.id||tgt;
    var s=posMap[src];var t=posMap[tgt];if(!s||!t)return;
    h+='<line x1="'+s.x+'" y1="'+s.y+'" x2="'+t.x+'" y2="'+t.y+'" stroke="#3f3f46" stroke-width="1.5"/>';
    if(e.label){var mx=(s.x+t.x)/2;var my=(s.y+t.y)/2;h+='<text x="'+mx+'" y="'+(my-4)+'" fill="#52525b" font-size="9" text-anchor="middle">'+esc(e.label)+'</text>'}
  });
  nodes.forEach(function(n){
    var p=posMap[n.id];if(!p)return;var ndata=n.data||n;var ntype=ndata.type||ndata.component_type||'ai_package';
    var col=typeColors[ntype]||'#71717a';var label=ndata.label||ndata.name||n.id;
    h+='<circle cx="'+p.x+'" cy="'+p.y+'" r="10" fill="'+col+'" stroke="#0a0a0a" stroke-width="2"><title>'+esc(label)+' ('+esc(ntype)+')</title></circle>';
    h+='<text x="'+p.x+'" y="'+(p.y+22)+'" fill="#a1a1aa" font-size="10" text-anchor="middle">'+esc(label.length>20?label.slice(0,18)+'..':label)+'</text>';
  });
  h+='</svg></div></div>';
  h+='<div class="card"><h2>Legend</h2><div style="display:flex;flex-wrap:wrap;gap:12px">';
  Object.keys(typeColors).forEach(function(t){h+='<span class="ml"><span style="color:'+typeColors[t]+'">&#9679;</span> '+t.replace(/_/g,' ')+'</span>'});
  h+='</div></div>';
  h+='<div class="card"><h2>Node List</h2><table><thead><tr><th>Name</th><th>Type</th><th>Files</th></tr></thead><tbody>';
  nodes.slice(0,50).forEach(function(n){var d=n.data||n;h+='<tr><td>'+esc(d.label||d.name||n.id)+'</td><td>'+esc(d.type||d.component_type||'-')+'</td><td>'+esc((d.files||[]).join(', ')||'-')+'</td></tr>'});
  if(nodes.length>50)h+='<tr><td colspan="3" class="ml">... and '+(nodes.length-50)+' more</td></tr>';
  h+='</tbody></table></div>';
  el.innerHTML=h;
}
function renderPolicies(data,el){
  var passed=data.passed!==false;var results=data.results||[];
  var h='<div class="card" style="border-color:'+(passed?'#22c55e':'#ef4444')+'"><div style="display:flex;align-items:center;gap:12px"><span style="font-size:2rem">'+(passed?'&#10003;':'&#10007;')+'</span>';
  h+='<div><div style="font-size:1.2rem;font-weight:700;color:'+(passed?'#4ade80':'#f87171')+'">'+(passed?'All Policies Passed':'Policy Violations Detected')+'</div>';
  h+='<div class="ml">'+(data.message||results.length+' policies evaluated')+'</div></div></div></div>';
  if(results.length){
    h+='<div class="card"><h2>Policy Results</h2><table><thead><tr><th>Policy</th><th>Status</th><th>Details</th></tr></thead><tbody>';
    results.forEach(function(r){
      var ok=r.passed!==false&&r.status!=='fail';
      h+='<tr><td style="font-weight:600">'+esc(r.name||r.policy||'-')+'</td><td>'+(ok?'<span class="badge b-pass">Pass</span>':'<span class="badge b-fail">Fail</span>')+'</td><td class="ml">'+esc(r.message||r.details||r.reason||'-')+'</td></tr>'});
    h+='</tbody></table></div>';
  }
  if(!results.length&&data.message){
    h+='<div class="card"><div class="empty"><p>'+esc(data.message)+'</p><p style="margin-top:8px;color:#71717a">Create a <code style="background:#27272a;padding:2px 6px;border-radius:4px">.scanllm/policies.yaml</code> file to define policies.</p></div></div>';
  }
  el.innerHTML=h;
}
function renderHistory(data,el){
  if(!data||!data.length){el.innerHTML='<div class="empty">No scan history yet. Run your first scan.</div>';return}
  var h='<div class="card"><h2>Scan History ('+data.length+' scans)</h2><table><thead><tr><th>Date</th><th>Risk Score</th><th>Grade</th><th>Findings</th></tr></thead><tbody>';
  data.forEach(function(s){
    var ts=s.timestamp||s.created_at||'';var d=ts?new Date(ts):null;var dateStr=d?d.toLocaleDateString()+' '+d.toLocaleTimeString():'Unknown';
    var risk=s.risk||{};var summary=s.summary||{};var grade=risk.grade||s.grade||'?';var score=risk.overall_score||s.risk_score||0;
    h+='<tr><td>'+esc(dateStr)+'</td><td><span style="color:'+gradeColor(grade)+'">'+score+'/100</span></td><td class="grade-'+grade+'">'+esc(grade)+'</td><td>'+(summary.total_findings||s.total_findings||0)+'</td></tr>'});
  h+='</tbody></table></div>';
  el.innerHTML=h;
}
function renderExport(data,el){
  var h='<div class="grid grid-3">';
  h+='<div class="card" style="text-align:center"><div style="font-size:2rem;margin-bottom:8px">&#128196;</div><h2>JSON Report</h2><p class="ml" style="margin-bottom:12px">Full scan data in JSON format</p><button class="btn" onclick="exportJSON()">Download JSON</button></div>';
  h+='<div class="card" style="text-align:center"><div style="font-size:2rem;margin-bottom:8px">&#128202;</div><h2>CSV Findings</h2><p class="ml" style="margin-bottom:12px">Findings table as CSV</p><button class="btn" onclick="exportCSV()">Download CSV</button></div>';
  h+='<div class="card" style="text-align:center"><div style="font-size:2rem;margin-bottom:8px">&#128203;</div><h2>Copy Summary</h2><p class="ml" style="margin-bottom:12px">Text summary to clipboard</p><button class="btn" onclick="copySummary()">Copy</button></div>';
  h+='</div>';
  h+='<div class="card" style="text-align:center"><h2>Re-scan Repository</h2><p class="ml" style="margin-bottom:12px">Trigger a fresh scan from the dashboard</p><button class="btn" onclick="triggerScan()" id="scan-btn">Run Scan</button><p id="scan-status" class="ml" style="margin-top:8px"></p></div>';
  h+='<p id="export-status" class="ml" style="text-align:center;margin-top:8px"></p>';
  el.innerHTML=h;
}
function exportJSON(){
  var data=_cache['/api/scan/latest'];if(!data){showExportStatus('No scan data cached','#f87171');return}
  var blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});var a=document.createElement('a');
  a.href=URL.createObjectURL(blob);a.download='scanllm-report.json';a.click();URL.revokeObjectURL(a.href);showExportStatus('JSON downloaded!','#4ade80');
}
function exportCSV(){
  var data=_cache['/api/scan/latest'];if(!data||!data.findings){showExportStatus('No findings to export','#f87171');return}
  var rows=[['Severity','Type','File','Line','Description']];
  data.findings.forEach(function(f){rows.push([f.severity||'',f.type||f.component_type||'',f.file||'',(f.line||'').toString(),'"'+(f.description||f.message||'').replace(/"/g,'""')+'"'])});
  var csv=rows.map(function(r){return r.join(',')}).join('\\n');
  var blob=new Blob([csv],{type:'text/csv'});var a=document.createElement('a');
  a.href=URL.createObjectURL(blob);a.download='scanllm-findings.csv';a.click();URL.revokeObjectURL(a.href);showExportStatus('CSV downloaded!','#4ade80');
}
function copySummary(){
  var data=_cache['/api/scan/latest'];if(!data){showExportStatus('No data','#f87171');return}
  var s=data.summary||{};var r=data.risk||{};
  var txt='ScanLLM Report\\n'+'Risk: '+((r.overall_score||0)+'/100 (Grade '+(r.grade||'?')+')')+'\\n'+'Findings: '+(s.total_findings||0)+'\\n'+'Files: '+(s.files_scanned||0)+'\\n'+'Providers: '+Object.keys(s.providers||{}).join(', ');
  navigator.clipboard.writeText(txt).then(function(){showExportStatus('Copied!','#4ade80')}).catch(function(){showExportStatus('Copy failed','#f87171')});
}
function showExportStatus(msg,color){var el=document.getElementById('export-status');if(el){el.textContent=msg;el.style.color=color;setTimeout(function(){el.textContent=''},3000)}}
function triggerScan(){
  var btn=document.getElementById('scan-btn');var st=document.getElementById('scan-status');
  btn.disabled=true;btn.textContent='Scanning...';st.textContent='Running scan...';st.style.color='#22d3ee';
  _cache={};
  fetch('/api/scan',{method:'POST'}).then(function(r){return r.json()}).then(function(d){
    if(d.error){st.textContent='Error: '+d.error;st.style.color='#f87171'}
    else{_cache['/api/scan/latest']=d;st.textContent='Scan complete!';st.style.color='#4ade80';setTimeout(function(){switchTab('overview',document.querySelector('.tab-btn'))},1000)}
  }).catch(function(e){st.textContent='Scan failed: '+e.message;st.style.color='#f87171'}).finally(function(){btn.disabled=false;btn.textContent='Run Scan'});
}
function openFeedback(){document.getElementById('fb-modal').classList.add('open');initStars()}
function closeFeedback(){document.getElementById('fb-modal').classList.remove('open');_fbRating=0}
function initStars(){var c=document.getElementById('fb-stars');c.innerHTML='';for(var i=1;i<=5;i++){var s=document.createElement('span');s.className='star';s.textContent='\\u2605';s.dataset.v=i;s.onclick=function(){_fbRating=parseInt(this.dataset.v);document.querySelectorAll('.star').forEach(function(st){st.classList.toggle('on',parseInt(st.dataset.v)<=_fbRating)})};c.appendChild(s)}}
function submitFeedback(){
  var msg=document.getElementById('fb-msg').value;var cat=document.getElementById('fb-cat').value;var st=document.getElementById('fb-status');
  if(!msg.trim()){st.textContent='Please enter a message';st.style.color='#f87171';return}
  st.textContent='Sending...';st.style.color='#22d3ee';
  fetch('/api/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rating:_fbRating,category:cat,message:msg,page:'dashboard'})})
    .then(function(r){return r.json()}).then(function(){st.textContent='Thanks for your feedback!';st.style.color='#4ade80';setTimeout(closeFeedback,1500)})
    .catch(function(){st.textContent='Failed to send';st.style.color='#f87171'});
}
loadTab('overview');
</script>
</body>
</html>"""


def create_app(repo_path: Path) -> Any:
    """Create a FastAPI app that serves scan data and the dashboard UI."""
    try:
        from fastapi import FastAPI, Request
        from fastapi.responses import HTMLResponse, JSONResponse
    except ImportError:
        raise ImportError(
            "FastAPI is required for `scanllm ui`. Install with: pip install scanllm[server]"
        )

    from cli.config import ScanLLMConfig

    config = ScanLLMConfig(repo_path)
    app = FastAPI(title="ScanLLM Local Dashboard", docs_url=None, redoc_url=None)

    @app.get("/", response_class=HTMLResponse)
    async def index():
        return HTMLResponse(_FALLBACK_HTML)

    @app.on_event("startup")
    async def _auto_scan_if_empty():
        """Auto-run an initial scan if no saved scans exist."""
        if config.get_latest_scan() is not None:
            return
        logger.info("No saved scans found — running initial scan on %s", repo_path)
        try:
            from core.scanner.engine import ScanEngine
            from core.scoring.risk_engine import RiskEngine
            from core.scoring.owasp_mapper import OwaspMapper
            from core.graph.builder import GraphBuilder
            from core.graph.serializer import GraphSerializer
            from core.graph.analyzer import GraphAnalyzer
            from datetime import datetime, timezone

            engine = ScanEngine()
            result = engine.scan(repo_path)
            findings = result.get("findings", [])

            builder = GraphBuilder()
            graph = builder.build(findings)
            serializer = GraphSerializer()
            graph_data = serializer.to_react_flow(graph)

            analyzer = GraphAnalyzer()
            graph_analysis = analyzer.analyze(graph)
            risk_engine = RiskEngine()
            risk_result = risk_engine.score(findings, graph_analysis)

            owasp_mapper = OwaspMapper()
            owasp_result = owasp_mapper.map_findings(findings)

            result["risk"] = risk_result
            result["owasp"] = owasp_result
            result["graph"] = graph_data
            result["risk_score"] = risk_result.get("overall_score", 0)
            result["timestamp"] = datetime.now(timezone.utc).isoformat()

            if not config.is_initialized():
                config.initialize()
            config.save_scan(result)
            logger.info("Auto-scan complete — %d findings saved", len(findings))
        except Exception as exc:
            logger.warning("Auto-scan failed: %s", exc)

    @app.get("/api/scan/latest")
    async def latest_scan():
        data = config.get_latest_scan()
        if data is None:
            return JSONResponse({"error": "No scans found. Click 'Run Scan' on the Export tab."})
        return JSONResponse(data)

    @app.get("/api/scan/history")
    async def scan_history():
        scans = config.get_scan_history()
        return JSONResponse(scans)

    @app.get("/api/graph")
    async def graph():
        data = config.get_latest_scan()
        if not data:
            return JSONResponse({"nodes": [], "edges": []})
        return JSONResponse(data.get("graph", {"nodes": [], "edges": []}))

    @app.get("/api/risk")
    async def risk():
        data = config.get_latest_scan()
        if not data:
            return JSONResponse({"overall_score": 0, "grade": "A"})
        return JSONResponse(data.get("risk", {"overall_score": 0, "grade": "A"}))

    @app.get("/api/owasp")
    async def owasp():
        data = config.get_latest_scan()
        if not data:
            return JSONResponse({"categories": [], "coverage": {}})
        return JSONResponse(data.get("owasp", {"categories": [], "coverage": {}}))

    @app.get("/api/policy")
    async def policy_eval():
        data = config.get_latest_scan()
        if not data:
            return JSONResponse({"passed": True, "results": []})

        # Run policy evaluation if policies exist
        policies_path = config.get_policies_path()
        if not policies_path:
            return JSONResponse({"passed": True, "results": [], "message": "No policies configured"})

        try:
            from core.policy.engine import PolicyEngine
            engine = PolicyEngine(policies_path=policies_path)
            findings = data.get("findings", [])
            summary = data.get("summary", {})
            result = engine.evaluate(findings, summary)
            return JSONResponse(result.to_dict())
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.get("/api/cost")
    async def cost_estimate():
        data = config.get_latest_scan()
        if not data:
            return JSONResponse({"models": [], "total_models_detected": 0})
        from core.cost.estimator import CostEstimator
        estimator = CostEstimator()
        result = estimator.estimate(data.get("findings", []))
        return JSONResponse(result.to_dict())

    @app.post("/api/feedback")
    async def submit_feedback(request: Request):
        """Save user feedback to local .scanllm/feedback.json."""
        body = await request.json()
        feedback_file = config.base_dir / "feedback.json"
        existing = []
        if feedback_file.exists():
            existing = json.loads(feedback_file.read_text())
        from datetime import datetime, timezone
        body["created_at"] = datetime.now(timezone.utc).isoformat()
        existing.append(body)
        feedback_file.write_text(json.dumps(existing, indent=2))
        return JSONResponse({"status": "ok", "message": "Thanks for your feedback!"})

    @app.post("/api/scan")
    async def trigger_scan():
        """Trigger a new scan from the UI."""
        try:
            from core.scanner.engine import ScanEngine
            from core.scoring.risk_engine import RiskEngine
            from core.scoring.owasp_mapper import OwaspMapper
            from core.graph.builder import GraphBuilder
            from core.graph.serializer import GraphSerializer
            from core.graph.analyzer import GraphAnalyzer

            engine = ScanEngine()
            result = engine.scan(repo_path)
            findings = result.get("findings", [])

            builder = GraphBuilder()
            graph = builder.build(findings)
            serializer = GraphSerializer()
            graph_data = serializer.to_react_flow(graph)

            analyzer = GraphAnalyzer()
            graph_analysis = analyzer.analyze(graph)
            risk_engine = RiskEngine()
            risk_result = risk_engine.score(findings, graph_analysis)

            owasp_mapper = OwaspMapper()
            owasp_result = owasp_mapper.map_findings(findings)

            from datetime import datetime, timezone
            result["risk"] = risk_result
            result["owasp"] = owasp_result
            result["graph"] = graph_data
            result["risk_score"] = risk_result.get("overall_score", 0)
            result["timestamp"] = datetime.now(timezone.utc).isoformat()

            config.save_scan(result)
            return JSONResponse(result)
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    return app


# Module-level app instance for uvicorn string import ("cli.server.app:app").
# Only created when this module is actually imported at runtime (i.e. when uvicorn loads it),
# not at CLI startup time.
def _get_app():
    import os as _os
    return create_app(Path(_os.environ.get("SCANLLM_REPO_PATH", ".")))

# Lazy — evaluated by uvicorn when it loads "cli.server.app:app"
import os as _os
if _os.environ.get("SCANLLM_REPO_PATH"):
    app = create_app(Path(_os.environ["SCANLLM_REPO_PATH"]))
else:
    app = None
