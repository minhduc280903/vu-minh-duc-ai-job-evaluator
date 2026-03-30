import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('joboko_fresher_jobs_hn.xlsx')

def score_job(row):
    score = 0
    title = str(row['title']).lower()
    company = str(row['company']).lower()
    req = str(row['requirements']).lower()
    
    # Yêu cầu về Title / Vị trí
    if 'data analyst' in title: score += 15
    if 'business analyst' in title or 'ba' in title: score += 10
    if 'thực tập' in title or 'intern' in title: score += 8
    if 'fresher' in title: score += 12
    if 'junior' in title: score += 12
    if 'risk' in title or 'rủi ro' in title or 'tín dụng' in title: score += 20
    
    # Ngành nghề công ty (Tài chính - Ngân hàng là một điểm cộng lớn)
    if 'ngân hàng' in company or 'tài chính' in company or 'bank' in company or 'finance' in company or 'chứng khoán' in company: 
        score += 15
    
    # Kỹ năng (Dựa theo profile của user)
    if 'python' in req: score += 5
    if 'sql' in req: score += 5
    if 'excel' in req: score += 2
    if 'power bi' in req or 'tableau' in req: score += 3
    
    # Loại trừ ngay lập tức các job mạo danh "Data" nhưng thực chất là Sale/Telesale/Nhập liệu
    bad_keywords = ['sale', 'telesale', 'kinh doanh', 'tư vấn', 'chốt đơn', 'nhập liệu', 'data entry', 'bán hàng', 'thị trường', 'cskh', 'chăm sóc khách hàng']
    for bad in bad_keywords:
        if bad in title:
            score -= 100
            break
            
    return score

df['score'] = df.apply(score_job, axis=1)
top_jobs = df[df['score'] > 0].sort_values(by='score', ascending=False).head(10)

print("Top 10 Jobs phù hợp nhất từ 147 jobs:\n" + "="*50)
for _, row in top_jobs.iterrows():
    print(f"🏆 {row['title']}")
    print(f"🏢 Công ty: {row['company']}")
    print(f"💰 Lương: {row['salary']} | 🎓 Yêu cầu KN: {row['level']}")
    print(f"🔗 Link: {row['url']}")
    print(f"⭐ Điểm Joboko Score: {row['score']}")
    print("-" * 50)
