import asyncio
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
import logging
import re
from datetime import datetime
from ybox_scraper import save_jobs, setup_database

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('careerviet_scraper')

# ============================================================
# CareerViet search URL pattern (confirmed from live site):
#   /viec-lam/{keyword}-kw-vi.html  (page 1)
#   /viec-lam/{keyword}-kw-trang-{n}-vi.html  (page N)
# NOTE: Vietnamese diacritics removed in slug (e.g. "tai chinh" not "tài chính")
# ============================================================
SEARCH_KEYWORDS = [
    "data analyst",
    "risk analyst",
    "financial analyst",
    "credit analyst",
    "business analyst",
    "python",
    "sql",
    "power bi",
    "ngan hang",
    "tai chinh",
    "kiem toan",
    "fresher finance",
    "chuyen vien phan tich",
    "data",
    "phan tich du lieu",
    "phan tich rui ro",
]

class CareerVietScraper:
    def __init__(self):
        self.base_url = "https://careerviet.vn"
        self.seen_ids = set()

    def strip_html(self, text):
        if not text:
            return ""
        clean = re.compile('<.*?>')
        text_without_tags = re.sub(clean, '', str(text))
        return text_without_tags.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').strip()

    async def fetch_job_detail(self, crawler, job_url):
        """Fetch and parse a single CareerViet job detail page."""
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
                'salary': '',
                'deadline': '',
                'location': '',
                'level': '',
            }

            # ---- Salary from detail (in li elements with strong label) ----
            for li in soup.find_all('li'):
                strong = li.find('strong')
                if not strong:
                    continue
                label = strong.get_text(strip=True).lower()
                p = li.find('p')
                value = p.get_text(strip=True) if p else ''
                if not value:
                    value = li.get_text(strip=True).replace(strong.get_text(strip=True), '').strip()
                
                if 'lương' in label or 'salary' in label:
                    detail['salary'] = value
                elif 'địa điểm' in label or 'location' in label or 'nơi làm' in label:
                    detail['location'] = value
                elif 'hạn nộp' in label or 'deadline' in label:
                    detail['deadline'] = value
                elif 'kinh nghiệm' in label or 'experience' in label:
                    detail['level'] = value
                elif 'cấp bậc' in label or 'level' in label:
                    if not detail['level']:
                        detail['level'] = value

            # ---- Content sections via h2/h3 headings ----
            for heading in soup.find_all(['h2', 'h3'], class_=re.compile(r'detail-title|title')):
                heading_text = heading.get_text(strip=True).lower()
                next_el = heading.find_next_sibling(['div', 'ul', 'p', 'section'])
                if not next_el and heading.parent:
                    next_el = heading.parent.find_next_sibling(['div', 'ul', 'section'])
                
                content = next_el.get_text(separator='\n', strip=True) if next_el else ''
                if not content:
                    continue
                    
                if 'mô tả' in heading_text or 'description' in heading_text:
                    detail['description'] = content
                elif 'yêu cầu' in heading_text or 'requirement' in heading_text:
                    detail['requirements'] = content
                elif 'phúc lợi' in heading_text or 'quyền lợi' in heading_text or 'benefit' in heading_text:
                    detail['benefits'] = content

            # Fallback
            if not detail['description']:
                main = soup.find('div', class_=re.compile(r'full-content|job-description|detail-content'))
                if main:
                    detail['description'] = main.get_text(separator='\n', strip=True)

            return detail
        except Exception as e:
            logger.error(f"Error parsing detail for {job_url}: {e}")
            return None

    def parse_job_list(self, html):
        """Parse CareerViet search results using confirmed selectors: a.job_link, a.company-name"""
        jobs = []
        if not html:
            return jobs

        soup = BeautifulSoup(html, 'html.parser')
        
        # PRIMARY: a.job_link (confirmed from live inspection)
        job_links = soup.find_all('a', class_='job_link')
        
        if not job_links:
            # Fallback: any link to /vi/tim-viec-lam/
            job_links = soup.find_all('a', href=re.compile(r'/vi/tim-viec-lam/.*\.html'))

        # Deduplicate links (CareerViet has duplicate links per job)
        seen_hrefs = set()
        unique_links = []
        for link in job_links:
            href = link.get('href', '')
            if href and href not in seen_hrefs:
                seen_hrefs.add(href)
                unique_links.append(link)
        
        logger.info(f"    Found {len(unique_links)} unique job links on page")
        
        for link in unique_links:
            try:
                url = link.get('href', '')
                if url and not url.startswith('http'):
                    url = f"{self.base_url}{url}"
                
                # CareerViet links: /vi/tim-viec-lam/title.JOBID.html
                if '/tim-viec-lam/' not in url:
                    continue
                # Skip search/filter links
                if '-kw' in url or '-ks' in url:
                    continue

                # Extract job ID: /vi/tim-viec-lam/title-here.35C6928D.html
                job_id = "unknown"
                id_match = re.search(r'\.([A-Z0-9]{6,12})\.html', url)
                if id_match:
                    job_id = id_match.group(1)
                else:
                    # Fallback
                    id_match = re.search(r'/([^/]+)\.html$', url)
                    if id_match:
                        job_id = id_match.group(1)[-10:]

                if job_id in self.seen_ids:
                    continue
                self.seen_ids.add(job_id)

                title = link.get('title', '') or link.get_text(strip=True)
                if not title:
                    continue

                # Find parent container
                parent = link.find_parent('div', class_=re.compile(r'job-item|figure'))
                if not parent:
                    parent = link.find_parent('div')
                
                # Company: a.company-name
                company = "N/A"
                if parent:
                    co = parent.find('a', class_='company-name') or parent.find('a', class_=re.compile(r'company'))
                    if co:
                        company = co.get_text(strip=True)

                # Salary: text containing "Lương:"
                salary = "Thỏa thuận"
                if parent:
                    sal = parent.find(string=re.compile(r'Lương'))
                    if sal:
                        sal_el = sal.parent
                        salary = sal_el.get_text(strip=True).replace('Lương:', '').strip()
                        if salary.startswith('$'):
                            salary = salary[1:].strip()

                # Location
                location = ""
                if parent:
                    loc = parent.find(string=re.compile(r'Hà Nội|Hồ Chí Minh|Đà Nẵng|Bình Dương|Đồng Nai'))
                    if loc:
                        location = loc.strip() if isinstance(loc, str) else loc.parent.get_text(strip=True)

                # Deadline
                deadline = ""
                if parent:
                    dl = parent.find(string=re.compile(r'Hạn nộp'))
                    if dl:
                        deadline = dl.parent.get_text(strip=True).replace('Hạn nộp:', '').strip()

                parsed_job = {
                    'id': f"cv_{job_id}",
                    'platform': 'CareerViet',
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
                logger.error(f"Error parsing CareerViet list item: {e}")

        return jobs

    async def scrape_keyword(self, crawler, keyword, max_pages=10):
        """Scrape a single keyword search on CareerViet."""
        keyword_slug = keyword.replace(' ', '-').lower()
        
        keyword_jobs = []
        for page in range(1, max_pages + 1):
            # Confirmed URL pattern with -vi.html suffix
            if page == 1:
                url = f"{self.base_url}/viec-lam/{keyword_slug}-kw-vi.html"
            else:
                url = f"{self.base_url}/viec-lam/{keyword_slug}-kw-trang-{page}-vi.html"
            
            logger.info(f"  [{keyword}] Fetching page {page}: {url}")

            try:
                result = await crawler.arun(url=url)
                html = result.html
            except Exception as e:
                logger.error(f"  [{keyword}] Crawl error page {page}: {e}")
                break

            if not html:
                logger.warning(f"  [{keyword}] No HTML on page {page}.")
                break

            parsed = self.parse_job_list(html)
            if not parsed:
                logger.info(f"  [{keyword}] No more jobs on page {page}.")
                break

            logger.info(f"  [{keyword}] Page {page}: {len(parsed)} jobs. Fetching details...")

            for job in parsed:
                if job['url']:
                    detail = await self.fetch_job_detail(crawler, job['url'])
                    if detail:
                        job.update({
                            'description': detail.get('description', ''),
                            'requirements': detail.get('requirements', ''),
                            'benefits': detail.get('benefits', ''),
                        })
                        if detail.get('level'):
                            job['level'] = detail['level']
                        if detail.get('salary') and job['salary'] in ('Thỏa thuận', 'Cạnh tranh', ''):
                            job['salary'] = detail['salary']
                        if detail.get('location') and not job['location']:
                            job['location'] = detail['location']
                        if detail.get('deadline') and not job['deadline']:
                            job['deadline'] = detail['deadline']
                    await asyncio.sleep(1.5)

            keyword_jobs.extend(parsed)
            inserted, updated = save_jobs(parsed)
            logger.info(f"  [{keyword}] P{page}: {inserted} new, {updated} updated")

        return keyword_jobs

    async def scrape(self, max_pages_per_keyword=10):
        logger.info("Starting CareerViet multi-keyword scraper...")
        all_jobs = []
        setup_database()

        async with AsyncWebCrawler() as crawler:
            for keyword in SEARCH_KEYWORDS:
                logger.info(f"--- CareerViet searching: '{keyword}' ---")
                jobs = await self.scrape_keyword(crawler, keyword, max_pages=max_pages_per_keyword)
                all_jobs.extend(jobs)

        logger.info(f"CareerViet Scrape complete. Total unique jobs: {len(all_jobs)}")
        return all_jobs

async def main():
    scraper = CareerVietScraper()
    await scraper.scrape(max_pages_per_keyword=10)

if __name__ == "__main__":
    asyncio.run(main())
