import sys, sqlite3
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('jobs.db')
c = conn.cursor()

print('=== FINAL DB STATS ===')
c.execute('SELECT COUNT(*) FROM jobs')
total = c.fetchone()[0]
print(f'Total jobs: {total}')

print('\n=== BY PLATFORM ===')
c.execute('SELECT platform, COUNT(*) FROM jobs GROUP BY platform ORDER BY COUNT(*) DESC')
for r in c.fetchall():
    print(f'  {r[0]}: {r[1]}')

print('\n=== SALARY COVERAGE ===')
c.execute("SELECT COUNT(*) FROM jobs WHERE salary IS NOT NULL AND salary != '' AND salary != 'Thỏa thuận' AND salary != 'Thoả thuận' AND salary != 'Sign in to view' AND salary != 'Cạnh tranh'")
has_sal = c.fetchone()[0]
print(f'  With real salary: {has_sal}/{total} ({has_sal*100//max(total,1)}%)')

print('\n=== SALARY BY PLATFORM ===')
c.execute("""
    SELECT platform, 
           COUNT(*) as total,
           SUM(CASE WHEN salary IS NOT NULL AND salary != '' AND salary != 'Thỏa thuận' AND salary != 'Thoả thuận' AND salary != 'Sign in to view' AND salary != 'Cạnh tranh' THEN 1 ELSE 0 END) as has_sal
    FROM jobs GROUP BY platform ORDER BY total DESC
""")
for r in c.fetchall():
    pct = r[2]*100//max(r[1],1)
    print(f'  {r[0]}: {r[2]}/{r[1]} ({pct}%)')

print('\n=== FINANCE/DATA JOBS ===')
c.execute("""SELECT COUNT(*) FROM jobs WHERE LOWER(title) LIKE '%analyst%' OR LOWER(title) LIKE '%finance%' OR LOWER(title) LIKE '%risk%' OR LOWER(title) LIKE '%credit%' OR LOWER(title) LIKE '%banking%' OR LOWER(title) LIKE '%audit%' OR LOWER(title) LIKE '%kiem toan%'""")
print(f'  Relevant titles: {c.fetchone()[0]}')

print('\n=== CAREERVIET SAMPLES ===')
c.execute("SELECT title, company, salary FROM jobs WHERE platform='CareerViet' LIMIT 5")
for r in c.fetchall():
    t = (r[0][:40]+'...') if len(r[0])>40 else r[0]
    print(f'  {t} | {r[1][:22]} | {r[2]}')

print('\n=== TOPCV WITH SALARY ===')
c.execute("SELECT title, salary FROM jobs WHERE platform='TopCV' AND salary NOT IN ('', 'Thỏa thuận', 'Thoả thuận') LIMIT 5")
for r in c.fetchall():
    t = (r[0][:45]+'...') if len(r[0])>45 else r[0]
    print(f'  {t} | {r[1]}')

conn.close()
