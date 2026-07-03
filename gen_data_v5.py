#!/usr/bin/env python3
"""
SV派单看板 v5 - 多Tab版本
- 派单明细（仅派单数据，按日期倒序）
- 通信月结
- 巡检
- 值守
- 批量问题
- 批量工单
"""
import sqlite3, json, os

DB_PATH = '/workspace/sv_dispatch.db'
OUTPUT = '/workspace/dashboard.html'

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# === 派单明细（2024/2025/2026合并） ===
def norm_date(s):
    """规范化日期为 8 位数字串"""
    if not s: return '0'
    s = s.strip()
    if len(s) == 8 and s.isdigit(): return s
    return '0'

dispatch = []
for r in c.execute("SELECT * FROM dispatch_orders"):
    sd = norm_date(r['start_date'])
    dispatch.append({
        't':'派单','y':r['year'],
        'c':r['customer_name'] or '','a':(r['address'] or '')[:25],
        'ct':r['contact_person'] or '','ph':r['contact_phone'] or '',
        'o':r['order_no'] or '','sv':r['service_type'] or '','pm':r['product_model'] or '',
        'q':r['quantity'] or '','cn':(r['service_content'] or '')[:30],
        'in':r['implement_no'] or '','sl':r['sales_person'] or '','slp':r['sales_phone'] or '',
        'sd':r['start_date'] or '','ed':r['expected_end_date'] or '',
        'ad':r['actual_end_date'] or '','mgr':r['implement_manager'] or '',
        'mgp':r['implement_manager_phone'] or '','st':r['status'] or '待处理',
        'rm':(r['remark'] or '')[:25],'pc':r['product_category'] or '','sr':r['task_source'] or '',
        '_sort': sd
    })
dispatch.sort(key=lambda x: x['_sort'], reverse=True)
for d in dispatch: del d['_sort']

# === 通信月结 ===
monthly = []
for r in c.execute("SELECT * FROM monthly_settlements"):
    monthly.append({
        'sn':r['serial_number'] or '','rec':r['record_no'] or '','dt':r['demand_date'] or '',
        'mu':r['mu_department'] or '','ini':r['initiator'] or '','pm':r['pm'] or '',
        'c':r['customer'] or '','pj':r['project_name'] or '','dmd':r['demand_type'] or '',
        'loc':r['service_location'] or '','dev':r['device_model'] or '',
        'det':(r['demand_detail'] or '')[:40],'q':r['quantity'] or 0,
        'sv':r['service_type'] or '','cnt':r['count_value'] or 0,
        'cnf':r['count_confirm'] or '','wo':r['work_order_no'] or '',
        'cc':r['cost_collect_no'] or '','rm':(r['remark'] or '')[:25]
    })
# 通信月结排序：按工单号或日期
monthly.sort(key=lambda x: x['wo'] or '0', reverse=True)

# === 巡检 ===
inspection = []
for r in c.execute("SELECT * FROM inspection_tasks"):
    inspection.append({
        'sn':r['serial_number'] or '','c':r['customer_name'] or '','a':(r['address'] or '')[:25],
        'ct':r['contact_person'] or '','ph':r['contact_phone'] or '',
        'o':r['order_no'] or '','sv':r['service_type'] or '','pm':r['product_model'] or '',
        'q':r['quantity'] or '','det':(r['requirement_detail'] or '')[:30],
        'in':r['implement_no'] or '','sl':r['sales_person'] or '','slp':r['sales_phone'] or '',
        'st':r['status'] or '','sd':r['start_date'] or '','ed':r['end_date'] or '',
        'rm':(r['remark'] or '')[:25]
    })
inspection.sort(key=lambda x: x['sd'] or '0', reverse=True)

