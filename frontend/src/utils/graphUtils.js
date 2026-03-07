/**
 * Graph utility functions for OSINT network visualization
 * Handles filtering, analysis, and manipulation of network data
 */

// Edge type definitions and styling
export const EDGE_TYPES = {
  MENTIONS: {
    color: '#ef4444',
    label: 'Mentions/Tags',
    weight: 1,
    description: 'Username mentioned or tagged in content',
  },
  CONNECTED_TO: {
    color: '#4ecdc4',
    label: 'Connected/Followed',
    weight: 5,
    description: 'Direct follow/connection between accounts',
  },
  USES_EMAIL: {
    color: '#95e1d3',
    label: 'Shared Email',
    weight: 3,
    description: 'Accounts using the same email address',
  },
  USES_PHONE: {
    color: '#f7dc6f',
    label: 'Shared Phone',
    weight: 4,
    description: 'Accounts using the same phone number',
  },
  POSTED_KEYWORD: {
    color: '#bb8fce',
    label: 'Posted Keyword',
    weight: 2,
    description: 'Posted keyword or phrase in profile',
  },
  REPORTED_AS: {
    color: '#e74c3c',
    label: 'Reported As Spam',
    weight: 6,
    description: 'Reported as spam, fake, or compromised',
  },
  SIMILAR_USERNAME: {
    color: '#85c1e2',
    label: 'Similar Username',
    weight: 2,
    description: 'Username pattern similarities detected',
  },
};

// Node type definitions and colors
export const NODE_TYPES = {
  profile: {
    color: '#ef4444',
    label: 'Profile',
    icon: '👤',
  },
  platform: {
    color: '#06b6d4',
    label: 'Platform',
    icon: '📱',
  },
  email: {
    color: '#f59e0b',
    label: 'Email',
    icon: '📧',
  },
  phone: {
    color: '#a855f7',
    label: 'Phone',
    icon: '☎️',
  },
  keyword: {
    color: '#10b981',
    label: 'Keyword',
    icon: '🔑',
  },
  mention: {
    color: '#3b82f6',
    label: 'Mention',
    icon: '💬',
  },
  location: {
    color: '#f97316',
    label: 'Location',
    icon: '📍',
  },
  org: {
    color: '#ec4899',
    label: 'Organization',
    icon: '🏢',
  },
};

/**
 * Filter graph nodes based on type
 */
export function filterNodesByType(nodes, selectedTypes) {
  if (!selectedTypes || selectedTypes.length === 0) {
    return nodes;
  }
  return nodes.filter(node => selectedTypes.includes(node.type));
}

/**
 * Filter graph edges based on type
 */
export function filterEdgesByType(edges, selectedTypes) {
  if (!selectedTypes || selectedTypes.length === 0) {
    return edges;
  }
  return edges.filter(edge => selectedTypes.includes(edge.type));
}

/**
 * Filter edges by confidence/weight threshold
 */
export function filterEdgesByConfidence(edges, minConfidence = 0) {
  return edges.filter(edge => {
    const confidence = edge.confidence ?? EDGE_TYPES[edge.type]?.weight ?? 1;
    return confidence >= minConfidence;
  });
}

/**
 * Get connected nodes within N hops
 */
export function getConnectedNodes(nodeId, nodes, edges, maxDepth = 1) {
  const connected = new Set([nodeId]);
  const toVisit = [{ id: nodeId, depth: 0 }];

  while (toVisit.length > 0) {
    const { id, depth } = toVisit.shift();
    if (depth >= maxDepth) continue;

    // Find connected nodes
    const connectedEdges = edges.filter(e => e.from === id || e.to === id);
    for (const edge of connectedEdges) {
      const nextId = edge.from === id ? edge.to : edge.from;
      if (!connected.has(nextId)) {
        connected.add(nextId);
        toVisit.push({ id: nextId, depth: depth + 1 });
      }
    }
  }

  return nodes.filter(n => connected.has(n.id));
}

/**
 * Calculate graph statistics
 */
export function calculateGraphStats(nodes, edges) {
  const nodeCount = nodes.length;
  const edgeCount = edges.length;

  // Calculate density
  const maxEdges = nodeCount * (nodeCount - 1) / 2;
  const density = maxEdges > 0 ? edgeCount / maxEdges : 0;

  // Average degree
  const degrees = new Array(nodeCount).fill(0);
  nodes.forEach((node, i) => {
    const connected = edges.filter(e => e.from === node.id || e.to === node.id);
    degrees[i] = connected.length;
  });
  const avgDegree = degrees.reduce((a, b) => a + b, 0) / Math.max(nodeCount, 1);

  // Find isolated nodes
  const isolatedCount = degrees.filter(d => d === 0).length;

  // Risk distribution
  const riskLevels = {
    critical: nodes.filter(n => n.risk_score >= 85).length,
    high: nodes.filter(n => n.risk_score >= 60 && n.risk_score < 85).length,
    medium: nodes.filter(n => n.risk_score >= 40 && n.risk_score < 60).length,
    low: nodes.filter(n => n.risk_score >= 20 && n.risk_score < 40).length,
    minimal: nodes.filter(n => n.risk_score < 20).length,
  };

  return {
    nodeCount,
    edgeCount,
    density: parseFloat(density.toFixed(3)),
    avgDegree: parseFloat(avgDegree.toFixed(2)),
    isolatedCount,
    riskDistribution: riskLevels,
    maxEdges,
  };
}

/**
 * Find the most connected nodes (hubs)
 */
