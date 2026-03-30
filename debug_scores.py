"""Check LLM scores and rationale quality"""
import sys, sqlite3, json
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('jobs.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print('=== LLM SCORE DISTRIBUTION ===')
c.execute("SELECT COUNT(*) as cnt, CASE WHEN llm_score = 0 THEN '0' WHEN llm_score BETWEEN 1 AND 29 THEN '1-29' WHEN llm_score BETWEEN 30 AND 49 THEN '30-49' WHEN llm_score BETWEEN 50 AND 69 THEN '50-69' WHEN llm_score BETWEEN 70 AND 100 THEN '70-100' ELSE 'not-scored' END as bucket FROM jobs WHERE keyword_score >= 25 GROUP BY bucket ORDER BY bucket")
for r in c.fetchall():
    print(f"  LLM {r['bucket']:>10}: {r['cnt']}")

print('\n=== TOP 10 BY FINAL SCORE (40%KW + 60%LLM) ===')
c.execute("SELECT title, keyword_score, llm_score, final_score, llm_rationale FROM jobs WHERE final_score > 0 ORDER BY final_score DESC LIMIT 10")
for i, r in enumerate(c.fetchall(), 1):
    t = (r['title'][:50]+'...') if len(r['title'])>50 else r['title']
    rat = (r['llm_rationale'][:80]+'...') if r['llm_rationale'] and len(r['llm_rationale'])>80 else (r['llm_rationale'] or '')
    print(f"  {i:>2}. KW:{r['keyword_score']} LLM:{r['llm_score']} Final:{r['final_score']} | {t}")
    if rat:
        print(f"      AI: {rat}")

print('\n=== SAMPLE: HIGH KW BUT LLM=0 (why?) ===')
c.execute("SELECT title, company, keyword_score, llm_score, llm_rationale FROM jobs WHERE keyword_score >= 70 AND llm_score = 0 LIMIT 5")
for r in c.fetchall():
    t = (r['title'][:50]+'...') if len(r['title'])>50 else r['title']
    rat = r['llm_rationale'] or 'NO RATIONALE'
    print(f"  KW:{r['keyword_score']} LLM:0 | {t}")
    print(f"    AI: {rat[:120]}")

conn.close()
