import asyncio
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
import logging
import sqlite3
import re
from datetime import datetime
from ybox_scraper import save_jobs, setup_database

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('itviec_scraper')

# ============================================================
# Keyword searches — ITviec supports ?query= parameter on /it-jobs
# ============================================================
SEARCH_KEYWORDS = [
    "data analyst",
    "risk analyst",
    "financial analyst",
    "business analyst",
    "credit analyst",
    "python",
    "sql",
    "power bi",
    "",  # Empty = all IT jobs (original behavior, last to get broad coverage)
]

class ITviecScraper:
    def __init__(self):
        self.base_url = "https://itviec.com"
        self.search_url = f"{self.base_url}/it-jobs"
        self.seen_ids = set()  # Dedup across keywords

    def strip_html(self, text):
        if not text:
            return ""
        clean = re.compile('<.*?>')
        text_without_tags = re.sub(clean, '', str(text))
        return text_without_tags.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').strip()

    async def fetch_job_detail(self, crawler, job_url):
        try:
            result = await crawler.arun(url=job_url)
            html = result.html
            if not html:
                return None
                
            soup = BeautifulSoup(html, 'html.parser')
            detail = {
                'description': '',
                'requirements': '',
                'benefits': '',
                'salary': ''
            }
            
            # Extract salary from detail page
            salary_el = soup.find('div', class_=re.compile(r'job-details__overview'))
            if salary_el:
                salary_text = salary_el.find(string=re.compile(r'\$|VND|USD|triệu'))
                if salary_text:
                    detail['salary'] = salary_text.strip()
            
            # Reasons to join
            reasons = soup.find('div', class_=re.compile(r'job-details__reasons-to-join'))
            if reasons:
                detail['benefits'] += self.strip_html(reasons.decode_contents()) + "\n\n"
            
            # Job Description
            paragraphs = soup.find_all('div', class_=re.compile(r'paragraph'))
            
            for p in paragraphs:
                title_h = p.find(['h1', 'h2', 'h3', 'h4'])
                if not title_h:
                     title_h = p.find_previous_sibling(['h1', 'h2', 'h3', 'h4'])
                     
                title_text = title_h.text.strip().lower() if title_h else p.text.strip().lower()[:30]
                content = self.strip_html(p.decode_contents())
                
                if 'mô tả' in title_text or 'job description' in title_text or 'responsibilities' in title_text:
                    detail['description'] = content
                elif 'yêu cầu' in title_text or 'skills' in title_text or 'requirements' in title_text or 'experience' in title_text:
                    detail['requirements'] = content
                elif 'quyền lợi' in title_text or 'why you' in title_text or 'benefits' in title_text or 'reasons' in title_text:
                     detail['benefits'] += content + "\n\n"

            return detail
        except Exception as e:
            logger.error(f"Error parsing detail for {job_url}: {e}")
            return None

    def parse_job_list(self, html):
        jobs = []
        if not html:
            return jobs
            
        soup = BeautifulSoup(html, 'html.parser')
        job_cards = soup.find_all('div', class_=re.compile(r'job-card'))
        
        for item in job_cards:
            try:
                # Title
                h3 = item.find('h3')
                title = h3.text.strip() if h3 else "N/A"
                
                # Link
                url = None
                job_link_a = item.find('a', attrs={"data-search--pagination-target": "jobCard"})
                if job_link_a:
                     url = job_link_a.get('href')
                else:
                    # Fallback URL extraction
                    sign_in_link = item.find('a', class_=re.compile('sign-in'))
                    if sign_in_link and 'job=' in sign_in_link.get('href', ''):
                         job_id = sign_in_link.get('href').split('job=')[1].split('&')[0]
                         url = f"/it-jobs/{job_id}"
                         
                if url and not url.startswith('http'):
                     url = f"{self.base_url}{url}"
                     
                if not url:
                     continue
                     
                # Job ID
                job_id = url.split('/')[-1].split('?')[0]
                if not job_id:
                     job_id = str(hash(url))
                
                # Dedup across keyword searches
                if job_id in self.seen_ids:
                    continue
                self.seen_ids.add(job_id)
                
                # Company
                company_a = item.find('a', class_=re.compile('text-rich-grey|company'))
                company = company_a.text.strip() if company_a else "N/A"
                
                # Salary
                salary = "Thỏa thuận"
                salary_a = item.find('a', class_=re.compile('view-salary|salary'))
                if salary_a:
                    salary = salary_a.text.strip()
                else:
                    salary_div = item.find(string=re.compile(r'\$|VND'))
                    if salary_div: salary = salary_div.strip()
                    
                if "Sign in" in salary:
                     salary = "Sign in to view"
                
                # Location
                location = "N/A"
                loc_div = item.find(class_=re.compile('text-rich-grey text-truncate'))
                if loc_div and ('Minh' in loc_div.text or 'Noi' in loc_div.text or 'Nang' in loc_div.text):
                     location = loc_div.text.strip()
                     
                # Skills
                skills_arr = [a.text.strip() for a in item.find_all('a', class_=re.compile(r'itag|skill')) if a.text.strip()]
                skills = ", ".join(skills_arr)
                     
                parsed_job = {
                    'id': f"itviec_{job_id}",
                    'platform': 'ITviec',
                    'title': title,
                    'company': company,
                    'url': url,
                    'summary': '',
                    'deadline': '',
                    'views': 0,
                    'published_at': datetime.now().isoformat(),
                    'salary': salary,
                    'location': location,
                    'skills': skills,
                    'raw': {}
                }
                jobs.append(parsed_job)
            except Exception as e:
                logger.error(f"Error parsing ITviec list item: {e}")
                
        return jobs

    async def scrape_keyword(self, crawler, keyword, max_pages=50):
        """Scrape a single keyword on ITviec."""
        keyword_jobs = []
        
        for page in range(1, max_pages + 1):
            if keyword:
                url = f"{self.search_url}?query={keyword.replace(' ', '+')}&page={page}"
            else:
                url = f"{self.search_url}?page={page}"
            
            label = keyword if keyword else "all IT jobs"
            logger.info(f"  [{label}] Fetching page {page}: {url}")
            
            result = await crawler.arun(url=url)
            html = result.html
            
            if not html:
                logger.warning(f"  [{label}] Failed to fetch page {page}.")
                break
                
            parsed = self.parse_job_list(html)
            if not parsed:
                logger.info(f"  [{label}] No more jobs on page {page}.")
                break
            
            logger.info(f"  [{label}] Page {page}: {len(parsed)} jobs. Fetching details...")
            
            for i, job in enumerate(parsed):
                if job['url']:
                    detail = await self.fetch_job_detail(crawler, job['url'])
                    if detail:
                        job.update({
                            'description': detail.get('description', ''),
                            'requirements': detail.get('requirements', ''),
                            'benefits': detail.get('benefits', '')
                        })
                        # Update salary from detail if list had generic 
                        if detail.get('salary') and job['salary'] in ('Thỏa thuận', 'Sign in to view', ''):
                            job['salary'] = detail['salary']
                    await asyncio.sleep(1)
            
            keyword_jobs.extend(parsed)
            
            inserted, updated = save_jobs(parsed)
            logger.info(f"  [{label}] P{page}: {inserted} new, {updated} updated")
        
        return keyword_jobs

    async def scrape(self, max_pages_per_keyword=50):
        logger.info(f"Starting ITviec multi-keyword scraper...")
        all_jobs = []
        setup_database()
        
        async with AsyncWebCrawler() as crawler:
            for keyword in SEARCH_KEYWORDS:
                label = keyword if keyword else "all IT jobs"
                logger.info(f"--- ITviec searching: '{label}' ---")
                
                # Fewer pages for targeted keywords (they return fewer results)
                pages = 10 if keyword else max_pages_per_keyword
                jobs = await self.scrape_keyword(crawler, keyword, max_pages=pages)
                all_jobs.extend(jobs)
                
        logger.info(f"ITviec Scrape complete. Total unique jobs: {len(all_jobs)}")
        return all_jobs

async def main():
    scraper = ITviecScraper()
    await scraper.scrape(max_pages_per_keyword=100)

if __name__ == "__main__":
    asyncio.run(main())
