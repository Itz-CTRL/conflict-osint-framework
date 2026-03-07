"""Graph Routes
Handles network graph operations.
Uses NetworkGraphBuilder for constructing and exporting network graphs.
"""

from flask import Blueprint, request, jsonify
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from models import Investigation, Entity, NetworkEdge, Finding
from services.network_builder import NetworkGraphBuilder
from utils import APIResponse
import json

logger = logging.getLogger(__name__)

graph_bp = Blueprint('graph', __name__, url_prefix='/api/graph')

# Initialize graph builder
graph_builder = NetworkGraphBuilder()


@graph_bp.route('/<case_id>', methods=['GET'])
def get_graph(case_id):
    """
    Get network graph for an investigation
    
    Returns:
    {
        "status": "success",
        "graph": {
            "nodes": [{"id": "...", "label": "...", "group": "...", ...}],
            "edges": [{"from": "...", "to": "...", "label": "...", ...}],
            "metadata": {
                "node_count": 25,
                "edge_count": 42,
                "central_node": "target_username"
            }
        }
    }
    """
    try:
        investigation = Investigation.query.get(case_id)
        if not investigation:
            return jsonify(APIResponse.error(case_id, "Investigation not found")), 404
        
        # Get all findings for this investigation
        findings = Finding.query.filter_by(investigation_id=case_id).all()
        findings_data = [
            json.loads(f.data) if isinstance(f.data, str) else f.data 
            for f in findings
        ]
        
        # Build graph from findings
        graph = graph_builder.build_from_investigation(
            {'username': investigation.primary_entity, 'id': case_id},
            findings_data
        )
        
        response = APIResponse.success(
            case_id,
            graph=graph,
            status='completed'
        )
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error getting graph: {str(e)}", exc_info=True)
        return jsonify(APIResponse.error(case_id, f"Server error: {str(e)}")), 500


