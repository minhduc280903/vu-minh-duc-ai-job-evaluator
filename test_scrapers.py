"""Quick test: run CareerViet + TopCV with just 1 keyword, 1 page each to verify parsing works."""
import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')

from ybox_scraper import setup_database
from careerviet_scraper import CareerVietScraper
from topcv_scraper import TopCVScraper
from crawl4ai import AsyncWebCrawler

async def test():
    setup_database()
    
    async with AsyncWebCrawler() as crawler:
        # Test CareerViet: 1 keyword, 1 page
        print("=== TESTING CAREERVIET ===")
        cv = CareerVietScraper()
        cv_jobs = await cv.scrape_keyword(crawler, "data analyst", max_pages=1)
        print(f"CareerViet result: {len(cv_jobs)} jobs")
        for j in cv_jobs[:3]:
            print(f"  [{j['id']}] {j['title'][:50]} | {j['company'][:25]} | sal={j['salary']}")
        
        print()
        
        # Test TopCV: 1 keyword, 1 page
        print("=== TESTING TOPCV ===")
        tc = TopCVScraper()
        tc_jobs = await tc.scrape_keyword(crawler, "data analyst", max_pages=1)
        print(f"TopCV result: {len(tc_jobs)} jobs")
        for j in tc_jobs[:3]:
            print(f"  [{j['id']}] {j['title'][:50]} | {j['company'][:25]} | sal={j['salary']}")

asyncio.run(test())
