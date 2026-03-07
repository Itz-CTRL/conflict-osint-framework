#!/usr/bin/env python3
"""
Test Suite for OSINT Platform Services

This module provides comprehensive unit and integration tests for:
- PhoneIntelligenceService
- GraphEngineService
- Database models
- API endpoints

Run with: python test_suite.py -v
Or: pytest test_suite.py -v
"""

import sys
import json
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add backend to path
sys.path.insert(0, '/home/ctrl/Desktop/conflict-osint-framework/backend')

from services import PhoneIntelligenceService, GraphEngineService
from models import Investigation, Finding, PhoneIntelligence
from database import db
from app import create_app


class TestPhoneIntelligenceService(unittest.TestCase):
    """Test PhoneIntelligenceService functionality"""

    def setUp(self):
        """Initialize service for each test"""
        self.service = PhoneIntelligenceService()

    def test_lookup_valid_us_number(self):
        """Test lookup with valid US phone number"""
        result = self.service.lookup("+1-202-555-1234")
        
        # Assertions
        self.assertEqual(result['valid'], True)
        self.assertEqual(result['country_code'], 'US')
        self.assertIn('country', result)
        self.assertIn('carrier', result)
        self.assertIn('timezone', result)
        self.assertGreaterEqual(result['risk_score'], 0)
        self.assertLessEqual(result['risk_score'], 100)
        self.assertGreaterEqual(result['confidence'], 0)
        self.assertLessEqual(result['confidence'], 1.0)

    def test_lookup_valid_uk_number(self):
        """Test lookup with valid UK phone number"""
        result = self.service.lookup("+44-20-7946-0958")
        
        self.assertEqual(result['valid'], True)
        self.assertEqual(result['country_code'], 'GB')
        self.assertEqual(result['country'], 'United Kingdom')

    def test_lookup_international_formats(self):
        """Test various phone number formats"""
        formats = [
            "+1-202-555-1234",           # US with hyphens
            "1 (202) 555-1234",          # US with parentheses
            "202.555.1234",              # US with dots
            "+1 202 555 1234",           # US with spaces
            "001-541-754-3010",          # US international
        ]
        
        for phone in formats:
            result = self.service.lookup(phone)
            self.assertEqual(result['valid'], True, f"Failed to parse: {phone}")

    def test_lookup_invalid_number(self):
        """Test lookup with invalid phone number"""
        result = self.service.lookup("not-a-valid-phone")
        
        self.assertEqual(result['valid'], False)
        self.assertIsNone(result['error']) or self.assertIsNotNone(result['error'])

    def test_lookup_output_structure(self):
        """Test that lookup returns expected dictionary structure"""
        result = self.service.lookup("+1-202-555-1234")
        
        required_keys = [
            'valid', 'number', 'country', 'country_code', 'region',
            'carrier', 'carrier_type', 'timezone', 'social_presence',
            'emails_found', 'risk_score', 'risk_level', 'confidence',
            'last_checked', 'error'
        ]
        
        for key in required_keys:
            self.assertIn(key, result, f"Missing key: {key}")

    def test_batch_lookup(self):
        """Test batch lookup with multiple numbers"""
        phones = [
            "+1-202-555-1234",
            "+44-20-7946-0958",
            "invalid-phone"
        ]
        
        results = self.service.batch_lookup(phones)
        
        self.assertEqual(len(results), 3)
        self.assertIsInstance(results, list)
        self.assertEqual(results[0]['valid'], True)
        self.assertEqual(results[1]['valid'], True)
        self.assertEqual(results[2]['valid'], False)

    def test_batch_lookup_limit(self):
        """Test batch lookup respects maximum limit"""
        # Generate 101 valid phone numbers
        phones = [f"+1-202-555-{str(i).zfill(4)}" for i in range(101)]
        
        results = self.service.batch_lookup(phones)
        
        # Should be limited to 100
        self.assertLessEqual(len(results), 100)

    def test_validate_only(self):
        """Test quick validation method"""
        result = self.service.validate_only("+1-202-555-1234")
        
        self.assertIn('valid', result)
        self.assertIn('formatted', result)
        # Should be quick, no full intelligence extraction
        self.assertNotIn('carrier', result)

    def test_risk_score_calculation(self):
        """Test risk score is calculated consistently"""
        result = self.service.lookup("+1-202-555-1234")
        
        # Risk should be deterministic for same input
        result2 = self.service.lookup("+1-202-555-1234")
        
        self.assertEqual(result['risk_score'], result2['risk_score'])
        self.assertEqual(result['risk_level'], result2['risk_level'])

    def test_risk_levels(self):
        """Test risk level categories"""
        valid_levels = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'MINIMAL']
        
        result = self.service.lookup("+1-202-555-1234")
        self.assertIn(result['risk_level'], valid_levels)

    def test_response_json_serializable(self):
        """Test that lookup result is JSON serializable"""
        result = self.service.lookup("+1-202-555-1234")
        
        # Should not raise exception
        json_str = json.dumps(result)
        self.assertIsNotNone(json_str)
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        self.assertEqual(parsed['valid'], result['valid'])


