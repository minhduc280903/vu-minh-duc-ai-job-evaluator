import asyncio
import aiohttp
import json
import logging
import sqlite3
import math
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('vnw_scraper')

DB_FILE = 'jobs.db'

# Make sure db exists
from ybox_scraper import save_jobs, setup_database

# ============================================================
# VietnamWorks Job Function Category IDs
# ============================================================
# parentId 5  = IT / Software
# parentId 3  = Banking & Financial Services
# parentId 1  = Accounting / Finance
# parentId 35 = Insurance
# childrenIds [-1] = all sub-categories
IT_CATEGORY = [{"field": "jobFunction", "value": '[{"parentId":5,"childrenIds":[-1]}]'}]
FINANCE_BANKING = [{"field": "jobFunction", "value": '[{"parentId":3,"childrenIds":[-1]}]'}]
ACCOUNTING = [{"field": "jobFunction", "value": '[{"parentId":1,"childrenIds":[-1]}]'}]
INSURANCE = [{"field": "jobFunction", "value": '[{"parentId":35,"childrenIds":[-1]}]'}]

# Targeted search queries — each will be run independently
SEARCH_CONFIGS = [
    # Keyword-based searches (no category filter — cross-category)
    {"query": "data analyst",       "filters": [], "label": "data analyst (all)"},
    {"query": "risk analyst",       "filters": [], "label": "risk analyst (all)"},
    {"query": "financial analyst",  "filters": [], "label": "financial analyst (all)"},
    {"query": "credit analyst",     "filters": [], "label": "credit analyst (all)"},
    {"query": "business analyst",   "filters": [], "label": "business analyst (all)"},
    {"query": "phân tích dữ liệu",  "filters": [], "label": "phân tích dữ liệu (all)"},
    {"query": "phân tích tài chính", "filters": [], "label": "phân tích tài chính (all)"},
    {"query": "python",             "filters": [], "label": "python (all)"},
    {"query": "sql",                "filters": [], "label": "sql (all)"},
    {"query": "power bi",           "filters": [], "label": "power bi (all)"},
    {"query": "fresher finance",    "filters": [], "label": "fresher finance (all)"},
    {"query": "fresher data",       "filters": [], "label": "fresher data (all)"},
    # Category-based searches (broad sweep)
    {"query": "",                   "filters": IT_CATEGORY,       "label": "IT category"},
    {"query": "",                   "filters": FINANCE_BANKING,   "label": "Finance/Banking category"},
    {"query": "",                   "filters": ACCOUNTING,        "label": "Accounting category"},
    {"query": "",                   "filters": INSURANCE,         "label": "Insurance category"},
]

