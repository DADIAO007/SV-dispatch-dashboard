#!/usr/bin/env python3
"""
SV派单看板自动生成脚本
直接从金山文档读取数据，生成静态HTML看板
用于GitHub Actions自动更新
"""
import json
import subprocess
import os
import sys

FILE_ID = 'nZL1azhGc1MphojViCR2rxeDwtT16Wmce'
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')

def kdocs(params):
    """调用kdocs-cli获取sheet数据"""
    env = {**os.environ, 'PATH': os.environ.get('PATH', '') + ':' + os.path.expanduser('~/.local/bin')}
    result = subprocess.run(
        ['kdocs-cli', 'sheet', 'get-range-data', json.dumps(params)],
        capture_output=True, text=True, env=env
    )
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr}", file=sys.stderr)
        return []
    try:
        data = json.loads(result.stdout)
        if data.get('code') != 0:
            return []
        return data['data']['detail']['rangeData']
    except:
        return []

def read_sheet(worksheet_id, max_row, col_count):
    """分批读取整个工作表"""
    all_cells = []
    batch_size = 200
    for start in range(1, max_row + 1, batch_size):
        end = min(start + batch_size - 1, max_row)
        cells = kdocs({
            'file_id': FILE_ID, 'worksheet_id': worksheet_id,
            'range': {'rowFrom': start, 'rowTo': end, 'colFrom': 0, 'colTo': col_count - 1}
        })
        if not cells:
            break
        all_cells.extend(cells)
        has = any(c.get('cellText', '') for c in cells)
        if not has:
            break
    return all_cells

def cells_to_rows(cells):
    rows = {}
    for c in cells:
        r = c['rowFrom']
        if r not in rows: rows[r] = {}
        rows[r][c['colFrom']] = c.get('cellText', '').strip()
    return rows

