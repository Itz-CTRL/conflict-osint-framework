// src/components/SimpleGraph.jsx
// D3-based simple username-platform relationship graph for Light Scan.
// Shows: center username node + surrounding platform nodes, connected by edges.
import { useEffect, useRef, useState, useMemo } from 'react';
import * as d3 from 'd3';
import { THEMES } from '../themes';
import { EmptyState } from './UI';

const NODE_RADIUS = {
  username: 24,
  platform: 16,
};

const NODE_COLORS = {
  username: '#ef4444',
  platform: '#2563eb',
};

/**
 * findings: array of { platform, profile_url, username, found }
 * targetUsername: the searched username string
 */
export default function SimpleGraph({ findings, targetUsername, theme }) {
  const t = THEMES[theme];
  const svgRef = useRef(null);
  const [selected, setSelected] = useState(null);
  const [dimensions, setDimensions] = useState({ width: 640, height: 420 });
  const containerRef = useRef(null);

  const found = useMemo(() => (findings || []).filter(f => f.found), [findings]);

  // Observe container size
  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver(entries => {
      const { width } = entries[0].contentRect;
      setDimensions({ width: Math.max(320, width), height: Math.max(300, Math.min(480, width * 0.6)) });
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    if (!svgRef.current || !found.length) return;

    const { width, height } = dimensions;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    svg.attr('width', width).attr('height', height);

    // Defs: arrowhead marker
    svg.append('defs').append('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 22)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', `${t.accent}88`);

    // Build node and link data
    const centerNode = { id: '__target__', label: `@${targetUsername}`, type: 'username' };
    const platformNodes = found.map(f => ({
      id: f.platform,
      label: f.platform,
      type: 'platform',
      url: f.profile_url,
      username: f.username,
    }));
    const nodes = [centerNode, ...platformNodes];
    const links = platformNodes.map(p => ({ source: '__target__', target: p.id }));

    // Force simulation (minimal: just position, then stop)
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(120).strength(0.7))
      .force('charge', d3.forceManyBody().strength(-320))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(40))
      .stop();

    // Run simulation ticks up-front (no live animation)
    for (let i = 0; i < 200; i++) simulation.tick();

    // Draw edges
    svg.append('g').attr('class', 'links')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', `${t.accent}55`)
      .attr('stroke-width', 2)
      .attr('marker-end', 'url(#arrow)')
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);

    // Draw node groups
    const node = svg.append('g').attr('class', 'nodes')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('transform', d => `translate(${d.x},${d.y})`)
      .style('cursor', d => d.type === 'platform' ? 'pointer' : 'default')
      .on('click', (event, d) => {
        event.stopPropagation();
        setSelected(prev => prev?.id === d.id ? null : d);
      });

    // Node circles
    node.append('circle')
      .attr('r', d => NODE_RADIUS[d.type] || 16)
      .attr('fill', d => `${NODE_COLORS[d.type] || t.accent}22`)
      .attr('stroke', d => NODE_COLORS[d.type] || t.accent)
      .attr('stroke-width', d => d.type === 'username' ? 2.5 : 1.5);

    // Node labels
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', d => (NODE_RADIUS[d.type] || 16) + 14)
      .attr('font-family', "'Sora', sans-serif")
      .attr('font-size', d => d.type === 'username' ? 12 : 10)
      .attr('font-weight', d => d.type === 'username' ? 700 : 500)
      .attr('fill', d => d.type === 'username' ? t.text : t.textMuted)
      .text(d => d.label.length > 12 ? d.label.slice(0, 12) + '…' : d.label);

    // Center node icon
    node.filter(d => d.type === 'username')
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('font-size', 14)
      .attr('fill', NODE_COLORS.username)
      .text('◎');

    // Platform node icon (initial char)
    node.filter(d => d.type === 'platform')
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('font-size', 10)
      .attr('font-weight', 700)
      .attr('fill', NODE_COLORS.platform)
      .text(d => d.label[0]);

    // Clear selection on background click
    svg.on('click', () => setSelected(null));
  }, [found, dimensions, theme, targetUsername, t.accent, t.text, t.textMuted]);

  if (!found.length) {
    return (
      <EmptyState
        icon="⬡"
        message="No platform profiles found to display in the graph."
        theme={theme}
      />
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Graph canvas */}
      <div
        ref={containerRef}
        style={{
          background: t.surfaceAlt,
          border: `1px solid ${t.border}`,
          borderRadius: 12,
          overflow: 'hidden',
          width: '100%',
        }}
      >
        <svg ref={svgRef} style={{ display: 'block', width: '100%' }} />
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', gap: 20, paddingLeft: 4 }}>
        {[
          { color: NODE_COLORS.username, label: 'Target Username' },
          { color: NODE_COLORS.platform, label: 'Platform Found' },
        ].map(item => (
          <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            <div style={{
              width: 10, height: 10, borderRadius: '50%',
              background: `${item.color}33`, border: `1.5px solid ${item.color}`,
              flexShrink: 0,
            }} />
            <span style={{ fontFamily: "'Sora',sans-serif", fontSize: 11, color: t.textMuted }}>
              {item.label}
            </span>
          </div>
        ))}
        <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.textMuted, marginLeft: 'auto' }}>
          click a node to select
        </span>
      </div>

      {/* Selected node info */}
      {selected && selected.type === 'platform' && (
        <div style={{
          padding: '12px 16px',
          background: t.surface,
          border: `1px solid ${t.accent}44`,
          borderRadius: 10,
          display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12,
        }}>
          <div>
            <div style={{ fontFamily: "'Sora',sans-serif", fontWeight: 700, fontSize: 13, color: t.text, marginBottom: 2 }}>
              {selected.label}
            </div>
            {selected.url && (
              <a
                href={selected.url}
                target="_blank"
                rel="noreferrer"
                style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: t.accent, textDecoration: 'none', letterSpacing: 0.5 }}
              >
                {selected.url.length > 60 ? selected.url.slice(0, 60) + '…' : selected.url} →
              </a>
            )}
          </div>
          <button
            onClick={() => setSelected(null)}
            style={{ background: 'none', border: 'none', color: t.textMuted, cursor: 'pointer', fontSize: 16, padding: 0 }}
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
