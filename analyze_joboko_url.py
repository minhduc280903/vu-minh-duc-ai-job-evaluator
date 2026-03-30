import asyncio
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
import re
import pandas as pd
from urllib.parse import quote_plus
import sys
import codecs

sys.stdout.reconfigure(encoding='utf-8')

def strip_html(text):
    if not text:
        return ""
    clean = re.compile('<.*?>')
    text_without_tags = re.sub(clean, '', str(text))
    return text_without_tags.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&amp;', '&').strip()

async def fetch_job_detail(crawler, job_url):
    try:
        result = await crawler.arun(url=job_url)
        html = result.html
        if not html: return None
        soup = BeautifulSoup(html, 'html.parser')
        detail = {'salary': '', 'level': '', 'description': '', 'requirements': ''}
        
        for item in soup.find_all('div', class_='item'):
            content_div = item.find('div', class_=re.compile(r'item-content'))
            if not content_div: continue
            text = content_div.get_text(strip=True)
            bold = content_div.find('span', class_='fw-bold')
            value = bold.get_text(strip=True) if bold else ''
            
            if 'thu nhập' in text.lower() or 'lương' in text.lower():
                detail['salary'] = value or text.split(':')[-1].strip()
            elif 'kinh nghiệm' in text.lower():
                detail['level'] = value or text.split(':')[-1].strip()
                
        for heading in soup.find_all('h3'):
            heading_text = heading.get_text(strip=True).lower()
            next_el = heading.find_next_sibling(['div', 'ul', 'ol', 'p', 'section'])
            if not next_el and heading.parent:
                next_el = heading.parent.find_next_sibling(['div', 'ul', 'ol', 'section'])
            if not next_el: continue
            
            content = next_el.get_text(separator='\n', strip=True)
            if 'mô tả' in heading_text or 'description' in heading_text:
                detail['description'] = content
            elif 'yêu cầu' in heading_text or 'requirement' in heading_text:
                detail['requirements'] = content
                
        return detail
    except Exception as e:
        return None

async def analyze_all():
    base_url = "https://vn.joboko.com"
    search_url_template = "https://vn.joboko.com/jobs?q=data+analyst&l=2&p={}"
    
    print("Bắt đầu quét toàn bộ các trang trên Joboko Hà Nội...")
    all_jobs = []
    seen_urls = set()
    
    async with AsyncWebCrawler(headless=True) as crawler:
        for page in range(1, 40): # Lấy tối đa 40 trang (Hà Nội có khoảng hơn 340 jobs)
            url = search_url_template.format(page)
            print(f"Đang quét trang {page}...")
            result = await crawler.arun(url=url)
            html = result.html
            if not html: break
            
            soup = BeautifulSoup(html, 'html.parser')
            job_links = soup.find_all('a', href=re.compile(r'/viec-lam-.*-xvi\d+'))
            
            page_jobs = []
            for link in job_links:
                href = link.get('href', '')
                if not href or href in seen_urls: continue
                text = link.get_text(strip=True)
                if not text or len(text) < 5: continue
                if '/cong-ty-' in href or 'tìm-việc' in href: continue
                seen_urls.add(href)
                full_url = href if href.startswith('http') else f"{base_url}{href}"
                
                parent = link.find_parent(['div', 'article'])
                company = ""
                if parent:
                    comp_link = parent.find('a', href=re.compile(r'/cong-ty-'))
                    if comp_link: company = comp_link.get_text(strip=True)
                
                page_jobs.append({'title': text, 'url': full_url, 'company': company})
                
            if not page_jobs:
                break
                
            all_jobs.extend(page_jobs)
            
        print(f"Đã tìm thấy tổng cộng {len(all_jobs)} công việc. Bắt đầu phân tích JD từng job...\n")
        print("-" * 50)
        
        suitable_jobs = []
        
        # Analyze each job detail
        for i, job in enumerate(all_jobs):
            detail = await fetch_job_detail(crawler, job['url'])
            if detail:
                level = detail.get('level', '').lower()
                title = job['title'].lower()
                
                # Logic phân loại Fresher/Junior
                is_fresher = False
                if 'thực tập' in title or 'intern' in title or 'fresher' in title or 'trainee' in title:
                    is_fresher = True
                elif 'không yêu cầu kinh nghiệm' in level or 'dưới 1 năm' in level or '1 năm' in level or level == '':
                    is_fresher = True
                # Loại trừ senior, lead, manager, hoặc yêu cầu 2+ năm kinh nghiệm
                if 'senior' in title or 'lead' in title or 'manager' in title or 'trưởng' in title:
                    is_fresher = False
                if '2 năm' in level or '3 năm' in level or '4 năm' in level or '5 năm' in level:
                    is_fresher = False
                    
                if is_fresher:
                    job['level'] = detail.get('level', 'Không đề cập')
                    job['salary'] = detail.get('salary', 'Thỏa thuận')
                    job['requirements'] = detail.get('requirements', '')[:200] + "..."
                    suitable_jobs.append(job)
                    
            await asyncio.sleep(0.5)
            
        df = pd.DataFrame(suitable_jobs)
        if not df.empty:
            df.to_excel('joboko_fresher_jobs_hn.xlsx', index=False)
            print(f"\n✅ Đã phân tích xong {len(all_jobs)} jobs.")
            print(f"✅ Đã lưu {len(suitable_jobs)} jobs phù hợp vào file joboko_fresher_jobs_hn.xlsx")
        else:
            print("\n❌ không tìm thấy job hợp lệ.")

if __name__ == "__main__":
    asyncio.run(analyze_all())
