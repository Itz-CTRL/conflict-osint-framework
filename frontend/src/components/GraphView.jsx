// src/components/GraphView.jsx
/**
 * Interactive Network Graph Visualization Component
 * Features:
 * - Zoom, pan, fit controls
 * - Node type & edge type filtering
 * - Confidence threshold slider
 * - Hover tooltips with metadata
 * - Export to PNG/SVG
 * - Real-time node selection
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { Network, DataSet } from 'vis-network/standalone';
import 'vis-network/styles/vis-network.min.css';
import { THEMES } from '../themes';
import { EmptyState, Card } from './UI';
import { useCaseContext } from '../contexts/CaseContext';

// Node type colours
const TYPE_COLORS = {
  profile:   '#ef4444',
  platform:  '#06b6d4',
  email:     '#f59e0b',
  phone:     '#a855f7',
  keyword:   '#10b981',
  mention:   '#3b82f6',
  username:  '#ef4444',
  target:    '#ef4444',
  location:  '#f97316',
  org:       '#ec4899',
  default:   '#6366f1',
};

const NODE_TYPE_FILTERS = [
  { key: 'all',      label: '◉ All',       icon: '🌐' },
  { key: 'profile',  label: '👤 Profile',  icon: '👤' },
  { key: 'platform', label: '📱 Platform', icon: '📱' },
  { key: 'email',    label: '📧 Email',    icon: '📧' },
  { key: 'phone',    label: '☎️ Phone',    icon: '☎️' },
  { key: 'keyword',  label: '🔑 Keyword',  icon: '🔑' },
  { key: 'mention',  label: '💬 Mention',  icon: '💬' },
];

const EDGE_TYPE_FILTERS = [
  'MENTIONS',
  'CONNECTED_TO',
  'USES_EMAIL',
  'USES_PHONE',
  'POSTED_KEYWORD',
  'REPORTED_AS',
  'SIMILAR_USERNAME'
];

export default function GraphView({ graphData, theme, targetUsername }) {
  const t = THEMES[theme];
  const { selectedNode, setSelectedNode, graphFilters, setGraphFilters: setGraphViewFilters } = useCaseContext();
  
  const containerRef = useRef(null);
  const networkRef = useRef(null);
  const nodesDS = useRef(null);
  const edgesDS = useRef(null);

  // UI State
  const [nodeFilter, setNodeFilter] = useState('all');
  const [edgeFilters, setEdgeFilters] = useState(EDGE_TYPE_FILTERS);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.0);
  const [tooltip, setTooltip] = useState({ visible: false, content: null, x: 0, y: 0 });
  const [stats, setStats] = useState({ nodes: 0, edges: 0, density: 0, avgDegree: 0 });
  const [exporting, setExporting] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedNodeData, setSelectedNodeData] = useState(null);

  const nodes = graphData?.nodes || [];
  const edges = graphData?.edges || [];
  const graphStats = graphData?.statistics || {};

  /**
   * Build vis.js network with enriched node/edge data
   */
  const buildNetwork = useCallback(() => {
    if (!containerRef.current || !nodes.length) return;

    // Destroy existing network
    if (networkRef.current) {
      networkRef.current.destroy();
      networkRef.current = null;
    }

    // Process and enrich nodes
    const enrichedNodes = nodes.map(n => {
      const nodeType = n.type || 'default';
      const isTarget = nodeType === 'profile' && n.label === targetUsername;
      const color = TYPE_COLORS[nodeType] || TYPE_COLORS.default;
      
      return {
        ...n,
        id: String(n.id),
        color: {
          background: isTarget ? '#ef4444' : color,
          border: isTarget ? '#ff6666' : `${color}cc`,
          highlight: { background: color, border: '#fff' },
          hover: { background: `${color}dd`, border: '#fff' },
        },
        size: isTarget ? 32 : (n.size || 18),
        font: {
          size: isTarget ? 14 : 11,
          color: '#fff',
          face: 'Sora, sans-serif',
          strokeWidth: 3,
          strokeColor: '#000',
          bold: isTarget ? { enabled: true } : {},
        },
        shadow: isTarget ? {
          enabled: true,
          color: '#ef4444',
          size: 24,
          x: 0,
          y: 0,
          blur: 12,
        } : { enabled: false },
        borderWidth: isTarget ? 3 : 1.5,
        borderWidthSelected: 3,
        _nodeType: nodeType,
        _isTarget: isTarget,
        _riskLevel: n.risk_level || 'UNKNOWN',
      };
    });

    // Process and enrich edges
    const enrichedEdges = edges.map(e => {
      const confidence = e.confidence || e.weight || 1.0;
      return {
        ...e,
        id: `${e.from}-${e.to}`,
        from: String(e.from),
        to: String(e.to),
        label: e.label || e.type || '',
        title: `Type: ${e.type}\nConfidence: ${(confidence * 100).toFixed(0)}%`,
        color: {
          color: getEdgeColor(e.type),
          highlight: getEdgeColor(e.type),
          hover: getEdgeColor(e.type),
          opacity: Math.max(0.3, confidence),
        },
        width: Math.max(1, (confidence || 1) * 3),
        font: {
          size: 9,
          color: t.textMuted,
          face: 'JetBrains Mono, monospace',
          align: 'middle',
        },
        smooth: {
          type: 'curvedCW',
          roundness: 0.15,
        },
        arrows: {
          to: {
            enabled: true,
            scaleFactor: 0.6,
            type: 'arrow',
          },
        },
        _confidence: confidence,
        _edgeType: e.type,
      };
    });

    nodesDS.current = new DataSet(enrichedNodes);
    edgesDS.current = new DataSet(enrichedEdges);

    const options = {
      physics: {
        enabled: true,
        barnesHut: {
          gravitationalConstant: -28000,
          centralGravity: 0.35,
          springLength: 200,
          springConstant: 0.035,
          damping: 0.15,
        },
        maxVelocity: 50,
        stabilization: {
          iterations: 200,
          fit: true,
        },
      },
      interaction: {
        hover: true,
        keyboard: {
          enabled: true,
          bindToWindow: false,
        },
        tooltipDelay: 150,
        multiselect: false,
        navigationButtons: false,
      },
      configure: false,
    };

    networkRef.current = new Network(
      containerRef.current,
      { nodes: nodesDS.current, edges: edgesDS.current },
      options
    );

    // Event: Network stabilized
    networkRef.current.on('stabilized', () => {
      networkRef.current?.fit({
        animation: {
          duration: 600,
          easingFunction: 'easeInOutQuad',
        },
      });
    });

    // Event: Node hover
    networkRef.current.on('hoverNode', (params) => {
      const nodeId = String(params.node);
      const nodeData = nodesDS.current.get(nodeId);
      if (nodeData) {
        setTooltip({
          visible: true,
          content: nodeData,
          x: params.pointer.DOM.x,
          y: params.pointer.DOM.y,
        });
      }
    });

    // Event: Node unhover
    networkRef.current.on('blurNode', () => {
      setTooltip(prev => ({ ...prev, visible: false }));
    });

    // Event: Node click
    networkRef.current.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = String(params.nodes[0]);
        const nodeData = nodesDS.current.get(nodeId);
        setSelectedNodeData(nodeData);
        setSelectedNode(nodeData);
      } else {
        setSelectedNodeData(null);
        setSelectedNode(null);
      }
    });

    // Update stats
    setStats({
      nodes: nodes.length,
      edges: edges.length,
      density: graphStats.density || 0,
      avgDegree: graphStats.avg_degree || 0,
    });

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graphData, theme, targetUsername]);

  useEffect(() => {
    buildNetwork();
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [buildNetwork]);

  /**
   * Apply node type filter
   */
  const applyNodeFilter = useCallback((type) => {
    setNodeFilter(type);
    if (!nodesDS.current) return;
    
    const allNodes = nodesDS.current.get();
    nodesDS.current.update(
      allNodes.map(n => ({
        id: n.id,
        hidden: type !== 'all' && n._nodeType !== type,
      }))
    );
  }, []);

  /**
   * Toggle edge type in filter
   */
  const toggleEdgeFilter = useCallback((edgeType) => {
    const newFilters = edgeFilters.includes(edgeType)
      ? edgeFilters.filter(e => e !== edgeType)
      : [...edgeFilters, edgeType];
    
    setEdgeFilters(newFilters);
    
    if (!edgesDS.current) return;
    const allEdges = edgesDS.current.get();
    edgesDS.current.update(
      allEdges.map(e => ({
        id: e.id,
        hidden: !newFilters.includes(e._edgeType) || (e._confidence < confidenceThreshold),
      }))
    );
    
    setGraphViewFilters({ ...graphFilters, edgeTypes: newFilters });
  }, [edgeFilters, confidenceThreshold, graphFilters, setGraphViewFilters]);

  /**
   * Apply confidence threshold filter
   */
  const applyConfidenceFilter = useCallback((threshold) => {
    setConfidenceThreshold(threshold);
    if (!edgesDS.current) return;
    
    const allEdges = edgesDS.current.get();
    edgesDS.current.update(
      allEdges.map(e => ({
        id: e.id,
        hidden: !edgeFilters.includes(e._edgeType) || (e._confidence < threshold),
      }))
    );
    
    setGraphViewFilters({ ...graphFilters, minConfidence: threshold });
  }, [edgeFilters, graphFilters, setGraphViewFilters]);

  /**
   * Graph control buttons
   */
  const handleFit = () => networkRef.current?.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } });
  const handleZoomIn = () => networkRef.current?.moveTo({ scale: (networkRef.current.getScale() * 1.25) });
  const handleZoomOut = () => networkRef.current?.moveTo({ scale: (networkRef.current.getScale() * 0.8) });

  /**
   * Export PNG
   */
  const handleExportPng = async () => {
    if (!networkRef.current || !containerRef.current) return;
    setExporting(true);
    try {
      const canvas = containerRef.current.querySelector('canvas');
      if (canvas) {
        const url = canvas.toDataURL('image/png');
        const a = document.createElement('a');
        a.href = url;
        a.download = `osint-graph-${Date.now()}.png`;
        a.click();
      }
    } finally {
      setExporting(false);
    }
  };

  /**
   * Export SVG — reads node/edge positions from vis-network and builds real SVG markup.
   */
  const handleExportSvg = () => {
    if (!networkRef.current || !nodesDS.current || !edgesDS.current) return;
    setExporting(true);
    try {
      const positions = networkRef.current.getPositions();
      const allNodes  = nodesDS.current.get();
      const allEdges  = edgesDS.current.get();

      // Calculate bounding box
      const xs = Object.values(positions).map(p => p.x);
      const ys = Object.values(positions).map(p => p.y);
      const minX = Math.min(...xs) - 60;
      const minY = Math.min(...ys) - 60;
      const maxX = Math.max(...xs) + 60;
      const maxY = Math.max(...ys) + 60;
      const W = maxX - minX;
      const H = maxY - minY;

      const toSvgX = x => (x - minX).toFixed(1);
      const toSvgY = y => (y - minY).toFixed(1);

      // Build edges
      const edgeSvg = allEdges
        .filter(e => !e.hidden && positions[e.from] && positions[e.to])
        .map(e => {
          const p1 = positions[e.from];
          const p2 = positions[e.to];
          const color = getEdgeColor(e._edgeType) || '#94a3b8';
          const conf  = e._confidence || 1;
          const midX  = ((p1.x + p2.x) / 2 - minX).toFixed(1);
          const midY  = ((p1.y + p2.y) / 2 - minY).toFixed(1);
          return `  <line x1="${toSvgX(p1.x)}" y1="${toSvgY(p1.y)}" x2="${toSvgX(p2.x)}" y2="${toSvgY(p2.y)}"
    stroke="${color}" stroke-width="${Math.max(1, conf * 2).toFixed(1)}" stroke-opacity="${Math.max(0.3, conf).toFixed(2)}" marker-end="url(#arrow)"/>
  ${e.label ? `<text x="${midX}" y="${midY}" fill="#64748b" font-size="8" font-family="monospace" text-anchor="middle">${e.label}</text>` : ''}`;
        }).join('\n');

      // Build nodes
      const nodeSvg = allNodes
        .filter(n => !n.hidden && positions[n.id])
        .map(n => {
          const pos   = positions[n.id];
          const color = TYPE_COLORS[n._nodeType] || TYPE_COLORS.default;
          const r     = n._isTarget ? 22 : 14;
          const cx    = toSvgX(pos.x);
          const cy    = toSvgY(pos.y);
          const label = (n.label || n.id).slice(0, 20);
          return `  <circle cx="${cx}" cy="${cy}" r="${r}" fill="${color}" stroke="${n._isTarget ? '#fff' : color + 'aa'}" stroke-width="${n._isTarget ? 3 : 1.5}" opacity="0.92"/>
  <text x="${cx}" y="${(parseFloat(cy) + 4).toFixed(1)}" fill="#fff" font-size="${n._isTarget ? 11 : 9}" font-family="Sora, sans-serif" font-weight="${n._isTarget ? 700 : 500}" text-anchor="middle">${label}</text>`;
        }).join('\n');

      const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${W.toFixed(0)}" height="${H.toFixed(0)}" viewBox="0 0 ${W.toFixed(0)} ${H.toFixed(0)}">
  <defs>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="8" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect width="100%" height="100%" fill="#0a1628"/>
${edgeSvg}
${nodeSvg}
  <text x="10" y="${H - 10}" fill="#334155" font-size="9" font-family="monospace">OSINT Graph Export · ${new Date().toISOString().slice(0, 10)}</text>
</svg>`;

      const blob = new Blob([svg], { type: 'image/svg+xml' });
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href     = url;
      a.download = `osint-graph-${Date.now()}.svg`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };

  if (!nodes.length && !edges.length) {
    return <EmptyState icon="🕸" message="No network graph data available for this investigation." theme={theme} />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      
      {/* Controls Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 12,
        padding: '12px 14px',
        background: t.surfaceAlt,
        borderRadius: 8,
        border: `1px solid ${t.border}`,
      }}>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
          {NODE_TYPE_FILTERS.map(f => (
            <button
              key={f.key}
              onClick={() => applyNodeFilter(f.key)}
              style={{
                padding: '5px 11px',
                background: nodeFilter === f.key ? `${TYPE_COLORS[f.key] || t.accent}22` : t.surface,
                border: `1px solid ${nodeFilter === f.key ? TYPE_COLORS[f.key] || t.accent : t.border}`,
                borderRadius: 18,
                color: nodeFilter === f.key ? TYPE_COLORS[f.key] || t.accent : t.textMuted,
                cursor: 'pointer',
                fontFamily: "'Sora',sans-serif",
                fontSize: 10,
                fontWeight: nodeFilter === f.key ? 700 : 500,
                transition: 'all 0.15s',
                whiteSpace: 'nowrap',
              }}
            >
              {f.icon} {f.label}
            </button>
          ))}
        </div>

        {/* Stats */}
        <div style={{
          display: 'flex',
          gap: 14,
          fontFamily: "'JetBrains Mono',monospace",
          fontSize: 9,
          color: t.textMuted,
          letterSpacing: 1,
        }}>
          <span>N: {stats.nodes}</span>
          <span>E: {stats.edges}</span>
          <span>D: {(stats.density || 0).toFixed(2)}</span>
        </div>

        {/* Filters Toggle */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          style={{
            padding: '5px 11px',
            background: showFilters ? `${t.accent}22` : t.surface,
            border: `1px solid ${showFilters ? t.accent : t.border}`,
            borderRadius: 18,
            color: showFilters ? t.accent : t.textMuted,
            cursor: 'pointer',
            fontFamily: "'Sora',sans-serif",
            fontSize: 10,
            fontWeight: 600,
            transition: 'all 0.15s',
          }}
        >
          ⚙ Filters {showFilters && '✓'}
        </button>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <Card theme={theme} style={{ padding: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            
            {/* Edge Type Filters */}
            <div>
              <div style={{
                fontFamily: "'Sora',sans-serif",
                fontSize: 11,
                fontWeight: 700,
                color: t.text,
                marginBottom: 10,
              }}>
                Edge Types
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {EDGE_TYPE_FILTERS.map(edgeType => (
                  <label key={edgeType} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    cursor: 'pointer',
                    fontFamily: "'Sora',sans-serif",
                    fontSize: 10,
                    color: t.text,
                  }}>
                    <input
                      type="checkbox"
                      checked={edgeFilters.includes(edgeType)}
                      onChange={() => toggleEdgeFilter(edgeType)}
                      style={{ cursor: 'pointer' }}
                    />
                    <span style={{
                      display: 'inline-block',
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      background: getEdgeColor(edgeType),
                      marginRight: 4,
                    }} />
                    {edgeType}
                  </label>
                ))}
              </div>
            </div>

            {/* Confidence Threshold */}
            <div>
              <div style={{
                fontFamily: "'Sora',sans-serif",
                fontSize: 11,
                fontWeight: 700,
                color: t.text,
                marginBottom: 10,
              }}>
                Confidence Threshold
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={confidenceThreshold}
                  onChange={(e) => applyConfidenceFilter(parseFloat(e.target.value))}
                  style={{
                    flex: 1,
                    cursor: 'pointer',
                  }}
                />
                <span style={{
                  fontFamily: "'JetBrains Mono',monospace",
                  fontSize: 10,
                  color: t.accent,
                  fontWeight: 700,
                  minWidth: 40,
                }}>
                  {(confidenceThreshold * 100).toFixed(0)}%
                </span>
              </div>
              <div style={{
                fontFamily: "'Sora',sans-serif",
                fontSize: 9,
                color: t.textMuted,
                marginTop: 8,
              }}>
                Showing edges with confidence ≥ {(confidenceThreshold * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Graph Container */}
      <div style={{ position: 'relative', width: '100%', height: 550, borderRadius: 12, overflow: 'hidden' }}>
        <div
          ref={containerRef}
          style={{
            width: '100%',
            height: '100%',
            background: t.surfaceAlt,
            border: `1px solid ${t.border}`,
            borderRadius: 12,
          }}
        />

        {/* Graph Controls */}
        <div style={{
          position: 'absolute',
          top: 12,
          right: 12,
          display: 'flex',
          flexDirection: 'column',
          gap: 6,
          zIndex: 10,
        }}>
          {[
            { label: '+', onClick: handleZoomIn, title: 'Zoom in' },
            { label: '−', onClick: handleZoomOut, title: 'Zoom out' },
            { label: '⊞', onClick: handleFit, title: 'Fit view' },
          ].map(btn => (
            <button key={btn.label} onClick={btn.onClick} title={btn.title} style={graphCtrlBtn(t)}>
              {btn.label}
            </button>
          ))}
          <div style={{ borderTop: `1px solid ${t.border}`, margin: '2px 0' }} />
          <button onClick={handleExportPng} title="Export PNG" style={graphCtrlBtn(t)}>
            <span style={{ fontSize: 10 }}>PNG</span>
          </button>
          <button onClick={handleExportSvg} title="Export SVG" style={graphCtrlBtn(t)}>
            <span style={{ fontSize: 10 }}>SVG</span>
          </button>
        </div>

        {/* Hover Tooltip */}
        {tooltip.visible && tooltip.content && (
          <div style={{
            position: 'absolute',
            left: Math.min(tooltip.x + 14, 450),
            top: Math.max(tooltip.y - 70, 8),
            background: `${t.surface}f5`,
            border: `1px solid ${t.accent}66`,
            borderRadius: 8,
            padding: '10px 12px',
            zIndex: 20,
            maxWidth: 240,
            boxShadow: `0 4px 16px rgba(0,0,0,0.15)`,
            backdropFilter: 'blur(8px)',
            pointerEvents: 'none',
          }}>
            <div style={{
              fontFamily: "'Sora',sans-serif",
              fontWeight: 700,
              fontSize: 11,
              color: t.text,
              marginBottom: 4,
            }}>
              {tooltip.content.label || tooltip.content.id}
            </div>
            <div style={{
              fontFamily: "'JetBrains Mono',monospace",
              fontSize: 8,
              color: TYPE_COLORS[tooltip.content._nodeType] || t.accent,
              letterSpacing: 0.5,
              textTransform: 'uppercase',
              marginBottom: 6,
            }}>
              {tooltip.content._nodeType}
            </div>
            {tooltip.content.title && (
              <div style={{
                fontFamily: "'Sora',sans-serif",
                fontSize: 9,
                color: t.textMuted,
                lineHeight: 1.4,
              }}>
                {tooltip.content.title}
              </div>
            )}
          </div>
        )}

        {/* Legend */}
        <div style={{
          position: 'absolute',
          bottom: 12,
          left: 12,
          zIndex: 10,
          background: `${t.surface}dd`,
          border: `1px solid ${t.border}`,
          borderRadius: 8,
          padding: '10px 12px',
          backdropFilter: 'blur(8px)',
          maxWidth: 200,
        }}>
          <div style={{
            fontFamily: "'JetBrains Mono',monospace",
            fontSize: 8,
            color: t.textSub,
            letterSpacing: 2,
            marginBottom: 10,
            fontWeight: 700,
            textTransform: 'uppercase',
          }}>
            Node Types
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            {Object.entries(TYPE_COLORS)
              .filter(([k]) => NODE_TYPE_FILTERS.some(f => f.key === k) || k === 'target')
              .map(([key, color]) => (
                <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                  <div style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    background: color,
                    flexShrink: 0,
                    boxShadow: `0 0 4px ${color}66`,
                  }} />
                  <span style={{
                    fontFamily: "'Sora',sans-serif",
                    fontSize: 9,
                    color: t.textMuted,
                    textTransform: 'capitalize',
                  }}>
                    {key}
                  </span>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Selected Node Details */}
      {selectedNodeData && (
        <Card theme={theme} style={{ padding: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <div style={{
              fontFamily: "'Sora',sans-serif",
              fontWeight: 700,
              fontSize: 12,
              color: t.text,
            }}>
              Selected: {selectedNodeData.label}
            </div>
            <button
              onClick={() => {
                setSelectedNodeData(null);
                setSelectedNode(null);
              }}
              style={{
                background: 'none',
                border: 'none',
                color: t.textMuted,
                cursor: 'pointer',
                fontSize: 14,
              }}
            >
              ✕
            </button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: 10 }}>
            <div>
              <span style={{ color: t.textMuted, fontWeight: 600 }}>Type:</span>
              <span style={{ color: t.text, marginLeft: 8 }}>{selectedNodeData._nodeType}</span>
            </div>
            <div>
              <span style={{ color: t.textMuted, fontWeight: 600 }}>Risk:</span>
              <span style={{ color: t.text, marginLeft: 8 }}>{selectedNodeData._riskLevel || 'N/A'}</span>
            </div>
          </div>
        </Card>
      )}

      {/* Keyboard Hints */}
      <div style={{
        fontFamily: "'JetBrains Mono',monospace",
        fontSize: 8,
        color: t.textMuted,
        letterSpacing: 0.5,
        textTransform: 'uppercase',
      }}>
        ← → ↑ ↓ pan · scroll zoom · + − resize · click node to select · use filters above
      </div>
    </div>
  );
}

/**
 * Get color for edge type
 */
function getEdgeColor(edgeType) {
  const colors = {
    MENTIONS: '#FF6B6B',
    CONNECTED_TO: '#4ECDC4',
    USES_EMAIL: '#95E1D3',
    USES_PHONE: '#F7DC6F',
    POSTED_KEYWORD: '#BB8FCE',
    REPORTED_AS: '#E74C3C',
    SIMILAR_USERNAME: '#85C1E2',
  };
  return colors[edgeType] || '#94a3b8';
}

/**
 * Graph control button style
 */
function graphCtrlBtn(t) {
  return {
    width: 36,
    height: 36,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: `${t.surface}dd`,
    border: `1px solid ${t.border}`,
    borderRadius: 8,
    color: t.text,
    cursor: 'pointer',
    fontFamily: "'Sora',sans-serif",
    fontWeight: 700,
    fontSize: 14,
    backdropFilter: 'blur(4px)',
    transition: 'all 0.15s',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  };
}
