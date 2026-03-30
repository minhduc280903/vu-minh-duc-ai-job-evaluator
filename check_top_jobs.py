import sqlite3
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

def show_top_jobs():
    conn = sqlite3.connect('jobs.db')
    df = pd.read_sql_query('''
        SELECT id, platform, title, company, salary, location, keyword_score, llm_score, final_score, url 
        FROM jobs 
        WHERE final_score > 0 OR keyword_score >= 25
        ORDER BY final_score DESC, keyword_score DESC 
        LIMIT 15
    ''', conn)
    
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(df)
    
    # Check how many need LLM 
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM jobs WHERE keyword_score >= 25 AND llm_score = -1")
    pending = c.fetchone()[0]
    print(f"\nJobs pending LLM evaluation: {pending}")
    
    conn.close()

if __name__ == '__main__':
    show_top_jobs()