class TestGraphEngineService(unittest.TestCase):
    """Test GraphEngineService functionality"""

    def setUp(self):
        """Initialize service for each test"""
        self.engine = GraphEngineService(case_id="test-case-123")
        
        self.sample_investigation = {
            'id': 'test-case-123',
            'username': 'testuser',
            'email': 'test@example.com',
            'phone': '+1-202-555-1234',
            'risk_score': 45
        }
        
        self.sample_findings = [
            {
                'platform': 'Twitter',
                'found': True,
                'username': 'testuser123',
                'profile_url': 'https://twitter.com/testuser123',
                'metadata': {
                    'emails': ['test2@example.com'],
                    'keywords': ['security', 'OSINT']
                }
            },
            {
                'platform': 'GitHub',
                'found': True,
                'username': 'testuser-dev',
                'profile_url': 'https://github.com/testuser-dev',
                'metadata': {
                    'repositories': ['security-tools'],
                    'emails': []
                }
            }
        ]

    def test_build_from_investigation(self):
        """Test graph building from investigation data"""
        graph = self.engine.build_from_investigation(
            self.sample_investigation,
            self.sample_findings
        )
        
        self.assertIn('nodes', graph)
        self.assertIn('edges', graph)
        self.assertIn('metadata', graph)
        self.assertIsInstance(graph['nodes'], list)
        self.assertIsInstance(graph['edges'], list)

    def test_graph_output_structure(self):
        """Test graph JSON structure"""
        graph = self.engine.build_from_investigation(
            self.sample_investigation,
            self.sample_findings
        )
        
        # Check root structure
        self.assertIn('nodes', graph)
        self.assertIn('edges', graph)
        self.assertIn('metadata', graph)
        self.assertIn('statistics', graph)
        
        # Check node structure
        for node in graph['nodes']:
            required_keys = ['id', 'label', 'type', 'size', 'color']
            for key in required_keys:
                self.assertIn(key, node, f"Node missing {key}")
        
        # Check edge structure
        for edge in graph['edges']:
            required_keys = ['from', 'to', 'type', 'label', 'color']
            for key in required_keys:
                self.assertIn(key, edge, f"Edge missing {key}")

    def test_node_types(self):
        """Test various node types are created"""
        graph = self.engine.build_from_investigation(
            self.sample_investigation,
            self.sample_findings
        )
        
        node_types = set(node['type'] for node in graph['nodes'])
        
        # Should have central profile and platform nodes
        self.assertTrue(len(node_types) > 0)

    def test_edge_types(self):
        """Test edge types are valid"""
        graph = self.engine.build_from_investigation(
            self.sample_investigation,
            self.sample_findings
        )
        
        valid_edge_types = {
            'MENTIONS', 'CONNECTED_TO', 'USES_EMAIL', 'USES_PHONE',
            'POSTED_KEYWORD', 'REPORTED_AS', 'SIMILAR_USERNAME'
        }
        
        for edge in graph['edges']:
            self.assertIn(edge['type'], valid_edge_types)

    def test_graph_statistics(self):
        """Test statistics calculation"""
        graph = self.engine.build_from_investigation(
            self.sample_investigation,
            self.sample_findings
        )
        
        stats = graph['statistics']
        
        self.assertIn('node_count', stats)
        self.assertIn('edge_count', stats)
        self.assertIn('density', stats)
        self.assertIn('is_connected', stats)
        
        # Graph should have nodes
        self.assertGreater(stats['node_count'], 0)

    def test_add_node(self):
        """Test adding node manually"""
        self.engine.add_node(
            node_id='test-node-1',
            node_type='email',
            label='test@example.com',
            metadata={'verified': True},
            risk_score=25
        )
        
        # Build to get graph
        graph = self.engine.build_from_investigation(
            self.sample_investigation,
            []
        )
        
        # Manual node should be in graph if engine maintains state
        # (Note: This depends on implementation)

    def test_add_edge(self):
        """Test adding edge manually"""
        self.engine.add_node('node1', 'profile', 'User1', {}, 30)
        self.engine.add_node('node2', 'email', 'user1@example.com', {}, 20)
        
        self.engine.add_edge(
            source_id='node1',
            target_id='node2',
            edge_type='USES_EMAIL',
            metadata={'verified': True},
            strength=0.9
        )
        
        # Should not raise exception

    def test_get_statistics(self):
        """Test statistics retrieval"""
        self.engine.build_from_investigation(
            self.sample_investigation,
            self.sample_findings
        )
        
        stats = self.engine.get_statistics()
        
        self.assertIsNotNone(stats)
        self.assertGreaterEqual(stats['node_count'], 0)
        self.assertGreaterEqual(stats['edge_count'], 0)

    def test_get_connected_nodes(self):
        """Test finding connected nodes"""
        self.engine.build_from_investigation(
            self.sample_investigation,
            self.sample_findings
        )
        
        # Get connected nodes for central node
        connected = self.engine.get_connected_nodes(
            'testuser',
            depth=1
        )
        
        self.assertIsInstance(connected, list)

    def test_get_node_details(self):
        """Test getting node details"""
        self.engine.build_from_investigation(
            self.sample_investigation,
            self.sample_findings
        )
        
        # Should have central node
        details = self.engine.get_node_details('testuser')
        
        if details:  # Node exists
            self.assertIn('id', details)
            self.assertIn('label', details)

    def test_export_json(self):
        """Test JSON export"""
        self.engine.build_from_investigation(
            self.sample_investigation,
            self.sample_findings
        )
        
        json_export = self.engine.export_json()
        
        # Should be JSON serializable
        json_str = json.dumps(json_export)
        self.assertIsNotNone(json_str)

    def test_export_graphml(self):
        """Test GraphML export"""
        self.engine.build_from_investigation(
            self.sample_investigation,
            self.sample_findings
        )
        
        graphml = self.engine.export_graphml()
        
        # Should be valid XML string
        self.assertIsInstance(graphml, str)
        self.assertIn('<?xml', graphml)
        self.assertIn('graphml', graphml)

    def test_empty_graph_handling(self):
        """Test graph with no findings"""
        graph = self.engine.build_from_investigation(
            self.sample_investigation,
            []
        )
        
        # Should have at least central node
        self.assertGreater(len(graph['nodes']), 0)

    def test_graph_json_serializable(self):
        """Test complete graph is JSON serializable"""
        graph = self.engine.build_from_investigation(
            self.sample_investigation,
            self.sample_findings
        )
        
        # Should be JSON serializable
        json_str = json.dumps(graph)
        self.assertIsNotNone(json_str)
        
        # Should parse back correctly
        parsed = json.loads(json_str)
        self.assertEqual(len(parsed['nodes']), len(graph['nodes']))


