import asyncio
import os
import sys
import logging

from ybox_scraper import YboxScraper
from vnw_scraper import VietnamWorksScraper
from topcv_scraper import TopCVScraper
from itviec_scraper import ITviecScraper
from careerviet_scraper import CareerVietScraper
from joboko_scraper import JobokoScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('run_all_scrapers')

async def main():
    logger.info("========== STARTING FULL SCRAPE (Targeted Multi-Keyword) ==========")
    
    # 1. Ybox (very fast, GraphQL API)
    logger.info("--- 1. YBOX ---")
    ybox = YboxScraper()
    await ybox.scrape(num_pages=None)
    
    # 2. VietnamWorks (API - fast, multi-query across IT + Finance + Accounting)
    logger.info("--- 2. VIETNAMWORKS (16 targeted queries) ---")
    vnw = VietnamWorksScraper()
    await vnw.scrape()
    
    # 3. TopCV (Crawl4AI - keyword search)
    logger.info("--- 3. TOPCV (14 keyword searches) ---")
    topcv = TopCVScraper()
    await topcv.scrape(max_pages_per_keyword=15)
    
    # 4. ITviec (Crawl4AI - keyword search)
    logger.info("--- 4. ITVIEC (8 keyword searches) ---")
    itviec = ITviecScraper()
    await itviec.scrape(max_pages_per_keyword=100)
    
    # 5. CareerViet (Crawl4AI - NEW, key for Finance/Banking)
    logger.info("--- 5. CAREERVIET (16 keyword searches) ---")
    careerviet = CareerVietScraper()
    await careerviet.scrape(max_pages_per_keyword=10)
    
    # 6. Joboko (Crawl4AI - keyword search, Hanoi focused)
    logger.info("--- 6. JOBOKO (13 keyword searches) ---")
    joboko = JobokoScraper()
    await joboko.scrape(max_pages_per_keyword=5)
    
    logger.info("========== ALL SCRAPES COMPLETED ==========")

if __name__ == "__main__":
    asyncio.run(main())
