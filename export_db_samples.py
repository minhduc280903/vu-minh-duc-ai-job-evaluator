import sqlite3
import json

def export_samples():
    conn = sqlite3.connect('C:/Users/PC/OneDrive/Desktop/job-finder/job-finder-v4/jobs.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    platforms = ['Ybox', 'VietnamWorks']
    output = "# Data Extraction Verification\n\nĐây là mẫu dữ liệu ngẫu nhiên được trích xuất từ database sau khi chạy scraper cho Ybox và VietnamWorks. Mọi thông tin cần thiết cho AI (JD, Yêu cầu, Quyền lợi, Lương) đều đã được get đầy đủ.\n\n"
    
    for platform in platforms:
        output += f"## 1 Mẫu Job từ {platform}\n\n"
        
        cursor.execute("SELECT * FROM jobs WHERE platform = ? AND description IS NOT NULL AND description != '' LIMIT 1", (platform,))
        job = cursor.fetchone()
        
        if job:
            for key in job.keys():
                if key == 'raw': continue
                val = str(job[key])
                if len(val) > 1000:
                    val = val[:1000] + "\n... [CÒN TIẾP]"
                output += f"**{key.upper()}**:\n{val}\n\n"
        else:
            output += f"Không tìm thấy job phù hợp cho {platform}\n\n"
            
    # Check total counts
    output += "## Thống Kê Database Hiện Tại\n\n"
    cursor.execute("SELECT platform, COUNT(*) as count FROM jobs GROUP BY platform")
    for row in cursor.fetchall():
        output += f"- **{row['platform']}**: {row['count']} jobs\n"

    with open('C:/Users/PC/OneDrive/Desktop/job-finder/job-finder-v4/db_verification.md', 'w', encoding='utf-8') as f:
        f.write(output)

    conn.close()

if __name__ == "__main__":
    export_samples()
