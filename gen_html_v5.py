#!/usr/bin/env python3
"""v5: 多Tab看板生成器"""
import json, os

with open('/workspace/dashboard_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

stats = data['stats']
dispatch = data['dispatch']
monthly = data['monthly']
inspection = data['inspection']
duty = data['duty']
batch_qa = data['batch_qa']
batch_wo = data['batch_wo']
yearly = data['yearly']
monthly_chart = data['monthly_chart']
ctop = data['ctop']
srv = data['srv']
prod = data['prod']
sales = data['sales']
status = data['status']
recent = data['recent']

# 各Tab的列定义
TABS = {
    'ov': {
        'name': '数据概览',
        'show_charts': True
    },
    'dispatch': {
        'name': '派单明细',
        'cols': ['序号','客户','地址','联系人','电话','单号','服务','产品','数量','内容','实施编号','销售','销售电话','开始','结束','状态','备注'],
        'fields': ['sn','c','a','ct','ph','o','sv','pm','q','cn','in','sl','slp','sd','ed','st','rm'],
        'data': dispatch
    },
    'monthly': {
        'name': '通信月结',
        'cols': ['序号','备案编号','需求时间','MU','PM','客户','项目','需求类型','服务地点','设备型号','数量','服务类型','计数','工单号'],
        'fields': ['sn','rec','dt','mu','pm','c','pj','dmd','loc','dev','q','sv','cnt','wo'],
        'data': monthly
    },
    'inspection': {
        'name': '巡检',
        'cols': ['序号','客户','地址','联系人','电话','单号','服务','产品','数量','需求细节','实施编号','销售','状态','开始','结束'],
        'fields': ['sn','c','a','ct','ph','o','sv','pm','q','det','in','sl','st','sd','ed'],
        'data': inspection
    },
    'duty': {
        'name': '值守',
        'cols': ['序号','客户','地址','联系人','电话','产品类别','任务来源','单号','服务','产品','数量','服务内容','实施编号','销售','状态','开始','结束','实际结束','实施经理','电话','备注'],
        'fields': ['sn','c','a','ct','ph','pc','sr','o','sv','pm','q','cn','in','sl','st','sd','ed','ad','mgr','mgp','rm'],
        'data': duty
    },
    'batch_qa': {
        'name': '批量问题',
        'cols': ['序号','问题名称','问题根因','解决方案','问题单编号','创建时间','设备型号','客户及数量','来源'],
        'fields': ['sn','name','cause','sol','qano','ct','dev','cq','src'],
        'data': batch_qa
    },
    'batch_wo': {
        'name': '批量工单',
        'cols': ['序号','客户','行业','地址','联系人','电话','产品类别','批量问题','问题编号','归集单位','产品型号','数量','服务内容','实施编号','工具使用','状态','开始','结束','实际结束','实施经理','电话'],
        'fields': ['sn','c','ind','a','ct','ph','pc','qa','qano','unit','pm','q','sv','in','tool','st','sd','ed','ad','mgr','mgp'],
        'data': batch_wo
    }
}

# 转为 JSON 字符串
dispatch_json = json.dumps(dispatch, ensure_ascii=False)
monthly_json = json.dumps(monthly, ensure_ascii=False)
inspection_json = json.dumps(inspection, ensure_ascii=False)
duty_json = json.dumps(duty, ensure_ascii=False)
batch_qa_json = json.dumps(batch_qa, ensure_ascii=False)
batch_wo_json = json.dumps(batch_wo, ensure_ascii=False)
stats_json = json.dumps({
    'stats': stats, 'yearly': yearly, 'monthly_chart': monthly_chart,
    'ctop': ctop, 'srv': srv, 'prod': prod,
    'sales': sales, 'status': status, 'recent': recent
}, ensure_ascii=False)

# 生成HTML
html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SV派单管理系统</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",Arial,sans-serif;background:#f0f2f5;color:#333}
#g{position:fixed;top:0;left:0;width:100%;height:100%;background:#1a73e8;display:flex;align-items:center;justify-content:center;z-index:9999}
#g>div{background:#fff;padding:36px 40px;border-radius:12px;text-align:center;max-width:340px;width:90%;box-shadow:0 8px 32px rgba(0,0,0,0.2)}
#g h2{font-size:22px;margin-bottom:8px}
#g p{color:#999;font-size:13px;margin-bottom:20px}
#g input{width:100%;padding:12px;border:2px solid #ddd;border-radius:8px;font-size:15px;outline:none;text-align:center;margin-bottom:12px}
#g input:focus{border-color:#1a73e8}
#g button{width:100%;padding:12px;background:#1a73e8;color:#fff;border:none;border-radius:8px;font-size:15px;cursor:pointer;font-weight:600}
#g button:hover{background:#1557b0}
#g .err{color:#e74c3c;font-size:12px;margin-top:10px;display:none}
.hdr{background:linear-gradient(135deg,#1a73e8,#0d47a1);color:#fff;padding:14px 20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
.hdr h1{font-size:20px}
.hdr p{opacity:.85;font-size:12px;margin-top:1px}
.tabs{display:flex;gap:2px;flex-wrap:wrap}
.tb{padding:7px 14px;border:none;background:rgba(255,255,255,0.15);color:#fff;border-radius:6px 6px 0 0;cursor:pointer;font-size:13px}
.tb.on{background:#fff;color:#1a73e8;font-weight:700}
.tb:hover:not(.on){background:rgba(255,255,255,0.25)}
.ct{max-width:1500px;margin:0 auto;padding:16px}
.st{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:16px}
.sc{background:#fff;border-radius:10px;padding:13px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.08)}
.sc .n{font-size:22px;font-weight:700;color:#1a73e8}
.sc .l{font-size:11px;color:#666;margin-top:3px}
.sc.g .n{color:#27ae60}.sc.o .n{color:#e67e22}.sc.p .n{color:#8e44ad}.sc.t .n{color:#1abc9c}.sc.r .n{color:#e74c3c}.sc.y .n{color:#f39c12}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px}
.cd{background:#fff;border-radius:10px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,0.08)}
.cd h3{font-size:13px;margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid #eee;font-weight:600}
.bar{display:flex;align-items:center;margin-bottom:5px;font-size:11px}
.bar .n{width:75px;color:#555;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar .b{flex:1;height:16px;background:#f0f2f5;border-radius:3px;overflow:hidden;margin:0 6px}
.bar .f{height:100%;background:linear-gradient(90deg,#1a73e8,#4285f4);border-radius:3px;display:flex;align-items:center;padding-left:5px;color:#fff;font-size:10px;font-weight:600;min-width:18px}
table{width:100%;border-collapse:collapse;font-size:11px}
th{background:#f8f9fa;padding:6px 7px;text-align:left;font-weight:600;color:#555;border-bottom:2px solid #e9ecef;white-space:nowrap;position:sticky;top:0}
td{padding:4px 7px;border-bottom:1px solid #f0f2f5;font-size:11px;max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
tr:hover{background:#f8f9ff}
.tb-bar{display:flex;gap:8px;margin-bottom:12px;align-items:center;flex-wrap:wrap}
.tb-bar select,.tb-bar input{padding:6px 10px;border:1px solid #ddd;border-radius:6px;font-size:12px;outline:none}
.tb-bar input{flex:1;min-width:200px}
.tb-bar input:focus{border-color:#1a73e8}
.tb-bar .info{font-size:12px;color:#999}
.pg{display:flex;justify-content:center;gap:4px;margin-top:10px;flex-wrap:wrap}
.pg button{padding:4px 9px;border:1px solid #ddd;border-radius:4px;background:#fff;cursor:pointer;font-size:11px}
.pg button.on{background:#1a73e8;color:#fff;border-color:#1a73e8}
.pg button:disabled{opacity:.3;cursor:default}
.tag{display:inline-block;padding:1px 5px;border-radius:3px;font-size:9px;color:#fff;font-weight:600}
.tag-p{background:#1a73e8}.tag-i{background:#27ae60}.tag-d{background:#8e44ad}.tag-m{background:#1abc9c}
.tabcontent{display:none}
.tabcontent.on{display:block}
@media(max-width:768px){.g2,.g3{grid-template-columns:1fr}.st{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>

<div id="g">
  <div>
    <h2>🔒 SV派单管理系统</h2>
    <p>请输入访问密码</p>
    <input type="password" id="pi" placeholder="输入密码" onkeydown="if(event.key==='Enter')go()">
    <button onclick="go()">进入系统</button>
    <div class="err" id="pe">密码错误</div>
  </div>
</div>

<div id="app" style="display:none">
<div class="hdr">
  <div><h1>📊 SV派单管理系统</h1><p>数据看板 · 自动同步</p></div>
  <div class="tabs" id="tabbar">
    <button class="tb on" data-tab="ov" onclick="sw(this)">📈 数据概览</button>
    <button class="tb" data-tab="dispatch" onclick="sw(this)">📋 派单明细</button>
    <button class="tb" data-tab="monthly" onclick="sw(this)">📊 通信月结</button>
    <button class="tb" data-tab="inspection" onclick="sw(this)">🔍 巡检</button>
    <button class="tb" data-tab="duty" onclick="sw(this)">🛡️ 值守</button>
    <button class="tb" data-tab="batch_qa" onclick="sw(this)">⚠️ 批量问题</button>
    <button class="tb" data-tab="batch_wo" onclick="sw(this)">📑 批量工单</button>
  </div>
</div>

<div class="ct">

<div id="ov" class="tabcontent on">
  <div class="st">
    <div class="sc"><div class="n">''' + str(stats['total']) + '''</div><div class="l">总记录</div></div>
    <div class="sc g"><div class="n">''' + str(stats['dispatch']) + '''</div><div class="l">派单</div></div>
    <div class="sc o"><div class="n">''' + str(stats['customers']) + '''</div><div class="l">合作客户</div></div>
    <div class="sc p"><div class="n">''' + str(stats['inspection']) + '''</div><div class="l">巡检</div></div>
    <div class="sc t"><div class="n">''' + str(stats['duty']) + '''</div><div class="l">值守</div></div>
    <div class="sc y"><div class="n">''' + str(stats['monthly']) + '''</div><div class="l">通信月结</div></div>
    <div class="sc r"><div class="n">''' + str(stats['batch_wo']) + '''</div><div class="l">批量工单</div></div>
    <div class="sc"><div class="n">''' + str(stats['batch_qa']) + '''</div><div class="l">批量问题</div></div>
  </div>

  <div class="g2">
    <div class="cd"><h3>📅 年度派单趋势</h3><div id="ch_yearly"></div></div>
    <div class="cd"><h3>📆 2026年月度派单</h3><div id="ch_monthly"></div></div>
  </div>

  <div class="g3">
    <div class="cd"><h3>🏆 TOP10 客户</h3><div id="ch_ctop"></div></div>
    <div class="cd"><h3>🔧 服务类型</h3><div id="ch_srv"></div></div>
    <div class="cd"><h3>💻 产品型号</h3><div id="ch_prod"></div></div>
  </div>

  <div class="g3">
    <div class="cd"><h3>👤 销售业绩</h3><div id="ch_sales"></div></div>
    <div class="cd"><h3>📌 2026状态</h3><div id="ch_status"></div></div>
    <div class="cd"><h3>🕐 最近派单</h3>
      <table><thead><tr><th>客户</th><th>服务</th><th>型号</th><th>日期</th></tr></thead><tbody id="recent_tb"></tbody></table>
    </div>
  </div>
</div>

'''

# 动态生成各 Tab
for tab_id, conf in TABS.items():
    if tab_id == 'ov': continue
    cols = conf['cols']
    fields = conf['fields']
    html += f'''
<div id="{tab_id}" class="tabcontent">
  <div class="cd">
    <div class="tb-bar">
      <input type="text" id="search_{tab_id}" placeholder="搜索..." oninput="doFilter('{tab_id}')">
      <span class="info" id="info_{tab_id}"></span>
    </div>
    <div style="overflow-x:auto;max-height:calc(100vh - 220px);overflow-y:auto">
      <table id="tb_{tab_id}">
        <thead><tr id="tbh_{tab_id}"></tr></thead>
        <tbody id="tbb_{tab_id}"></tbody>
      </table>
    </div>
    <div class="pg" id="pg_{tab_id}"></div>
  </div>
</div>
'''

html += '''
</div>
</div>

<script>
var PASSWORD="Zxk980213@zxy";
var STATS=''' + stats_json + ''';
var DATA={
  dispatch:''' + dispatch_json + ''',
  monthly:''' + monthly_json + ''',
  inspection:''' + inspection_json + ''',
  duty:''' + duty_json + ''',
  batch_qa:''' + batch_qa_json + ''',
  batch_wo:''' + batch_wo_json + '''
};
var COLS={
  dispatch:["序号","客户","地址","联系人","电话","单号","服务","产品","数量","内容","实施编号","销售","销售电话","开始","结束","状态","备注"],
  monthly:["序号","备案编号","需求时间","MU","PM","客户","项目","需求类型","服务地点","设备型号","数量","服务类型","计数","工单号"],
  inspection:["序号","客户","地址","联系人","电话","单号","服务","产品","数量","需求细节","实施编号","销售","状态","开始","结束"],
  duty:["序号","客户","地址","联系人","电话","产品类别","任务来源","单号","服务","产品","数量","服务内容","实施编号","销售","状态","开始","结束","实际结束","实施经理","电话","备注"],
  batch_qa:["序号","问题名称","问题根因","解决方案","问题单编号","创建时间","设备型号","客户及数量","来源"],
  batch_wo:["序号","客户","行业","地址","联系人","电话","产品类别","批量问题","问题编号","归集单位","产品型号","数量","服务内容","实施编号","工具使用","状态","开始","结束","实际结束","实施经理","电话"]
};
var FIELDS={
  dispatch:["sn","c","a","ct","ph","o","sv","pm","q","cn","in","sl","slp","sd","ed","st","rm"],
  monthly:["sn","rec","dt","mu","pm","c","pj","dmd","loc","dev","q","sv","cnt","wo"],
  inspection:["sn","c","a","ct","ph","o","sv","pm","q","det","in","sl","st","sd","ed"],
  duty:["sn","c","a","ct","ph","pc","sr","o","sv","pm","q","cn","in","sl","st","sd","ed","ad","mgr","mgp","rm"],
  batch_qa:["sn","name","cause","sol","qano","ct","dev","cq","src"],
  batch_wo:["sn","c","ind","a","ct","ph","pc","qa","qano","unit","pm","q","sv","in","tool","st","sd","ed","ad","mgr","mgp"]
};
var PER_PAGE=50;
var state={};

function go(){
  if(document.getElementById("pi").value===PASSWORD){
    document.getElementById("g").style.display="none";
    document.getElementById("app").style.display="block";
    initOverview();
  }else{
    var e=document.getElementById("pe");
    e.style.display="block";
    e.textContent="密码错误";
  }
}

function sw(btn){
  document.querySelectorAll(".tb").forEach(function(b){b.classList.remove("on")});
  btn.classList.add("on");
  document.querySelectorAll(".tabcontent").forEach(function(t){t.classList.remove("on")});
  var tab=btn.getAttribute("data-tab");
  document.getElementById(tab).classList.add("on");
  if(tab!=="ov" && !state[tab]) doFilter(tab);
}

function initOverview(){
  bar("ch_yearly",STATS.yearly.map(function(i){return i.year+"年"}),STATS.yearly.map(function(i){return i.count}),"rgba(26,115,232,0.7)");
  bar("ch_monthly",STATS.monthly_chart.map(function(i){return (i.month||"").substring(4)+"月"}),STATS.monthly_chart.map(function(i){return i.count}),"rgba(230,126,34,0.7)");
  bar("ch_ctop",STATS.ctop.map(function(i){return i.name}),STATS.ctop.map(function(i){return i.count}),"rgba(26,115,232,0.7)");
  bar("ch_srv",STATS.srv.map(function(i){return i.name}),STATS.srv.map(function(i){return i.count}),"rgba(39,174,96,0.7)");
  bar("ch_prod",STATS.prod.map(function(i){return i.name}),STATS.prod.map(function(i){return i.count}),"rgba(142,68,173,0.7)");
  bar("ch_sales",STATS.sales.map(function(i){return i.name}),STATS.sales.map(function(i){return i.count}),"rgba(26,188,156,0.7)");
  bar("ch_status",STATS.status.map(function(i){return i.name}),STATS.status.map(function(i){return i.count}),"rgba(231,76,60,0.7)");
  var html="";
  for(var i=0;i<STATS.recent.length;i++){
    var r=STATS.recent[i];
    html+="<tr><td><b>"+r.c+"</b></td><td>"+(r.sv||"-")+"</td><td>"+(r.pm||"-")+"</td><td>"+(r.sd||"-")+"</td></tr>";
  }
  document.getElementById("recent_tb").innerHTML=html;
}

function bar(elId,labels,values,color){
  var el=document.getElementById(elId);
  if(!el||!labels.length) return;
  var max=Math.max.apply(null,values)||1;
  var html="";
  for(var i=0;i<labels.length;i++){
    var w=(values[i]/max*100).toFixed(1);
    html+="<div class=\"bar\"><span class=\"n\" title=\""+labels[i]+"\">"+labels[i]+"</span><span class=\"b\"><span class=\"f\" style=\"width:"+w+"%;background:"+color+"\">"+values[i]+"</span></span></div>";
  }
  el.innerHTML=html;
}

function doFilter(tab){
  if(!DATA[tab]) return;
  var kw=(document.getElementById("search_"+tab).value||"").toLowerCase();
  state[tab]={kw:kw,page:1,filtered:DATA[tab].filter(function(r){
    if(!kw) return true;
    return JSON.stringify(r).toLowerCase().indexOf(kw)>=0;
  })};
  renderTable(tab);
}

function renderTable(tab){
  var s=state[tab];
  if(!s) return;
  var total=s.filtered.length;
  var pages=Math.ceil(total/PER_PAGE)||1;
  if(s.page>pages) s.page=pages;
  var start=(s.page-1)*PER_PAGE;
  var page=s.filtered.slice(start,start+PER_PAGE);
  document.getElementById("info_"+tab).textContent="共 "+total+" 条，第 "+(total?start+1:0)+"-"+Math.min(start+PER_PAGE,total)+" 条";
  
  var cols=COLS[tab], fields=FIELDS[tab];
  document.getElementById("tbh_"+tab).innerHTML="<tr>"+cols.map(function(t){return "<th>"+t+"</th>"}).join("")+"</tr>";
  
  var html="";
  for(var i=0;i<page.length;i++){
    var r=page[i];
    html+="<tr>";
    for(var j=0;j<fields.length;j++){
      var v=r[fields[j]]||"-";
      html+="<td title=\""+v+"\">"+v+"</td>";
    }
    html+="</tr>";
  }
  document.getElementById("tbb_"+tab).innerHTML=html||"<tr><td colspan=\""+cols.length+"\" style=\"text-align:center;padding:20px;color:#999\">无匹配记录</td></tr>";
  
  var pg="";
  var s2=Math.max(1,s.page-3);
  var e2=Math.min(pages,s.page+3);
  pg+="<button onclick=\"goPage('"+tab+"',1)\" "+(s.page<=1?"disabled":"")+">首页</button>";
  pg+="<button onclick=\"goPage('"+tab+"',"+(s.page-1)+")\" "+(s.page<=1?"disabled":"")+">‹</button>";
  if(s2>1) pg+="<span style=\"padding:5px 4px;color:#999\">...</span>";
  for(var p=s2;p<=e2;p++){
    pg+="<button onclick=\"goPage('"+tab+"',"+p+")\" class=\""+(p===s.page?"on":"")+"\">"+p+"</button>";
  }
  if(e2<pages) pg+="<span style=\"padding:5px 4px;color:#999\">...</span>";
  pg+="<button onclick=\"goPage('"+tab+"',"+(s.page+1)+")\" "+(s.page>=pages?"disabled":"")+">›</button>";
  pg+="<button onclick=\"goPage('"+tab+"',"+pages+")\" "+(s.page>=pages?"disabled":"")+">末页</button>";
  document.getElementById("pg_"+tab).innerHTML=pg;
}

function goPage(tab,p){
  if(!state[tab]) return;
  state[tab].page=p;
  renderTable(tab);
}
</script>
</body>
</html>'''

with open('/workspace/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ 生成: {os.path.getsize('/workspace/dashboard.html')/1024:.1f} KB")
print(f"   Tab数量: {len(TABS)}")
for tid, conf in TABS.items():
    print(f"   - {conf['name']}: {len(conf.get('data',[]))} 条")
