import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from './ui/sheet';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import {
  Brain, Database, Layers, Bot, Server, Cpu, Hash,
  Download, AlertTriangle, FileCode, ChevronRight,
  Filter, Eye, EyeOff, KeyRound
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

// Check if dagre is available
let dagre = null;
try {
  dagre = require('@dagrejs/dagre');
} catch (e) {
  try {
    dagre = require('dagre');
  } catch (e2) {
    // dagre not installed, will use backend positions
  }
}

// ---------------------------------------------------------------------------
// Node type configuration with dark-theme-compatible colors
// ---------------------------------------------------------------------------
const NODE_TYPE_CONFIG = {
  llm_provider: {
    color: '#3b82f6',
    bgColor: 'rgba(59,130,246,0.15)',
    borderColor: 'rgba(59,130,246,0.4)',
    icon: Brain,
    label: 'LLM Provider',
    filterKey: 'llm_provider',
  },
  vector_db: {
    color: '#8b5cf6',
    bgColor: 'rgba(139,92,246,0.15)',
    borderColor: 'rgba(139,92,246,0.4)',
    icon: Database,
    label: 'Vector DB',
    filterKey: 'vector_db',
  },
  orchestration_framework: {
    color: '#22c55e',
    bgColor: 'rgba(34,197,94,0.15)',
    borderColor: 'rgba(34,197,94,0.4)',
    icon: Layers,
    label: 'Framework',
    filterKey: 'orchestration_framework',
  },
  agent_tool: {
    color: '#f59e0b',
    bgColor: 'rgba(245,158,11,0.15)',
    borderColor: 'rgba(245,158,11,0.4)',
    icon: Bot,
    label: 'Agent Tool',
    filterKey: 'agent_tool',
  },
  mcp_server: {
    color: '#06b6d4',
    bgColor: 'rgba(6,182,212,0.15)',
    borderColor: 'rgba(6,182,212,0.4)',
    icon: Server,
    label: 'MCP Server',
    filterKey: 'mcp_server',
  },
  inference_server: {
    color: '#ec4899',
    bgColor: 'rgba(236,72,153,0.15)',
    borderColor: 'rgba(236,72,153,0.4)',
    icon: Cpu,
    label: 'Inference Server',
    filterKey: 'inference_server',
  },
  embedding_service: {
    color: '#6366f1',
    bgColor: 'rgba(99,102,241,0.15)',
    borderColor: 'rgba(99,102,241,0.4)',
    icon: Hash,
    label: 'Embedding',
    filterKey: 'embedding_service',
  },
  secret: {
    color: '#ef4444',
    bgColor: 'rgba(239,68,68,0.15)',
    borderColor: 'rgba(239,68,68,0.4)',
    icon: KeyRound,
    label: 'Secret',
    filterKey: 'secret',
  },
  config_reference: {
    color: '#71717a',
    bgColor: 'rgba(113,113,122,0.15)',
    borderColor: 'rgba(113,113,122,0.4)',
    icon: FileCode,
    label: 'Config',
    filterKey: 'config_reference',
  },
};

const DEFAULT_CONFIG = {
  color: '#71717a',
  bgColor: 'rgba(113,113,122,0.15)',
  borderColor: 'rgba(113,113,122,0.4)',
  icon: FileCode,
  label: 'Component',
  filterKey: 'unknown',
};

function getNodeConfig(type) {
  return NODE_TYPE_CONFIG[type] || DEFAULT_CONFIG;
}

function getRiskColor(score) {
  if (score == null || score === 0) return '#94a3b8';
  if (score >= 75) return '#ef4444';
  if (score >= 50) return '#f59e0b';
  if (score >= 25) return '#eab308';
  return '#22c55e';
}

// ---------------------------------------------------------------------------
// Dagre layout helper
// ---------------------------------------------------------------------------
function applyDagreLayout(nodes, edges, direction = 'LR') {
  if (!dagre || !nodes.length) return nodes;

  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({
    rankdir: direction,
    nodesep: 80,
    ranksep: 200,
    marginx: 40,
    marginy: 40,
  });

  nodes.forEach((node) => {
    const isCluster = node.data?.is_cluster;
    g.setNode(node.id, {
      width: isCluster ? 260 : 220,
      height: isCluster ? 110 : 90,
    });
  });

  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target);
  });

  dagre.layout(g);

  return nodes.map((node) => {
    const pos = g.node(node.id);
    if (!pos) return node;
    return {
      ...node,
      position: {
        x: pos.x - (pos.width || 220) / 2,
        y: pos.y - (pos.height || 90) / 2,
      },
    };
  });
}

