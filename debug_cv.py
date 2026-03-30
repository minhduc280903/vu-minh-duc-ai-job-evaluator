"""Debug CareerViet: test just the HTML parsing"""
import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')

from ybox_scraper import setup_database
from careerviet_scraper import CareerVietScraper
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup

async def debug():
    setup_database()
    
    async with AsyncWebCrawler() as crawler:
        # Fetch the CareerViet search page
        url = "https://careerviet.vn/viec-lam/data-analyst-kw-vi.html"
        print(f"Fetching: {url}")
        result = await crawler.arun(url=url)
        html = result.html
        
        if not html:
            print("ERROR: No HTML returned!")
            return
        
        print(f"HTML length: {len(html)}")
        
        # Check what a.job_link returns
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try different selectors
        job_links = soup.find_all('a', class_='job_link')
        print(f"\na.job_link: {len(job_links)} found")
        for link in job_links[:3]:
            print(f"  href: {link.get('href', 'N/A')[:80]}")
            print(f"  title: {link.get('title', link.get_text(strip=True))[:60]}")
        
        # Check for any job-item divs
        job_items = soup.find_all('div', class_='job-item')
        print(f"\ndiv.job-item: {len(job_items)} found")
        
        # Check for any result-job-hover
        result_items = soup.find_all('div', class_='result-job-hover')
        print(f"div.result-job-hover: {len(result_items)} found")
        
        # Check for any figure elements
        figures = soup.find_all('div', class_='figure')
        print(f"div.figure: {len(figures)} found")
        
        # Check main container
        main_listing = soup.find('div', class_='main-listing')
        print(f"\ndiv.main-listing: {'Found' if main_listing else 'NOT found'}")
        
        # Check all hrefs containing /viec-lam/
        all_job_hrefs = soup.find_all('a', href=lambda h: h and '/viec-lam/' in h and '-kw' not in h)
        print(f"\nAll /viec-lam/ links (excl -kw): {len(all_job_hrefs)}")
        for link in all_job_hrefs[:5]:
            href = link.get('href', '')
            title = link.get('title', link.get_text(strip=True))
            print(f"  {title[:50]} -> {href[:80]}")
        
        # Now actually run the parser
        print("\n=== RUNNING parse_job_list ===")
        cv = CareerVietScraper()
        jobs = cv.parse_job_list(html)
        print(f"Result: {len(jobs)} jobs parsed")
        for j in jobs[:3]:
            print(f"  [{j['id']}] {j['title'][:45]} | {j['company'][:20]} | {j['salary']}")

asyncio.run(debug())