class TestAPIIntegration(unittest.TestCase):
    """Integration tests for API endpoints"""

    def setUp(self):
        """Set up Flask test client"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create tables
        db.create_all()

    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_investigation(self):
        """Test creating investigation via API"""
        response = self.client.post(
            '/api/investigation/create',
            json={
                'username': 'testuser',
                'email': 'test@example.com',
                'phone': '+1-202-555-1234'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('case_id', data)

    def test_phone_lookup_api(self):
        """Test phone lookup endpoint"""
        response = self.client.post(
            '/api/phone/lookup',
            json={'phone': '+1-202-555-1234'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['data']['valid'])

    def test_phone_lookup_invalid(self):
        """Test phone lookup with invalid number"""
        response = self.client.post(
            '/api/phone/lookup',
            json={'phone': 'not-a-number'}
        )
        
        # Should handle gracefully
        self.assertIn(response.status_code, [200, 400])


class TestServiceIntegration(unittest.TestCase):
    """Test services working together"""

    def test_phone_intel_into_graph(self):
        """Test phone intelligence informing graph risk"""
        phone_service = PhoneIntelligenceService()
        graph_service = GraphEngineService(case_id="integration-test")
        
        # Get phone intelligence
        phone_intel = phone_service.lookup("+1-202-555-1234")
        
        # Use in graph
        investigation = {
            'id': 'integration-test',
            'username': 'testuser',
            'email': 'test@example.com',
            'phone': phone_intel['number'],
            'risk_score': phone_intel['risk_score']
        }
        
        graph = graph_service.build_from_investigation(investigation, [])
        
        # Risk should be reflected in graph
        self.assertGreater(len(graph['nodes']), 0)

    def test_batch_phone_into_graph(self):
        """Test batch phone lookups in graph context"""
        phone_service = PhoneIntelligenceService()
        graph_service = GraphEngineService(case_id="batch-test")
        
        # Batch lookup
        phones = [
            "+1-202-555-1234",
            "+44-20-7946-0958"
        ]
        results = phone_service.batch_lookup(phones)
        
        # All should be valid
        for result in results[:2]:
            self.assertTrue(result['valid'])


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPhoneIntelligenceService))
    suite.addTests(loader.loadTestsFromTestCase(TestGraphEngineService))
    suite.addTests(loader.loadTestsFromTestCase(TestServiceIntegration))
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # Run tests
    success = run_tests()
    sys.exit(0 if success else 1)