# === 值守 ===
duty = []
for r in c.execute("SELECT * FROM duty_tasks"):
    duty.append({
        'sn':r['serial_number'] or '','c':r['customer_name'] or '','a':(r['address'] or '')[:25],
        'ct':r['contact_person'] or '','ph':r['contact_phone'] or '',
        'pc':r['product_category'] or '','sr':r['task_source'] or '',
        'o':r['order_no'] or '','sv':r['service_type'] or '','pm':r['product_model'] or '',
        'q':r['quantity'] or '','cn':(r['service_content'] or '')[:30],
        'in':r['implement_no'] or '','sl':r['sales_person'] or '','slp':r['sales_phone'] or '',
        'st':r['status'] or '','sd':r['start_date'] or '','ed':r['expected_end_date'] or '',
        'ad':r['actual_end_date'] or '','mgr':r['implement_manager'] or '',
        'mgp':r['implement_manager_phone'] or '','rm':(r['remark'] or '')[:25]
    })
duty.sort(key=lambda x: x['sd'] or '0', reverse=True)

conn.close()

# === 批量问题/批量工单 - 直接从生成的JSON文件读取 ===
# （将后续写入文件）
BATCH_FILE = '/workspace/batch_data.json'
batch_data = {}
if os.path.exists(BATCH_FILE):
    with open(BATCH_FILE) as f:
        batch_data = json.load(f)
    batch_qa = batch_data.get('qa', [])
    batch_wo = batch_data.get('wo', [])
else:
    # Placeholder - script will need to fetch
    batch_qa = []
    batch_wo = []
    print("⚠️ batch_data.json 不存在，将需要拉取")

# === 统计概览 ===
stats = {
    'total': len(dispatch) + len(inspection) + len(duty) + len(monthly),
    'dispatch': len(dispatch),
    'inspection': len(inspection),
    'duty': len(duty),
    'monthly': len(monthly),
    'batch_qa': len(batch_qa),
    'batch_wo': len(batch_wo),
    'customers': len(set(d['c'] for d in dispatch if d['c'])),
    'd2024': sum(1 for d in dispatch if d['y']==2024),
    'd2025': sum(1 for d in dispatch if d['y']==2025),
    'd2026': sum(1 for d in dispatch if d['y']==2026),
}

# Top stats
from collections import Counter
ctop = Counter(d['c'] for d in dispatch).most_common(10)
ctop_data = [{'name':n,'count':c} for n,c in ctop]

srv = Counter(d['sv'] for d in dispatch if d['sv']).most_common(12)
srv_data = [{'name':n,'count':c} for n,c in srv]

prod = Counter(d['pm'] for d in dispatch if d['pm']).most_common(10)
prod_data = [{'name':n,'count':c} for n,c in prod]

sales = Counter(d['sl'] for d in dispatch if d['sl'] and d['sl']!='\\').most_common(10)
sales_data = [{'name':n,'count':c} for n,c in sales]

yearly = Counter(d['y'] for d in dispatch if d['y'])
yearly_data = [{'year':y,'count':c} for y,c in sorted(yearly.items())]

monthly_2026 = Counter(d['sd'][:6] for d in dispatch if d['y']==2026 and len(d['sd'])==8)
monthly_data = [{'month':m,'count':c} for m,c in sorted(monthly_2026.items())]

recent = [d for d in dispatch if d['y']==2026][:10]

status_data = [{'name':'待处理','count':len([d for d in dispatch if d['y']==2026])}]

data = {
    'stats': stats,
    'dispatch': dispatch,
    'monthly': monthly,
    'inspection': inspection,
    'duty': duty,
    'batch_qa': batch_qa,
    'batch_wo': batch_wo,
    'yearly': yearly_data,
    'monthly_chart': monthly_data,
    'ctop': ctop_data,
    'srv': srv_data,
    'prod': prod_data,
    'sales': sales_data,
    'status': status_data,
    'recent': recent,
}

# Save for verification
with open('/workspace/dashboard_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print(f"派单明细: {len(dispatch)}")
print(f"通信月结: {len(monthly)}")
print(f"巡检: {len(inspection)}")
print(f"值守: {len(duty)}")
print(f"批量问题: {len(batch_qa)}")
print(f"批量工单: {len(batch_wo)}")
print(f"1st dispatch: {dispatch[0]['sd']} - {dispatch[0]['c']}")
