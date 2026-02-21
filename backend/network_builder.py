"""
Network graph builder for OSINT investigations
Converts investigation data into interactive network visualizations
"""
import json
import networkx as nx
from datetime import datetime


class NetworkGraphBuilder:
    """Builds network graphs from investigation findings"""

    def __init__(self):
        self.graph = nx.Graph()
        self.nodes = []
        self.edges = []
        self.node_id_counter = 0

    def build_from_investigation(self, investigation, findings):
        """
        Build a network graph from investigation data
        
        Args:
            investigation: Investigation object with username, id, created_at
            findings: List of Finding objects with platform data
            
        Returns:
            dict: Network data with nodes and edges for Vis.js
        """
        self.graph.clear()
        self.nodes = []
        self.edges = []
        self.node_id_counter = 0

        # Central node - the investigated username
        central_node_id = self._add_node(
            label=f"@{investigation['username']}",
            type='target',
            title=f"Investigation #{investigation['id']}"
        )

        # Parse findings and build network
        platforms_found = []
        
        for finding in findings:
            if finding['platform'] == 'ANALYSIS':
                continue

            if finding.get('found'):
                platforms_found.append(finding)
                
                # Add platform node
                platform_node_id = self._add_node(
                    label=finding['platform'],
                    type='platform',
                    title=finding.get('profile_url', '')
                )

                # Connect username to platform
                self._add_edge(
                    central_node_id,
                    platform_node_id,
                    label='found_on'
                )

                # Parse platform-specific data
                try:
                    data = json.loads(finding.get('data', '{}'))
                    
                    # Extract meaningful attributes from platform data
                    self._extract_platform_details(
                        data,
                        platform_node_id,
                        finding['platform']
                    )
                except:
                    pass

        return {
            'nodes': self.nodes,
            'edges': self.edges,
            'summary': {
                'target': investigation['username'],
                'platforms_found': len(platforms_found),
                'total_nodes': len(self.nodes),
                'total_connections': len(self.edges)
            }
        }

    def _add_node(self, label, type='default', title='', size=30):
        """Add a node to the network"""
        node_id = f"node_{self.node_id_counter}"
        self.node_id_counter += 1

        # Define node colors and styles by type
        type_config = {
            'target': {
                'color': '#FF1744',
                'size': 45,
                'icon': '👤'
            },
            'platform': {
                'color': '#00BCD4',
                'size': 35,
                'icon': '📱'
            },
            'location': {
                'color': '#FFA726',
                'size': 25,
                'icon': '📍'
            },
            'organization': {
                'color': '#26C6DA',
                'size': 25,
                'icon': '🏢'
            },
            'connection': {
                'color': '#66BB6A',
                'size': 25,
                'icon': '🔗'
            }
        }

        config = type_config.get(type, {
            'color': '#757575',
            'size': size,
            'icon': '●'
        })

        node = {
            'id': node_id,
            'label': label,
            'title': title,
            'color': config['color'],
            'size': config['size'],
            'font': {
                'size': 14,
                'face': 'Sora',
                'color': '#fff'
            },
            'type': type
        }

        self.nodes.append(node)
        self.graph.add_node(node_id)
        return node_id

    def _add_edge(self, source_id, target_id, label='', weight=1):
        """Add an edge connecting two nodes"""
        edge = {
            'from': source_id,
            'to': target_id,
            'label': label,
            'width': weight,
            'smooth': {
                'type': 'continuous'
            }
        }
        self.edges.append(edge)
        self.graph.add_edge(source_id, target_id, weight=weight)

    def _extract_platform_details(self, data, platform_node_id, platform_name):
        """Extract details from platform-specific data and add to network"""
        
        if platform_name == 'GitHub':
            # Add location node if available
            if data.get('location'):
                location_node_id = self._add_node(
                    label=data['location'],
                    type='location',
                    title='GitHub Location'
                )
                self._add_edge(platform_node_id, location_node_id, 'located_at')

            # Add organization node if available
            if data.get('company'):
                org_node_id = self._add_node(
                    label=data['company'],
                    type='organization',
                    title='GitHub Company'
                )
                self._add_edge(platform_node_id, org_node_id, 'works_at')

        elif platform_name == 'Reddit':
            # Add subreddit activity (if we have post data)
            if isinstance(data, dict) and data.get('recent_posts'):
                for i, post in enumerate(data['recent_posts'][:5]):
                    subreddit = post.get('subreddit', 'unknown')
                    subreddit_node_id = self._add_node(
                        label=f"r/{subreddit}",
                        type='connection',
                        title=f"Reddit Community"
                    )
                    self._add_edge(
                        platform_node_id,
                        subreddit_node_id,
                        f"active_in"
                    )

    def get_graph_stats(self):
        """Calculate network statistics"""
        if not self.graph.nodes():
            return {}

        return {
            'node_count': self.graph.number_of_nodes(),
            'edge_count': self.graph.number_of_edges(),
            'density': nx.density(self.graph) if self.graph.number_of_nodes() > 1 else 0,
            'avg_clustering': nx.average_clustering(self.graph) if self.graph.number_of_nodes() > 1 else 0,
        }
