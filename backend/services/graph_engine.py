"""Graph Engine Service
Handles network graph construction, analysis, and export.
Wraps NetworkGraphBuilder and adds intelligence analysis features.

Input: Investigation data and findings
Output: Structured graph JSON with confidence scores, edge types, centrality metrics
"""

import logging
import json
from datetime import datetime
import networkx as nx

logger = logging.getLogger(__name__)


class GraphEngineService:
    """Graph construction and analysis service.
    
    Builds network graphs from investigation findings and provides
    advanced analysis including centrality measures, community detection,
    and risk propagation through the network.
    """
    
    # Edge type definitions
    EDGE_TYPES = {
        'MENTIONS': {
            'weight': 1,
            'color': '#FF6B6B',
            'label': 'Mentions/Tags in content'
        },
        'CONNECTED_TO': {
            'weight': 5,
            'color': '#4ECDC4',
            'label': 'Connected/Followed'
        },
        'USES_EMAIL': {
            'weight': 3,
            'color': '#95E1D3',
            'label': 'Account uses same email'
        },
        'USES_PHONE': {
            'weight': 4,
            'color': '#F7DC6F',
            'label': 'Account uses same phone'
        },
        'POSTED_KEYWORD': {
            'weight': 2,
            'color': '#BB8FCE',
            'label': 'Posted keyword/phrase'
        },
        'REPORTED_AS': {
            'weight': 6,
            'color': '#E74C3C',
            'label': 'Reported as spam/fake'
        },
        'SIMILAR_USERNAME': {
            'weight': 2,
            'color': '#85C1E2',
            'label': 'Similar username pattern'
        }
    }
    
    def __init__(self, case_id=None):
        """
        Initialize graph engine.
        
        Args:
            case_id (str): Case identifier for logging
        """
        self.case_id = case_id
        self.graph = nx.Graph()
        self.central_node = None
        self.nodes_data = {}
        self.edges_data = []
    
    def build_from_investigation(self, investigation, findings):
        """
        Build graph from investigation data and findings.
        
        Args:
            investigation (dict): Investigation metadata including:
                - id (str): Case ID
                - username (str): Target username
                - email (str): Target email (optional)
                - phone (str): Target phone (optional)
            
            findings (list): List of finding dicts, each with:
                - platform (str): Platform name
                - found (bool): Whether found
                - profile_url (str): URL if found
                - username (str): Username on platform
                - metadata (dict): Additional data
            
            Returns:
                dict: Vis.js-compatible graph with nodes, edges, and metadata
        """
        try:
            # Create central node
            self.central_node = investigation['username']
            self._add_central_node(investigation)
            
            # Process findings
            if findings:
                self._process_findings(findings, investigation)
            
            # Calculate centrality metrics
            self._calculate_centrality()
            
            # Build output
            output = self._build_visjs_output()
            
            logger.info(f"Graph built for {self.case_id}: {len(self.nodes_data)} nodes, {len(self.edges_data)} edges")
            return output
        
        except Exception as e:
            logger.error(f"Error building graph: {str(e)}", exc_info=True)
            return self._empty_graph()
    
    def add_node(self, node_id, node_type, label, metadata=None, risk_score=0):
        """
        Add node to graph.
        
        Args:
            node_id (str): Unique node identifier
            node_type (str): Node type ('platform', 'email', 'phone', 'username', 'keyword')
            label (str): Display label
            metadata (dict): Additional attributes
            risk_score (float): Risk score 0-100
        """
        if node_id in self.nodes_data:
            return
        
        metadata = metadata or {}
        
        self.nodes_data[node_id] = {
            'id': node_id,
            'label': label,
            'type': node_type,
            'risk_score': risk_score,
            'risk_level': self._get_risk_level(risk_score),
            'size': 25 + (risk_score / 100) * 25,  # Size based on risk
            'color': self._get_node_color(node_type, risk_score),
            'title': f"{label}\nType: {node_type}\nRisk: {risk_score}",
            'metadata': metadata
        }
        
        self.graph.add_node(node_id, **self.nodes_data[node_id])
    
    def add_edge(self, source_id, target_id, edge_type='CONNECTED_TO', metadata=None, strength=1.0):
        """
        Add edge between nodes with relationship type and strength.
        
        Args:
            source_id (str): Source node ID
            target_id (str): Target node ID
            edge_type (str): Type of relationship (see EDGE_TYPES)
            metadata (dict): Additional edge data
            strength (float): Edge strength 0-1 (affects visualization)
        """
        if source_id == target_id:
            return
        
        metadata = metadata or {}
        edge_type_info = self.EDGE_TYPES.get(edge_type, self.EDGE_TYPES['CONNECTED_TO'])
        
        edge_data = {
            'from': source_id,
            'to': target_id,
            'type': edge_type,
            'label': edge_type_info['label'],
            'color': edge_type_info['color'],
            'weight': edge_type_info['weight'] * strength,
            'width': 1 + (edge_type_info['weight'] * strength) / 2,
            'arrows': 'to' if edge_type in ['MENTIONS', 'REPORTS_TO'] else None,
            'smooth': {'type': 'continuous'},
            'metadata': metadata
        }
        
        self.edges_data.append(edge_data)
        self.graph.add_edge(source_id, target_id, **edge_data)
    
    def get_statistics(self):
        """
        Get graph statistics and metrics.
        
        Returns:
            dict: Graph statistics including:
                - node_count (int)
                - edge_count (int)
                - density (float)
                - avg_clustering (float)
                - avg_degree (float)
                - diameter (int)
                - is_connected (bool)
        """
        if not self.graph.nodes():
            return self._empty_stats()
        
        try:
            nodes = len(self.graph.nodes())
            edges = len(self.graph.edges())
            
            # Density: (actual edges) / (possible edges)
            density = nx.density(self.graph) if nodes > 1 else 0
            
            # Clustering coefficient (transitivity)
            clustering = nx.transitivity(self.graph) if nodes > 2 else 0
            
            # Average degree
            avg_degree = (2 * edges / nodes) if nodes > 0 else 0
            
            # Diameter (longest shortest path)
            try:
                if nx.is_connected(self.graph):
                    diameter = nx.diameter(self.graph)
                else:
                    # For disconnected graphs, take diameter of largest component
                    largest_cc = max(nx.connected_components(self.graph), key=len)
                    subgraph = self.graph.subgraph(largest_cc)
                    diameter = nx.diameter(subgraph) if len(largest_cc) > 1 else 0
            except:
                diameter = 0
            
            # Connectivity
            is_connected = nx.is_connected(self.graph)
            
            return {
                'node_count': nodes,
                'edge_count': edges,
                'density': round(density, 4),
                'avg_clustering': round(clustering, 4),
                'avg_degree': round(avg_degree, 2),
                'diameter': diameter,
                'is_connected': is_connected,
                'central_node': self.central_node
            }
        
        except Exception as e:
            logger.error(f"Error calculating stats: {str(e)}")
            return self._empty_stats()
    
    def get_connected_nodes(self, node_id, depth=1):
        """
        Get all nodes connected to a given node within specified depth.
        
        Args:
            node_id (str): Starting node ID
            depth (int): Search depth (1 = direct neighbors, 2 = neighbors of neighbors)
            
        Returns:
            list: Connected node IDs
        """
        if node_id not in self.graph:
            return []
        
        connected = set()
        to_explore = {node_id}
        current_depth = 0
        
        while to_explore and current_depth < depth:
            next_explore = set()
            for node in to_explore:
                neighbors = set(self.graph.neighbors(node))
                connected.update(neighbors)
                next_explore.update(neighbors)
            to_explore = next_explore
            current_depth += 1
        
        return list(connected)
    
    def get_node_details(self, node_id):
        """
        Get detailed information about a specific node.
        
        Args:
            node_id (str): Node identifier
            
        Returns:
            dict: Node details with connections
        """
        if node_id not in self.nodes_data:
            return None
        
        node = self.nodes_data[node_id]
        
        # Get connected edges
        connected_edges = [
            e for e in self.edges_data
            if e['from'] == node_id or e['to'] == node_id
        ]
        
        return {
            **node,
            'connected_edges': connected_edges,
            'connection_count': len(connected_edges)
        }
    
    def export_json(self):
        """
        Export graph as complete JSON structure.
        
        Returns:
            dict: Graph data with nodes, edges, metadata, and statistics
        """
        return {
            'nodes': list(self.nodes_data.values()),
            'edges': self.edges_data,
            'metadata': {
                'central_node': self.central_node,
                'generated_at': datetime.utcnow().isoformat(),
                'case_id': self.case_id
            },
            'statistics': self.get_statistics()
        }
    
    def export_graphml(self):
        """
        Export graph in GraphML format for desktop tools like Gephi.
        
        Returns:
            str: GraphML XML string
        """
        try:
            # Prefer direct to_graphml if available
            if hasattr(nx, 'to_graphml'):
                return nx.to_graphml(self.graph)
            # Some networkx versions provide write_graphml or generate_graphml
            if hasattr(nx, 'generate_graphml'):
                return "\n".join(nx.generate_graphml(self.graph))
            if hasattr(nx, 'write_graphml'):
                # write to string via io
                import io
                buf = io.StringIO()
                nx.write_graphml(self.graph, buf)
                return buf.getvalue()
            logger.warning("GraphML export not supported by installed networkx; returning minimal GraphML placeholder")
            return '<?xml version="1.0" encoding="utf-8"?>\n<graphml></graphml>'
        except Exception as e:
            logger.warning(f"GraphML export failed: {e}")
            return '<?xml version="1.0" encoding="utf-8"?>\n<graphml></graphml>'
    
    # ==================== Private Helper Methods ====================
    
    def _add_central_node(self, investigation):
        """Add the central node (target of investigation)."""
        node_id = investigation.get('username', 'unknown')
        
        self.add_node(
            node_id,
            'profile',
            f"@{node_id}",
            metadata={
                'email': investigation.get('email'),
                'phone': investigation.get('phone'),
                'case_id': investigation.get('id')
            },
            risk_score=investigation.get('risk_score', 0)
        )
    
    def _process_findings(self, findings, investigation):
        """Process findings into graph nodes and edges."""
        target = investigation['username']
        target_email = investigation.get('email')
        target_phone = investigation.get('phone')
        
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            
            platform = finding.get('platform', 'Unknown')
            found = finding.get('found', False)
            
            if not found:
                continue
            
            # Create platform node
            platform_node_id = f"platform_{platform.lower()}"
            self.add_node(
                platform_node_id,
                'platform',
                platform,
                metadata={'url': finding.get('profile_url')}
            )
            
            # Connect target to platform
            self.add_edge(
                target,
                platform_node_id,
                edge_type='CONNECTED_TO',
                metadata={'platform': platform}
            )
            
            # Process metadata
            metadata = finding.get('metadata', {})
            
            # Add username node if different
            username = finding.get('username')
            if username and username != target:
                username_node_id = f"username_{platform.lower()}_{username}"
                self.add_node(
                    username_node_id,
                    'username',
                    username,
                    metadata={'platform': platform}
                )
                self.add_edge(platform_node_id, username_node_id, 'CONNECTED_TO')
            
            # Add associated emails
            emails = metadata.get('emails', [])
            if isinstance(emails, list):
                for email in emails:
                    if email and email != target_email:
                        email_node_id = f"email_{email.replace('@', '_at_')}"
                        self.add_node(email_node_id, 'email', email)
                        
                        # Connect via email
                        self.add_edge(
                            target,
                            email_node_id,
                            edge_type='USES_EMAIL',
                            strength=0.8
                        )
            
            # Add keywords found
            keywords = metadata.get('keywords', [])
            if isinstance(keywords, list):
                for keyword in keywords[:3]:  # Limit to 3 per finding
                    if keyword:
                        keyword_node_id = f"keyword_{keyword.lower().replace(' ', '_')}"
                        self.add_node(keyword_node_id, 'keyword', keyword)
                        self.add_edge(
                            target,
                            keyword_node_id,
                            edge_type='POSTED_KEYWORD',
                            strength=0.5
                        )
    
    def _calculate_centrality(self):
        """Calculate and update node centrality metrics."""
        if not self.graph.nodes():
            return
        
        try:
            # Betweenness centrality (bridge nodes)
            betweenness = nx.betweenness_centrality(self.graph)
            
            # Degree centrality (highly connected)
            degree = nx.degree_centrality(self.graph)
            
            for node_id in self.nodes_data:
                centrality_score = (betweenness.get(node_id, 0) + degree.get(node_id, 0)) / 2
                self.nodes_data[node_id]['centrality'] = round(centrality_score, 4)
        
        except Exception as e:
            logger.warning(f"Could not calculate centrality: {str(e)}")
    
    def _build_visjs_output(self):
        """Build Vis.js compatible output format."""
        return {
            'nodes': list(self.nodes_data.values()),
            'edges': self.edges_data,
            'metadata': {
                'central_node': self.central_node,
                'node_count': len(self.nodes_data),
                'edge_count': len(self.edges_data),
                'generated_at': datetime.utcnow().isoformat(),
                'case_id': self.case_id
            }
        }
    
    def _get_risk_level(self, risk_score):
        """Convert risk score to risk level."""
        if risk_score >= 80:
            return 'CRITICAL'
        elif risk_score >= 60:
            return 'HIGH'
        elif risk_score >= 40:
            return 'MEDIUM'
        elif risk_score >= 20:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def _get_node_color(self, node_type, risk_score):
        """Get node color based on type and risk."""
        type_colors = {
            'profile': '#FF6B6B',      # Red for target
            'platform': '#4ECDC4',     # Teal for platforms
            'username': '#95E1D3',     # Light green
            'email': '#F7DC6F',        # Yellow
            'phone': '#BB8FCE',        # Purple
            'keyword': '#85C1E2'       # Blue
        }
        
        base_color = type_colors.get(node_type, '#CCCCCC')
        
        # Adjust brightness based on risk (higher risk = darker)
        if risk_score > 70:
            return '#CC0000'  # Dark red for high risk
        elif risk_score > 40:
            return '#FF6B6B'  # Medium red
        
        return base_color
    
    def _empty_graph(self):
        """Return empty graph structure."""
        return {
            'nodes': [],
            'edges': [],
            'metadata': {
                'node_count': 0,
                'edge_count': 0,
                'generated_at': datetime.utcnow().isoformat(),
                'error': 'Failed to build graph'
            }
        }
    
    def _empty_stats(self):
        """Return empty statistics structure."""
        return {
            'node_count': 0,
            'edge_count': 0,
            'density': 0,
            'avg_clustering': 0,
            'avg_degree': 0,
            'diameter': 0,
            'is_connected': False,
            'central_node': self.central_node
        }
