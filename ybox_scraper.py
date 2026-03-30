import asyncio
import aiohttp
import sqlite3
import json
import logging
import re
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ybox_scraper')

# Database connection
DB_FILE = 'jobs.db'

def strip_html(text):
    """Remove HTML tags from a string."""
    if not text:
        return ""
    # Remove HTML tags
    clean = re.compile('<.*?>')
    text_without_tags = re.sub(clean, '', text)
    # Basic unescaping of common HTML entities
    text_without_tags = text_without_tags.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    return text_without_tags.strip()

def setup_database():
    """Create the SQLite database and necessary tables if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create jobs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        platform TEXT NOT NULL,
        title TEXT NOT NULL,
        company TEXT,
        url TEXT,
        summary TEXT,
        deadline TEXT,
        views INTEGER,
        published_at TEXT,
        salary TEXT,
        domain TEXT,
        level TEXT,
        location TEXT,
        skills TEXT,
        requirements TEXT,
        benefits TEXT,
        description TEXT,
        raw_data TEXT,
        relevance_score INTEGER DEFAULT -1,
        evaluation_reason TEXT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(id, platform)
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database setup complete.")

def save_jobs(jobs_data):
    """Save scraped jobs to the SQLite database."""
    if not jobs_data:
        return 0, 0
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    inserted = 0
    updated = 0
    
    for job in jobs_data:
        try:
            # Check if job exists
            cursor.execute('SELECT id, salary, description, requirements, benefits FROM jobs WHERE id = ? AND platform = ?', (job['id'], job['platform']))
            exists = cursor.fetchone()
            
            if exists:
                # Smart update: don't overwrite non-empty fields with empty ones
                existing_salary = exists[1] or ''
                existing_desc = exists[2] or ''
                existing_req = exists[3] or ''
                existing_ben = exists[4] or ''
                
                new_salary = job.get('salary', '') or existing_salary
                new_desc = job.get('description', '') or existing_desc
                new_req = job.get('requirements', '') or existing_req
                new_ben = job.get('benefits', '') or existing_ben
                
                # Also check existing level
                cursor.execute('SELECT level FROM jobs WHERE id = ? AND platform = ?', (job['id'], job['platform']))
                existing_level_row = cursor.fetchone()
                existing_level = (existing_level_row[0] if existing_level_row else '') or ''
                new_level = job.get('level', '') or existing_level
                
                cursor.execute('''
                UPDATE jobs SET 
                    views = ?, 
                    deadline = ?,
                    salary = ?,
                    description = ?,
                    requirements = ?,
                    benefits = ?,
                    location = ?,
                    skills = ?,
                    level = ?,
                    raw_data = ?
                WHERE id = ? AND platform = ?
                ''', (
                    job.get('views', 0),
                    job.get('deadline', '') or '',
                    new_salary,
                    new_desc,
                    new_req,
                    new_ben,
                    job.get('location', '') or '',
                    job.get('skills', '') or '',
                    new_level,
                    json.dumps(job.get('raw', {})),
                    job['id'], 
                    job['platform']
                ))
                updated += 1
            else:
                # Insert new job
                cursor.execute('''
                INSERT INTO jobs (
                    id, platform, title, company, url, summary, 
                    deadline, views, published_at, salary, description, requirements, benefits, location, skills, level, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job['id'],
                    job['platform'],
                    job['title'],
                    job['company'],
                    job['url'],
                    job.get('summary', ''),
                    job.get('deadline', ''),
                    job.get('views', 0),
                    job.get('published_at', ''),
                    job.get('salary', ''),
                    job.get('description', ''),
                    job.get('requirements', ''),
                    job.get('benefits', ''),
                    job.get('location', ''),
                    job.get('skills', ''),
                    job.get('level', ''),
                    json.dumps(job.get('raw', {}))
                ))
                inserted += 1
        except Exception as e:
            logger.error(f"Error saving job {job.get('id')}: {e}")
            
    conn.commit()
    conn.close()
    
    return inserted, updated

class YboxScraper:
    def __init__(self):
        self.endpoint = "https://api.ybox.vn/graphql"
        # We use communityId for 'Tuyển dụng'
        self.community_id = "5a4542f355ae5009afa5a3ec" 
        self.base_url = "https://ybox.vn/tuyen-dung-viec-lam"
        
    def _build_query(self, page=1, limit=10, location_label="Hà Nội"):
        # Map location to the specific additionFields format seen in the user's payload
        # For Hanoi:
        # [{"_id":"5a5b97755abab6091b72d107","label":"Hà Nội","labelTmp":null,"key":2,"fieldId":"5a5b97755abab6091b72d102","parentKey":"e"}]
        # For Ho Chi Minh it would be different, but we can default to empty or a specific one if needed.
        # Let's use the exact string provided by the user for Hanoi for now, or an empty array if not filtering.
        
        addition_fields_str = '[]'
        if location_label == "Hà Nội":
            addition_fields_str = '"{{\\"_id\\":\\"5a5b97755abab6091b72d107\\",\\"label\\":\\"Hà N\\u1ed9i\\",\\"labelTmp\\":null,\\"key\\":2,\\"fieldId\\":\\"5a5b97755abab6091b72d102\\",\\"parentKey\\":\\"e\\"}}"'
            addition_fields_param = r'additionFields: "[{\"_id\":\"5a5b97755abab6091b72d107\",\"label\":\"Hà Nội\",\"labelTmp\":null,\"key\":2,\"fieldId\":\"5a5b97755abab6091b72d102\",\"parentKey\":\"e\"}]",'
        else:
            addition_fields_param = ""
            
        # The user's query block:
        query = f"""{{
        SearchPosts (limit: {limit}, page: {page}, {addition_fields_param} communityId: "{self.community_id}") {{
          count
          edges {{
            _id sortId lang title photo link urlIReview isQc
            statistics {{ totalLikes totalDislikes reactionPoints totalComments totalViews postCalculatedScores totalUserViews }}
            publishedAt anonymousMode anonymousPhoto anonymousName active slug postType anonymousBio deadlineNumber updatedAt acceptedAt deadline summary deleted forceDeleted newest highlights selective totalBookmark content introCompany nameCompany emailCompany emailCompanyRepeat bookmarked
            reactions {{
              likes {{ liked totalLikes }}
              dislikes {{ disliked totalDislikes }}
              FBShares {{ shared totalShares }}
            }}
            community {{ _id name url enableDeadline }}
            publisher {{ _id username fullName avatar bio intro coverImage }}
            totalComment
          }}
        }}
        }}"""
        return query

    def _build_detail_query(self, post_id):
        query = f"""{{
        Post(postId: "{post_id}") {{
          _id
          title
          jobs {{
            title
            chinhsach
            yeucau
            mota
          }}
        }}
        }}"""
        return query
        
    async def fetch_job_detail(self, session, post_id):
        import urllib.parse
        query = self._build_detail_query(post_id)
        url = f"{self.endpoint}?query={urllib.parse.quote(query)}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://ybox.vn/"
        }
        
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    return None
        except Exception as e:
            logger.error(f"Error fetching detail for {post_id}: {e}")
            return None

    async def fetch_page(self, session, page, limit=10):
        query = self._build_query(page=page, limit=limit)
        import urllib.parse
        
        # We need to ensure the query is URL encoded, but NOT the { } at the very beginning/end
        # The user's example: https://api.ybox.vn/graphql?query={%20SearchPosts...}
        # A safer approach for GraphQL is a POST request with JSON payload: {"query": query}
        # But if we must use GET matching the user exactly:
        
        url = f"{self.endpoint}?query={urllib.parse.quote(query)}"

        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://ybox.vn/"
        }
        
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Failed to fetch page {page}. Status: {response.status}")
                    text = await response.text()
                    logger.debug(f"Response: {text}")
                    return None
        except Exception as e:
            logger.error(f"Exception fetching page {page}: {e}")
            return None

    def parse_jobs(self, graphql_data):
        jobs = []
        if not graphql_data or 'data' not in graphql_data or 'SearchPosts' not in graphql_data['data']:
            return jobs
            
        edges = graphql_data['data']['SearchPosts'].get('edges', [])
        
        for item in edges:
            try:
                job_id = item.get('_id')
                if not job_id:
                    continue
                    
                title = item.get('title', 'No Title')
                
                # Skip expired jobs
                deadline_number = item.get('deadlineNumber')
                current_timestamp_ms = datetime.now().timestamp() * 1000
                
                if deadline_number and deadline_number < current_timestamp_ms:
                    continue
                    
                # Skip Non-IT jobs
                title_lower = title.lower()
                relevant_keywords = [
                    # IT
                    'it', 'developer', 'engineer', 'frontend', 'backend', 'fullstack',
                    'data', 'ai', 'tester', 'qa', 'qc', 'devops', 'software',
                    'phần mềm', 'lập trình', 'ui/ux', 'system', 'c++', 'java',
                    'react', 'node', 'python',
                    # Finance/Banking/Analytics
                    'analyst', 'finance', 'banking', 'risk', 'credit',
                    'tài chính', 'ngân hàng', 'phân tích', 'rủi ro', 'kiểm toán',
                    'audit', 'accounting', 'kế toán', 'bi ', 'business intelligence',
                    'actuarial', 'compliance', 'aml', 'fraud', 'treasury',
                    'investment', 'đầu tư', 'chứng khoán', 'securities',
                    'power bi', 'sql', 'excel'
                ]
                if not any(kw in title_lower for kw in relevant_keywords):
                    continue
                    
                # Default values
                company_name = "N/A"
                if item.get('publisher') and isinstance(item['publisher'], dict):
                    company_name = item['publisher'].get('fullName', 'N/A')
                    
                # YBox job URL construction
                # /tuyen-dung/[id] is usually the pattern, or /tuyen-dung-[something]/[ID]
                url = f"{self.base_url}/{job_id}"
                
                # Statistics
                stats = item.get('statistics', {})
                views = stats.get('totalViews', 0)
                
                # Ybox doesn't have a structured salary field,
                # but sometimes salary info is in the summary or content text.
                salary_text = ''
                summary_text = item.get('summary', '') or ''
                content_text = item.get('content', '') or ''
                combined_text = (summary_text + ' ' + content_text).lower()
                # Try to extract salary patterns like "10-15 triệu", "lương: ..."
                salary_match = re.search(
                    r'(?:lương|salary|mức lương)[:\s]*(\S[^\n]{3,50})',
                    combined_text, re.IGNORECASE
                )
                if salary_match:
                    salary_text = salary_match.group(1).strip()
                
                parsed_job = {
                    'id': str(job_id),
                    'platform': 'Ybox',
                    'title': title,
                    'company': company_name,
                    'url': url,
                    'summary': summary_text,
                    'deadline': item.get('deadline', ''),
                    'views': views,
                    'published_at': item.get('publishedAt', ''),
                    'salary': salary_text,
                    'raw': item
                }
                jobs.append(parsed_job)
            except Exception as e:
                logger.error(f"Error parsing an item: {e}")
                
        return jobs

    async def scrape(self, num_pages=None, limit=20):
        logger.info("Starting Ybox scraper...")
        all_jobs = []
        
        # Setup DB
        setup_database()
        
        async with aiohttp.ClientSession() as session:
            # First fetch to get total count
            logger.info("Fetching Ybox page 1 to determine total count...")
            data = await self.fetch_page(session, 1, limit=limit)
            
            if not data or 'data' not in data or 'SearchPosts' not in data['data']:
                logger.error("Failed to get initial data from Ybox.")
                return []
                
            total_count = data['data']['SearchPosts'].get('count', 0)
            logger.info(f"Total jobs found on Ybox: {total_count}")
            
            import math
            calculated_pages = math.ceil(total_count / limit)
            
            target_pages = calculated_pages
            if num_pages is not None:
                target_pages = min(num_pages, calculated_pages)
                
            logger.info(f"Will scrape {target_pages} pages (limit={limit} per page).")
            
            # Helper to fetch details and save
            async def process_jobs(parsed_jobs):
                if not parsed_jobs:
                    return 0, 0
                # Fetch details for each job concurrently
                tasks = [self.fetch_job_detail(session, job['id']) for job in parsed_jobs]
                details = await asyncio.gather(*tasks)
                
                for i, detail in enumerate(details):
                    if detail and 'data' in detail and 'Post' in detail['data'] and detail['data']['Post']:
                        post_data = detail['data']['Post']
                        jobs_arr = post_data.get('jobs', [])
                        
                        # A post might have multiple sub-jobs, we join them or take the first
                        mota_list = []
                        yeucau_list = []
                        chinhsach_list = []
                        
                        for j in jobs_arr:
                            if j.get('mota'): mota_list.append(strip_html(j['mota']))
                            if j.get('yeucau'): yeucau_list.append(strip_html(j['yeucau']))
                            if j.get('chinhsach'): chinhsach_list.append(strip_html(j['chinhsach']))
                            
                        parsed_jobs[i]['description'] = "\n".join(mota_list)
                        parsed_jobs[i]['requirements'] = "\n".join(yeucau_list)
                        parsed_jobs[i]['benefits'] = "\n".join(chinhsach_list)
                        parsed_jobs[i]['raw']['post_detail'] = post_data
                
                inserted, updated = save_jobs(parsed_jobs)
                return inserted, updated

            # Process page 1 since we already fetched it
            parsed = self.parse_jobs(data)
            if parsed:
                all_jobs.extend(parsed)
                inserted, updated = await process_jobs(parsed)
                logger.info(f"Page 1 DB Update: Inserted {inserted}, Updated {updated}")
            
            # Loop remaining pages
            for page in range(2, target_pages + 1):
                logger.info(f"Fetching Ybox page {page}/{target_pages}...")
                data = await self.fetch_page(session, page, limit=limit)
                
                if not data:
                    logger.warning(f"No data returned for page {page}. Stopping.")
                    break
                    
                parsed = self.parse_jobs(data)
                logger.info(f"Page {page} parsed {len(parsed)} summary jobs.")
                
                if not parsed:
                    break
                    
                all_jobs.extend(parsed)
                
                # Fetch details and save batch
                inserted, updated = await process_jobs(parsed)
                logger.info(f"DB Update P{page}: Inserted {inserted}, Updated {updated}")
                
                # Polite delay
                await asyncio.sleep(1)
                
        logger.info(f"Ybox Scrape complete. Total jobs processed: {len(all_jobs)}")
        return all_jobs

async def main():
    scraper = YboxScraper()
    # Scrape all pages by default
    await scraper.scrape()

if __name__ == "__main__":
    asyncio.run(main())
