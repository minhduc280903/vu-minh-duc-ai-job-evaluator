"""Backfill: extract experience level from existing description/requirements text into level column"""
import sys, sqlite3, re
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('jobs.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Get all jobs where level is empty
c.execute("SELECT id, platform, title, description, requirements FROM jobs WHERE level IS NULL OR level = ''")
jobs = c.fetchall()
print(f"Jobs without level: {len(jobs)}")

# Patterns to extract experience requirements
exp_patterns = [
    # Vietnamese patterns
    (re.compile(r'(\d+)\s*[-–]\s*(\d+)\s*(?:năm|Năm|NĂM)', re.IGNORECASE), lambda m: f"{m.group(1)} - {m.group(2)} Năm"),
    (re.compile(r'(?:ít nhất|tối thiểu|trên|từ)\s*(\d+)\s*(?:năm|Năm)', re.IGNORECASE), lambda m: f"Trên {m.group(1)} Năm"),
    (re.compile(r'(\d+)\+?\s*(?:năm|Năm)\s*(?:kinh nghiệm|kinh nghiêm)', re.IGNORECASE), lambda m: f"{m.group(1)} Năm"),
    # English patterns  
    (re.compile(r'(\d+)\s*[-–]\s*(\d+)\s*(?:years?|yrs?)', re.IGNORECASE), lambda m: f"{m.group(1)} - {m.group(2)} Years"),
    (re.compile(r'(?:at least|minimum|over)\s*(\d+)\s*(?:years?|yrs?)', re.IGNORECASE), lambda m: f"{m.group(1)}+ Years"),
    (re.compile(r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)', re.IGNORECASE), lambda m: f"{m.group(1)}+ Years"),
]

updated = 0
for job in jobs:
    text = f"{job['description'] or ''} {job['requirements'] or ''}"
    level_val = ""
    
    for pattern, formatter in exp_patterns:
        match = pattern.search(text)
        if match:
            level_val = formatter(match)
            break
    
    # Also check title for seniority clues
    title = (job['title'] or '').lower()
    if not level_val:
        if 'fresher' in title or 'intern' in title or 'thực tập' in title:
            level_val = "Fresher/Intern"
        elif 'junior' in title:
            level_val = "Junior"
    
    if level_val:
        c.execute("UPDATE jobs SET level = ? WHERE id = ? AND platform = ?", 
                  (level_val, job['id'], job['platform']))
        updated += 1

conn.commit()

# Stats
c.execute("SELECT COUNT(*) FROM jobs WHERE level IS NOT NULL AND level != ''")
has_level = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM jobs")
total = c.fetchone()[0]
print(f"Backfilled: {updated}")
print(f"Total with level: {has_level}/{total} ({has_level*100//max(total,1)}%)")

# Show sample
print("\n=== SAMPLE LEVEL VALUES ===")
c.execute("SELECT title, level, platform FROM jobs WHERE level IS NOT NULL AND level != '' LIMIT 15")
for r in c.fetchall():
    t = (r['title'][:45]+'...') if len(r['title'])>45 else r['title']
    print(f"  [{r['platform'][:4]}] {r['level']:20} | {t}")

conn.close()
