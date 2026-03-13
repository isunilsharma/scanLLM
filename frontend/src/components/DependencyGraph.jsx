import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from './ui/sheet';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import {
  Brain, Database, Layers, Bot, Server, Cpu, Hash,
  Download, AlertTriangle, FileCode, ExternalLink, X
} from 'lucide-react';

// Check if @xyflow/react is available
let ReactFlow, MiniMap, Controls, Background, useNodesState, useEdgesState, Handle, Position;
let xyflowAvailable = false;

try {
  const xyflow = require('@xyflow/react');
  ReactFlow = xyflow.ReactFlow;
  MiniMap = xyflow.MiniMap;
  Controls = xyflow.Controls;
  Background = xyflow.Background;
  useNodesState = xyflow.useNodesState;
  useEdgesState = xyflow.useEdgesState;
  Handle = xyflow.Handle;
  Position = xyflow.Position;
  xyflowAvailable = true;
  require('@xyflow/react/dist/style.css');
} catch (e) {
  // @xyflow/react not installed
}

const NODE_TYPE_CONFIG = {
  llm_provider: { color: '#3b82f6', bgColor: '#eff6ff', borderColor: '#bfdbfe', icon: Brain, label: 'LLM Provider' },
  vector_db: { color: '#8b5cf6', bgColor: '#f5f3ff', borderColor: '#ddd6fe', icon: Database, label: 'Vector DB' },
  orchestration_framework: { color: '#22c55e', bgColor: '#f0fdf4', borderColor: '#bbf7d0', icon: Layers, label: 'Framework' },
  agent_tool: { color: '#f59e0b', bgColor: '#fffbeb', borderColor: '#fde68a', icon: Bot, label: 'Agent Tool' },
  mcp_server: { color: '#06b6d4', bgColor: '#ecfeff', borderColor: '#a5f3fc', icon: Server, label: 'MCP Server' },
  inference_server: { color: '#ec4899', bgColor: '#fdf2f8', borderColor: '#fbcfe8', icon: Cpu, label: 'Inference Server' },
  embedding_service: { color: '#6366f1', bgColor: '#eef2ff', borderColor: '#c7d2fe', icon: Hash, label: 'Embedding' },
};

const DEFAULT_CONFIG = { color: '#64748b', bgColor: '#f8fafc', borderColor: '#e2e8f0', icon: FileCode, label: 'Component' };

function getNodeConfig(type) {
  return NODE_TYPE_CONFIG[type] || DEFAULT_CONFIG;
}

function getRiskColor(score) {
  if (score == null) return '#94a3b8';
  if (score >= 75) return '#ef4444';
  if (score >= 50) return '#f59e0b';
  if (score >= 25) return '#eab308';
  return '#22c55e';
}

// Custom node component for the graph
const CustomNode = ({ data, selected }) => {
  const config = getNodeConfig(data.type);
  const Icon = config.icon;
  const riskColor = getRiskColor(data.risk_score);

  return (
    <div
      className="relative"
      style={{
        minWidth: 180,
        maxWidth: 240,
        borderRadius: 12,
        border: `2px solid ${selected ? config.color : config.borderColor}`,
        backgroundColor: config.bgColor,
        padding: '12px 16px',
        cursor: 'pointer',
        boxShadow: selected ? `0 0 0 2px ${config.color}40` : '0 1px 3px rgba(0,0,0,0.08)',
        transition: 'box-shadow 0.2s, border-color 0.2s',
      }}
    >
      {xyflowAvailable && Handle && Position && (
        <>
          <Handle type="target" position={Position.Top} style={{ background: config.color, width: 8, height: 8 }} />
          <Handle type="source" position={Position.Bottom} style={{ background: config.color, width: 8, height: 8 }} />
        </>
      )}

      <div className="flex items-start gap-2">
        <div
          className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: `${config.color}20` }}
        >
          <Icon size={16} style={{ color: config.color }} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-slate-900 truncate">{data.label}</p>
          <div className="flex items-center gap-1.5 mt-1">
            <span
              className="text-[10px] font-medium px-1.5 py-0.5 rounded-full"
              style={{ backgroundColor: `${config.color}15`, color: config.color }}
            >
              {config.label}
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between mt-2 pt-2 border-t" style={{ borderColor: config.borderColor }}>
        <span className="text-[11px] text-slate-500">
          {data.file_count || 0} file{(data.file_count || 0) !== 1 ? 's' : ''}
        </span>
        {data.risk_score != null && (
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: riskColor }} />
            <span className="text-[11px] font-medium" style={{ color: riskColor }}>
              {data.risk_score}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