@graph_bp.route('/<case_id>/statistics', methods=['GET'])
def get_graph_stats(case_id):
    """
    Get graph statistics
    
    Returns:
    {
        "status": "success",
        "statistics": {
            "total_nodes": 25,
            "total_edges": 42,
            "central_node": "target_username",
            "avg_degree": 3.36,
            "density": 0.34
        }
    }
    """
    try:
        investigation = Investigation.query.get(case_id)
        if not investigation:
            return jsonify(APIResponse.error(case_id, "Investigation not found")), 404
        
        # Get findings
        findings = Finding.query.filter_by(investigation_id=case_id).all()
        findings_data = [
            json.loads(f.data) if isinstance(f.data, str) else f.data 
            for f in findings
        ]
        
        # Build graph
        graph = graph_builder.build_from_investigation(
            {'username': investigation.primary_entity, 'id': case_id},
            findings_data
        )
        
        # Calculate statistics
        nodes = graph.get('nodes', [])
        edges = graph.get('edges', [])
        
        stats = {
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'central_node': investigation.primary_entity,
            'avg_degree': (2 * len(edges) / len(nodes)) if nodes else 0,
            'density': (2 * len(edges) / (len(nodes) * (len(nodes) - 1))) if len(nodes) > 1 else 0
        }
        
        return jsonify({
            'status': 'success',
            'case_id': case_id,
            'statistics': stats
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting graph stats: {str(e)}")
        return jsonify(APIResponse.error(case_id, f"Server error: {str(e)}")), 500


@graph_bp.route('/<case_id>/entities', methods=['GET'])
def get_entities(case_id):
    """
    Get all entities in graph
    
    Query params:
    - type: filter by entity type
    - limit: max results (default 100)
    """
    try:
        investigation = Investigation.query.get(case_id)
        if not investigation:
            return jsonify(APIResponse.error(case_id, "Investigation not found")), 404
        
        entity_type = request.args.get('type')
        limit = request.args.get('limit', 100, type=int)
        
        query = Entity.query.filter_by(investigation_id=case_id)
        
        if entity_type:
            query = query.filter_by(entity_type=entity_type)
        
        entities = query.limit(limit).all()
        entities_data = [e.to_dict() for e in entities]
        
        return jsonify({
            'status': 'success',
            'case_id': case_id,
            'entities': entities_data,
            'count': len(entities_data)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting entities: {str(e)}")
        return jsonify(APIResponse.error(case_id, f"Server error: {str(e)}")), 500


@graph_bp.route('/<case_id>/edges', methods=['GET'])
def get_edges(case_id):
    """
    Get all edges in graph
    
    Query params:
    - type: filter by edge type
    - limit: max results (default 100)
    """
    try:
        investigation = Investigation.query.get(case_id)
        if not investigation:
            return jsonify(APIResponse.error(case_id, "Investigation not found")), 404
        
        edge_type = request.args.get('type')
        limit = request.args.get('limit', 100, type=int)
        
        query = NetworkEdge.query.filter_by(investigation_id=case_id)
        
        if edge_type:
            query = query.filter_by(edge_type=edge_type)
        
        edges = query.limit(limit).all()
        edges_data = [e.to_dict() for e in edges]
        
        return jsonify({
            'status': 'success',
            'case_id': case_id,
            'edges': edges_data,
            'count': len(edges_data)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting edges: {str(e)}")
        return jsonify(APIResponse.error(case_id, f"Server error: {str(e)}")), 500


@graph_bp.route('/<case_id>/connected/<entity_id>', methods=['GET'])
def get_connected_entities(case_id, entity_id):
    """
    Get all entities connected to a specific entity
    
    Query params:
    - depth: search depth (default 1)
    """
    try:
        investigation = Investigation.query.get(case_id)
        if not investigation:
            return jsonify(APIResponse.error(case_id, "Investigation not found")), 404
        
        depth = request.args.get('depth', 1, type=int)
        
        # Get edges connected to entity
        connected_edges = NetworkEdge.query.filter(
            (NetworkEdge.source_entity_id == entity_id) | (NetworkEdge.target_entity_id == entity_id),
            NetworkEdge.investigation_id == case_id
        ).all()
        
        # Collect connected entity IDs
        connected_ids = set()
        for edge in connected_edges:
            if edge.source_entity_id == entity_id:
                connected_ids.add(edge.target_entity_id)
            else:
                connected_ids.add(edge.source_entity_id)
        
        # Get entity objects
        connected = Entity.query.filter(
            Entity.id.in_(connected_ids),
            Entity.investigation_id == case_id
        ).all()
        
        connected_data = [e.to_dict() for e in connected]
        
        return jsonify({
            'status': 'success',
            'case_id': case_id,
            'entity_id': entity_id,
            'depth': depth,
            'entities': connected_data,
            'count': len(connected_data)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting connected entities: {str(e)}")
        return jsonify(APIResponse.error(case_id, f"Server error: {str(e)}")), 500


@graph_bp.route('/<case_id>/entity/<entity_id>', methods=['GET'])
def get_entity_details(case_id, entity_id):
    """
    Get details for a specific entity
    """
    try:
        investigation = Investigation.query.get(case_id)
        if not investigation:
            return jsonify(APIResponse.error(case_id, "Investigation not found")), 404
        
        entity = Entity.query.filter_by(
            investigation_id=case_id,
            id=entity_id
        ).first()
        
        if not entity:
            return jsonify(APIResponse.error(case_id, "Entity not found")), 404
        
        # Get connected edges
        connected_edges = NetworkEdge.query.filter(
            (NetworkEdge.source_entity_id == entity_id) | (NetworkEdge.target_entity_id == entity_id),
            NetworkEdge.investigation_id == case_id
        ).all()
        
        edges_data = [e.to_dict() for e in connected_edges]
        
        return jsonify({
            'status': 'success',
            'case_id': case_id,
            'entity': entity.to_dict(),
            'connected_edges': edges_data,
            'connection_count': len(edges_data)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting entity details: {str(e)}")
        return jsonify(APIResponse.error(case_id, f"Server error: {str(e)}")), 500


@graph_bp.route('/<case_id>/export', methods=['GET'])
def export_graph(case_id):
    """
    Export graph in various formats
    
    Query params:
    - format: 'json' (default), 'graphml', 'gexf'
    """
    try:
        investigation = Investigation.query.get(case_id)
        if not investigation:
            return jsonify(APIResponse.error(case_id, "Investigation not found")), 404
        
        format_type = request.args.get('format', 'json').lower()
        
        # Get findings
        findings = Finding.query.filter_by(investigation_id=case_id).all()
        findings_data = [
            json.loads(f.data) if isinstance(f.data, str) else f.data 
            for f in findings
        ]
        
        # Build graph
        graph = graph_builder.build_from_investigation(
            {'username': investigation.primary_entity, 'id': case_id},
            findings_data
        )
        
        if format_type == 'json':
            return jsonify({
                'status': 'success',
                'case_id': case_id,
                'format': 'json',
                'graph': graph
            }), 200
        
        else:
            return jsonify(APIResponse.error(case_id, f"Unsupported format: {format_type}")), 400
    
    except Exception as e:
        logger.error(f"Error exporting graph: {str(e)}")
        return jsonify(APIResponse.error(case_id, f"Server error: {str(e)}")), 500
