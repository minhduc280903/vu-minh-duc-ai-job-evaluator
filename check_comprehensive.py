import sqlite3
import json

def check_comprehensive_data():
    conn = sqlite3.connect('C:/Users/PC/OneDrive/Desktop/job-finder/job-finder-v4/jobs.db')
    conn.row_factory = sqlite3.Row  # To access columns by name
    cursor = conn.cursor()
    
    platforms = ['Ybox', 'VietnamWorks']
    
    for platform in platforms:
        print(f"\n{'='*50}")
        print(f"SAMPLE JOB FROM: {platform}")
        print(f"{'='*50}")
        
        cursor.execute("SELECT * FROM jobs WHERE platform = ? AND description IS NOT NULL AND description != '' LIMIT 1", (platform,))
        job = cursor.fetchone()
        
        if job:
            for key in job.keys():
                val = job[key]
                if key in ['raw']: continue # Skip printing full raw json to keep it readable
                
                if isinstance(val, str) and len(val) > 300:
                    val = val[:300] + " ... [TRUNCATED]"
                print(f"{key.upper()}: {val}")
        else:
            print(f"No comprehensive job found for {platform}")
            
    # Check total counts
    print(f"\n{'='*50}")
    print("DATABASE SUMMARY")
    print(f"{'='*50}")
    cursor.execute("SELECT platform, COUNT(*) as count FROM jobs GROUP BY platform")
    for row in cursor.fetchall():
        print(f"{row['platform']}: {row['count']} jobs")

    conn.close()

if __name__ == "__main__":
    check_comprehensive_data()
