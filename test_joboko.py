"""Quick test: scrape 1 page of 'data analyst' from Joboko"""
import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8')
from joboko_scraper import JobokoScraper
from ybox_scraper import setup_database, save_jobs

async def test():
    setup_database()
    scraper = JobokoScraper()
    from crawl4ai import AsyncWebCrawler
    async with AsyncWebCrawler(headless=True) as crawler:
        jobs = await scraper.scrape_keyword(crawler, "data analyst", max_pages=1)
        print(f"\nTotal jobs found: {len(jobs)}")
        for j in jobs[:5]:
            print(f"\n  Title: {j['title']}")
            print(f"  Company: {j['company']}")
            print(f"  Salary: {j['salary']}")
            print(f"  Location: {j['location']}")
            print(f"  Level: {j.get('level', '')}")
            print(f"  Desc: {(j.get('description',''))[:80]}...")
            print(f"  URL: {j['url']}")

asyncio.run(test())
