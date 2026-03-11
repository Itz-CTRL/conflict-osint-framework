"""CSV Data Export Service
Exports investigation data in CSV format for analysis.

Supports:
- Findings export
- Entity export
- Graph export (edges)
- Full investigation export
"""

import logging
import csv
from io import StringIO
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class CSVExporter:
    """Export investigation data to CSV format"""
    
    @staticmethod
    def export_findings(investigation_id: str, findings: List[Dict[str, Any]]) -> str:
        """
        Export findings to CSV
        
        Args:
            investigation_id: Case ID
            findings: List of finding dicts
            
        Returns:
            CSV string
        """
        try:
            output = StringIO()
            
            if not findings:
                output.write("NO_DATA\n")
                return output.getvalue()
            
            # Get field names from first finding
            fieldnames = list(findings[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(findings)
            
            return output.getvalue()
        except Exception as e:
            logger.error(f"Error exporting findings to CSV: {str(e)}")
            return ""
    
    @staticmethod
    def export_entities(entities: List[Dict[str, Any]]) -> str:
        """
        Export entities (emails, phones, mentions, keywords) to CSV
        
        Args:
            entities: List of entity dicts
            
        Returns:
            CSV string
        """
        try:
            output = StringIO()
            
            if not entities:
                output.write("NO_DATA\n")
                return output.getvalue()
            
            fieldnames = ['entity_type', 'entity_value', 'platform', 'confidence', 'verified']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for entity in entities:
                writer.writerow({
                    'entity_type': entity.get('entity_type', ''),
                    'entity_value': entity.get('entity_value', ''),
                    'platform': entity.get('platform', ''),
                    'confidence': entity.get('confidence_score', 0),
                    'verified': entity.get('verified', False)
                })
            
            return output.getvalue()
        except Exception as e:
            logger.error(f"Error exporting entities to CSV: {str(e)}")
            return ""
    
    @staticmethod
    def export_investigation_summary(investigation_data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """
        Export investigation summary to CSV (single row)
        
        Args:
            investigation_data: Investigation dict
            analysis: Analysis dict
            
        Returns:
            CSV string
        """
        try:
            output = StringIO()
            
            fieldnames = [
                'case_id', 'username', 'email', 'phone',
                'status', 'risk_score', 'risk_level',
                'platforms_checked', 'platforms_found',
                'behavior_flags_count', 'keyword_hits_count',
                'created_at', 'completed_at'
            ]
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            row = {
                'case_id': investigation_data.get('case_id', ''),
                'username': investigation_data.get('username', ''),
                'email': investigation_data.get('email', ''),
                'phone': investigation_data.get('phone', ''),
                'status': investigation_data.get('status', ''),
                'risk_score': investigation_data.get('risk_score', 0),
                'risk_level': investigation_data.get('risk_level', ''),
                'platforms_checked': investigation_data.get('platforms_checked', 0),
                'platforms_found': investigation_data.get('platforms_found', 0),
                'behavior_flags_count': len(analysis.get('behavior_flags', [])),
                'keyword_hits_count': len(analysis.get('keyword_hits', [])),
                'created_at': investigation_data.get('created_at', ''),
                'completed_at': investigation_data.get('completed_at', '')
            }
            
            writer.writerow(row)
            
            return output.getvalue()
        except Exception as e:
            logger.error(f"Error exporting summary to CSV: {str(e)}")
            return ""
    
    @staticmethod
    def export_network_edges(edges: List[Dict[str, Any]]) -> str:
        """
        Export network graph edges to CSV
        
        Args:
            edges: List of edge dicts
            
        Returns:
            CSV string
        """
        try:
            output = StringIO()
            
            if not edges:
                output.write("NO_DATA\n")
                return output.getvalue()
            
            fieldnames = ['source', 'target', 'edge_type', 'weight', 'confidence']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for edge in edges:
                writer.writerow({
                    'source': edge.get('from', ''),
                    'target': edge.get('to', ''),
                    'edge_type': edge.get('type', ''),
                    'weight': edge.get('weight', 0),
                    'confidence': edge.get('confidence', 0)
                })
            
            return output.getvalue()
        except Exception as e:
            logger.error(f"Error exporting edges to CSV: {str(e)}")
            return ""
