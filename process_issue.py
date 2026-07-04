#!/usr/bin/env python3
"""GitHub Actions: 解析 Issue body JSON，写入 WPS 表格（支持所有Tab类型）"""
import json, subprocess, os, sys, re

# WPS 文件配置
MAIN_FILE_ID = 'nZL1azhGc1MphojViCR2rxeDwtT16Wmce'  # SV派单记录表
BATCH_FILE_ID = 'HrX6hKXrK1MU6samwDYK1xEzaRgVM4EZ1'  # 1.批量工单

# 各Tab对应的 Worksheet ID 和列映射
TAB_CONFIG = {
    'dispatch': {
        'file_id': MAIN_FILE_ID,
        'worksheet_id': 27,
        'key_col': 5,           # 单号列（用于编辑时查找行）
        'search_range': (1, 1000),
        'last_row_range': (790, 1200),
        'default_last_row': 798,
        'columns': [
            # (col_index, field_key, default_value)
            (0, 'sn', ''),         # 序号（自动）
            (1, 'c', ''),          # 客户
            (2, 'a', ''),          # 地址
            (3, 'ct', ''),         # 联系人
            (4, 'ph', ''),         # 电话
            (5, 'o', ''),          # 单号
            (6, 'sv', ''),         # 服务类型
            (7, 'pm', ''),         # 产品型号
            (8, 'q', ''),          # 数量
            (9, 'cn', ''),         # 服务内容
            (10, 'in', ''),        # 实施编号
            (11, 'sl', ''),        # 销售
            (12, 'slp', ''),       # 销售电话
            (13, 'sd', ''),        # 开始日期
            (14, 'ed', ''),        # 结束日期
            (15, 'rm', ''),        # 备注
            (16, 'pc', 'CX-SV'),   # 产品类别
            (17, 'sr', 'CRM'),     # 来源
        ]
    },
    'monthly': {
        'file_id': MAIN_FILE_ID,
        'worksheet_id': 18,
        'key_col': 1,           # 备案编号列
        'search_range': (1, 600),
        'last_row_range': (300, 600),
        'default_last_row': 320,
        'columns': [
            (0, 'sn', ''),
            (1, 'rec', ''),        # 备案编号
            (2, 'dt', ''),         # 需求时间
            (3, 'mu', ''),         # MU
            (4, 'pm', ''),         # PM
            (5, 'ini', ''),        # 发起人
            (6, 'c', ''),          # 客户
            (7, 'pj', ''),         # 项目
            (8, 'dmd', ''),        # 需求类型
            (9, 'loc', ''),        # 服务地点
            (10, 'dev', ''),       # 设备型号
            (11, 'det', ''),       # 需求细节
            (12, 'q', ''),         # 数量
            (13, 'sv', ''),        # 服务类型
            (14, 'cnt', ''),       # 计数
            (15, 'cnf', ''),       # 计数确认
            (16, 'wo', ''),        # 工单号
            (17, 'cc', ''),        # 费用归集编号
            (18, 'rm', ''),        # 备注
        ]
    },
    'inspection': {
        'file_id': MAIN_FILE_ID,
        'worksheet_id': 28,
        'key_col': 5,           # 单号列
        'search_range': (1, 300),
        'last_row_range': (50, 200),
        'default_last_row': 70,
        'columns': [
            (0, 'sn', ''),
            (1, 'c', ''),
            (2, 'a', ''),
            (3, 'ct', ''),
            (4, 'ph', ''),
            (5, 'o', ''),
            (6, 'sv', ''),
            (7, 'pm', ''),
            (8, 'q', ''),
            (9, 'det', ''),
            (10, 'in', ''),
            (11, 'sl', ''),
            (12, 'slp', ''),
            (13, 'st', ''),
            (14, 'sd', ''),
            (15, 'ed', ''),
            (16, 'rm', ''),
        ]
    },
    'duty': {
        'file_id': MAIN_FILE_ID,
        'worksheet_id': 15,
        'key_col': 7,           # 单号列
        'search_range': (1, 400),
        'last_row_range': (50, 300),
        'default_last_row': 82,
        'columns': [
            (0, 'sn', ''),
            (1, 'c', ''),
            (2, 'a', ''),
            (3, 'ct', ''),
            (4, 'ph', ''),
            (5, 'pc', ''),
            (6, 'sr', ''),
            (7, 'o', ''),
            (8, 'sv', ''),
            (9, 'pm', ''),
            (10, 'q', ''),
            (11, 'cn', ''),
            (12, 'in', ''),
            (13, 'sl', ''),
            (14, 'slp', ''),
            (15, 'st', ''),
            (16, 'sd', ''),
            (17, 'ed', ''),
            (18, 'ad', ''),
            (19, 'mgr', ''),
            (20, 'mgp', ''),
            (21, 'rm', ''),
        ]
    },
    'batch_qa': {
        'file_id': BATCH_FILE_ID,
        'worksheet_id': 1,      # 需要确认实际工作表ID
        'key_col': 4,           # 问题单编号
        'search_range': (1, 200),
        'last_row_range': (1, 200),
        'default_last_row': 33,
        'columns': [
            (0, 'sn', ''),
            (1, 'name', ''),
            (2, 'cause', ''),
            (3, 'sol', ''),
            (4, 'qano', ''),
            (5, 'ct', ''),
            (6, 'dev', ''),
            (7, 'cq', ''),
            (8, 'src', ''),
        ]
    },
    'batch_wo': {
        'file_id': BATCH_FILE_ID,
        'worksheet_id': 2,      # 需要确认实际工作表ID
        'key_col': 8,           # 问题编号
        'search_range': (1, 200),
        'last_row_range': (1, 200),
        'default_last_row': 110,
        'columns': [
            (0, 'sn', ''),
            (1, 'c', ''),
            (2, 'ind', ''),
            (3, 'a', ''),
            (4, 'ct', ''),
            (5, 'ph', ''),
            (6, 'pc', ''),
            (7, 'qa', ''),
            (8, 'qano', ''),
            (9, 'unit', ''),
            (10, 'pm', ''),
            (11, 'q', ''),
            (12, 'sv', ''),
            (13, 'in', ''),
            (14, 'tool', ''),
            (15, 'st', ''),
            (16, 'sd', ''),
            (17, 'ed', ''),
            (18, 'ad', ''),
            (19, 'mgr', ''),
            (20, 'mgp', ''),
        ]
    },
}

