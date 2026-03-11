# -*- coding: utf-8 -*-
"""Scrapy spider for deep investigation crawling.

This spider is a scaffold: it accepts start_urls via `-a start_urls="url1,url2"`
and extracts emails and mentions from pages it visits. It writes JSON lines.

Run example:
  scrapy runspider backend/spiders/investigation_spider.py -a start_urls="https://example.com,https://example.org" -o output.jl

Note: This file is a scaffold and requires Scrapy installed to run.
"""

from scrapy import Spider, Request
import re

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', re.I)
MENTION_RE = re.compile(r'@([A-Za-z0-9_\.-]+)')

class InvestigationSpider(Spider):
    name = 'investigation_spider'

    def __init__(self, start_urls=None, max_pages=50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if start_urls:
            self.start_urls = [u.strip() for u in start_urls.split(',') if u.strip()]
        else:
            self.start_urls = []
        self.max_pages = int(max_pages)

    def parse(self, response):
        text = response.text
        emails = EMAIL_RE.findall(text)
        mentions = MENTION_RE.findall(text)

        yield {
            'url': response.url,
            'status': response.status,
            'emails': list(set([e.lower() for e in emails])),
            'mentions': list(set(mentions)),
        }

        # follow links (simple depth-limited following is done by Scrapy settings)
        for href in response.css('a::attr(href)').getall():
            yield response.follow(href, callback=self.parse)
