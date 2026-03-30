import sqlite3

def write_top_jobs():
    conn = sqlite3.connect('jobs.db')
    c = conn.cursor()
    c.execute('''
        SELECT title, company, salary, location, final_score, url 
        FROM jobs 
        WHERE final_score > 0
        ORDER BY final_score DESC 
        LIMIT 10
    ''')
    jobs = c.fetchall()
    
    with open('top_jobs_report.txt', 'w', encoding='utf-8') as f:
        for j in jobs:
            f.write(f"Title: {j[0]}\n")
            f.write(f"Company: {j[1]}\n")
            f.write(f"Salary: {j[2]}\n")
            f.write(f"Location: {j[3]}\n")
            f.write(f"Final Score: {j[4]}\n")
            f.write(f"URL: {j[5]}\n")
            f.write("-" * 40 + "\n")
            
    conn.close()

if __name__ == '__main__':
    write_top_jobs()