// ---------------------------------------------------------------------------
// Custom node component - handles both cluster and individual nodes
// ---------------------------------------------------------------------------
const CustomNode = ({ data, selected }) => {
  const config = getNodeConfig(data.component_type || data.type);
  const Icon = config.icon;
  const riskColor = getRiskColor(data.risk_score);
  const isCluster = data.is_cluster;
  const modelCount = data.model_count || 0;

  return (
    <div
      className="relative"
      style={{
        minWidth: isCluster ? 220 : 180,
        maxWidth: isCluster ? 280 : 240,
        borderRadius: 12,
        border: `2px solid ${selected ? config.color : config.borderColor}`,
        backgroundColor: config.bgColor,
        padding: '12px 16px',
        cursor: 'pointer',
        boxShadow: selected
          ? `0 0 0 2px ${config.color}40, 0 4px 12px rgba(0,0,0,0.4)`
          : '0 2px 8px rgba(0,0,0,0.3)',
        transition: 'box-shadow 0.2s, border-color 0.2s',
        backdropFilter: 'blur(8px)',
      }}
    >
      {xyflowAvailable && Handle && Position && (
        <>
          <Handle
            type="target"
            position={Position.Left}
            style={{
              background: config.color,
              width: 8,
              height: 8,
              border: `2px solid ${config.bgColor}`,
            }}
          />
          <Handle
            type="source"
            position={Position.Right}
            style={{
              background: config.color,
              width: 8,
              height: 8,
              border: `2px solid ${config.bgColor}`,
            }}
          />
        </>
      )}

      <div className="flex items-start gap-2.5">
        <div
          className="flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: `${config.color}25` }}
        >
          <Icon size={18} style={{ color: config.color }} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-zinc-100 truncate">
            {data.label}
          </p>
          <div className="flex items-center gap-1.5 mt-1">
            <span
              className="text-[10px] font-medium px-1.5 py-0.5 rounded-full"
              style={{
                backgroundColor: `${config.color}20`,
                color: config.color,
              }}
            >
              {config.label}
            </span>
            {isCluster && modelCount > 0 && (
              <span
                className="text-[10px] font-bold px-1.5 py-0.5 rounded-full"
                style={{
                  backgroundColor: `${config.color}30`,
                  color: config.color,
                }}
              >
                {modelCount} model{modelCount !== 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Cluster children preview */}
      {isCluster && data.children && data.children.length > 0 && (
        <div
          className="mt-2 pt-2 border-t flex flex-wrap gap-1"
          style={{ borderColor: `${config.color}20` }}
        >
          {data.children.slice(0, 3).map((child, i) => (
            <span
              key={i}
              className="text-[9px] px-1.5 py-0.5 rounded"
              style={{
                backgroundColor: `${config.color}10`,
                color: `${config.color}cc`,
              }}
            >
              {child}
            </span>
          ))}
          {data.children.length > 3 && (
            <span
              className="text-[9px] px-1.5 py-0.5 rounded"
              style={{
                backgroundColor: `${config.color}10`,
                color: `${config.color}99`,
              }}
            >
              +{data.children.length - 3} more
            </span>
          )}
        </div>
      )}

      <div
        className="flex items-center justify-between mt-2 pt-2 border-t"
        style={{ borderColor: `${config.color}15` }}
      >
        <span className="text-[11px] text-zinc-500">
          {data.file_count || 0} file{(data.file_count || 0) !== 1 ? 's' : ''}
        </span>
        <div className="flex items-center gap-2">
          {data.risk_score != null && data.risk_score > 0 && (
            <div className="flex items-center gap-1">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: riskColor }}
              />
              <span
                className="text-[11px] font-medium"
                style={{ color: riskColor }}
              >
                {data.risk_score}
              </span>
            </div>
          )}
          <ChevronRight size={12} className="text-zinc-600" />
        </div>
      </div>
    </div>
  );
};

