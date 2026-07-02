#!/usr/bin/env python3
"""生成静态数据看板HTML"""
import sqlite3, json, os

DB_PATH = '/workspace/sv_dispatch.db'
OUTPUT = '/workspace/dashboard.html'

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

def q(sql, params=None):
    c = conn.cursor()
    if params: c.execute(sql, params)
    else: c.execute(sql)
    return [dict(r) for r in c.fetchall()]

stats = {
    'grand_total': q("SELECT COUNT(*)+COUNT(*)+COUNT(*)+COUNT(*) as c FROM dispatch_orders, inspection_tasks, duty_tasks, monthly_settlements LIMIT 1")[0]['c'],
    'dispatch_total': q("SELECT COUNT(*) as c FROM dispatch_orders")[0]['c'],
    'customers': q("SELECT COUNT(DISTINCT customer_name) as c FROM dispatch_orders")[0]['c'],
    'inspection': q("SELECT COUNT(*) as c FROM inspection_tasks")[0]['c'],
    'duty': q("SELECT COUNT(*) as c FROM duty_tasks")[0]['c'],
    'settlement': q("SELECT COUNT(*) as c FROM monthly_settlements")[0]['c'],
}
yearly_trend = q("SELECT year, COUNT(*) as count FROM dispatch_orders WHERE year>=2024 GROUP BY year ORDER BY year")
monthly_2026 = q("SELECT substr(start_date,1,6) as month, COUNT(*) as count FROM dispatch_orders WHERE year=2026 AND start_date IS NOT NULL AND start_date!='' GROUP BY month ORDER BY month")
customer_top = q("SELECT customer_name,COUNT(*) as count,SUM(COALESCE(quantity,0)) as total_qty FROM dispatch_orders GROUP BY customer_name ORDER BY count DESC LIMIT 10")
service_dist = q("SELECT service_type,COUNT(*) as count FROM dispatch_orders WHERE service_type IS NOT NULL AND service_type!='' GROUP BY service_type ORDER BY count DESC LIMIT 15")
sales_rank = q("SELECT sales_person,COUNT(*) as count FROM dispatch_orders WHERE sales_person IS NOT NULL AND sales_person!='' GROUP BY sales_person ORDER BY count DESC LIMIT 10")
product_model = q("SELECT product_model,COUNT(*) as count,SUM(COALESCE(quantity,0)) as total_qty FROM dispatch_orders WHERE product_model IS NOT NULL AND product_model!='' GROUP BY product_model ORDER BY count DESC LIMIT 15")
status_data = q("""SELECT COALESCE(NULLIF(status,''),'未标记') as status,COUNT(*) as count FROM(
    SELECT status FROM dispatch_orders WHERE year=2026
    UNION ALL SELECT status FROM inspection_tasks
    UNION ALL SELECT status FROM duty_tasks
) WHERE status IS NOT NULL GROUP BY status ORDER BY count DESC""")
recent = q("SELECT customer_name,order_no,service_type,product_model,start_date,sales_person FROM dispatch_orders WHERE year=2026 ORDER BY rowid DESC LIMIT 10")

conn.close()

data = {
    'yearly_trend': yearly_trend,
    'monthly_2026': monthly_2026,
    'customer_top': customer_top,
    'service_dist': service_dist,
    'sales_rank': sales_rank,
    'product_model': product_model,
    'status_data': status_data,
    'recent': recent,
}

