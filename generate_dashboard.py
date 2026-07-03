#!/usr/bin/env python3
"""
SV派单看板自动生成脚本 v3
- 统计数据内嵌 index.html（~15KB）
- 明细数据拆到 records.json（异步加载）
- 修复搜索递归 bug
- 加防抖 + 分页优化
"""
import json, subprocess, os, sys

FILE_ID = 'nZL1azhGc1MphojViCR2rxeDwtT16Wmce'
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')

def kdocs(params):
    env = {**os.environ, 'PATH': os.environ.get('PATH','') + ':' + os.path.expanduser('~/.local/bin')}
    r = subprocess.run(['kdocs-cli','sheet','get-range-data',json.dumps(params)], capture_output=True, text=True, env=env)
    if r.returncode != 0: return []
    try:
        d = json.loads(r.stdout)
        return d['data']['detail']['rangeData'] if d.get('code')==0 else []
    except: return []

def read_sheet(ws_id, max_row, cols):
    cells = []
    for s in range(1, max_row+1, 200):
        e = min(s+199, max_row)
        cs = kdocs({'file_id':FILE_ID,'worksheet_id':ws_id,'range':{'rowFrom':s,'rowTo':e,'colFrom':0,'colTo':cols-1}})
        if not cs: break
        cells.extend(cs)
        if not any(c.get('cellText','') for c in cs): break
    return cells

def to_rows(cells):
    rows = {}
    for c in cells:
        r = c['rowFrom']
        if r not in rows: rows[r] = {}
        rows[r][c['colFrom']] = c.get('cellText','').strip()
    return rows

def normalize_records(rows, year, layout):
    records = []
    for r, row in rows.items():
        vals = {}
        for std_key, col_idx in layout.items():
            vals[std_key] = row.get(col_idx, '')
        if not vals.get('customer', ''): continue
        vals['year'] = year
        records.append(vals)
    return records