raw = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('ISSUE_BODY', '')
m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
if m:
    raw = m.group(1)
try:
    req = json.loads(raw)
except Exception:
    print(f"❌ 无法解析 JSON: {raw[:200]}")
    sys.exit(1)

tab = req.get('tab', 'dispatch')
cfg = TAB_CONFIG.get(tab)
if not cfg:
    print(f"❌ 未知 Tab: {tab}")
    sys.exit(1)

FILE_ID = cfg['file_id']
WORKSHEET_ID = cfg['worksheet_id']
KEY_COL = cfg['key_col']
env = {**os.environ, 'PATH': os.environ.get('PATH','') + ':' + os.path.expanduser('~/.local/bin')}

def call_kdocs(payload):
    with open('/tmp/payload.json','w',encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False)
    r = subprocess.run(['kdocs-cli','sheet','update-range-data','--file','/tmp/payload.json'],
                       capture_output=True, text=True, env=env, timeout=30)
    ok = r.returncode == 0
    try:
        result = json.loads(r.stdout)
        ok = ok and result.get('code') == 0
    except:
        pass
    return ok, r.stdout[:200]

def get_last_row():
    sr, er = cfg['last_row_range']
    r = subprocess.run(['kdocs-cli','sheet','get-range-data', json.dumps({
        'file_id': FILE_ID, 'worksheet_id': WORKSHEET_ID,
        'range': {'rowFrom': sr, 'rowTo': er, 'colFrom': 0, 'colTo': 1}
    })], capture_output=True, text=True, env=env, timeout=15)
    try:
        cells = json.loads(r.stdout)['data']['detail']['rangeData']
    except:
        return cfg['default_last_row']
    last = cfg['default_last_row']
    for c in cells:
        if c.get('cellText',''): last = max(last, c['rowFrom'])
    return last

def find_row_by_key(key_val):
    """查询关键字段所在行号"""
    sr, er = cfg['search_range']
    r = subprocess.run(['kdocs-cli','sheet','get-range-data', json.dumps({
        'file_id': FILE_ID, 'worksheet_id': WORKSHEET_ID,
        'range': {'rowFrom': sr, 'rowTo': er, 'colFrom': KEY_COL, 'colTo': KEY_COL}
    })], capture_output=True, text=True, env=env, timeout=30)
    try:
        cells = json.loads(r.stdout)['data']['detail']['rangeData']
    except:
        return None
    for c in cells:
        if c.get('cellText','').strip() == str(key_val).strip():
            return c['rowFrom']
    return None

def write_row(row_idx, d):
    """在指定行写入数据"""
    rangeData = []
    for col_idx, field_key, default in cfg['columns']:
        v = d.get(field_key, default)
        if v or v == 0:
            rangeData.append({
                'opType': 'formula',
                'rowFrom': row_idx, 'rowTo': row_idx,
                'colFrom': col_idx, 'colTo': col_idx,
                'formula': str(v)
            })
    payload = {'file_id': FILE_ID, 'worksheet_id': WORKSHEET_ID, 'rangeData': rangeData}
    return call_kdocs(payload)

action = req.get('action', 'add')
data = req.get('data', {})

print(f"📋 处理: tab={tab}, action={action}, 文件={FILE_ID}, 工作表={WORKSHEET_ID}")

ok = False
if action == 'add':
    row = get_last_row() + 1
    ok, msg = write_row(row, data)
    summary = data.get('c') or data.get('name') or data.get('rec') or '?'
    print(f"{'✅' if ok else '❌'} 新增: 行{row}, 标识={summary}")

elif action == 'edit':
    key_val = req.get('original_key', '') or data.get(cfg['columns'][KEY_COL][1], '')
    row = find_row_by_key(key_val)
    if row:
        ok, msg = write_row(row, data)
        print(f"{'✅' if ok else '❌'} 编辑: 行{row}, 关键值={key_val}")
    else:
        print(f"⚠️ 找不到关键值={key_val}, 改为新增")
        row = get_last_row() + 1
        ok, msg = write_row(row, data)
        print(f"{'✅' if ok else '❌'} 新增: 行{row}")

if ok:
    print("🎉 写入WPS成功！")
else:
    print(f"❌ 写入失败: {msg}")

sys.exit(0 if ok else 1)
