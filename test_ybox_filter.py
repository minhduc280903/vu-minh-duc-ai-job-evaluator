import asyncio
from ybox_scraper import YboxScraper

async def run_test():
    s = YboxScraper()
    await s.scrape(num_pages=2)

if __name__ == '__main__':
    asyncio.run(run_test())