def read_all_data():
    print("读取数据中...")
    rows26 = to_rows(read_sheet(27, 1000, 18))
    rows25 = to_rows(read_sheet(25, 1500, 22))
    rows24 = to_rows(read_sheet(1, 600, 22))
    rows_insp = to_rows(read_sheet(28, 200, 17))
    rows_duty = to_rows(read_sheet(15, 300, 23))
    rows_ms = to_rows(read_sheet(18, 500, 19))
    print(f"  2026:{len(rows26)} 2025:{len(rows25)} 2024:{len(rows24)} 巡检:{len(rows_insp)} 值守:{len(rows_duty)} 月结:{len(rows_ms)}")

    layout26 = {'serial':0,'customer':1,'address':2,'contact':3,'phone':4,'order_no':5,'service':6,
               'product':7,'qty':8,'content':9,'impl_no':10,'sales':11,'sales_phone':12,
               'start_date':13,'end_date':14,'remark':15,'pcat':16,'source':17}
    layout25 = {'serial':0,'customer':1,'address':2,'contact':3,'phone':4,'order_no':5,'service':6,
               'product':7,'qty':8,'content':9,'impl_no':10,'sales':11,'sales_phone':12,
               'status':13,'start_date':14,'end_date':15,'actual_end':16,'mgr':17,'mgr_phone':18,
               'remark':19,'pcat':20,'source':21}
    layout24 = {'serial':0,'customer':1,'address':2,'contact':3,'phone':4,
               'pcat':5,'source':6,'order_no':7,'service':8,'product':9,'qty':10,
               'content':11,'impl_no':12,'sales':13,'sales_phone':14,
               'status':15,'start_date':16,'end_date':17,'actual_end':18,'mgr':19,'mgr_phone':20,'remark':21}

    all_dispatch = normalize_records(rows26, 2026, layout26)
    all_dispatch += normalize_records(rows25, 2025, layout25)
    all_dispatch += normalize_records(rows24, 2024, layout24)

    insp = []
    for r, row in rows_insp.items():
        if not row.get(1,''): continue
        insp.append({'t':'巡检','y':0,'c':row.get(1,''),'a':row.get(2,'')[:30],
                    'ct':row.get(3,''),'ph':row.get(4,''),'o':row.get(5,''),'sv':row.get(6,''),
                    'pm':row.get(7,''),'q':row.get(8,''),'cn':row.get(9,'')[:40],'in':row.get(10,''),
                    'sl':row.get(11,''),'sd':row.get(14,''),'ed':row.get(15,''),'st':row.get(13,''),'rm':row.get(16,'')[:30]})
    duty = []
    for r, row in rows_duty.items():
        if not row.get(1,''): continue
        duty.append({'t':'值守','y':0,'c':row.get(1,''),'a':row.get(2,'')[:30],
                    'ct':row.get(3,''),'ph':row.get(4,''),'o':row.get(7,''),'sv':row.get(8,''),
                    'pm':row.get(9,''),'q':row.get(10,''),'cn':row.get(11,'')[:40],'in':row.get(12,''),
                    'sl':row.get(13,''),'sd':row.get(16,''),'ed':row.get(17,''),'st':row.get(15,''),'rm':row.get(21,'')[:30]})
    ms = []
    for r, row in rows_ms.items():
        if not row.get(6,''): continue
        ms.append({'t':'月结','y':0,'c':row.get(6,''),'a':row.get(9,'')[:30],
                   'ct':'','ph':'','o':row.get(1,''),'sv':row.get(13,''),'pm':row.get(10,''),
                   'q':row.get(12,''),'cn':row.get(11,'')[:40],'in':'','sl':row.get(5,''),
                   'sd':row.get(2,''),'ed':'','st':'','rm':row.get(18,'')[:30]})

    # 统计数据（只嵌入这部分到HTML，体积小）
    total_disp = len(all_dispatch)
    customers = len(set(d['customer'] for d in all_dispatch))
    disp2026 = sum(1 for d in all_dispatch if d.get('year')==2026)
    yc = {}
    for d in all_dispatch: yc[d['year']] = yc.get(d['year'],0)+1
    yearly = [{'year':y,'count':yc[y]} for y in sorted(yc)]
    mc = {}
    for d in all_dispatch:
        if d.get('year')==2026:
            sd = d.get('start_date','')
            if sd and len(sd)>=6: mc[sd[:6]] = mc.get(sd[:6],0)+1
    monthly = [{'month':m,'count':mc[m]} for m in sorted(mc)]
    cc = {}
    for d in all_dispatch: cc[d['customer']] = cc.get(d['customer'],0)+1
    ctop = [{'name':n,'count':c} for n,c in sorted(cc.items(),key=lambda x:-x[1])[:10]]
    sc = {}
    for d in all_dispatch:
        s = d.get('service','')
        if s: sc[s] = sc.get(s,0)+1
    srv = [{'name':n,'count':c} for n,c in sorted(sc.items(),key=lambda x:-x[1])[:15]]
    pc = {}
    for d in all_dispatch:
        p = d.get('product','')
        if p: pc[p] = pc.get(p,0)+1
    prod = [{'name':n,'count':c} for n,c in sorted(pc.items(),key=lambda x:-x[1])[:12]]
    sl = {}
    for d in all_dispatch:
        s = d.get('sales','')
        if s and s != '\\': sl[s] = sl.get(s,0)+1
    sales = [{'name':n,'count':c} for n,c in sorted(sl.items(),key=lambda x:-x[1])[:10]]
    st = {}
    for d in all_dispatch:
        if d.get('year')==2026:
            s = d.get('status','') or '未标记'
            st[s] = st.get(s,0)+1
    for d in insp: st[d.get('st','') or '未标记'] = st.get(d.get('st','') or '未标记',0)+1
    for d in duty: st[d.get('st','') or '未标记'] = st.get(d.get('st','') or '未标记',0)+1
    status = [{'name':n,'count':c} for n,c in sorted(st.items(),key=lambda x:-x[1])]
    recent = []
    for d in all_dispatch:
        if d.get('year')==2026:
            recent.append({'customer':d['customer'],'order':d.get('order_no',''),'service':d.get('service',''),
                         'model':d.get('product',''),'date':d.get('start_date',''),'sales':d.get('sales','')})
            if len(recent)>=10: break

    # 明细记录（拆到 records.json）
    all_records = []
    for d in all_dispatch:
        all_records.append({'t':'派单','y':d.get('year',0),'c':d['customer'],'a':d.get('address','')[:30],
            'ct':d.get('contact',''),'ph':d.get('phone',''),'o':d.get('order_no',''),'sv':d.get('service',''),
            'pm':d.get('product',''),'q':d.get('qty',''),'cn':d.get('content','')[:40],'in':d.get('impl_no',''),
            'sl':d.get('sales',''),'sd':d.get('start_date',''),'ed':d.get('end_date',''),'st':d.get('status',''),
            'rm':d.get('remark','')[:30],'pc':d.get('pcat',''),'sr':d.get('source','')})
    all_records.extend(insp)
    all_records.extend(duty)
    all_records.extend(ms)

    # 按开始日期倒序，最新在前
    all_records.sort(key=lambda r: r.get('sd',''), reverse=True)

    # 返回两部分：统计（嵌入HTML）+ 明细（单独JSON）
    stats = {
        'stats':{'grand_total':total_disp+len(insp)+len(duty)+len(ms),
                 'dispatch_total':total_disp,'dispatch_2026':disp2026,'customers':customers,
                 'inspection':len(insp),'duty':len(duty),'settlement':len(ms)},
        'yearly':yearly,'monthly':monthly,'ctop':ctop,'srv':srv,'prod':prod,
        'sales':sales,'status':status,'recent':recent
    }
    return stats, all_records


