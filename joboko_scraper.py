import asyncio
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
import logging
import sqlite3
import re
from datetime import datetime
from urllib.parse import quote_plus
from ybox_scraper import save_jobs, setup_database

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('joboko_scraper')

# ============================================================
# Joboko search structure (confirmed from browser inspection):
#   Search URL: /jobs?q={keyword}&page={page}
#   Job detail: /viec-lam-{slug}-xvi{id}
#   Job ID: extracted from URL pattern xvi{digits}
#
#   Listing selectors (from browser DOM):
#     Job cards: div.nw-job-item or article elements
#     Title: a.fz-16.fw-bold or h2/h3 with link
#     Company: company name near title
#     Salary/Location: in card metadata
#
#   Detail page:
#     Title: .block-title span.fz-18.fw-bold
#     Salary: text near $ icon or "Thu nhập"
#     Experience: text near "Kinh nghiệm" label
#     Description: div.job-desc or heading "Mô tả công việc"
#     Requirements: div.job-requirement or heading "Yêu cầu"
#     Benefits: div.job-benefit or heading "Quyền lợi"
#     Deadline: span.item-date
# ============================================================

SEARCH_KEYWORDS = [
    "data analyst",
    "risk analyst",
    "financial analyst",
    "credit analyst",
    "business analyst",
    "phân tích dữ liệu",
    "phân tích tài chính",
    "phân tích rủi ro",
    "power bi",
    "kiểm toán",
    "chuyên viên phân tích",
    "data engineer",
    "fresher tài chính",
]


