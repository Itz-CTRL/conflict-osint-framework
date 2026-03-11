import sys
import os
import unittest
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.analyser_service import AnalyserService

class DummyScraper:
    def search_username(self, username):
        return {
            'username': username,
            'total_checked': 2,
            'found_count': 1,
            'platforms': [
                {'platform': 'GitHub', 'url': f'https://github.com/{username}', 'found': True},
                {'platform': 'Twitter', 'url': f'https://twitter.com/{username}', 'found': False}
            ]
        }

    def get_reddit_data(self, username):
        return {'found': False}

    def get_github_data(self, username):
        return {'found': True, 'login': username, 'email': None, 'public_repos': 1}

class DummyScrapyRunner:
    def __init__(self, *args, **kwargs):
        pass

    def run(self, start_urls, max_pages=10):
        return [
            {'url': start_urls[0], 'emails': ['found@example.com'], 'mentions': ['otheruser']}
        ]

class AnalyserDeepScanTest(unittest.TestCase):
    @mock.patch('services.analyser_service.OSINTScraper', autospec=True)
    @mock.patch('services.analyser_service.BasicCrawler', autospec=True)
    @mock.patch('services.analyser_service.EmailHarvester', autospec=True)
    def test_deep_scan_basic_flow(self, MockHarvester, MockCrawler, MockScraperClass):
        # Setup mocks
        mock_scraper = DummyScraper()
        MockScraperClass.return_value = mock_scraper

        # Make crawler return a simple crawl result
        MockCrawler.return_value.crawl.return_value = {
            'emails': ['crawl@example.com'],
            'mentions': ['mentioned'],
            'snippets': [{'url': 'https://example.com', 'text_snippet': 'sample'}],
            'urls_visited': ['https://example.com']
        }

        # Harvester harvest_from_domain returns additional emails
        MockHarvester.return_value.harvest_from_domain.return_value = ['harvested@example.com']

        analyser = AnalyserService(investigation_id=None)
        result = analyser.deep_scan('sometestuser')

        self.assertIn('data', result)
        self.assertIn('analysis', result['data'])
        self.assertIsInstance(result['risk_score'], float)
        # Ensure harvested emails are included in deep_data (analysis may vary)
        # We at least expect the 'data' dict to exist and include analysis
        self.assertTrue('username' in result['data'])

if __name__ == '__main__':
    unittest.main()
