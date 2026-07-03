#!/usr/bin/env python3
"""GitHub Actions: 解析 Issue body JSON，写入 WPS 表格"""
import json, subprocess, os, sys, re

FILE_ID = 'nZL1azhGc1MphojViCR2rxeDwtT16Wmce'
WORKSHEET_ID = 27

raw = sys.argv[1] if len(sys.argv) > 1 else ''
# 提取 JSON 块（可能在 ``` 中）
m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
if m:
    raw = m.group(1)
try:
    req = json.loads(raw)
except:
    print(f"❌ 无法解析 JSON")
    sys.exit(1)

env = {**os.environ, 'PATH': os.environ.get('PATH','') + ':' + os.path.expanduser('~/.local/bin')}

def call_kdocs(payload):
    with open('/tmp/payload.json','w',encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False)
    r = subprocess.run(['kdocs-cli','sheet','update-range-data','--file','/tmp/payload.json'],
                       capture_output=True, text=True, env=env, timeout=30)
    return r.returncode == 0, r.stdout[:200]

def get_last_row():
    r = subprocess.run(['kdocs-cli','sheet','get-range-data', json.dumps({
        'file_id': FILE_ID, 'worksheet_id': WORKSHEET_ID,
        'range': {'rowFrom': 790, 'rowTo': 1200, 'colFrom': 0, 'colTo': 1}
    })], capture_output=True, text=True, env=env, timeout=15)
    try:
        cells = json.loads(r.stdout)['data']['detail']['rangeData']
    except:
        return 798
    last = 798
    for c in cells:
        if c.get('cellText',''): last = max(last, c['rowFrom'])
    return last

def find_row_by_order(order_no):
    """查询单号所在行号"""
    r = subprocess.run(['kdocs-cli','sheet','get-range-data', json.dumps({
        'file_id': FILE_ID, 'worksheet_id': WORKSHEET_ID,
        'range': {'rowFrom': 1, 'rowTo': 1000, 'colFrom': 5, 'colTo': 5}
    })], capture_output=True, text=True, env=env, timeout=30)
    try:
        cells = json.loads(r.stdout)['data']['detail']['rangeData']
    except:
        return None
    for c in cells:
        if c.get('cellText','').strip() == order_no:
            return c['rowFrom']
    return None

def write_row(row_idx, d):
    """在指定行写入数据"""
    vals = [
        '', d.get('customer',''), d.get('address',''),
        d.get('contact',''), d.get('phone',''),
        d.get('order_no',''), d.get('service',''), d.get('product',''),
        d.get('qty',''), d.get('content',''),
        d.get('impl_no',''), d.get('sales',''), '',
        d.get('start_date',''), '',
        d.get('remark',''), d.get('pcat','CX-SV'), d.get('source','CRM')
    ]
    rangeData = []
    for i, v in enumerate(vals):
        if v:
            rangeData.append({'opType':'formula','rowFrom':row_idx,'rowTo':row_idx,'colFrom':i,'colTo':i,'formula':str(v)})
    payload = {'file_id':FILE_ID,'worksheet_id':WORKSHEET_ID,'rangeData':rangeData}
    return call_kdocs(payload)

action = req.get('action','add')
data = req.get('data',{})

if action == 'add':
    row = get_last_row() + 1
    ok, msg = write_row(row, data)
    print(f"{'✅' if ok else '❌'} 新增: 行{row}, 客户={data.get('customer','?')}")

elif action == 'edit':
    order_no = req.get('original_order_no','') or data.get('order_no','')
    row = find_row_by_order(order_no)
    if row:
        ok, msg = write_row(row, data)
        print(f"{'✅' if ok else '❌'} 编辑: 行{row}, 单号={order_no}")
    else:
        print(f"❌ 找不到单号={order_no}, 改为新增")
        row = get_last_row() + 1
        ok, msg = write_row(row, data)
        print(f"{'✅' if ok else '❌'} 新增: 行{row}")

sys.exit(0 if ok else 1)