class JobokoScraper:
    def __init__(self):
        self.base_url = "https://vn.joboko.com"
        self.seen_ids = set()

    def strip_html(self, text):
        if not text:
            return ""
        clean = re.compile('<.*?>')
        text_without_tags = re.sub(clean, '', str(text))
        return text_without_tags.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&amp;', '&').strip()

    def parse_job_list(self, html):
        """Parse Joboko search results."""
        jobs = []
        if not html:
            return jobs

        soup = BeautifulSoup(html, 'html.parser')

        # Find all job links that match the /viec-lam-*-xvi pattern
        job_links = soup.find_all('a', href=re.compile(r'/viec-lam-.*-xvi\d+'))

        # Deduplicate and extract unique job URLs
        seen_urls = set()
        unique_jobs = []
        for link in job_links:
            href = link.get('href', '')
            if not href or href in seen_urls:
                continue
            # Only count actual job title links (not "Xem tất cả" etc.)
            text = link.get_text(strip=True)
            if not text or len(text) < 5:
                continue
            # Skip company links and category links
            if '/cong-ty-' in href or 'tìm-việc' in href:
                continue
            seen_urls.add(href)
            unique_jobs.append((href, text))

        for href, title in unique_jobs:
            try:
                # Extract job ID from URL: -xvi{digits}
                id_match = re.search(r'-xvi(\d+)', href)
                if not id_match:
                    continue

                job_id = f"joboko_{id_match.group(1)}"

                if job_id in self.seen_ids:
                    continue
                self.seen_ids.add(job_id)

                # Build full URL
                job_url = href if href.startswith('http') else f"{self.base_url}{href}"

                # Try to find company, salary, location from nearby elements
                company = ""
                salary = ""
                location = ""

                # Look for the parent container of this link
                parent = link.find_parent(['div', 'article', 'li', 'section'])
                if parent:
                    # Company: often in a link to /cong-ty-* nearby
                    comp_link = parent.find('a', href=re.compile(r'/cong-ty-'))
                    if comp_link:
                        company = comp_link.get_text(strip=True)

                    # Salary: look for VND, triệu, etc.
                    text_content = parent.get_text(' ', strip=True)
                    sal_match = re.search(
                        r'(\d[\d,.]+\s*(?:triệu|VND|tr)[\s\S]*?(?:triệu|VND|tr)?)',
                        text_content, re.IGNORECASE
                    )
                    if sal_match:
                        salary = sal_match.group(1).strip()
                    elif 'thỏa thuận' in text_content.lower() or 'thoả thuận' in text_content.lower():
                        salary = 'Thỏa thuận'

                    # Location: look for common city names
                    loc_match = re.search(
                        r'(Hà Nội|Hồ Chí Minh|HCM|Đà Nẵng|Hải Phòng|Cần Thơ|Bắc Ninh|Bình Dương)',
                        text_content
                    )
                    if loc_match:
                        location = loc_match.group(1)

                parsed_job = {
                    'id': job_id,
                    'platform': 'Joboko',
                    'title': title,
                    'company': company,
                    'url': job_url,
                    'summary': '',
                    'deadline': '',
                    'views': 0,
                    'published_at': datetime.now().isoformat(),
                    'salary': salary,
                    'location': location,
                    'skills': '',
                    'level': '',
                    'raw': {}
                }
                jobs.append(parsed_job)
            except Exception as e:
                logger.error(f"Error parsing Joboko list item: {e}")

        return jobs

    async def fetch_job_detail(self, crawler, job_url):
        """Fetch and parse a single Joboko job detail page."""
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
                'skills': '',
                'company': '',
            }

            # ---- Company name ----
            comp_el = soup.find('a', class_=re.compile(r'nw-company-hero__text'))
            if comp_el:
                detail['company'] = comp_el.get_text(strip=True)

            # ---- Structured metadata from div.block-entry > div.item > div.item-content ----
            for item in soup.find_all('div', class_='item'):
                content_div = item.find('div', class_=re.compile(r'item-content'))
                if not content_div:
                    continue

                text = content_div.get_text(strip=True)
                bold = content_div.find('span', class_='fw-bold')
                value = bold.get_text(strip=True) if bold else ''

                if 'thu nhập' in text.lower() or 'lương' in text.lower():
                    detail['salary'] = value or text.split(':')[-1].strip()
                elif 'kinh nghiệm' in text.lower():
                    detail['level'] = value or text.split(':')[-1].strip()
                elif 'hạn nộp' in text.lower():
                    detail['deadline'] = value or text.split(':')[-1].strip()
                elif 'địa điểm' in text.lower() or 'nơi làm' in text.lower():
                    detail['location'] = value or text.split(':')[-1].strip()

            # ---- Also try span.item-date for deadline ----
            if not detail['deadline']:
                date_el = soup.find('span', class_=re.compile(r'item-date'))
                if date_el:
                    detail['deadline'] = date_el.get('data-value', '') or date_el.get_text(strip=True)

            # ---- Location from address block ----
            if not detail['location']:
                addr = soup.find('div', class_=re.compile(r'block-address'))
                if addr:
                    detail['location'] = addr.get_text(strip=True)

            # ---- Skills tags ----
            skill_tags = soup.find_all(['span', 'a'], class_=re.compile(r'tag|skill|keyword'))
            if skill_tags:
                skills = [t.get_text(strip=True) for t in skill_tags
                         if t.get_text(strip=True) and len(t.get_text(strip=True)) < 30]
                detail['skills'] = ', '.join(skills[:15])

            # ---- Content sections via h3 headings ----
            for heading in soup.find_all('h3'):
                heading_text = heading.get_text(strip=True).lower()
                next_el = heading.find_next_sibling(['div', 'ul', 'ol', 'p', 'section'])
                if not next_el:
                    if heading.parent:
                        next_el = heading.parent.find_next_sibling(['div', 'ul', 'ol', 'section'])
                if not next_el:
                    continue

                content = next_el.get_text(separator='\n', strip=True)
                if not content or len(content) < 10:
                    continue

                if 'mô tả' in heading_text or 'description' in heading_text:
                    detail['description'] = content
                elif 'yêu cầu' in heading_text or 'requirement' in heading_text:
                    detail['requirements'] = content
                elif 'quyền lợi' in heading_text or 'phúc lợi' in heading_text or 'benefit' in heading_text:
                    detail['benefits'] = content

            # ---- Fallback: class-based extraction ----
            if not detail['description']:
                desc_el = soup.find('div', class_=re.compile(r'job-desc'))
                if desc_el:
                    detail['description'] = desc_el.get_text(separator='\n', strip=True)

            if not detail['requirements']:
                req_el = soup.find('div', class_=re.compile(r'job-require'))
                if req_el:
                    detail['requirements'] = req_el.get_text(separator='\n', strip=True)

            if not detail['benefits']:
                ben_el = soup.find('div', class_=re.compile(r'job-benefit'))
                if ben_el:
                    detail['benefits'] = ben_el.get_text(separator='\n', strip=True)

            return detail
        except Exception as e:
            logger.error(f"Error parsing Joboko detail for {job_url}: {e}")
            return None

    async def scrape_keyword(self, crawler, keyword, max_pages=10):
        """Scrape a single keyword search on Joboko."""
        keyword_encoded = quote_plus(keyword)

        keyword_jobs = []
        for page in range(1, max_pages + 1):
            url = f"{self.base_url}/jobs?q={keyword_encoded}&p={page}"

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
                            'skills': detail.get('skills', ''),
                        })
                        if detail.get('company') and not job['company']:
                            job['company'] = detail['company']
                        if detail.get('level'):
                            job['level'] = detail['level']
                        if detail.get('salary'):
                            job['salary'] = detail['salary']
                        if detail.get('location') and not job['location']:
                            job['location'] = detail['location']
                        if detail.get('deadline') and not job['deadline']:
                            job['deadline'] = detail['deadline']
                    await asyncio.sleep(1)  # Be polite

            keyword_jobs.extend(parsed)
            inserted, updated = save_jobs(parsed)
            logger.info(f"  [{keyword}] P{page}: {inserted} new, {updated} updated")

        return keyword_jobs

    async def scrape(self, max_pages_per_keyword=10):
        """Main scrape: search all keywords."""
        setup_database()
        all_jobs = []

        logger.info(f"Starting Joboko scraper with {len(SEARCH_KEYWORDS)} keywords")

        async with AsyncWebCrawler(headless=True) as crawler:
            for kw in SEARCH_KEYWORDS:
                logger.info(f"\n{'='*50}")
                logger.info(f"Searching: '{kw}'")
                logger.info(f"{'='*50}")
                jobs = await self.scrape_keyword(crawler, kw, max_pages_per_keyword)
                all_jobs.extend(jobs)
                logger.info(f"  [{kw}] Total: {len(jobs)} jobs")
                await asyncio.sleep(2)

        logger.info(f"\n{'='*50}")
        logger.info(f"Joboko scraping complete!")
        logger.info(f"Total unique jobs: {len(all_jobs)}")
        return all_jobs


async def main():
    scraper = JobokoScraper()
    jobs = await scraper.scrape(max_pages_per_keyword=5)
    logger.info(f"Done! Scraped {len(jobs)} jobs from Joboko")


if __name__ == "__main__":
    asyncio.run(main())