class VietnamWorksScraper:
    def __init__(self):
        self.base_url = "https://www.vietnamworks.com"
        self.url = "https://ms.vietnamworks.com/job-search/v1.0/search"
        self.seen_ids = set()  # Dedup across queries
        
    def _build_payload(self, page=0, hits_per_page=50, query="", filters=None):
        payload = {
          "userId": 0,
          "query": query,
          "filter": filters or [],
          "ranges": [],
          "order": [],
          "hitsPerPage": hits_per_page,
          "page": page,
          "retrieveFields": [
            "jobTitle", "companyName", "jobDescription", "jobRequirement", 
            "jobUrl", "salaryMax", "salaryMin", "skills", "benefits", 
            "workingLocations", "approvedOn", "expiredOn", "jobId",
            "isSalaryVisible", "salaryUnit"
          ],
          "summaryVersion": ""
        }
        return payload

    async def fetch_page(self, session, page, hits_per_page=50, query="", filters=None):
        payload = self._build_payload(page, hits_per_page, query, filters)
        
        headers = {
            "x-source": "Page-Container",
            "Content-Type": "application/json",
            "Referer": "https://www.vietnamworks.com/",
            "Origin": "https://www.vietnamworks.com"
        }
        
        try:
            async with session.post(self.url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch VNW page {page}. Status: {response.status}")
                    text = await response.text()
                    logger.debug(f"Response: {text}")
                    return None
        except Exception as e:
            logger.error(f"Exception fetching VNW page {page}: {e}")
            return None

    def strip_html(self, text):
        """Clean HTML tags for DB consistency natively inside the scraper."""
        if not text:
            return ""
        import re
        clean = re.compile('<.*?>')
        text_without_tags = re.sub(clean, '', str(text))
        return text_without_tags.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').strip()

    def parse_jobs(self, api_data):
        jobs = []
        if not api_data or 'data' not in api_data:
            return jobs
            
        hits = api_data.get('data', [])
        
        # Sometimes hits are wrapped in another layer, double check types
        if isinstance(hits, dict) and 'items' in hits:
             hits = hits.get('items', [])
        elif not isinstance(hits, list):
             logger.error("Data node is not a list. Check API mapping.")
             return jobs
        
        for item in hits:
            try:
                job_id = item.get('jobId')
                if not job_id:
                    continue
                
                # Dedup across queries
                if job_id in self.seen_ids:
                    continue
                self.seen_ids.add(job_id)
                    
                title = item.get('jobTitle', 'No Title')
                company_name = item.get('companyName', 'N/A')
                url = item.get('jobUrl', '')
                if url and not url.startswith('http'):
                    url = f"{self.base_url}{url}"
                elif not url:
                    url = f"{self.base_url}/viec-lam/{job_id}-jv"
                
                # Salary — extract even when isSalaryVisible=false
                salary = "Thỏa thuận"
                salary_min = item.get('salaryMin', 0)
                salary_max = item.get('salaryMax', 0)
                salary_unit = item.get('salaryUnit', '')
                is_visible = item.get('isSalaryVisible', False)
                
                if salary_min and salary_max and salary_min > 0:
                    unit_str = f" {salary_unit}" if salary_unit else ""
                    salary = f"{salary_min:,} - {salary_max:,}{unit_str}"
                elif salary_max and salary_max > 0:
                    unit_str = f" {salary_unit}" if salary_unit else ""
                    salary = f"Up to {salary_max:,}{unit_str}"
                elif not is_visible:
                    salary = "Thỏa thuận"
                
                # Location
                locations = item.get('workingLocations', [])
                location_str = ", ".join([loc.get('address', loc.get('cityName', '')) for loc in locations]) if isinstance(locations, list) else str(locations)
                
                # Skills
                skills = item.get('skills', [])
                skills_str = ", ".join([skill.get('skillName', str(skill)) for skill in skills]) if isinstance(skills, list) else str(skills)
                
                # Extract detailed fields 
                description = self.strip_html(item.get('jobDescription', ''))
                requirements = self.strip_html(item.get('jobRequirement', ''))
                benefits_arr = item.get('benefits', [])
                benefits_str = ", ".join([b.get('benefitName', str(b)) for b in benefits_arr]) if isinstance(benefits_arr, list) else str(benefits_arr)
                
                parsed_job = {
                    'id': f"vnw_{job_id}",
                    'platform': 'VietnamWorks',
                    'title': title,
                    'company': company_name,
                    'url': url,
                    'summary': skills_str,
                    'deadline': str(item.get('expiredOn', '')),
                    'views': 0,
                    'published_at': str(item.get('approvedOn', '')),
                    'salary': salary,
                    'location': location_str,
                    'skills': skills_str,
                    'description': description,
                    'requirements': requirements,
                    'benefits': benefits_str,
                    'raw': item
                }
                jobs.append(parsed_job)
            except Exception as e:
                logger.error(f"Error parsing VNW item {item.get('jobId')}: {e}")
                
        return jobs

    async def _get_total_pages(self, session, hits_per_page=50, query="", filters=None):
        """Returns (total_hits, total_pages, first_page_data)."""
        data = await self.fetch_page(session, page=0, hits_per_page=hits_per_page, query=query, filters=filters)
        if data:
            if 'meta' in data:
                total_hits = data['meta'].get('nbHits', 0)
                return total_hits, math.ceil(total_hits / hits_per_page), data
            else:
                logger.error("Missing 'meta' in response payload")
        else:
            logger.error("No data received from API")
        return 0, 0, None

    async def scrape_query(self, session, query="", filters=None, label="", max_pages=50):
        """Scrape a single query/filter combination."""
        hits_per_page = 50
        
        total_hits, total_pages, first_page_data = await self._get_total_pages(session, hits_per_page, query, filters)
        if total_pages == 0:
            logger.info(f"  [{label}] No jobs found.")
            return []
        
        # Cap pages to avoid endless scraping
        pages_to_scrape = min(total_pages, max_pages)
        logger.info(f"  [{label}] {total_hits} jobs, {pages_to_scrape} pages to scrape")
        
        query_jobs = []
        for page in range(0, pages_to_scrape):
            # Reuse first page data from _get_total_pages
            if page == 0 and first_page_data:
                data = first_page_data
            else:
                data = await self.fetch_page(session, page, hits_per_page=hits_per_page, query=query, filters=filters)
            
            if not data:
                break
                
            parsed = self.parse_jobs(data)
            
            if not parsed and page > 0:
                break
                
            query_jobs.extend(parsed)
            
            # Save batch
            if parsed:
                inserted, updated = save_jobs(parsed)
                logger.info(f"  [{label}] P{page+1}: {len(parsed)} parsed, {inserted} new, {updated} updated")
            
            await asyncio.sleep(0.3)  # Be polite
        
        return query_jobs

    async def scrape(self):
        """Run all targeted search queries."""
        logger.info("Starting VietnamWorks multi-query scraper...")
        all_jobs = []
        
        setup_database()
        
        async with aiohttp.ClientSession() as session:
            for config in SEARCH_CONFIGS:
                logger.info(f"--- Searching: {config['label']} ---")
                jobs = await self.scrape_query(
                    session,
                    query=config['query'],
                    filters=config['filters'],
                    label=config['label'],
                    max_pages=30  # Cap per-query
                )
                all_jobs.extend(jobs)
                await asyncio.sleep(0.5)
                
        logger.info(f"VNW Scrape complete. Total unique jobs: {len(all_jobs)} (deduped from {len(self.seen_ids)} seen)")
        return all_jobs

async def main():
    scraper = VietnamWorksScraper()
    await scraper.scrape()

if __name__ == "__main__":
    asyncio.run(main())
