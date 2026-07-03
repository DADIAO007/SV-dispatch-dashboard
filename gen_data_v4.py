#!/usr/bin/env python3
"""重新生成数据 - 按日期倒序"""
import sqlite3, json, os

conn = sqlite3.connect('/workspace/sv_dispatch.db')
c = conn.cursor()
data = {'stats': {}, 'records': []}

r = c.execute('SELECT COUNT(*), COUNT(DISTINCT customer_name) FROM dispatch_orders').fetchone()
data['stats']['total'] = r[0]
data['stats']['customers'] = r[1]
data['stats']['d2026'] = c.execute('SELECT COUNT(*) FROM dispatch_orders WHERE year=2026').fetchone()[0]
data['stats']['d2025'] = c.execute('SELECT COUNT(*) FROM dispatch_orders WHERE year=2025').fetchone()[0]
data['stats']['d2024'] = c.execute('SELECT COUNT(*) FROM dispatch_orders WHERE year=2024').fetchone()[0]
data['stats']['inspection'] = c.execute('SELECT COUNT(*) FROM inspection_tasks').fetchone()[0]
data['stats']['duty'] = c.execute('SELECT COUNT(*) FROM duty_tasks').fetchone()[0]
data['stats']['settlement'] = c.execute('SELECT COUNT(*) FROM monthly_settlements').fetchone()[0]

data['yearly'] = [{'year':y,'count':c2} for y,c2 in c.execute('SELECT year,COUNT(*) FROM dispatch_orders GROUP BY year ORDER BY year')]
data['monthly'] = [{'month':m,'count':c2} for m,c2 in c.execute("SELECT substr(start_date,1,6),COUNT(*) FROM dispatch_orders WHERE year=2026 AND length(start_date)=8 GROUP BY 1 ORDER BY 1")]
data['ctop'] = [{'name':n,'count':c2} for n,c2 in c.execute('SELECT customer_name,COUNT(*) FROM dispatch_orders GROUP BY 1 ORDER BY 2 DESC LIMIT 10')]
data['srv'] = [{'name':n,'count':c2} for n,c2 in c.execute("SELECT service_type,COUNT(*) FROM dispatch_orders WHERE service_type!='' GROUP BY 1 ORDER BY 2 DESC LIMIT 12")]
data['prod'] = [{'name':n,'count':c2} for n,c2 in c.execute("SELECT product_model,COUNT(*) FROM dispatch_orders WHERE product_model!='' GROUP BY 1 ORDER BY 2 DESC LIMIT 10")]
data['sales'] = [{'name':n,'count':c2} for n,c2 in c.execute("SELECT sales_person,COUNT(*) FROM dispatch_orders WHERE sales_person!='' AND sales_person!='\\' GROUP BY 1 ORDER BY 2 DESC LIMIT 10")]
data['status'] = [{'name':s,'count':c2} for s,c2 in c.execute("SELECT COALESCE(NULLIF(status,''),'未标记'),COUNT(*) FROM dispatch_orders WHERE year=2026 GROUP BY 1 ORDER BY 2 DESC")]
data['recent'] = [{'c':r[0],'o':r[1],'s':r[2],'m':r[3],'d':r[4]} for r in c.execute("SELECT customer_name,order_no,service_type,product_model,start_date FROM dispatch_orders WHERE year=2026 AND length(start_date)=8 ORDER BY start_date DESC LIMIT 10")]

all_rows = list(c.execute("SELECT year,customer_name,address,contact_person,contact_phone,order_no,service_type,product_model,quantity,service_content,implement_no,sales_person,sales_phone,start_date,expected_end_date,actual_end_date,implement_manager,implement_manager_phone,status,remark FROM dispatch_orders"))

records = []
for r in all_rows:
    sd = r[13] or ''
    sort_key = sd if len(sd) == 8 else '0'
    records.append({
        't': '派单', 'y': r[0], 'c': r[1] or '', 'a': (r[2] or '')[:25], 'ct': r[3] or '', 'ph': r[4] or '',
        'o': r[5] or '', 'sv': r[6] or '', 'pm': r[7] or '', 'q': r[8] or '', 'cn': (r[9] or '')[:30],
        'in': r[10] or '', 'sl': r[11] or '', 'sd': sd, 'ed': r[14] or '', 'st': r[18] or '', 'rm': (r[19] or '')[:25],
        '_sort': sort_key
    })

records.sort(key=lambda x: x['_sort'], reverse=True)
for r in records:
    del r['_sort']
data['records'] = records

conn.close()
print(f'Records: {len(records)}')
print(f'First: {records[0]["sd"]} - {records[0]["c"]}')
print(f'Last: {records[-1]["sd"]} - {records[-1]["c"]}')

with open('/workspace/dashboard_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
print(f'Size: {os.path.getsize("/workspace/dashboard_data.json")/1024:.1f} KB')