def generate_html(stats):
    s = stats['stats']
    recent_rows = ''.join(
        f'<tr><td><b>{r["customer"]}</b></td><td>{r["service"] or "-"}</td><td>{r["model"] or "-"}</td><td>{r["date"] or "-"}</td><td>{r["sales"] or "-"}</td></tr>'
        for r in stats['recent']
    )
    stats_json = json.dumps(stats, ensure_ascii=False)

    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SV派单管理系统 - 数据看板</title>
<script src="https://lib.baomitu.com/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f2f5;color:#333}
#pwGate{position:fixed;top:0;left:0;width:100%;height:100%;background:#1a73e8;display:flex;align-items:center;justify-content:center;z-index:9999}
#pwGate>div{background:#fff;padding:36px;border-radius:16px;text-align:center;box-shadow:0 4px 24px rgba(0,0,0,.3);max-width:360px;width:90%}
#pwGate h2{font-size:20px;margin-bottom:6px}#pwGate p{color:#999;font-size:13px;margin-bottom:16px}
#pwGate input{padding:10px;border:2px solid #ddd;border-radius:8px;font-size:15px;width:100%;text-align:center;outline:none}
#pwGate input:focus{border-color:#1a73e8}
#pwGate button{margin-top:12px;padding:10px 30px;background:#1a73e8;color:#fff;border:none;border-radius:8px;font-size:14px;cursor:pointer}
#pwGate .err{color:#e74c3c;font-size:12px;margin-top:8px;display:none}
.header{background:linear-gradient(135deg,#1a73e8,#0d47a1);color:#fff;padding:20px 30px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}
.header h1{font-size:24px}.header p{opacity:.85;font-size:13px}
.nav-tabs{display:flex;gap:4px}
.nav-btn{padding:10px 22px;border:none;background:rgba(255,255,255,.15);color:#fff;border-radius:8px 8px 0 0;cursor:pointer;font-size:14px;font-weight:500;transition:all .2s}
.nav-btn.active{background:#fff;color:#1a73e8;font-weight:700}
.nav-btn:hover:not(.active){background:rgba(255,255,255,.25)}
.container{max-width:1400px;margin:0 auto;padding:20px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:18px}
.sc{background:#fff;border-radius:12px;padding:14px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.sc .n{font-size:26px;font-weight:700;color:#1a73e8}.sc .l{font-size:11px;color:#666;margin-top:3px}
.sc.gn .n{color:#27ae60}.sc.or .n{color:#e67e22}.sc.pu .n{color:#8e44ad}.sc.te .n{color:#1abc9c}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px}
.card{background:#fff;border-radius:12px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.card h3{font-size:14px;margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid #f0f2f5}
.card canvas{max-height:250px;width:100%}
table{width:100%;border-collapse:collapse;font-size:12px}
th{background:#f8f9fa;padding:7px 8px;text-align:left;font-weight:600;color:#555;border-bottom:2px solid #e9ecef;white-space:nowrap}
td{padding:5px 8px;border-bottom:1px solid #f0f2f5;font-size:11px;max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
tr:hover{background:#f8f9ff}
.toolbar{display:flex;gap:10px;margin-bottom:14px;align-items:center;flex-wrap:wrap}
.toolbar select,.toolbar input{padding:8px 12px;border:1px solid #ddd;border-radius:8px;font-size:13px;outline:none}
.toolbar input{flex:1;min-width:200px}.toolbar input:focus{border-color:#1a73e8}
.toolbar .info{font-size:12px;color:#999}
.pagination{display:flex;justify-content:center;gap:4px;margin-top:14px;flex-wrap:wrap}
.pagination button{padding:5px 10px;border:1px solid #ddd;border-radius:6px;background:#fff;cursor:pointer;font-size:12px}
.pagination button:hover{background:#f0f2f5}
.pagination button.active{background:#1a73e8;color:#fff;border-color:#1a73e8}
.pagination button:disabled{opacity:.4;cursor:default}
.type-badge{display:inline-block;padding:2px 6px;border-radius:4px;font-size:10px;color:#fff;font-weight:600}
.type-p{background:#1a73e8}.type-i{background:#27ae60}.type-d{background:#8e44ad}.type-m{background:#1abc9c}
.loading{text-align:center;padding:40px;color:#999;font-size:14px}
@media(max-width:768px){.g2,.g3{grid-template-columns:1fr}.stats{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>
<div id="pwGate">
  <div>
    <h2>🔒 SV派单管理系统</h2>
    <p>请输入访问密码</p>
    <input type="password" id="pwInput" placeholder="输入密码..." onkeydown="if(event.key==='Enter')checkPw()">
    <br><button onclick="checkPw()">进入系统</button>
    <div class="err" id="pwErr">密码错误</div>
  </div>
</div>
<div id="mainApp" style="display:none">



<div class="header">
  <div><h1>📊 SV派单管理系统</h1><p>数据看板 · 自动同步</p></div>
  <div class="nav-tabs">
    <button class="nav-btn active" onclick="switchTab('overview',this)">📈 数据概览</button>
    <button class="nav-btn" onclick="switchTab('detail',this)">📋 数据明细</button>
  </div>
</div>
<div class="container">
<div id="tabOverview">
  <div class="stats">
    <div class="sc"><div class="n">''' + str(s['grand_total']) + '''</div><div class="l">总记录数</div></div>
    <div class="sc"><div class="n">''' + str(s['dispatch_total']) + '''</div><div class="l">派单记录</div></div>
    <div class="sc gn"><div class="n">''' + str(s['customers']) + '''</div><div class="l">合作客户</div></div>
    <div class="sc or"><div class="n">''' + str(s['inspection']) + '''</div><div class="l">巡检任务</div></div>
    <div class="sc pu"><div class="n">''' + str(s['duty']) + '''</div><div class="l">值守任务</div></div>
    <div class="sc te"><div class="n">''' + str(s['settlement']) + '''</div><div class="l">通信月结</div></div>
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
      <tbody>''' + recent_rows + '''</tbody></table>
    </div>
  </div>
</div>

<div id="tabDetail" style="display:none">
  <div class="card">
    <div class="toolbar">
      <select id="filterYear" onchange="doFilter()">
        <option value="all">全部年份</option>
        <option value="2026" selected>2026年</option>
        <option value="2025">2025年</option>
        <option value="2024">2024年</option>
      </select>
      <select id="filterType" onchange="doFilter()">
        <option value="all">全部类型</option>
        <option value="派单">派单</option>
        <option value="巡检">巡检</option>
        <option value="值守">值守</option>
        <option value="月结">通信月结</option>
      </select>
      <input type="text" id="searchInput" placeholder="搜索：客户/单号/产品/服务/销售..." oninput="debounceSearch()">
      <span class="info" id="recordInfo"></span>
      <button onclick="openForm()" style="margin-left:auto;padding:8px 18px;background:#1a73e8;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:13px">＋ 新增记录</button>
    </div>
    <div style="overflow-x:auto" id="tableContainer"><div class="loading">加载数据中...</div></div>
    <div class="pagination" id="pagination"></div>
  </div>
</div>
</div>

<!-- 新增/编辑弹窗 -->
<div id="editModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:1000;overflow-y:auto">
<div style="background:#fff;max-width:700px;margin:30px auto;border-radius:12px;padding:24px;box-shadow:0 8px 32px rgba(0,0,0,0.2)">
<h3 id="modalTitle" style="margin-bottom:16px;font-size:16px">新增记录</h3>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
<div><label style="font-size:12px;color:#666">客户名称 *</label><input id="ef_customer" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;font-size:13px"></div>
<div><label style="font-size:12px;color:#666">单号</label><input id="ef_order_no" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;font-size:13px"></div>
<div><label style="font-size:12px;color:#666">联系人</label><input id="ef_contact" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;font-size:13px"></div>
<div><label style="font-size:12px;color:#666">电话</label><input id="ef_phone" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;font-size:13px"></div>
<div><label style="font-size:12px;color:#666">地址</label><input id="ef_address" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;font-size:13px"></div>
<div><label style="font-size:12px;color:#666">服务类型</label><input id="ef_service" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;font-size:13px"></div>
<div><label style="font-size:12px;color:#666">产品型号</label><input id="ef_product" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;font-size:13px"></div>
<div><label style="font-size:12px;color:#666">数量</label><input id="ef_qty" type="number" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;font-size:13px"></div>
<div><label style="font-size:12px;color:#666">服务内容</label><input id="ef_content" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;font-size:13px"></div>
<div><label style="font-size:12px;color:#666">销售</label><input id="ef_sales" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;font-size:13px"></div>
<div><label style="font-size:12px;color:#666">开始日期</label><input id="ef_start_date" placeholder="20260701" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;font-size:13px"></div>
<div><label style="font-size:12px;color:#666">备注</label><input id="ef_remark" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;font-size:13px"></div>
</div>
<input type="hidden" id="ef_edit_idx" value="">
<div style="margin-top:16px;display:flex;gap:10px;justify-content:flex-end">
  <button onclick="closeForm()" style="padding:8px 20px;border:1px solid #ddd;border-radius:6px;background:#fff;cursor:pointer;font-size:13px">取消</button>
  <button onclick="submitForm()" style="padding:8px 20px;background:#1a73e8;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;font-weight:600">提交到 GitHub Issue</button>
</div>
<div id="formMsg" style="margin-top:10px;font-size:12px;color:#666"></div>
</div>
</div>

<script>
// 密码验证
var PW='SV2026';
function checkPw(){
  try{
    var v=document.getElementById('pwInput').value;
    if(v===PW){
      document.getElementById('pwGate').style.display='none';
      document.getElementById('mainApp').style.display='block';
      setTimeout(initCharts,200);
    }else{
      var err=document.getElementById('pwErr');
      err.style.display='block';
      err.textContent='密码错误';
    }
  }catch(e){
    alert('错误: '+e.message);
  }
}

// 统计数据（内嵌，体积小）
var S = ''' + stats_json + ''';
var C=['#1a73e8','#e67e22','#27ae60','#8e44ad','#e74c3c','#1abc9c','#f39c12','#2ecc71','#9b59b6','#e91e63','#00bcd4','#ff5722'];

// 图表初始化（密码验证通过后才调用）
var chartsInited=false;
function ci(id,t,lbs,vals,bg){try{new Chart(document.getElementById(id),{type:t,data:{labels:lbs,datasets:[{data:vals,backgroundColor:bg||'rgba(26,115,232,0.7)',borderColor:'#1a73e8',borderWidth:t==='line'?2:0,borderRadius:4,tension:.3}]},options:{responsive:true,plugins:{legend:{display:t==='doughnut'}},scales:{y:{beginAtZero:true,grid:{color:'#eee'}},x:{grid:{display:false}}}}})}catch(e){console.log('Chart error:',id,e)}}
function initCharts(){
  if(chartsInited) return; chartsInited=true;
  ci('c1','bar',S.yearly.map(function(i){return i.year}),S.yearly.map(function(i){return i.count}));
  ci('c2','line',S.monthly.map(function(i){return(i.month||'').slice(-2)+'月'}),S.monthly.map(function(i){return i.count}));
  ci('c3','bar',S.ctop.map(function(i){return i.name.length>5?i.name.slice(0,5)+'..':i.name}),S.ctop.map(function(i){return i.count}),C);
  ci('c4','doughnut',S.srv.map(function(i){return i.name}),S.srv.map(function(i){return i.count}),C);
  ci('c5','bar',S.prod.map(function(i){return i.name.length>8?i.name.slice(0,8)+'..':i.name}),S.prod.map(function(i){return i.count}),C);
  ci('c6','bar',S.sales.map(function(i){return i.name}),S.sales.map(function(i){return i.count}),C);
  ci('c7','doughnut',S.status.map(function(i){return i.name}),S.status.map(function(i){return i.count}),C);
}

// 明细数据（异步加载）
var RECORDS=null, filtered=[], PER_PAGE=50, currentPage=1, searchTimer=null;

function switchTab(tab,btn){
  document.querySelectorAll('.nav-btn').forEach(function(b){b.classList.remove('active')});
  btn.classList.add('active');
  document.getElementById('tabOverview').style.display=tab==='overview'?'block':'none';
  document.getElementById('tabDetail').style.display=tab==='detail'?'block':'none';
  if(tab==='detail' && !RECORDS) loadRecords();
}

function loadRecords(){
  fetch('records.json')
    .then(function(r){return r.json()})
    .then(function(data){
      RECORDS=data;
      doFilter();
    })
    .catch(function(e){
      document.getElementById('tableContainer').innerHTML='<div class="loading">数据加载失败: '+e.message+'</div>';
    });
}

// 防抖搜索
function debounceSearch(){
  clearTimeout(searchTimer);
  searchTimer=setTimeout(doFilter,300);
}

// 过滤数据（不调用renderTable，消除递归）
function doFilter(){
  if(!RECORDS) return;
  var year=document.getElementById('filterYear').value;
  var type=document.getElementById('filterType').value;
  var kw=(document.getElementById('searchInput').value||'').toLowerCase();
  filtered=RECORDS.filter(function(r){
    if(year!=='all'&&r.y!=parseInt(year))return false;
    if(type!=='all'&&r.t!==type)return false;
    if(!kw)return true;
    return (r.c||'').toLowerCase().indexOf(kw)>=0||(r.o||'').toLowerCase().indexOf(kw)>=0
        ||(r.pm||'').toLowerCase().indexOf(kw)>=0||(r.sv||'').toLowerCase().indexOf(kw)>=0
        ||(r.sl||'').toLowerCase().indexOf(kw)>=0||(r.ct||'').toLowerCase().indexOf(kw)>=0;
  });
  currentPage=1;
  renderTable();
}

// 渲染表格（不调用doFilter，消除递归）
function renderTable(){
  var total=filtered.length;
  var pages=Math.ceil(total/PER_PAGE)||1;
  if(currentPage>pages)currentPage=pages;
  var start=(currentPage-1)*PER_PAGE;
  var page=filtered.slice(start,start+PER_PAGE);
  document.getElementById('recordInfo').textContent='共 '+total+' 条，第 '+(start+1)+'-'+Math.min(start+PER_PAGE,total)+' 条';

  var th=['类型','客户','地址','联系人','电话','单号','服务','产品','数量','内容','实施编号','销售','开始','结束','状态','备注',''];
  var h='<table><thead><tr>';
  th.forEach(function(t){h+='<th>'+t+'</th>'});
  h+='</tr></thead><tbody>';
  page.forEach(function(r,idx){
    var tc=r.t==='派单'?'type-p':r.t==='巡检'?'type-i':r.t==='值守'?'type-d':'type-m';
    var gIdx=start+idx;
    h+='<tr><td><span class="type-badge '+tc+'">'+r.t+'</span></td>';
    h+='<td><b>'+(r.c||'-')+'</b></td><td>'+(r.a||'-')+'</td><td>'+(r.ct||'-')+'</td>';
    h+='<td>'+(r.ph||'-')+'</td><td style="font-size:10px">'+(r.o||'-')+'</td>';
    h+='<td>'+(r.sv||'-')+'</td><td>'+(r.pm||'-')+'</td><td>'+(r.q||'-')+'</td>';
    h+='<td>'+(r.cn||'-')+'</td><td>'+(r.in||'-')+'</td><td>'+(r.sl||'-')+'</td>';
    h+='<td>'+(r.sd||'-')+'</td><td>'+(r.ed||'-')+'</td><td>'+(r.st||'-')+'</td>';
    h+='<td style="font-size:10px">'+(r.rm||'-')+'</td>';
    h+='<td><button onclick="editRecord('+gIdx+')" style="padding:3px 8px;font-size:10px;border:1px solid #1a73e8;background:#fff;color:#1a73e8;border-radius:4px;cursor:pointer" title="编辑">✎</button></td></tr>';
  });
  h+='</tbody></table>';
  document.getElementById('tableContainer').innerHTML=h;

  // 分页：只显示当前页前后5页
  var pg='';
  var showStart=Math.max(1,currentPage-5);
  var showEnd=Math.min(pages,currentPage+5);
  pg+='<button onclick="goPage(1)" '+(currentPage<=1?'disabled':'')+'>首页</button>';
  pg+='<button onclick="goPage('+(currentPage-1)+')" '+(currentPage<=1?'disabled':'')+'>‹</button>';
  if(showStart>1) pg+='<span style="padding:5px 4px;color:#999">...</span>';
  for(var p=showStart;p<=showEnd;p++){
    pg+='<button onclick="goPage('+p+')" class="'+(p===currentPage?'active':'')+'">'+p+'</button>';
  }
  if(showEnd<pages) pg+='<span style="padding:5px 4px;color:#999">...</span>';
  pg+='<button onclick="goPage('+(currentPage+1)+')" '+(currentPage>=pages?'disabled':'')+'>›</button>';
  pg+='<button onclick="goPage('+pages+')" '+(currentPage>=pages?'disabled':'')+'>末页</button>';
  document.getElementById('pagination').innerHTML=pg;
}

function goPage(p){currentPage=p;renderTable();}

// ====== 新增/编辑功能 ======
var EDIT_MODE='add';  // 'add' or 'edit'

function openForm(){
  EDIT_MODE='add';
  document.getElementById('modalTitle').textContent='新增记录';
  ['customer','order_no','contact','phone','address','service','product','qty','content','sales','start_date','remark'].forEach(function(f){
    document.getElementById('ef_'+f).value='';
  });
  document.getElementById('ef_edit_idx').value='';
  document.getElementById('formMsg').textContent='';
  document.getElementById('editModal').style.display='block';
}

function editRecord(idx){
  var r=filtered[idx];
  if(!r) return;
  EDIT_MODE='edit';
  document.getElementById('modalTitle').textContent='编辑记录: '+(r.c||'');
  document.getElementById('ef_customer').value=r.c||'';
  document.getElementById('ef_order_no').value=r.o||'';
  document.getElementById('ef_contact').value=r.ct||'';
  document.getElementById('ef_phone').value=r.ph||'';
  document.getElementById('ef_address').value=r.a||'';
  document.getElementById('ef_service').value=r.sv||'';
  document.getElementById('ef_product').value=r.pm||'';
  document.getElementById('ef_qty').value=r.q||'';
  document.getElementById('ef_content').value=r.cn||'';
  document.getElementById('ef_sales').value=r.sl||'';
  document.getElementById('ef_start_date').value=r.sd||'';
  document.getElementById('ef_remark').value=r.rm||'';
  document.getElementById('ef_edit_idx').value=idx;
  document.getElementById('formMsg').textContent='';
  document.getElementById('editModal').style.display='block';
}

function closeForm(){
  document.getElementById('editModal').style.display='none';
}

function submitForm(){
  var customer=document.getElementById('ef_customer').value.trim();
  if(!customer){alert('请填写客户名称');return;}
  
  var data={
    customer:customer,
    order_no:document.getElementById('ef_order_no').value.trim(),
    contact:document.getElementById('ef_contact').value.trim(),
    phone:document.getElementById('ef_phone').value.trim(),
    address:document.getElementById('ef_address').value.trim(),
    service:document.getElementById('ef_service').value.trim(),
    product:document.getElementById('ef_product').value.trim(),
    qty:document.getElementById('ef_qty').value.trim(),
    content:document.getElementById('ef_content').value.trim(),
    sales:document.getElementById('ef_sales').value.trim(),
    start_date:document.getElementById('ef_start_date').value.trim(),
    remark:document.getElementById('ef_remark').value.trim(),
    source:'CRM',pcat:'CX-SV'
  };
  
  var payload={action:EDIT_MODE,data:data};
  if(EDIT_MODE==='edit'){
    var idx=parseInt(document.getElementById('ef_edit_idx').value);
    if(idx>=0&&idx<filtered.length){payload.original_order_no=filtered[idx].o||'';}
  }
  
  var title=encodeURIComponent('数据编辑:'+(EDIT_MODE==='add'?'新增':'编辑')+':'+data.customer);
  var body=encodeURIComponent('```json\n'+JSON.stringify(payload,null,2)+'\n```\n\n> 请直接点击 Submit new issue 提交');
  var url='https://github.com/DADIAO007/SV-dispatch-dashboard/issues/new?title='+title+'&body='+body;
  
  document.getElementById('formMsg').innerHTML='<a href="'+url+'" target="_blank" style="color:#1a73e8;font-weight:600">👉 点击此处打开 GitHub Issue 确认提交</a><br><span style="color:#999;font-size:11px">提交后2分钟内自动同步到看板</span>';
}
</script>
</div>
</body>
</html>'''


def main():
    print("="*50)
    print("SV派单看板生成器 v3 (拆分数据)")
    print("="*50)
    stats, records = read_all_data()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 输出 index.html（只含统计，体积小）
    html = generate_html(stats)
    html_path = os.path.join(OUTPUT_DIR, 'index.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ index.html: {os.path.getsize(html_path)/1024:.1f} KB")

    # 输出 records.json（明细数据，异步加载）
    json_path = os.path.join(OUTPUT_DIR, 'records.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False)
    print(f"✅ records.json: {os.path.getsize(json_path)/1024:.1f} KB ({len(records)} 条)")

    s = stats['stats']
    print(f"   总:{s['grand_total']} | 派单:{s['dispatch_total']} | 巡检:{s['inspection']} | 值守:{s['duty']} | 月结:{s['settlement']}")


if __name__ == '__main__':
    main()
