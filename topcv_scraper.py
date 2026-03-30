import asyncio
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
import logging
import sqlite3
import re
from datetime import datetime
from ybox_scraper import save_jobs, setup_database

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('topcv_scraper')

# ============================================================
# TopCV search URLs (confirmed from live site):
#   /tim-viec-lam-{slug}  -> search results page  
#   /viec-lam/{slug}      -> alternative path
# Job items use: div.job-item-search-result or div.job-item-2
# Title: h3.title a  or a.title
# Company: a.company  or a.company_name
# Salary: div.salary or label.salary
# ============================================================
SEARCH_KEYWORDS = [
    "data analyst",
    "risk analyst", 
    "financial analyst",
    "credit analyst",
    "business analyst",
    "phan tich du lieu",
    "phan tich tai chinh",
    "phan tich rui ro",
    "python developer",
    "ngan hang",
    "fresher tai chinh",
    "power bi",
    "kiem toan",
    "chuyen vien phan tich",
]

class TopCVScraper:
    def __init__(self):
        self.base_url = "https://www.topcv.vn"
        self.seen_ids = set()

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
                'skills': '',
                'salary': '',
                'deadline': '',
                'level': ''
            }

            # ---- Structured metadata from detail: div.job-detail__info--section ----
            salary_sections = soup.find_all('div', class_=re.compile(r'job-detail__info--section'))
            for sec in salary_sections:
                label = sec.find('div', class_=re.compile(r'job-detail__info--section-content-title'))
                value = sec.find('div', class_=re.compile(r'job-detail__info--section-content-value'))
                if label and value:
                    label_text = label.get_text(strip=True).lower()
                    if 'lương' in label_text or 'salary' in label_text:
                        detail['salary'] = value.get_text(strip=True)
                    elif 'kinh nghiệm' in label_text or 'experience' in label_text:
                        detail['level'] = value.get_text(strip=True)
                    elif 'cấp bậc' in label_text:
                        if not detail['level']:
                            detail['level'] = value.get_text(strip=True)
            # Fallback salary
            if not detail['salary']:
                salary_el = soup.find('div', class_=re.compile(r'job-info__item.*salary'))
                if salary_el:
                    detail['salary'] = salary_el.get_text(strip=True)

            # ---- Content: div.job-description__item ----
            desc_items = soup.find_all('div', class_='job-description__item')
            for item in desc_items:
                title_el = item.find('h3', class_=re.compile(r'job-description__item--title'))
                content_el = item.find('div', class_=re.compile(r'job-description__item--content'))
                
                if title_el and content_el:
                    title_text = title_el.get_text(strip=True).lower()
                    content = content_el.get_text(separator='\n', strip=True)
                    
                    if 'mô tả' in title_text or 'description' in title_text:
                        detail['description'] = content
                    elif 'yêu cầu' in title_text or 'requirement' in title_text:
                        detail['requirements'] = content
                    elif 'quyền lợi' in title_text or 'benefit' in title_text:
                        detail['benefits'] = content

            # Fallback: h3 based extraction
            if not detail['description']:
                for h3 in soup.find_all('h3'):
                    text = h3.get_text(strip=True)
                    sib = h3.find_next_sibling()
                    if sib:
                        content = sib.get_text(separator='\n', strip=True)
                        if 'Mô tả công việc' in text:
                            detail['description'] = content
                        elif 'Yêu cầu ứng viên' in text:
                            detail['requirements'] = content
                        elif 'Quyền lợi' in text:
                            detail['benefits'] = content
               
            # Deadline
            deadline_tag = soup.find(string=re.compile('Hạn nộp hồ sơ'))
            if deadline_tag:
                span = deadline_tag.find_next('span')
                if span:
                    detail['deadline'] = span.get_text(strip=True)
                        
            return detail
        except Exception as e:
            logger.error(f"Error parsing detail for {job_url}: {e}")
            return None

    def parse_job_list(self, html):
        jobs = []
        if not html:
            return jobs
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try multiple selectors confirmed from live site
        job_items = soup.find_all('div', class_='job-item-search-result')
        if not job_items:
            job_items = soup.find_all('div', class_='job-item-2')
        if not job_items:
            job_items = soup.find_all('div', class_=re.compile(r'job-list-item|job-item'))
        
        for item in job_items:
            try:
                # ---- Title + URL ----
                title_a = None
                # Try: a.title.quickview-job, or h3.title > a, or a.title
                title_a = item.find('a', class_=re.compile(r'title'))
                if not title_a:
                    h3 = item.find('h3', class_='title')
                    if h3:
                        title_a = h3.find('a')
                     
                if not title_a:
                    continue
                    
                url = title_a.get('href', '')
                if url and not url.startswith('http'):
                    url = f"{self.base_url}{url}"
                
                if '/brand/' in url or '/cong-ty/' in url:
                    continue
                
                # Job ID from URL
                job_id = "unknown"
                id_match = re.search(r'/([^/]+)\.html', url)
                if id_match:
                    job_id = id_match.group(1)
                else:
                    # URL might be /viec-lam/slug-jXXXXXX
                    id_match = re.search(r'-j(\d+)', url)
                    if id_match:
                        job_id = f"j{id_match.group(1)}"
                    else:
                        job_id = str(hash(url))[-10:]

                if job_id in self.seen_ids:
                    continue
                self.seen_ids.add(job_id)
                
                title = title_a.get_text(strip=True)
                
                # ---- Company ----
                company = "N/A"
                co = item.find('a', class_=re.compile(r'company_name|company'))
                if co:
                    company = co.get_text(strip=True)
                
                # ---- Salary ----
                salary = "Thỏa thuận"
                sal = item.find(['div', 'label', 'span'], class_=re.compile(r'salary'))
                if sal:
                    salary = sal.get_text(strip=True)
                
                # ---- Location ----
                location = ""
                loc = item.find(['div', 'label', 'span'], class_=re.compile(r'location|address'))
                if loc:
                    location = loc.get_text(strip=True)
                
                # ---- Deadline ----
                deadline = ""
                time_el = item.find('div', class_='time')
                if time_el:
                    deadline = time_el.get_text(strip=True)
                    
                if deadline and ('Hết hạn' in deadline or 'Expired' in deadline):
                    continue
                    
                parsed_job = {
                    'id': f"topcv_{job_id}",
                    'platform': 'TopCV',
                    'title': title,
                    'company': company,
                    'url': url,
                    'summary': '',
                    'deadline': deadline,
                    'views': 0,
                    'published_at': datetime.now().isoformat(),
                    'salary': salary,
                    'location': location,
                    'skills': '',
                    'raw': {}
                }
                jobs.append(parsed_job)
            except Exception as e:
                logger.error(f"Error parsing TopCV list item: {e}")
                
        return jobs

    async def scrape_keyword(self, crawler, keyword, max_pages=20):
        """Scrape a single keyword search on TopCV."""
        # TopCV URL: /tim-viec-lam-{slug}
        keyword_slug = keyword.replace(' ', '-').lower()
        
        keyword_jobs = []
        for page in range(1, max_pages + 1):
            # Use slug-based URL (confirmed working from browser)
            url = f"{self.base_url}/tim-viec-lam-{keyword_slug}?page={page}"
            logger.info(f"  [{keyword}] Fetching page {page}: {url}")
            
            try:
                result = await crawler.arun(url=url)
                html = result.html
            except Exception as e:
                logger.error(f"  [{keyword}] Crawl error: {e}")
                break
                
            if not html:
                logger.warning(f"  [{keyword}] Failed to fetch page {page}.")
                break
                
            parsed = self.parse_job_list(html)
            if not parsed:
                logger.info(f"  [{keyword}] No more jobs on page {page}.")
                break
            
            logger.info(f"  [{keyword}] Page {page}: {len(parsed)} jobs. Fetching details...")
            
            for job in parsed:
                if job['url'] and '/brand/' not in job['url']:
                    detail = await self.fetch_job_detail(crawler, job['url'])
                    if detail:
                        job.update({
                            'description': detail.get('description', ''),
                            'requirements': detail.get('requirements', ''),
                            'benefits': detail.get('benefits', ''),
                            'skills': detail.get('skills', '')
                        })
                        if detail.get('level'):
                            job['level'] = detail['level']
                        if detail.get('salary') and job['salary'] in ('Thỏa thuận', ''):
                            job['salary'] = detail['salary']
                        if detail.get('deadline'):
                            job['deadline'] = detail.get('deadline')
                    await asyncio.sleep(1)
            
            keyword_jobs.extend(parsed)
            inserted, updated = save_jobs(parsed)
            logger.info(f"  [{keyword}] P{page}: {inserted} new, {updated} updated")
        
        return keyword_jobs

    async def scrape(self, max_pages_per_keyword=15):
        logger.info(f"Starting TopCV multi-keyword scraper...")
        all_jobs = []
        setup_database()
        
        async with AsyncWebCrawler() as crawler:
            for keyword in SEARCH_KEYWORDS:
                logger.info(f"--- TopCV searching: '{keyword}' ---")
                jobs = await self.scrape_keyword(crawler, keyword, max_pages=max_pages_per_keyword)
                all_jobs.extend(jobs)
                
        logger.info(f"TopCV Scrape complete. Total unique jobs: {len(all_jobs)}")
        return all_jobs

async def main():
    scraper = TopCVScraper()
    await scraper.scrape(max_pages_per_keyword=15)

if __name__ == "__main__":
    asyncio.run(main())
