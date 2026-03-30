"""Run only CareerViet + TopCV (the two fixed scrapers)"""
import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('run_fixed')

from topcv_scraper import TopCVScraper
from careerviet_scraper import CareerVietScraper

async def main():
    logger.info("=== RUNNING FIXED SCRAPERS ===")
    
    # TopCV (14 keywords)
    logger.info("--- TOPCV ---")
    topcv = TopCVScraper()
    await topcv.scrape(max_pages_per_keyword=10)
    
    # CareerViet (16 keywords)
    logger.info("--- CAREERVIET ---")
    careerviet = CareerVietScraper()
    await careerviet.scrape(max_pages_per_keyword=5)
    
    logger.info("=== DONE ===")

if __name__ == "__main__":
    asyncio.run(main())