const nodeTypes = { custom: CustomNode };

// ---------------------------------------------------------------------------
// Filter toggle bar
// ---------------------------------------------------------------------------
const FilterBar = ({ filters, onToggle, nodeCounts }) => {
  // Only show categories that have nodes
  const activeCategories = Object.entries(NODE_TYPE_CONFIG).filter(
    ([key]) => (nodeCounts[key] || 0) > 0
  );

  if (activeCategories.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-1.5 px-4 py-2 border-b border-zinc-800 bg-zinc-950/50">
      <Filter size={14} className="text-zinc-500 mr-1" />
      {activeCategories.map(([key, config]) => {
        const Icon = config.icon;
        const isVisible = filters[key] !== false;
        const count = nodeCounts[key] || 0;

        return (
          <button
            key={key}
            onClick={() => onToggle(key)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all"
            style={{
              backgroundColor: isVisible ? `${config.color}15` : 'transparent',
              color: isVisible ? config.color : '#52525b',
              border: `1px solid ${isVisible ? `${config.color}30` : '#27272a'}`,
              opacity: isVisible ? 1 : 0.5,
            }}
          >
            {isVisible ? (
              <Eye size={12} />
            ) : (
              <EyeOff size={12} />
            )}
            <Icon size={12} />
            <span>{config.label}</span>
            <span
              className="ml-0.5 px-1 py-0 rounded text-[10px]"
              style={{
                backgroundColor: isVisible ? `${config.color}20` : '#27272a',
              }}
            >
              {count}
            </span>
          </button>
        );
      })}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Node detail panel
// ---------------------------------------------------------------------------
const NodeDetailPanel = ({ node, onClose }) => {
  if (!node) return null;

  const data = node.data || {};
  const config = getNodeConfig(data.component_type || data.type);
  const Icon = config.icon;
  const isCluster = data.is_cluster;

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
            <SheetTitle className="text-zinc-100">{data.label}</SheetTitle>
            <SheetDescription>
              <Badge
                variant="outline"
                className="mt-1"
                style={{ borderColor: config.color, color: config.color }}
              >
                {config.label}
              </Badge>
              {isCluster && (
                <Badge
                  variant="outline"
                  className="mt-1 ml-1.5"
                  style={{ borderColor: config.color, color: config.color }}
                >
                  Cluster ({data.model_count || 0} models)
                </Badge>
              )}
            </SheetDescription>
          </div>
        </div>
      </SheetHeader>

      <Separator className="my-4" />

      <ScrollArea className="h-[calc(100vh-200px)]">
        <div className="space-y-6 pr-2">
          {/* Risk Score */}
          {data.risk_score != null && data.risk_score > 0 && (
            <div>
              <h4 className="text-sm font-medium text-zinc-100 mb-2">
                Risk Score
              </h4>
              <div className="flex items-center gap-3">
                <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${data.risk_score}%`,
                      backgroundColor: getRiskColor(data.risk_score),
                    }}
                  />
                </div>
                <span
                  className="text-sm font-semibold"
                  style={{ color: getRiskColor(data.risk_score) }}
                >
                  {data.risk_score}/100
                </span>
              </div>
            </div>
          )}

          {/* Children (models) for cluster nodes */}
          {isCluster && data.children && data.children.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-zinc-100 mb-2">
                Models ({data.children.length})
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {data.children.map((child, i) => (
                  <Badge
                    key={i}
                    variant="secondary"
                    className="text-xs"
                    style={{
                      backgroundColor: `${config.color}15`,
                      color: config.color,
                      borderColor: `${config.color}30`,
                    }}
                  >
                    {child}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Model Details (non-cluster) */}
          {!isCluster && data.models && data.models.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-zinc-100 mb-2">
                Models
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {data.models.map((model, i) => (
                  <Badge key={i} variant="secondary" className="text-xs">
                    {model}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Files */}
          {data.files && data.files.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-zinc-100 mb-2">
                Files ({data.files.length})
              </h4>
              <div className="space-y-2">
                {data.files.map((file, i) => {
                  const filePath = file.file_path || file.path || '';
                  const lineNumber = file.line_number;
                  const lines = file.lines;
                  return (
                    <div
                      key={i}
                      className="p-3 bg-zinc-800/50 rounded-lg border border-zinc-800"
                    >
                      <p className="text-xs font-mono text-zinc-300 truncate">
                        {filePath}
                      </p>
                      {lineNumber && (
                        <p className="text-[11px] text-zinc-500 mt-1">
                          Line {lineNumber}
                        </p>
                      )}
                      {lines && lines.length > 0 && (
                        <p className="text-[11px] text-zinc-500 mt-1">
                          Lines: {lines.join(', ')}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Risk Flags */}
          {data.risk_flags && data.risk_flags.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-zinc-100 mb-2">
                Risk Flags
              </h4>
              <div className="space-y-2">
                {data.risk_flags.map((flag, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2 p-2 bg-amber-500/10 rounded-lg border border-amber-500/20"
                  >
                    <AlertTriangle
                      size={14}
                      className="text-amber-500 mt-0.5 flex-shrink-0"
                    />
                    <div>
                      <p className="text-xs font-medium text-amber-300">
                        {flag.title || flag.owasp}
                      </p>
                      <p className="text-[11px] text-amber-400 mt-0.5">
                        {flag.message}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Metadata */}
          {data.metadata && Object.keys(data.metadata).length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-zinc-100 mb-2">
                Metadata
              </h4>
              <div className="bg-zinc-800/50 rounded-lg p-3 border border-zinc-800">
                {Object.entries(data.metadata).map(([key, value]) => (
                  <div key={key} className="flex justify-between py-1 text-xs">
                    <span className="text-zinc-500">{key}</span>
                    <span className="text-zinc-300 font-medium text-right max-w-[60%] truncate">
                      {Array.isArray(value) ? value.join(', ') : String(value)}
                    </span>
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

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
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
            <Layers size={48} className="text-zinc-600 mb-4" />
            <p className="text-zinc-400 font-medium mb-2">
              Install @xyflow/react to enable dependency graph visualization
            </p>
            <code className="text-xs bg-zinc-800 px-3 py-1.5 rounded-md text-zinc-400">
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

const DependencyGraphInner = ({
  graphData,
  selectedNode,
  setSelectedNode,
  sheetOpen,
  setSheetOpen,
}) => {
  // Category visibility filters
  const [filters, setFilters] = useState({});

  const toggleFilter = useCallback((key) => {
    setFilters((prev) => ({
      ...prev,
      [key]: prev[key] === false ? true : false,
    }));
  }, []);

  // Count nodes per category (before filtering)
  const nodeCounts = useMemo(() => {
    if (!graphData?.nodes?.length) return {};
    const counts = {};
    graphData.nodes.forEach((node) => {
      const ctype = node.data?.component_type || node.type || 'unknown';
      counts[ctype] = (counts[ctype] || 0) + 1;
    });
    return counts;
  }, [graphData]);

  // Process and filter nodes for React Flow
  const { filteredNodes, filteredEdges } = useMemo(() => {
    if (!graphData?.nodes?.length) return { filteredNodes: [], filteredEdges: [] };

    // Build the visible node set based on filters
    const visibleNodeIds = new Set();
    const processedNodes = [];

    graphData.nodes.forEach((node) => {
      const ctype = node.data?.component_type || node.type || 'unknown';
      if (filters[ctype] === false) return; // filtered out

      visibleNodeIds.add(node.id);
      processedNodes.push({
        id: node.id,
        type: 'custom',
        position: node.position || { x: 0, y: 0 },
        data: {
          label: node.data?.label || node.label || node.id,
          type: node.data?.component_type || node.type || 'component',
          component_type: node.data?.component_type || node.type || 'component',
          file_count: node.data?.file_count || node.data?.files?.length || 0,
          risk_score: node.data?.risk_score ?? null,
          files: node.data?.files || [],
          models: node.data?.models || [],
          children: node.data?.children || [],
          is_cluster: node.data?.is_cluster || false,
          model_count: node.data?.model_count || 0,
          risk_flags: node.data?.risk_flags || [],
          metadata: node.data?.metadata || {},
        },
      });
    });

    // Filter edges to only include visible nodes
    const processedEdges = (graphData.edges || [])
      .filter((edge) => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target))
      .map((edge) => {
        const rel = edge.label || edge.data?.label || '';
        const isHighPriority = ['feeds-into', 'has-access-to', 'import-chain'].includes(rel);

        return {
          id: edge.id || `${edge.source}-${edge.target}`,
          source: edge.source,
          target: edge.target,
          label: rel,
          type: 'smoothstep',
          animated: edge.animated || false,
          style: {
            stroke: isHighPriority ? '#52525b' : '#3f3f46',
            strokeWidth: isHighPriority ? 1.5 : 1,
            opacity: isHighPriority ? 0.8 : 0.4,
          },
          labelStyle: {
            fontSize: 10,
            fill: '#71717a',
            fontWeight: isHighPriority ? 500 : 400,
          },
          labelBgStyle: { fill: '#09090b', fillOpacity: 0.9 },
          labelBgPadding: [4, 2],
          labelBgBorderRadius: 4,
        };
      });

    // Apply dagre layout if available
    const layoutNodes = applyDagreLayout(processedNodes, processedEdges, 'LR');

    return { filteredNodes: layoutNodes, filteredEdges: processedEdges };
  }, [graphData, filters]);

  const [nodes, setNodes, onNodesChange] = useNodesState(filteredNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(filteredEdges);

  // Update when filtered data changes
  useEffect(() => {
    setNodes(filteredNodes);
    setEdges(filteredEdges);
  }, [filteredNodes, filteredEdges, setNodes, setEdges]);

  const onNodeClick = useCallback(
    (event, node) => {
      setSelectedNode(node);
      setSheetOpen(true);
    },
    [setSelectedNode, setSheetOpen]
  );

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
    const svgBlob = new Blob([svgData], {
      type: 'image/svg+xml;charset=utf-8',
    });
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
            <Layers size={48} className="text-zinc-600 mb-4" />
            <p className="text-zinc-500 mb-1">
              No dependency graph data available
            </p>
            <p className="text-xs text-zinc-500">
              Run a full scan to generate the AI dependency graph
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Stats summary
  const totalNodes = graphData.nodes?.length || 0;
  const totalEdges = graphData.edges?.length || 0;
  const clusterCount = (graphData.nodes || []).filter(
    (n) => n.data?.is_cluster
  ).length;

  // MiniMap color function
  const miniMapNodeColor = (node) => {
    const config = getNodeConfig(node.data?.component_type || node.data?.type);
    return config.color;
  };

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between py-3">
        <div className="flex items-center gap-3">
          <CardTitle className="text-lg">AI Dependency Graph</CardTitle>
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <span>{totalNodes} nodes</span>
            <span className="text-zinc-700">|</span>
            <span>{totalEdges} edges</span>
            {clusterCount > 0 && (
              <>
                <span className="text-zinc-700">|</span>
                <span>{clusterCount} clustered</span>
              </>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleExportPng}>
            <Download size={14} className="mr-1.5" />
            PNG
          </Button>
        </div>
      </CardHeader>

      {/* Filter bar */}
      <FilterBar
        filters={filters}
        onToggle={toggleFilter}
        nodeCounts={nodeCounts}
      />

      <CardContent className="p-0">
        <div style={{ height: 600 }} className="bg-zinc-950">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.3 }}
            minZoom={0.1}
            maxZoom={2}
            attributionPosition="bottom-left"
            proOptions={{ hideAttribution: true }}
            defaultEdgeOptions={{
              type: 'smoothstep',
              style: { stroke: '#3f3f46', strokeWidth: 1 },
            }}
          >
            <Controls
              position="top-right"
              style={{
                borderRadius: 8,
                overflow: 'hidden',
                border: '1px solid #27272a',
              }}
            />
            <MiniMap
              nodeColor={miniMapNodeColor}
              nodeStrokeWidth={2}
              zoomable
              pannable
              maskColor="rgba(0,0,0,0.7)"
              style={{
                border: '1px solid #27272a',
                borderRadius: 8,
                backgroundColor: '#09090b',
              }}
            />
            <Background color="#1c1c1c" gap={24} size={1} />
          </ReactFlow>
        </div>
      </CardContent>

      {/* Node Detail Sheet */}
      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent side="right" className="w-full sm:max-w-md bg-zinc-950 border-zinc-800">
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
