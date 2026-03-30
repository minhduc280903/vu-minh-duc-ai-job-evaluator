import sqlite3
from datetime import datetime
import dateutil.parser

def check_expired():
    conn = sqlite3.connect('jobs.db')
    c = conn.cursor()
    c.execute("SELECT id, platform, deadline FROM jobs WHERE deadline != ''")
    rows = c.fetchall()
    
    current_time = datetime.now()
    expired_count = {'Ybox': 0, 'VietnamWorks': 0, 'TopCV': 0, 'ITviec': 0}
    total_count = {'Ybox': 0, 'VietnamWorks': 0, 'TopCV': 0, 'ITviec': 0}
    
    for row in rows:
        job_id, platform, deadline_str = row
        if platform in total_count:
            total_count[platform] += 1
            
        try:
             # parse ISO date
             dt = dateutil.parser.isoparse(deadline_str).replace(tzinfo=None) # naive comparison
             if dt < current_time:
                 expired_count[platform] += 1
        except Exception as e:
             # handle simple strings like "30/04/2026"
             try:
                  dt = datetime.strptime(deadline_str, "%d/%m/%Y")
                  if dt < current_time:
                       expired_count[platform] += 1
             except:
                  pass
                  
    print(f"Current Date: {current_time.isoformat()}")
    print("Expired Jobs in DB:")
    for p in expired_count:
        print(f"{p}: {expired_count[p]} expired out of {total_count[p]} with explicit deadlines")
    
    conn.close()

if __name__ == '__main__':
    check_expired()