def read_all_sheets():
    """读取所有工作表中的统计数据"""
    stats = {}
    
    # ====== 派单记录 ======
    # 2026派单 (ws=27, 18col)
    rows2026 = cells_to_rows(read_sheet(27, 800, 18))
    # 2025派单 (ws=25, 22col)
    rows2025 = cells_to_rows(read_sheet(25, 1500, 22))
    # 2024派单 (ws=1, 22col)
    rows2024 = cells_to_rows(read_sheet(1, 600, 22))
    
    # 巡检 (ws=28, 17col)
    rows_insp = cells_to_rows(read_sheet(28, 200, 17))
    # 值守 (ws=15, 23col)
    rows_duty = cells_to_rows(read_sheet(15, 300, 23))
    # 通信月结 (ws=18, 19col)
    rows_ms = cells_to_rows(read_sheet(18, 500, 19))
    
    print(f"  2026派单: {len(rows2026)}行, 2025派单: {len(rows2025)}行, 2024派单: {len(rows2024)}行")
    print(f"  巡检: {len(rows_insp)}行, 值守: {len(rows_duty)}行, 通信月结: {len(rows_ms)}行")
    
    # ----- 统计数据 -----
    all_dispatch = []
    for r, row in rows2026.items():
        vals = {0: row.get(0,''), 1: row.get(1,''), 5: row.get(5,''), 6: row.get(6,''),
                7: row.get(7,''), 8: row.get(8,''), 9: row.get(9,''), 10: row.get(10,''),
                11: row.get(11,''), 12: row.get(12,''), 13: row.get(13,''), 14: row.get(14,''),
                16: row.get(16,''), 17: row.get(17,'')}
        if vals[1]: 
            vals['year'] = 2026
            all_dispatch.append(vals)
    
    for r, row in rows2025.items():
        vals = {0: row.get(0,''), 1: row.get(1,''), 5: row.get(5,''), 6: row.get(6,''),
                7: row.get(7,''), 8: row.get(8,''), 9: row.get(9,''), 10: row.get(10,''),
                11: row.get(11,''), 12: row.get(12,''), 13: row.get(13,''), 14: row.get(14,''),
                15: row.get(15,''), 20: row.get(20,''), 21: row.get(21,'')}
        if vals[1]:
            vals['year'] = 2025
            all_dispatch.append(vals)
    
    for r, row in rows2024.items():
        # 2024布局: 0序号 1客户 2地址 3联系人 4电话 5产品类别 6任务来源 7单号 8服务 9产品型号 10数量
        # 11服务内容 12实施编号 13销售 14销售电话 15状态 16开始时间 17预计结束 18实际结束 19实施经理 20电话 21备注
        vals = {0: row.get(0,''), 1: row.get(1,''), 5: row.get(7,''),
                6: row.get(8,''), 7: row.get(9,''), 8: row.get(10,''), 9: row.get(11,''),
                10: row.get(12,''), 11: row.get(13,''), 12: row.get(14,''),
                13: row.get(16,''), 14: row.get(17,''), 15: row.get(15,''),
                20: row.get(5,''), 21: row.get(6,'')}
        if vals[1]:
            vals['year'] = 2024
            all_dispatch.append(vals)
    
    # ---- 统计 ----
    dispatch_total = len(all_dispatch)
    dispatch_2026 = sum(1 for d in all_dispatch if d.get('year') == 2026)
    customers = len(set(d[1] for d in all_dispatch if d[1]))
    
    # 年度趋势
    years_count = {}
    for d in all_dispatch:
        y = d.get('year')
        years_count[y] = years_count.get(y, 0) + 1
    yearly_trend = [{'year': y, 'count': years_count[y]} for y in sorted(years_count.keys())]
    
    # 2026月度
    monthly = {}
    for d in all_dispatch:
        if d.get('year') == 2026:
            sd = d.get(13, '')
            if sd and len(sd) >= 6:
                m = sd[:6]
                monthly[m] = monthly.get(m, 0) + 1
            elif d.get(14,'') and len(d.get(14,'')) >= 6:
                m = d[14][:6]
                monthly[m] = monthly.get(m, 0) + 1
    monthly_data = [{'month': m, 'count': monthly[m]} for m in sorted(monthly.keys())]
    
    # TOP10客户
    cust_count = {}
    for d in all_dispatch:
        c = d[1]
        cust_count[c] = cust_count.get(c, 0) + 1
    top10 = sorted(cust_count.items(), key=lambda x: -x[1])[:10]
    customer_top = [{'name': c, 'count': n} for c, n in top10]
    
    # 服务类型
    srv_count = {}
    for d in all_dispatch:
        s = d.get(6, '')
        if s:
            srv_count[s] = srv_count.get(s, 0) + 1
    srv_top = sorted(srv_count.items(), key=lambda x: -x[1])[:15]
    service_dist = [{'name': n, 'count': c} for n, c in srv_top]
    
    # 产品型号
    prod_count = {}
    for d in all_dispatch:
        p = d.get(7, '')
        if p:
            prod_count[p] = prod_count.get(p, 0) + 1
    prod_top = sorted(prod_count.items(), key=lambda x: -x[1])[:12]
    product_data = [{'name': n, 'count': c} for n, c in prod_top]
    
    # 销售
    sale_count = {}
    for d in all_dispatch:
        s = d.get(11, '')
        if s and s != '\\' and s != '/':
            sale_count[s] = sale_count.get(s, 0) + 1
    sale_top = sorted(sale_count.items(), key=lambda x: -x[1])[:10]
    sales_data = [{'name': n, 'count': c} for n, c in sale_top]
    
    # 状态
    status_count = {}
    for d in all_dispatch:
        if d.get('year') == 2026:
            s = d.get(13, '') or (d.get(15, ''))
            if not s: s = '未标记'
            status_count[s] = status_count.get(s, 0) + 1
    for r, row in rows_insp.items():
        s = row.get(13, '') or '未标记'
        status_count[s] = status_count.get(s, 0) + 1
    for r, row in rows_duty.items():
        s = row.get(15, '') or '未标记'
        status_count[s] = status_count.get(s, 0) + 1
    status_data = [{'name': n, 'count': status_count[n]} for n in sorted(status_count.keys(), key=lambda x: -status_count[x])]
    
    # 最近10条 (仅2026年，按开始时间倒序)
    recent_2026 = []
    for r, row in rows2026.items():
        start_d = row.get(13, '')
        if start_d and len(start_d) >= 8 and start_d.isdigit():
            recent_2026.append((start_d, r, row))
    recent_2026.sort(key=lambda x: -int(x[0]))
    
    recent = []
    for _, r, row in recent_2026[:10]:
        recent.append({
            'customer': row.get(1,''), 'order': row.get(5,''), 'service': row.get(6,''),
            'model': row.get(7,''), 'date': row.get(13,''), 'sales': row.get(11,'')
        })
    
    return {
        'stats': {
            'grand_total': dispatch_total + len(rows_insp) + len(rows_duty) + len(rows_ms),
            'dispatch_total': dispatch_total,
            'dispatch_2026': dispatch_2026,
            'customers': customers,
            'inspection': len(rows_insp),
            'duty': len(rows_duty),
            'settlement': len(rows_ms),
        },
        'yearly_trend': yearly_trend,
        'monthly_2026': monthly_data,
        'customer_top': customer_top,
        'service_dist': service_dist,
        'product_data': product_data,
        'sales_data': sales_data,
        'status_data': status_data,
        'recent': recent,
    }