recent_html = ''
for r in recent:
    recent_html += f'<tr><td><strong>{r["customer_name"]}</strong></td><td>{r["service_type"] or "-"}</td><td>{r["product_model"] or "-"}</td><td>{r["start_date"] or "-"}</td><td>{r["sales_person"] or "-"}</td></tr>'

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SV派单管理系统 - 数据看板</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f2f5;color:#333}}
.header{{background:linear-gradient(135deg,#1a73e8,#0d47a1);color:white;padding:20px 30px}}
.header h1{{font-size:24px;margin-bottom:4px}}
.header p{{opacity:.85;font-size:14px}}
.container{{max-width:1400px;margin:0 auto;padding:20px}}
.stats-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:20px}}
.stat-card{{background:white;border-radius:12px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,.06);text-align:center}}
.stat-card .num{{font-size:28px;font-weight:700;color:#1a73e8}}
.stat-card .label{{font-size:12px;color:#666;margin-top:4px}}
.stat-card.green .num{{color:#27ae60}}
.stat-card.orange .num{{color:#e67e22}}
.stat-card.purple .num{{color:#8e44ad}}
.stat-card.teal .num{{color:#1abc9c}}
.grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}}
.grid-3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px}}
.card{{background:white;border-radius:12px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,.06)}}
.card h3{{font-size:14px;margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid #f0f2f5}}
.card canvas{{max-height:260px;max-width:100%}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{background:#f8f9fa;padding:8px 10px;text-align:left;font-weight:600;color:#555;border-bottom:2px solid #e9ecef}}
td{{padding:6px 10px;border-bottom:1px solid #f0f2f5}}
tr:hover{{background:#f8f9ff}}
@media(max-width:768px){{.grid-2,.grid-3{{grid-template-columns:1fr}}.stats-row{{grid-template-columns:repeat(2,1fr)}}}}
</style>
</head>
<body>
<div class="header"><h1>SV派单管理系统</h1><p>数据看板</p></div>
<div class="container">
  <div class="stats-row">
    <div class="stat-card"><div class="num">{stats["grand_total"]}</div><div class="label">总记录数</div></div>
    <div class="stat-card"><div class="num">{stats["dispatch_total"]}</div><div class="label">派单记录</div></div>
    <div class="stat-card green"><div class="num">{stats["customers"]}</div><div class="label">合作客户</div></div>
    <div class="stat-card orange"><div class="num">{stats["inspection"]}</div><div class="label">巡检任务</div></div>
    <div class="stat-card purple"><div class="num">{stats["duty"]}</div><div class="label">值守任务</div></div>
    <div class="stat-card teal"><div class="num">{stats["settlement"]}</div><div class="label">通信月结</div></div>
  </div>
  <div class="grid-2">
    <div class="card"><h3>年度派单趋势</h3><canvas id="c1"></canvas></div>
    <div class="card"><h3>2026年月度派单</h3><canvas id="c2"></canvas></div>
  </div>
  <div class="grid-3">
    <div class="card"><h3>TOP10客户</h3><canvas id="c3"></canvas></div>
    <div class="card"><h3>服务类型分布</h3><canvas id="c4"></canvas></div>
    <div class="card"><h3>产品型号排行</h3><canvas id="c5"></canvas></div>
  </div>
  <div class="grid-3">
    <div class="card"><h3>销售业绩排行</h3><canvas id="c6"></canvas></div>
    <div class="card"><h3>任务状态分布</h3><canvas id="c7"></canvas></div>
    <div class="card"><h3>最近派单</h3>
      <table><thead><tr><th>客户</th><th>服务</th><th>型号</th><th>日期</th><th>销售</th></tr></thead>
      <tbody>{recent_html}</tbody></table>
    </div>
  </div>
</div>
<script>
var DATA = {json.dumps(data, ensure_ascii=False)};

var colors = ['#1a73e8','#e67e22','#27ae60','#8e44ad','#e74c3c','#1abc9c','#f39c12','#2ecc71','#9b59b6','#e91e63','#00bcd4','#ff5722','#7cb342','#5c6bc0','#26a69a'];

function chart(id, type, labels, vals, bg) {{
  new Chart(document.getElementById(id), {{
    type: type,
    data: {{labels: labels, datasets: [{{data: vals, backgroundColor: bg || 'rgba(26,115,232,0.6)', borderColor: '#1a73e8', borderWidth: type==='line'?2:0, borderRadius: 4, tension: 0.3}}]}},
    options: {{responsive: true, maintainAspectRatio: true, plugins: {{legend: {{display: type==='doughnut'}}}}, scales: {{y: {{beginAtZero: true, grid: {{color: '#f0f0f0'}}}}, x: {{grid: {{display: false}}}}}}}}
  }});
}}

chart('c1','bar', DATA.yearly_trend.map(function(i){{return i.year}}), DATA.yearly_trend.map(function(i){{return i.count}}));
chart('c2','line', DATA.monthly_2026.map(function(i){{return (i.month||'').slice(4)+'月'}}), DATA.monthly_2026.map(function(i){{return i.count}}));
chart('c3','bar', DATA.customer_top.map(function(i){{return i.customer_name.length>6?i.customer_name.slice(0,6)+'..':i.customer_name}}), DATA.customer_top.map(function(i){{return i.count}}), colors.slice(0,10));
chart('c4','doughnut', DATA.service_dist.map(function(i){{return i.service_type}}), DATA.service_dist.map(function(i){{return i.count}}), colors);
chart('c5','bar', DATA.product_model.map(function(i){{return (i.product_model||'').length>10?(i.product_model||'').slice(0,10)+'..':i.product_model||''}}), DATA.product_model.map(function(i){{return i.count}}), colors);
chart('c6','bar', DATA.sales_rank.map(function(i){{return i.sales_person}}), DATA.sales_rank.map(function(i){{return i.count}}), colors);
chart('c7','doughnut', DATA.status_data.map(function(i){{return i.status}}), DATA.status_data.map(function(i){{return i.count}}), colors);
</script>
</body>
</html>'''

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(html)

size = os.path.getsize(OUTPUT)
print(f"✅ 静态看板已生成: {OUTPUT} ({size/1024:.1f} KB)")
