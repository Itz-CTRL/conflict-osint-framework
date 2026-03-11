"""
Integration tests for light and deep scan investigation flow.
Tests the full pipeline from investigation creation through deep scanning.
"""

import sys
import os
import unittest
from unittest import mock
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.analyser_service import AnalyserService
from services.sherlock_checker import SherlockChecker
from services.crawler import BasicCrawler
from services.email_harvester import EmailHarvester


class MockFinding:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockInvestigation:
    query = None
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestLightScanFlow(unittest.TestCase):
    """Test light scan with Sherlock integration."""
    
    @mock.patch('services.analyser_service.SherlockChecker', autospec=True)
    @mock.patch('services.analyser_service.BehaviorAnalyzer', autospec=True)
    def test_light_scan_with sherlock(self, MockAnalyzer, MockSherlock):
        """Test light scan uses Sherlock for platform checking."""
        mock_sherlock = MockSherlock.return_value
        mock_sherlock.get_available_sites.return_value = [
            'GitHub', 'Twitter', 'Facebook', 'Instagram'
        ]
        mock_sherlock.check_username.return_value = {
            'found': {
                'count': 2,
                'sites': [
                    {
                        'site': 'GitHub',
                        'url': 'https://github.com/torvalds',
                        'profile_url': 'https://github.com/torvalds',
                        'status_code': 200
                    },
                    {
                        'site': 'Twitter',
                        'url': 'https://twitter.com/torvalds',
                        'profile_url': 'https://twitter.com/torvalds',
                        'status_code': 200
                    }
                ]
            }
        }
        
        mock_analyzer = MockAnalyzer.return_value
        mock_analyzer.analyze.return_value = {
            'username': 'torvalds',
            'risk_score': 15,
            'risk_level': 'LOW',
            'findings': []
        }
        
        analyser = AnalyserService(investigation_id=None)
        result = analyser.light_scan('torvalds')
        
        # Verify Sherlock was called
        MockSherlock.assert_called()
        mock_sherlock.check_username.assert_called_with('torvalds')
        
        # Verify result structure
        self.assertIn('data', result)
        self.assertIn('analysis', result['data'])
        self.assertEqual(result['risk_score'], 15)
        self.assertEqual(result['data']['platforms_found'], 2)
        
    @mock.patch('services.analyser_service.SherlockChecker', autospec=True)
    @mock.patch('services.analyser_service.BehaviorAnalyzer', autospec=True)
    def test_light_scan_no_findings(self, MockAnalyzer, MockSherlock):
        """Test light scan when username not found on any platform."""
        mock_sherlock = MockSherlock.return_value
        mock_sherlock.get_available_sites.return_value = [
            'GitHub', 'Twitter', 'Facebook', 'Instagram'
        ]
        mock_sherlock.check_username.return_value = {
            'found': {'count': 0, 'sites': []}
        }
        
        mock_analyzer = MockAnalyzer.return_value
        mock_analyzer.analyze.return_value = {
            'username': 'fakeuserxyznotreal',
            'risk_score': 0,
            'risk_level': 'LOW',
            'findings': []
        }
        
        analyser = AnalyserService(investigation_id=None)
        result = analyser.light_scan('fakeuserxyznotreal')
        
        self.assertEqual(result['data']['platforms_found'], 0)
        self.assertEqual(result['risk_score'], 0)


class TestDeepScanFlow(unittest.TestCase):
    """Test deep scan with crawlers, spiders, and email harvesting."""
    
    @mock.patch('services.analyser_service.SherlockChecker', autospec=True)
    @mock.patch('services.analyser_service.BasicCrawler', autospec=True)
    @mock.patch('services.analyser_service.EmailHarvester', autospec=True)
    @mock.patch('services.analyser_service.BehaviorAnalyzer', autospec=True)
    @mock.patch('services.analyser_service.OSINTScraper', autospec=True)
    def test_deep_scan_flow(self, MockScraper, MockAnalyzer, MockHarvester, 
                           MockCrawler, MockSherlock):
        """Test full deep scan pipeline."""
        # Setup mocks
        mock_sherlock = MockSherlock.return_value
        mock_sherlock.get_available_sites.return_value = ['GitHub', 'Twitter', 'Reddit']
        mock_sherlock.check_username.return_value = {
            'found': {
                'count': 1,
                'sites': [
                    {
                        'site': 'GitHub',
                        'url': 'https://github.com/testuser',
                        'profile_url': 'https://github.com/testuser',
                        'status_code': 200
                    }
                ]
            }
        }
        
        mock_scraper = MockScraper.return_value
        mock_scraper.get_reddit_data.return_value = {'found': False}
        mock_scraper.get_github_data.return_value = {'found': True, 'public_repos': 5}
        
        mock_crawler = MockCrawler.return_value
        mock_crawler.crawl.return_value = {
            'emails': ['user@example.com'],
            'mentions': ['mentioned_user'],
            'snippets': [],
            'urls_visited': ['https://github.com/testuser']
        }
        
        mock_harvester = MockHarvester.return_value
        mock_harvester.harvest_from_domain.return_value = ['admin@example.com']
        
        mock_analyzer = MockAnalyzer.return_value
        mock_analyzer.analyze.return_value = {
            'username': 'testuser',
            'risk_score': 25,
            'risk_level': 'LOW',
            'findings': ['Found on GitHub']
        }
        
        analyser = AnalyserService(investigation_id=None)
        result = analyser.deep_scan('testuser')
        
        # Verify structure
        self.assertIn('data', result)
        self.assertIn('analysis', result['data'])
        self.assertGreaterEqual(result['risk_score'], 0)
        
        # Verify Sherlock was used (through light_scan which is called first)
        MockSherlock.assert_called()


class TestSherlockChecker(unittest.TestCase):
    """Test Sherlock wrapper functionality."""
    
    def test_sherlock_available_sites(self):
        """Test getting available sites."""
        checker = SherlockChecker()
        sites = checker.get_available_sites()
        
        self.assertIsInstance(sites, list)
        self.assertGreater(len(sites), 5)
        self.assertIn('GitHub', sites)
        self.assertIn('Twitter', sites)
    
    @mock.patch('services.sherlock_checker.requests.head')
    def test_sherlock_check_single_platform(self, mock_head):
        """Test checking a single platform."""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.url = 'https://github.com/testuser'
        mock_head.return_value = mock_response
        
        checker = SherlockChecker()
        result = checker.check_username('testuser', sites=['GitHub'])
        
        self.assertEqual(result['found']['count'], 1)
        self.assertEqual(result['found']['sites'][0]['site'], 'GitHub')


class TestEmailHarvester(unittest.TestCase):
    """Test email harvesting functionality."""
    
    def test_harvest_from_text(self):
        """Test email extraction from text."""
        harvester = EmailHarvester()
        text = "Contact us at support@example.com or admin@example.com"
        
        emails = harvester.harvest_from_text(text)
        
        self.assertIn('support@example.com', emails)
        self.assertIn('admin@example.com', emails)
    
    def test_harvest_from_text_case_insensitive(self):
        """Test email extraction is case-insensitive."""
        harvester = EmailHarvester()
        text = "Email: Support@Example.COM"
        
        emails = harvester.harvest_from_text(text)
        
        self.assertEqual(emails[0].lower(), 'support@example.com')


if __name__ == '__main__':
    unittest.main()
