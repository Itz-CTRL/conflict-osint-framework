"""Runner for the Scrapy investigation spider.

Attempts to run the spider via subprocess `scrapy runspider` and collects JSONL output.
If Scrapy is not installed or `scrapy` is unavailable in PATH, this runner will
raise a clear error so the caller can fallback to `BasicCrawler`.
"""

import subprocess
import json
import tempfile
import os
import logging
from typing import List

logger = logging.getLogger(__name__)

def run_investigation_spider(start_urls: List[str], max_pages: int = 50, timeout: int = 60):
    if not start_urls:
        return []

    spider_path = os.path.join(os.path.dirname(__file__), '..', 'spiders', 'investigation_spider.py')
    spider_path = os.path.abspath(spider_path)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.jl') as outfj:
        out_path = outfj.name

    cmd = [
        'scrapy', 'runspider', spider_path,
        '-a', f"start_urls={','.join(start_urls)}",
        '-s', f"CLOSESPIDER_PAGECOUNT={max_pages}",
        '-o', out_path
    ]

    try:
        logger.info(f"Running scrapy spider: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, timeout=timeout)

        results = []
        with open(out_path, 'r', encoding='utf-8') as fh:
            for line in fh:
                try:
                    results.append(json.loads(line))
                except Exception:
                    continue
        return results
    except FileNotFoundError:
        raise RuntimeError('Scrapy not found in PATH; install Scrapy or use BasicCrawler')
    except subprocess.CalledProcessError as e:
        logger.debug(f"Scrapy run failed: {e}")
        return []
    finally:
        try:
            os.remove(out_path)
        except Exception:
            pass