def generate_html(data):
    """生成看板HTML"""
    s = data['stats']
    recent_html = ''
    for r in data['recent']:
        recent_html += f'<tr><td><b>{r["customer"]}</b></td><td>{r["service"] or "-"}</td><td>{r["model"] or "-"}</td><td>{r["date"] or "-"}</td><td>{r["sales"] or "-"}</td></tr>'
    
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SV派单管理系统 - 数据看板</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f2f5;color:#333;padding:0}}
.header{{background:linear-gradient(135deg,#1a73e8,#0d47a1);color:#fff;padding:24px 30px}}
.header h1{{font-size:26px;margin-bottom:4px}}
.header p{{opacity:.85;font-size:14px}}
.header .ts{{font-size:12px;opacity:.6;margin-top:6px}}
.container{{max-width:1400px;margin:0 auto;padding:20px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:20px}}
.sc{{background:#fff;border-radius:12px;padding:16px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.06)}}
.sc .n{{font-size:28px;font-weight:700;color:#1a73e8}}
.sc .l{{font-size:12px;color:#666;margin-top:4px}}
.sc.gn .n{{color:#27ae60}}.sc.or .n{{color:#e67e22}}.sc.pu .n{{color:#8e44ad}}.sc.te .n{{color:#1abc9c}}.sc.rd .n{{color:#e74c3c}}
.g2{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}}
.g3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px}}
.card{{background:#fff;border-radius:12px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,.06)}}
.card h3{{font-size:14px;margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid #f0f2f5}}
.card canvas{{max-height:260px;width:100%}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{background:#f8f9fa;padding:8px 10px;text-align:left;font-weight:600;color:#555;border-bottom:2px solid #e9ecef}}
td{{padding:6px 10px;border-bottom:1px solid #f0f2f5;font-size:12px}}
tr:hover{{background:#f8f9ff}}
@media(max-width:768px){{.g2,.g3{{grid-template-columns:1fr}}.stats{{grid-template-columns:repeat(2,1fr)}}}}
</style>
</head>
<body>
<div class="header">
  <h1>SV派单管理系统</h1>
  <p>数据看板 · 自动从金山文档同步</p>
  <div class="ts" id="ts"></div>
</div>
<div class="container">
  <div class="stats">
    <div class="sc"><div class="n">{s["grand_total"]}</div><div class="l">总记录数</div></div>
    <div class="sc"><div class="n">{s["dispatch_total"]}</div><div class="l">派单记录</div><div style="font-size:11px;color:#999">2026年: {s["dispatch_2026"]}</div></div>
    <div class="sc gn"><div class="n">{s["customers"]}</div><div class="l">合作客户</div></div>
    <div class="sc or"><div class="n">{s["inspection"]}</div><div class="l">巡检任务</div></div>
    <div class="sc pu"><div class="n">{s["duty"]}</div><div class="l">值守任务</div></div>
    <div class="sc te"><div class="n">{s["settlement"]}</div><div class="l">通信月结</div></div>
  </div>
  <div class="g2">
    <div class="card"><h3>年度派单趋势</h3><canvas id="c1"></canvas></div>
    <div class="card"><h3>2026年月度派单</h3><canvas id="c2"></canvas></div>
  </div>
  <div class="g3">
    <div class="card"><h3>TOP10 客户</h3><canvas id="c3"></canvas></div>
    <div class="card"><h3>服务类型分布</h3><canvas id="c4"></canvas></div>
    <div class="card"><h3>产品型号排行</h3><canvas id="c5"></canvas></div>
  </div>
  <div class="g3">
    <div class="card"><h3>销售业绩排行</h3><canvas id="c6"></canvas></div>
    <div class="card"><h3>任务状态分布</h3><canvas id="c7"></canvas></div>
    <div class="card"><h3>最近10条派单</h3>
      <table><thead><tr><th>客户</th><th>服务</th><th>型号</th><th>日期</th><th>销售</th></tr></thead>
      <tbody>{recent_html}</tbody></table>
    </div>
  </div>
</div>
<script>
var D = {json.dumps(data, ensure_ascii=False)};
var C = ['#1a73e8','#e67e22','#27ae60','#8e44ad','#e74c3c','#1abc9c','#f39c12','#2ecc71','#9b59b6','#e91e63','#00bcd4','#ff5722'];
document.getElementById('ts').textContent = '更新于: '+new Date().toLocaleString('zh-CN',{{timeZone:'Asia/Shanghai'}});
function ci(id,t,lbs,vals,bg){{new Chart(document.getElementById(id),{{type:t,data:{{labels:lbs,datasets:[{{data:vals,backgroundColor:bg||'rgba(26,115,232,0.7)',borderColor:'#1a73e8',borderWidth:t==='line'?2:0,borderRadius:4,tension:.3}}]}},options:{{responsive:true,plugins:{{legend:{{display:t==='doughnut'}}}},scales:{{y:{{beginAtZero:true,grid:{{color:'#eee'}}}},x:{{grid:{{display:false}}}}}}}}}})}}
ci('c1','bar',D.yearly_trend.map(function(i){{return i.year}}),D.yearly_trend.map(function(i){{return i.count}}));
ci('c2','line',D.monthly_2026.map(function(i){{return (i.month||'').slice(-2)+'月'}}),D.monthly_2026.map(function(i){{return i.count}}));
ci('c3','bar',D.customer_top.map(function(i){{return i.name.length>5?i.name.slice(0,5)+'..':i.name}}),D.customer_top.map(function(i){{return i.count}}),C);
ci('c4','doughnut',D.service_dist.map(function(i){{return i.name}}),D.service_dist.map(function(i){{return i.count}}),C);
ci('c5','bar',D.product_data.map(function(i){{return i.name.length>8?i.name.slice(0,8)+'..':i.name}}),D.product_data.map(function(i){{return i.count}}),C);
ci('c6','bar',D.sales_data.map(function(i){{return i.name}}),D.sales_data.map(function(i){{return i.count}}),C);
ci('c7','doughnut',D.status_data.map(function(i){{return i.name}}),D.status_data.map(function(i){{return i.count}}),C);
</script>
</body>
</html>'''


def main():
    print("=" * 50)
    print("SV派单看板生成器")
    print("=" * 50)
    
    print("读取数据中...")
    data = read_all_sheets()
    
    print("生成HTML...")
    html = generate_html(data)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, 'index.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    size = os.path.getsize(output_path)
    print(f"✅ 看板已生成: {output_path} ({size/1024:.1f} KB)")
    print(f"   总记录: {data['stats']['grand_total']}")
    print(f"   派单: {data['stats']['dispatch_total']} | 巡检: {data['stats']['inspection']} | 值守: {data['stats']['duty']} | 月结: {data['stats']['settlement']}")


if __name__ == '__main__':
    main()
