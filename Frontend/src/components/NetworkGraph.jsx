// src/components/NetworkGraph.jsx
import { useEffect, useRef } from 'react';
import { Network } from 'vis-network/standalone';
import 'vis-network/styles/vis-network.min.css';
import { THEMES } from '../themes';

export default function NetworkGraph({ networkData, theme }) {
  const containerRef = useRef(null);
  const networkRef = useRef(null);
  const t = THEMES[theme];

  useEffect(() => {
    if (!containerRef.current || !networkData) return;

    const nodes = networkData.nodes || [];
    const edges = networkData.edges || [];

    const options = {
      physics: {
        enabled: true,
        barnesHut: {
          gravitationalConstant: -26000,
          centralGravity: 0.3,
          springLength: 200,
        },
        maxVelocity: 50,
        solver: 'barnesHut',
        timestep: 0.35,
      },
      nodes: {
        shape: 'dot',
        scaling: {
          min: 10,
          max: 30,
        },
        font: {
          size: 14,
          face: 'Sora, sans-serif',
          color: '#fff',
          strokeWidth: 2,
          strokeColor: '#000',
        },
        shadow: {
          enabled: true,
          color: 'rgba(0,0,0,0.3)',
          size: 10,
          x: 3,
          y: 3,
        },
      },
      edges: {
        color: {
          color: `${t.accent}44`,
          highlight: t.accent,
        },
        width: 2,
        font: {
          size: 12,
          color: t.text,
          face: 'Sora, sans-serif',
        },
        smooth: {
          type: 'continuous',
          roundness: 0.5,
        },
        arrows: {
          to: {
            enabled: true,
            scaleFactor: 0.5,
          },
        },
      },
      interaction: {
        hover: true,
        keyboard: true,
        navigationButtons: true,
        keyboard: {
          enabled: true,
        },
      },
      configure: false,
    };

    const data = { nodes, edges };

    if (networkRef.current) {
      networkRef.current.destroy();
    }

    networkRef.current = new Network(containerRef.current, data, options);

    // Event listeners
    networkRef.current.on('click', () => {
      const selectedNode = networkRef.current.getSelectedNodes()[0];
      const selectedEdge = networkRef.current.getSelectedEdges()[0];

      if (selectedNode) {
        const nodeData = nodes.find(n => n.id === selectedNode);
        if (nodeData?.title) {
          console.log('Selected node:', nodeData);
        }
      }
    });

    networkRef.current.on('animationFinished', () => {
      networkRef.current.fit();
    });

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [networkData, theme]);

  const handleFitView = () => {
    if (networkRef.current) {
      networkRef.current.fit();
    }
  };

  const handleZoomIn = () => {
    if (networkRef.current) {
      const currentScale = networkRef.current.getScale();
      networkRef.current.setOptions({ physics: false });
      networkRef.current.moveTo({ scale: currentScale * 1.2 });
      networkRef.current.setOptions({ physics: { enabled: true } });
    }
  };

  const handleZoomOut = () => {
    if (networkRef.current) {
      const currentScale = networkRef.current.getScale();
      networkRef.current.setOptions({ physics: false });
      networkRef.current.moveTo({ scale: currentScale * 0.8 });
      networkRef.current.setOptions({ physics: { enabled: true } });
    }
  };

  if (!networkData) {
    return (
      <div style={{
        padding: 40,
        textAlign: 'center',
        color: t.textMuted,
        fontFamily: "'Sora',sans-serif",
      }}>
        No network data available
      </div>
    );
  }

  return (
    <div style={{ position: 'relative', width: '100%', height: 500 }}>
      <div
        ref={containerRef}
        style={{
          width: '100%',
          height: '100%',
          background: t.surfaceAlt,
          borderRadius: 12,
          border: `1px solid ${t.border}`,
          position: 'relative',
        }}
      />

      {/* Controls */}
      <div style={{
        position: 'absolute',
        top: 16,
        right: 16,
        display: 'flex',
        gap: 8,
        zIndex: 10,
      }}>
        <button
          onClick={handleZoomIn}
          title="Zoom In"
          style={{
            padding: '8px 12px',
            borderRadius: 6,
            background: t.accentGrad,
            color: '#fff',
            border: 'none',
            cursor: 'pointer',
            fontWeight: 700,
            fontSize: 14,
          }}
        >
          +
        </button>
        <button
          onClick={handleZoomOut}
          title="Zoom Out"
          style={{
            padding: '8px 12px',
            borderRadius: 6,
            background: t.accentGrad,
            color: '#fff',
            border: 'none',
            cursor: 'pointer',
            fontWeight: 700,
            fontSize: 14,
          }}
        >
          −
        </button>
        <button
          onClick={handleFitView}
          title="Fit View"
          style={{
            padding: '8px 12px',
            borderRadius: 6,
            background: t.accentGrad,
            color: '#fff',
            border: 'none',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: 12,
          }}
        >
          Fit
        </button>
      </div>

      {/* Legend */}
      <div style={{
        position: 'absolute',
        bottom: 16,
        left: 16,
        background: `${t.surface}dd`,
        border: `1px solid ${t.border}`,
        borderRadius: 8,
        padding: 12,
        fontSize: 11,
        zIndex: 10,
      }}>
        <div style={{ fontWeight: 700, marginBottom: 8, color: t.text }}>Legend</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <LegendItem color="#FF1744" label="Target User" theme={theme} />
          <LegendItem color="#00BCD4" label="Platform" theme={theme} />
          <LegendItem color="#FFA726" label="Location" theme={theme} />
          <LegendItem color="#26C6DA" label="Organization" theme={theme} />
          <LegendItem color="#66BB6A" label="Connection" theme={theme} />
        </div>
      </div>
    </div>
  );
}

function LegendItem({ color, label, theme }) {
  const t = THEMES[theme];
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: t.textMuted }}>
      <div
        style={{
          width: 12,
          height: 12,
          borderRadius: '50%',
          background: color,
          border: `1px solid ${color}`,
        }}
      />
      {label}
    </div>
  );
}
