"""Network Graph Builder Service
Builds network graphs from investigation findings.
Converts investigation data into interactive network visualizations.
Provides graph operations: add nodes/edges, build Central node patterns, export JSON.

Supports multiple edge types with confidence scores:
- MENTIONS: Username mentioned or tagged
- CONNECTED_TO: Direct follow/friend relationship  
- USES_EMAIL: Shared email address
- USES_PHONE: Shared phone number
- POSTED_KEYWORD: Posted keywords in profile
- REPORTED_AS: Reported as spam/fake/compromised
- SIMILAR_USERNAME: Username pattern similarities
"""

import json
import networkx as nx
from datetime import datetime
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class NetworkGraphBuilder:
    """
    Builds network graphs from investigation findings.
    Creates Vis.js-compatible JSON with central node pattern and labeled edges.
    """

    # Edge type definitions with colors and weights
    EDGE_TYPES = {
        'MENTIONS': {
            'color': '#ef4444',
            'weight': 1,
            'description': 'Username mentioned or tagged in content'
        },
        'CONNECTED_TO': {
            'color': '#4ecdc4',
            'weight': 5,
            'description': 'Direct follow/connection between accounts'
        },
        'USES_EMAIL': {
            'color': '#95e1d3',
            'weight': 3,
            'description': 'Accounts using the same email address'
        },
        'USES_PHONE': {
            'color': '#f7dc6f',
            'weight': 4,
            'description': 'Accounts using the same phone number'
        },
        'POSTED_KEYWORD': {
            'color': '#bb8fce',
            'weight': 2,
            'description': 'Posted keyword or phrase in profile'
        },
        'REPORTED_AS': {
            'color': '#e74c3c',
            'weight': 6,
            'description': 'Reported as spam, fake, or compromised'
        },
        'SIMILAR_USERNAME': {
            'color': '#85c1e2',
            'weight': 2,
            'description': 'Username pattern similarities detected'
        },
    }
    
    # Node type definitions
    NODE_TYPES = {
        'profile': {'color': '#ef4444', 'icon': '👤'},       # Red - target
        'platform': {'color': '#06b6d4', 'icon': '📱'},     # Cyan - social media
        'email': {'color': '#f59e0b', 'icon': '📧'},        # Amber - email
        'phone': {'color': '#a855f7', 'icon': '☎️'},        # Purple - phone
        'keyword': {'color': '#10b981', 'icon': '🔑'},      # Green - keyword
        'mention': {'color': '#3b82f6', 'icon': '💬'},      # Blue - mention
        'location': {'color': '#f97316', 'icon': '📍'},     # Orange - location
        'organization': {'color': '#ec4899', 'icon': '🏢'}, # Pink - org
    }

    def __init__(self):
        """Initialize graph builder"""
        self.graph = nx.Graph()
        self.nodes: List[Dict[str, Any]] = []
        self.edges: List[Dict[str, Any]] = []
        self.node_id_counter = 0
        self.node_id_map = {}  # Map friendly names to node IDs

    def build_from_investigation(
        self,
        investigation: Dict[str, Any],
        findings: List[Dict[str, Any]],
        entities: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Build a network graph from investigation data with central node pattern.
        Handles missing or invalid data gracefully by returning partial graphs.
        
        Args:
            investigation: Dict with keys: username, id, email (optional), phone (optional)
            findings: List of Finding dicts from platform checks
            entities: Optional list of Entity dicts with relationships
            
        Returns:
            Dict with:
                nodes: List of nodes for Vis.js
                edges: List of edges for Vis.js with type and confidence
                metadata: Graph metadata and statistics
                central_node: ID and info of central node
        """
        try:
            self.graph.clear()
            self.nodes = []
            self.edges = []
            self.node_id_counter = 0
            self.node_id_map = {}

            # Validate investigation data
            if not investigation:
                logger.warning("No investigation data provided")
                return self._empty_graph()
            
            username = investigation.get('username', 'Unknown')
            if not username:
                logger.warning("No username in investigation data")
                return self._empty_graph()

            # Create central node = target username/email/phone
            try:
                central_data = {
                    'label': username,
                    'type': 'profile',
                    'is_central': True,
                    'risk_score': 0,
                    'metadata': {
                        'email': investigation.get('email'),
                        'phone': investigation.get('phone'),
                        'investigation_id': investigation.get('id'),
                    }
                }
                
                central_node_id = self._add_node(**central_data)
                self.node_id_map['central'] = central_node_id
                logger.debug(f"Created central node for {username}")
            except Exception as e:
                logger.error(f"Error creating central node: {str(e)}")
                return self._empty_graph()

            # Add entities (emails, phones, mentions) - continue on errors
            if entities:
                try:
                    self._process_entities(entities, central_node_id)
                except Exception as e:
                    logger.warning(f"Error processing entities: {str(e)}")
        
            # Add findings from platform checks - handle failures per-finding
            platforms_found = 0
            if findings:
                for finding in findings:
                    try:
                        if isinstance(finding, dict) and finding.get('found') and finding.get('platform') != 'ANALYSIS':
                            self._process_finding(finding, central_node_id)
                            platforms_found += 1
                    except Exception as e:
                        platform = finding.get('platform', 'Unknown') if isinstance(finding, dict) else 'Unknown'
                        logger.warning(f"Error processing finding for {platform}: {str(e)}")
                        # Continue with other findings

            # Calculate and return graph stats
            try:
                stats = self._calculate_statistics()
            except Exception as e:
                logger.warning(f"Error calculating statistics: {str(e)}")
                stats = {'density': 0, 'avg_degree': 0}

            graph_data = {
                'nodes': self.nodes,
                'edges': self.edges,
                'metadata': {
                    'node_count': len(self.nodes),
                    'edge_count': len(self.edges),
                    'platforms_found': platforms_found,
                    'density': stats.get('density', 0),
                    'avg_degree': stats.get('avg_degree', 0),
                    'created_at': datetime.utcnow().isoformat(),
                },
                'statistics': stats,
                'central_node': {
                    'id': central_node_id if 'central_node_id' in locals() else None,
                    'label': username,
                    'type': 'profile'
                },
                'edge_types': list(self.EDGE_TYPES.keys()),
                'node_types': list(self.NODE_TYPES.keys())
            }
            
            logger.info(f"Graph built: {len(self.nodes)} nodes, {len(self.edges)} edges")
            return graph_data
        
        except Exception as e:
            logger.error(f"Unexpected error building graph: {str(e)}", exc_info=True)
            return self._empty_graph()

    def _process_entities(
        self,
        entities: List[Dict[str, Any]],
        central_node_id: str
    ) -> None:
        """
        Process entities (emails, phones, mentions, keywords) and add to graph.
        Continues processing even if individual entities fail.
        
        Args:
            entities: List of Entity dicts
            central_node_id: ID of central node to connect to
        """
        if not entities:
            return
        
        for entity in entities:
            try:
                if not isinstance(entity, dict):
                    logger.warning(f"Invalid entity format: {type(entity)}")
                    continue
                
                entity_type = entity.get('type', 'unknown')
                entity_value = entity.get('value', '')
                confidence = entity.get('confidence_score', 0.7)
                
                if not entity_value:
                    continue
                
                # Add entity node
                entity_node_id = self._add_node(
                    label=entity_value,
                    type=entity_type,
                    risk_score=entity.get('risk_score', 0),
                    metadata=entity.get('metadata', {})
                )
                
                # Determine edge type based on entity type and relationship
                edge_type = self._determine_edge_type(entity_type)
                
                # Connect to central node
                self._add_edge(
                    from_id=central_node_id,
                    to_id=entity_node_id,
                    edge_type=edge_type,
                    confidence=confidence,
                    label=entity_type.upper().replace('_', ' ')
                )
            except Exception as e:
                logger.warning(f"Error processing entity: {str(e)}")
                continue

    def _process_finding(
        self,
        finding: Dict[str, Any],
        central_node_id: str
    ) -> None:
        """
        Process platform finding and add to graph.
        Handles missing or invalid data gracefully.
        
        Args:
            finding: Finding dict from platform check
            central_node_id: Central node ID
        """
        try:
            if not isinstance(finding, dict):
                logger.warning(f"Invalid finding format: {type(finding)}")
                return
            
            platform = finding.get('platform', 'Unknown')
            if not platform:
                logger.warning("Finding has no platform name")
                return
            
            found = finding.get('found', False)
            if not found:
                return
            
            profile_url = finding.get('profile_url', '')
            confidence = finding.get('confidence', 0.8)
            
            # Add platform node
            try:
                platform_node_id = self._add_node(
                    label=platform,
                    type='platform',
                    metadata={
                        'url': profile_url,
                        'verified': finding.get('verified', False),
                        'followers': finding.get('followers'),
                    }
                )
            except Exception as e:
                logger.error(f"Error creating platform node for {platform}: {str(e)}")
                return
            
            # Connect username to platform with CONNECTED_TO edge
            try:
                self._add_edge(
                    from_id=central_node_id,
                    to_id=platform_node_id,
                    edge_type='CONNECTED_TO',
                    confidence=confidence,
                    label='Account Found'
                )
            except Exception as e:
                logger.error(f"Error connecting to platform node {platform}: {str(e)}")
                return
            
            # Extract additional details from finding data
            try:
                data = finding.get('data')
                if isinstance(data, str):
                    data = json.loads(data)
                
                if data and isinstance(data, dict):
                    self._extract_platform_details(data, platform, platform_node_id)
            except Exception as e:
                logger.warning(f"Could not parse finding data for {platform}: {str(e)}")
                # Continue - base finding is already added
        
        except Exception as e:
            logger.error(f"Unexpected error processing finding: {str(e)}")

    def _extract_platform_details(
        self,
        data: Dict[str, Any],
        platform: str,
        platform_node_id: str
    ) -> None:
        """
        Extract and add additional details from platform-specific data.
        Continues processing even if some details fail.
        
        Args:
            data: Platform-specific data dict
            platform: Platform name
            platform_node_id: Node ID of platform
        """
        if not isinstance(data, dict):
            logger.warning(f"Invalid data format for platform details: {type(data)}")
            return
        
        # Email address
        try:
            email = data.get('email')
            if email and isinstance(email, str):
                email_node_id = self._add_node(
                    label=email,
                    type='email',
                    metadata={'platform': platform}
                )
                self._add_edge(
                    platform_node_id,
                    email_node_id,
                    edge_type='USES_EMAIL',
                    confidence=0.9,
                    label='Associated Email'
                )
        except Exception as e:
            logger.debug(f"Could not add email from platform: {str(e)}")
        
        # Location
        try:
            location = data.get('location')
            if location and isinstance(location, str):
                location_node_id = self._add_node(
                    label=location,
                    type='location',
                    metadata={'platform': platform}
                )
                self._add_edge(
                    platform_node_id,
                    location_node_id,
                    edge_type='CONNECTED_TO',
                    confidence=0.7,
                    label='Location'
                )
        except Exception as e:
            logger.debug(f"Could not add location from platform: {str(e)}")
        
        # Organization/Company
        if 'company' in data and data['company']:
            org_node_id = self._add_node(
                label=data['company'],
                type='organization',
                metadata={'platform': platform}
            )
            self._add_edge(
                platform_node_id,
                org_node_id,
                edge_type='CONNECTED_TO',
                confidence=0.8,
                label='Works At'
            )
        
        # Keywords in bio
        if 'keywords' in data and data['keywords']:
            for keyword in data['keywords'][:3]:  # Limit to 3
                keyword_node_id = self._add_node(
                    label=keyword,
                    type='keyword',
                    metadata={'platform': platform}
                )
                self._add_edge(
                    platform_node_id,
                    keyword_node_id,
                    edge_type='POSTED_KEYWORD',
                    confidence=0.6,
                    label='Keyword'
                )
        
        # Mentions/Related accounts
        if 'mentions' in data and data['mentions']:
            for mention in data['mentions'][:2]:  # Limit to 2
                mention_node_id = self._add_node(
                    label=mention,
                    type='mention',
                    metadata={'platform': platform}
                )
                self._add_edge(
                    platform_node_id,
                    mention_node_id,
                    edge_type='MENTIONS',
                    confidence=0.5,
                    label='Mentions'
                )

    def _add_node(
        self,
        label: str,
        type: str = 'profile',
        risk_score: float = 0,
        is_central: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a node to the graph.
        
        Args:
            label: Display label
            type: Node type (profile, platform, email, phone, keyword, mention, location, organization)
            risk_score: Risk score 0-100
            is_central: Whether this is the central/target node
            metadata: Additional metadata dict
            
        Returns:
            Node ID (string)
        """
        node_id = f"node_{self.node_id_counter}"
        self.node_id_counter += 1
        
        # Get type configuration
        type_config = self.NODE_TYPES.get(type, {'color': '#6b7280', 'icon': '●'})
        
        # Size based on risk score and centrality
        if is_central:
            size = 50
        else:
            size = 30 + (risk_score / 100 * 20)  # Larger for higher risk
        
        node = {
            'id': node_id,
            'label': label,
            'type': type,
            'color': type_config['color'],
            'size': int(size),
            'title': f"{type.upper()}: {label}",
            'font': {'size': 14, 'color': '#fff'},
            'physics': True,
            'risk_score': max(0, min(100, risk_score)),
            'is_central': is_central,
            'metadata': metadata or {}
        }
        
        self.nodes.append(node)
        self.graph.add_node(node_id)
        
        return node_id

    def _add_edge(
        self,
        from_id: str,
        to_id: str,
        edge_type: str = 'MENTIONS',
        confidence: float = 1.0,
        label: str = ''
    ) -> None:
        """
        Add an edge connecting two nodes.
        
        Args:
            from_id: Source node ID
            to_id: Target node ID
            edge_type: Type of relationship (see EDGE_TYPES)
            confidence: Confidence score 0-1
            label: Display label
        """
        # Get edge type configuration
        type_config = self.EDGE_TYPES.get(edge_type, {
            'color': '#cbd5e0',
            'weight': 1,
            'description': label
        })
        
        edge = {
            'from': from_id,
            'to': to_id,
            'type': edge_type,
            'label': label or edge_type.replace('_', ' '),
            'title': f"{edge_type}: {type_config['description']} (confidence: {confidence:.2%})",
            'color': type_config['color'],
            'width': 2 + (confidence * 3),
            'confidence': round(confidence, 3),
            'weight': type_config['weight'],
            'smooth': {'type': 'continuous'},
            'arrows': 'from' if edge_type in ['MENTIONS', 'REPORTED_AS'] else None,
        }
        
        self.edges.append(edge)
        self.graph.add_edge(from_id, to_id, weight=type_config['weight'])

    def _determine_edge_type(self, entity_type: str) -> str:
        """
        Determine edge type based on entity type.
        
        Args:
            entity_type: Type of entity
            
        Returns:
            Edge type constant
        """
        type_mapping = {
            'email': 'USES_EMAIL',
            'phone': 'USES_PHONE',
            'mention': 'MENTIONS',
            'keyword': 'POSTED_KEYWORD',
            'location': 'CONNECTED_TO',
        }
        return type_mapping.get(entity_type, 'CONNECTED_TO')

    def _calculate_statistics(self) -> Dict[str, float]:
        """
        Calculate network statistics.
        
        Returns:
            Dict with density, average degree, clustering, etc.
        """
        if not self.graph.nodes():
            return {}
        
        try:
            density = nx.density(self.graph)
            
            # Calculate average degree
            degrees = [d for n, d in self.graph.degree()]
            avg_degree = sum(degrees) / len(degrees) if degrees else 0
            
            # Calculate clustering coefficient
            if self.graph.number_of_nodes() > 1:
                avg_clustering = nx.average_clustering(self.graph)
            else:
                avg_clustering = 0
            
            return {
                'density': round(density, 3),
                'avg_degree': round(avg_degree, 2),
                'avg_clustering': round(avg_clustering, 3),
                'node_count': self.graph.number_of_nodes(),
                'edge_count': self.graph.number_of_edges(),
                'is_connected': nx.is_connected(self.graph) if self.graph.number_of_nodes() > 0 and nx.is_connected(self.graph) is not None else False,
            }
        except Exception as e:
            logger.warning(f"Error calculating statistics: {str(e)}")
            return {}

    def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get complete graph statistics.
        
        Returns:
            Dict with comprehensive graph metrics
        """
        return self._calculate_statistics()

    def add_node(
        self,
        label: str,
        node_type: str = 'default',
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Public method to add a node.
        
        Args:
            label: Node label
            node_type: Node type
            metadata: Optional metadata
            
        Returns:
            Node ID
        """
        return self._add_node(label, node_type, metadata=metadata)

    def add_edge(
        self,
        from_id: str,
        to_id: str,
        relation_type: str = 'connected',
        confidence: float = 1.0
    ) -> None:
        """
        Public method to add an edge.
        
        Args:
            from_id: Source node ID
            to_id: Target node ID
            relation_type: Type of relationship
            confidence: Confidence score
        """
        self._add_edge(from_id, to_id, relation_type, confidence)

    def export_json(self) -> str:
        """
        Export graph as JSON string.
        
        Returns:
            JSON string representation of graph
        """
        data = {
            'nodes': self.nodes,
            'edges': self.edges,
            'stats': self.get_graph_stats()
        }
        return json.dumps(data, indent=2)
    
    def _empty_graph(self) -> Dict[str, Any]:
        """
        Return an empty but valid graph structure.
        Used as fallback when graph building fails.
        
        Returns:
            Empty graph dict
        """
        return {
            'nodes': [],
            'edges': [],
            'metadata': {
                'node_count': 0,
                'edge_count': 0,
                'platforms_found': 0,
                'density': 0,
                'avg_degree': 0,
                'created_at': datetime.utcnow().isoformat(),
                'error': 'Graph failed to build, returning empty structure'
            },
            'central_node': {
                'id': None,
                'label': 'Unknown',
                'type': 'profile'
            },
            'edge_types': list(self.EDGE_TYPES.keys()),
            'node_types': list(self.NODE_TYPES.keys())
        }

    def export_graphml(self) -> str:
        """
        Export graph as GraphML format (compatible with Gephi).
        
        Returns:
            GraphML XML string
        """
        try:
            if hasattr(nx, 'generate_graphml'):
                return '\n'.join(nx.generate_graphml(self.graph))
            if hasattr(nx, 'to_graphml'):
                return nx.to_graphml(self.graph)
            if hasattr(nx, 'write_graphml'):
                import io
                buf = io.StringIO()
                nx.write_graphml(self.graph, buf)
                return buf.getvalue()
            return '<?xml version="1.0" encoding="utf-8"?>\n<graphml></graphml>'
        except Exception as e:
            logger.warning(f"GraphML export failed: {e}")
            return '<?xml version="1.0" encoding="utf-8"?>\n<graphml></graphml>'