export function findHubNodes(nodes, edges, topN = 5) {
  const degrees = {};
  nodes.forEach(node => {
    degrees[node.id] = 0;
  });

  edges.forEach(edge => {
    degrees[edge.from] = (degrees[edge.from] || 0) + 1;
    degrees[edge.to] = (degrees[edge.to] || 0) + 1;
  });

  return Object.entries(degrees)
    .sort((a, b) => b[1] - a[1])
    .slice(0, topN)
    .map(([nodeId]) => nodes.find(n => n.id === nodeId))
    .filter(Boolean);
}

/**
 * Find shortest path between two nodes
 */
export function findShortestPath(fromId, toId, nodes, edges) {
  const visited = new Set();
  const queue = [{ id: fromId, path: [fromId] }];

  while (queue.length > 0) {
    const { id, path } = queue.shift();
    
    if (id === toId) {
      return path;
    }

    if (visited.has(id)) continue;
    visited.add(id);

    const connectedEdges = edges.filter(e => e.from === id || e.to === id);
    for (const edge of connectedEdges) {
      const nextId = edge.from === id ? edge.to : edge.from;
      if (!visited.has(nextId)) {
        queue.push({ id: nextId, path: [...path, nextId] });
      }
    }
  }

  return null; // No path found
}

/**
 * Group nodes by type
 */
export function groupNodesByType(nodes) {
  const grouped = {};
  Object.keys(NODE_TYPES).forEach(type => {
    grouped[type] = nodes.filter(n => n.type === type);
  });
  return grouped;
}

/**
 * Group edges by type
 */
export function groupEdgesByType(edges) {
  const grouped = {};
  Object.keys(EDGE_TYPES).forEach(type => {
    grouped[type] = edges.filter(e => e.type === type);
  });
  return grouped;
}

/**
 * Export graph to different formats
 */
export function exportGraph(nodes, edges, format = 'json') {
  const data = { nodes, edges };

  switch (format.toLowerCase()) {
    case 'json':
      return JSON.stringify(data, null, 2);

    case 'csv':
      // CSV format for spreadsheet
      let csv = 'id,label,type,risk_score,count\n';
      nodes.forEach(node => {
        const connections = edges.filter(
          e => e.from === node.id || e.to === node.id
        ).length;
        csv += `"${node.id}","${node.label}","${node.type}",${node.risk_score},${connections}\n`;
      });
      return csv;

    case 'graphml':
      // GraphML format for Gephi/Cytoscape
      return generateGraphML(nodes, edges);

    default:
      return JSON.stringify(data, null, 2);
  }
}

/**
 * Generate GraphML format
 */
function generateGraphML(nodes, edges) {
  let graphml = '<?xml version="1.0" encoding="UTF-8"?>\n';
  graphml += '<graphml xmlns="http://graphml.graphdrawing.org/xmlformat/graphml.xsd">\n';
  graphml += '  <graph mode="static" edgedefault="undirected">\n';

  // Add nodes
  nodes.forEach(node => {
    graphml += `    <node id="${node.id}" label="${node.label}">\n`;
    graphml += `      <data key="type">${node.type}</data>\n`;
    graphml += `      <data key="risk">${node.risk_score || 0}</data>\n`;
    graphml += `    </node>\n`;
  });

  // Add edges
  edges.forEach((edge, index) => {
    graphml += `    <edge id="e${index}" source="${edge.from}" target="${edge.to}" label="${edge.type}">\n`;
    graphml += `      <data key="type">${edge.type}</data>\n`;
    graphml += `      <data key="weight">${edge.weight || 1}</data>\n`;
    graphml += `    </edge>\n`;
  });

  graphml += '  </graph>\n';
  graphml += '</graphml>';

  return graphml;
}

/**
 * Download data as file
 */
export function downloadFile(content, filename, mimeType = 'application/json') {
  const blob = new Blob([content], { type: mimeType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Take canvas screenshot
 */
export function captureCanvasAsImage(canvas, format = 'png') {
  return new Promise(resolve => {
    try {
      const mimeType = format === 'png' ? 'image/png' : 'image/svg+xml';
      canvas.toBlob(blob => {
        resolve(blob);
      }, mimeType);
    } catch (err) {
      console.error('Screenshot failed:', err);
      resolve(null);
    }
  });
}

/**
 * Validate graph data structure
 */
export function validateGraphData(graphData) {
  const errors = [];

  if (!graphData) {
    return ['Graph data is empty'];
  }

  if (!Array.isArray(graphData.nodes)) {
    errors.push('Nodes must be an array');
  } else if (graphData.nodes.length === 0) {
    errors.push('Graph has no nodes');
  } else {
    graphData.nodes.forEach((node, i) => {
      if (!node.id) errors.push(`Node ${i} missing id`);
      if (!node.label) errors.push(`Node ${i} missing label`);
      if (!node.type) errors.push(`Node ${i} missing type`);
    });
  }

  if (!Array.isArray(graphData.edges)) {
    errors.push('Edges must be an array');
  } else {
    graphData.edges.forEach((edge, i) => {
      if (!edge.from) errors.push(`Edge ${i} missing from`);
      if (!edge.to) errors.push(`Edge ${i} missing to`);
      if (!edge.type) errors.push(`Edge ${i} missing type`);
    });
  }

  return errors;
}

export default {
  EDGE_TYPES,
  NODE_TYPES,
  filterNodesByType,
  filterEdgesByType,
  filterEdgesByConfidence,
  getConnectedNodes,
  calculateGraphStats,
  findHubNodes,
  findShortestPath,
  groupNodesByType,
  groupEdgesByType,
  exportGraph,
  downloadFile,
  captureCanvasAsImage,
  validateGraphData,
};