const nodeTypes = { custom: CustomNode };

// Node detail panel content
const NodeDetailPanel = ({ node, onClose }) => {
  if (!node) return null;

  const config = getNodeConfig(node.data.type);
  const Icon = config.icon;

  return (
    <>
      <SheetHeader>
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: `${config.color}15` }}
          >
            <Icon size={20} style={{ color: config.color }} />
          </div>
          <div>
            <SheetTitle>{node.data.label}</SheetTitle>
            <SheetDescription>
              <Badge variant="outline" className="mt-1" style={{ borderColor: config.color, color: config.color }}>
                {config.label}
              </Badge>
            </SheetDescription>
          </div>
        </div>
      </SheetHeader>

      <Separator className="my-4" />

      <ScrollArea className="h-[calc(100vh-200px)]">
        <div className="space-y-6 pr-2">
          {/* Risk Score */}
          {node.data.risk_score != null && (
            <div>
              <h4 className="text-sm font-medium text-slate-900 mb-2">Risk Score</h4>
              <div className="flex items-center gap-3">
                <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${node.data.risk_score}%`,
                      backgroundColor: getRiskColor(node.data.risk_score),
                    }}
                  />
                </div>
                <span className="text-sm font-semibold" style={{ color: getRiskColor(node.data.risk_score) }}>
                  {node.data.risk_score}/100
                </span>
              </div>
            </div>
          )}

          {/* Model Details */}
          {node.data.models && node.data.models.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-900 mb-2">Models</h4>
              <div className="flex flex-wrap gap-1.5">
                {node.data.models.map((model, i) => (
                  <Badge key={i} variant="secondary" className="text-xs">
                    {model}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Files */}
          {node.data.files && node.data.files.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-900 mb-2">
                Files ({node.data.files.length})
              </h4>
              <div className="space-y-2">
                {node.data.files.map((file, i) => (
                  <div
                    key={i}
                    className="p-3 bg-slate-50 rounded-lg border border-slate-100"
                  >
                    <p className="text-xs font-mono text-slate-700 truncate">{file.path}</p>
                    {file.lines && file.lines.length > 0 && (
                      <p className="text-[11px] text-slate-500 mt-1">
                        Lines: {file.lines.join(', ')}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Risk Flags */}
          {node.data.risk_flags && node.data.risk_flags.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-900 mb-2">Risk Flags</h4>
              <div className="space-y-2">
                {node.data.risk_flags.map((flag, i) => (
                  <div key={i} className="flex items-start gap-2 p-2 bg-amber-50 rounded-lg border border-amber-100">
                    <AlertTriangle size={14} className="text-amber-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs font-medium text-amber-800">{flag.title || flag.owasp}</p>
                      <p className="text-[11px] text-amber-700 mt-0.5">{flag.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Metadata */}
          {node.data.metadata && Object.keys(node.data.metadata).length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-slate-900 mb-2">Metadata</h4>
              <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                {Object.entries(node.data.metadata).map(([key, value]) => (
                  <div key={key} className="flex justify-between py-1 text-xs">
                    <span className="text-slate-500">{key}</span>
                    <span className="text-slate-700 font-medium">{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </ScrollArea>
    </>
  );
};

const DependencyGraph = ({ graphData }) => {
  const [selectedNode, setSelectedNode] = useState(null);
  const [sheetOpen, setSheetOpen] = useState(false);

  // If @xyflow/react is not available, show fallback
  if (!xyflowAvailable) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Dependency Graph</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Layers size={48} className="text-slate-300 mb-4" />
            <p className="text-slate-600 font-medium mb-2">
              Install @xyflow/react to enable dependency graph visualization
            </p>
            <code className="text-xs bg-slate-100 px-3 py-1.5 rounded-md text-slate-600">
              npm install @xyflow/react
            </code>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <DependencyGraphInner
      graphData={graphData}
      selectedNode={selectedNode}
      setSelectedNode={setSelectedNode}
      sheetOpen={sheetOpen}
      setSheetOpen={setSheetOpen}
    />
  );
};

const DependencyGraphInner = ({ graphData, selectedNode, setSelectedNode, sheetOpen, setSheetOpen }) => {
  // Process nodes for React Flow
  const initialNodes = useMemo(() => {
    if (!graphData?.nodes?.length) return [];
    return graphData.nodes.map((node) => ({
      id: node.id,
      type: 'custom',
      position: node.position || { x: 0, y: 0 },
      data: {
        label: node.data?.label || node.label || node.id,
        type: node.data?.type || node.type || 'component',
        file_count: node.data?.file_count || node.data?.files?.length || 0,
        risk_score: node.data?.risk_score ?? null,
        files: node.data?.files || [],
        models: node.data?.models || [],
        risk_flags: node.data?.risk_flags || [],
        metadata: node.data?.metadata || {},
      },
    }));
  }, [graphData]);

  // Process edges
  const initialEdges = useMemo(() => {
    if (!graphData?.edges?.length) return [];
    return graphData.edges.map((edge) => ({
      id: edge.id || `${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
      label: edge.label || edge.data?.label || '',
      type: 'smoothstep',
      animated: edge.animated || false,
      style: { stroke: '#94a3b8', strokeWidth: 1.5 },
      labelStyle: { fontSize: 10, fill: '#64748b' },
      labelBgStyle: { fill: '#fff', fillOpacity: 0.9 },
      labelBgPadding: [4, 2],
      labelBgBorderRadius: 4,
    }));
  }, [graphData]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update when graphData changes
  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
    setSheetOpen(true);
  }, [setSelectedNode, setSheetOpen]);

  const handleExportPng = useCallback(() => {
    const svgElement = document.querySelector('.react-flow__viewport');
    if (!svgElement) return;

    const canvas = document.createElement('canvas');
    const rect = svgElement.getBoundingClientRect();
    canvas.width = rect.width * 2;
    canvas.height = rect.height * 2;
    const ctx = canvas.getContext('2d');
    ctx.scale(2, 2);

    const svgData = new XMLSerializer().serializeToString(svgElement);
    const img = new Image();
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);

    img.onload = () => {
      ctx.drawImage(img, 0, 0);
      URL.revokeObjectURL(url);
      const a = document.createElement('a');
      a.download = 'dependency-graph.png';
      a.href = canvas.toDataURL('image/png');
      a.click();
    };
    img.src = url;
  }, []);

  // Empty state
  if (!graphData?.nodes?.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Dependency Graph</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Layers size={48} className="text-slate-300 mb-4" />
            <p className="text-slate-500 mb-1">No dependency graph data available</p>
            <p className="text-xs text-slate-400">Run a full scan to generate the AI dependency graph</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // MiniMap color function
  const miniMapNodeColor = (node) => {
    const config = getNodeConfig(node.data?.type);
    return config.color;
  };

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between py-4">
        <CardTitle className="text-lg">AI Dependency Graph</CardTitle>
        <div className="flex items-center gap-2">
          {/* Legend */}
          <div className="hidden lg:flex items-center gap-3 mr-4">
            {Object.entries(NODE_TYPE_CONFIG).map(([key, config]) => {
              const Icon = config.icon;
              return (
                <div key={key} className="flex items-center gap-1">
                  <Icon size={12} style={{ color: config.color }} />
                  <span className="text-[10px] text-slate-500">{config.label}</span>
                </div>
              );
            })}
          </div>
          <Button variant="outline" size="sm" onClick={handleExportPng}>
            <Download size={14} className="mr-1.5" />
            PNG
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div style={{ height: 600 }} className="border-t border-slate-200">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            minZoom={0.2}
            maxZoom={2}
            attributionPosition="bottom-left"
          >
            <Controls position="top-right" />
            <MiniMap
              nodeColor={miniMapNodeColor}
              nodeStrokeWidth={3}
              zoomable
              pannable
              style={{ border: '1px solid #e2e8f0', borderRadius: 8 }}
            />
            <Background color="#e2e8f0" gap={20} size={1} />
          </ReactFlow>
        </div>
      </CardContent>

      {/* Node Detail Sheet */}
      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent side="right" className="w-full sm:max-w-md">
          <NodeDetailPanel
            node={selectedNode}
            onClose={() => setSheetOpen(false)}
          />
        </SheetContent>
      </Sheet>
    </Card>
  );
};

export default DependencyGraph;
