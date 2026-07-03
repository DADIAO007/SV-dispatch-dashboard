#!/usr/bin/env python3
"""
SV派单看板生成器 v4 - 极简稳定版
- 统计数据 + 明细数据全部内嵌到单一 HTML
- 零外部依赖（无CDN、无动态加载）
- 密码门用最简单 inline script
- 客户端分页+搜索，纯JS，不依赖任何框架
"""
import json
import os

# 读取数据
with open('/workspace/dashboard_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

stats = data['stats']
records = data['records']
yearly = data['yearly']
monthly = data['monthly']
ctop = data['ctop']
srv = data['srv']
prod = data['prod']
sales = data['sales']
status = data['status']
recent = data['recent']

# 转换 records 为 JS 可用格式
records_json = json.dumps(records, ensure_ascii=False)
stats_json = json.dumps({
    'stats': stats, 'yearly': yearly, 'monthly': monthly,
    'ctop': ctop, 'srv': srv, 'prod': prod,
    'sales': sales, 'status': status, 'recent': recent
}, ensure_ascii=False)

# 生成 HTML（全部内嵌，无外部依赖）
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
.hdr{background:linear-gradient(135deg,#1a73e8,#0d47a1);color:#fff;padding:18px 24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}
.hdr h1{font-size:22px}
.hdr p{opacity:.85;font-size:12px;margin-top:2px}
.tabs{display:flex;gap:2px}
.tb{padding:9px 18px;border:none;background:rgba(255,255,255,0.15);color:#fff;border-radius:6px 6px 0 0;cursor:pointer;font-size:14px}
.tb.on{background:#fff;color:#1a73e8;font-weight:700}
.ct{max-width:1400px;margin:0 auto;padding:18px}
.st{display:grid;grid-template-columns:repeat(auto-fit,minmax(135px,1fr));gap:10px;margin-bottom:18px}
.sc{background:#fff;border-radius:10px;padding:14px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.08)}
.sc .n{font-size:24px;font-weight:700;color:#1a73e8}
.sc .l{font-size:11px;color:#666;margin-top:3px}
.sc.g .n{color:#27ae60}.sc.o .n{color:#e67e22}.sc.p .n{color:#8e44ad}.sc.t .n{color:#1abc9c}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px}
.cd{background:#fff;border-radius:10px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,0.08)}
.cd h3{font-size:13px;margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid #eee;font-weight:600}
.bar{display:flex;align-items:center;margin-bottom:6px;font-size:12px}
.bar .n{width:80px;color:#555;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar .b{flex:1;height:18px;background:#f0f2f5;border-radius:3px;overflow:hidden;margin:0 8px;position:relative}
.bar .f{height:100%;background:linear-gradient(90deg,#1a73e8,#4285f4);border-radius:3px;display:flex;align-items:center;padding-left:6px;color:#fff;font-size:11px;font-weight:600;min-width:24px}
table{width:100%;border-collapse:collapse;font-size:12px}
th{background:#f8f9fa;padding:7px 8px;text-align:left;font-weight:600;color:#555;border-bottom:2px solid #e9ecef;white-space:nowrap}
td{padding:5px 8px;border-bottom:1px solid #f0f2f5;font-size:11px;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
tr:hover{background:#f8f9ff}
.tb-bar{display:flex;gap:10px;margin-bottom:12px;align-items:center;flex-wrap:wrap}
.tb-bar select,.tb-bar input{padding:7px 10px;border:1px solid #ddd;border-radius:6px;font-size:13px;outline:none}
.tb-bar input{flex:1;min-width:200px}
.tb-bar input:focus{border-color:#1a73e8}
.tb-bar .info{font-size:12px;color:#999}
.tb-bar button{padding:7px 16px;background:#1a73e8;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;font-weight:600}
.pg{display:flex;justify-content:center;gap:4px;margin-top:12px;flex-wrap:wrap}
.pg button{padding:5px 10px;border:1px solid #ddd;border-radius:4px;background:#fff;cursor:pointer;font-size:12px}
.pg button.on{background:#1a73e8;color:#fff;border-color:#1a73e8}
.pg button:disabled{opacity:.3;cursor:default}
.tag{display:inline-block;padding:2px 6px;border-radius:3px;font-size:10px;color:#fff;font-weight:600}
.tag-p{background:#1a73e8}.tag-i{background:#27ae60}.tag-d{background:#8e44ad}.tag-m{background:#1abc9c}
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
  <div class="tabs">
    <button class="tb on" onclick="sw('ov',this)">📈 数据概览</button>
    <button class="tb" onclick="sw('dt',this)">📋 数据明细</button>
  </div>
</div>

<div class="ct">

<div id="ov">
  <div class="st">
    <div class="sc"><div class="n">''' + str(stats['total'] + stats['inspection'] + stats['duty'] + stats['settlement']) + '''</div><div class="l">总记录</div></div>
    <div class="sc"><div class="n">''' + str(stats['total']) + '''</div><div class="l">派单</div></div>
    <div class="sc g"><div class="n">''' + str(stats['customers']) + '''</div><div class="l">合作客户</div></div>
    <div class="sc o"><div class="n">''' + str(stats['d2026']) + '''</div><div class="l">2026年</div></div>
    <div class="sc p"><div class="n">''' + str(stats['inspection']) + '''</div><div class="l">巡检</div></div>
    <div class="sc t"><div class="n">''' + str(stats['duty'] + stats['settlement']) + '''</div><div class="l">值守+月结</div></div>
  </div>

  <div class="g2">
    <div class="cd">
      <h3>📅 年度派单趋势</h3>
      <div id="ch_yearly"></div>
    </div>
    <div class="cd">
      <h3>📆 2026年月度派单</h3>
      <div id="ch_monthly"></div>
    </div>
  </div>

  <div class="g3">
    <div class="cd">
      <h3>🏆 TOP10 客户</h3>
      <div id="ch_ctop"></div>
    </div>
    <div class="cd">
      <h3>🔧 服务类型分布</h3>
      <div id="ch_srv"></div>
    </div>
    <div class="cd">
      <h3>💻 产品型号排行</h3>
      <div id="ch_prod"></div>
    </div>
  </div>

  <div class="g3">
    <div class="cd">
      <h3>👤 销售业绩</h3>
      <div id="ch_sales"></div>
    </div>
    <div class="cd">
      <h3>📌 状态分布</h3>
      <div id="ch_status"></div>
    </div>
    <div class="cd">
      <h3>🕐 最近派单</h3>
      <table>
        <thead><tr><th>客户</th><th>服务</th><th>型号</th><th>日期</th></tr></thead>
        <tbody id="recent_tb"></tbody>
      </table>
    </div>
  </div>
</div>

<div id="dt" style="display:none">
  <div class="cd">
    <div class="tb-bar">
      <select id="fy" onchange="doFilter()">
        <option value="all">全部年份</option>
        <option value="2026" selected>2026年</option>
        <option value="2025">2025年</option>
        <option value="2024">2024年</option>
      </select>
      <input type="text" id="sq" placeholder="搜索客户/单号/产品/服务/销售..." oninput="doFilter()">
      <span class="info" id="info"></span>
      <button onclick="openForm()">＋ 新增</button>
    </div>
    <div style="overflow-x:auto"><table id="tb">
      <thead><tr id="tbh"></tr></thead>
      <tbody id="tbb"></tbody>
    </table></div>
    <div class="pg" id="pg"></div>
  </div>
</div>

</div>
</div>

<!-- 编辑弹窗 -->
<div id="modal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:1000;overflow-y:auto">
<div style="background:#fff;max-width:680px;margin:30px auto;border-radius:12px;padding:24px">
<h3 id="mt" style="margin-bottom:16px">新增记录</h3>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
<div><label style="font-size:12px;color:#666">客户名称*</label><input id="f_c" style="width:100%;padding:7px;border:1px solid #ddd;border-radius:4px"></div>
<div><label style="font-size:12px;color:#666">单号</label><input id="f_o" style="width:100%;padding:7px;border:1px solid #ddd;border-radius:4px"></div>
<div><label style="font-size:12px;color:#666">联系人</label><input id="f_ct" style="width:100%;padding:7px;border:1px solid #ddd;border-radius:4px"></div>
<div><label style="font-size:12px;color:#666">电话</label><input id="f_ph" style="width:100%;padding:7px;border:1px solid #ddd;border-radius:4px"></div>
<div><label style="font-size:12px;color:#666">地址</label><input id="f_a" style="width:100%;padding:7px;border:1px solid #ddd;border-radius:4px"></div>
<div><label style="font-size:12px;color:#666">服务</label><input id="f_sv" style="width:100%;padding:7px;border:1px solid #ddd;border-radius:4px"></div>
<div><label style="font-size:12px;color:#666">产品</label><input id="f_pm" style="width:100%;padding:7px;border:1px solid #ddd;border-radius:4px"></div>
<div><label style="font-size:12px;color:#666">数量</label><input id="f_q" type="number" style="width:100%;padding:7px;border:1px solid #ddd;border-radius:4px"></div>
<div><label style="font-size:12px;color:#666">服务内容</label><input id="f_cn" style="width:100%;padding:7px;border:1px solid #ddd;border-radius:4px"></div>
<div><label style="font-size:12px;color:#666">销售</label><input id="f_sl" style="width:100%;padding:7px;border:1px solid #ddd;border-radius:4px"></div>
<div><label style="font-size:12px;color:#666">开始日期</label><input id="f_sd" placeholder="20260701" style="width:100%;padding:7px;border:1px solid #ddd;border-radius:4px"></div>
<div><label style="font-size:12px;color:#666">备注</label><input id="f_rm" style="width:100%;padding:7px;border:1px solid #ddd;border-radius:4px"></div>
</div>
<input type="hidden" id="f_idx" value="">
<div style="margin-top:16px;display:flex;gap:10px;justify-content:flex:end">
  <button onclick="closeForm()" style="padding:8px 18px;border:1px solid #ddd;background:#fff;border-radius:6px;cursor:pointer">取消</button>
  <button onclick="submitForm()" style="padding:8px 18px;background:#1a73e8;color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:600">提交到 GitHub</button>
</div>
<div id="fm" style="margin-top:10px;font-size:12px"></div>
</div>
</div>

<script>
var PASSWORD='SV2026';
var STATS=''' + stats_json + ''';
var RECORDS=''' + records_json + ''';
var COLS=['类型','客户','地址','联系人','电话','单号','服务','产品','数量','内容','实施编号','销售','开始','结束','状态','备注'];
var F=['t','c','a','ct','ph','o','sv','pm','q','cn','in','sl','sd','ed','st','rm'];
var PER_PAGE=50;

// 密码验证
function go(){
  var v=document.getElementById('pi').value;
  if(v===PASSWORD){
    document.getElementById('g').style.display='none';
    document.getElementById('app').style.display='block';
    initOverview();
  }else{
    var err=document.getElementById('pe');
    err.style.display='block';
    err.textContent='密码错误';
  }
}

// Tab切换
function sw(tab,btn){
  document.querySelectorAll('.tb').forEach(function(b){b.classList.remove('on')});
  btn.classList.add('on');
  document.getElementById('ov').style.display=tab==='ov'?'block':'none';
  document.getElementById('dt').style.display=tab==='dt'?'block':'none';
  if(tab==='dt') doFilter();
}

// 概览 - 纯CSS bar图（无CDN依赖）
function initOverview(){
  renderBar('ch_yearly', STATS.yearly.map(function(i){return i.year+'年'}), STATS.yearly.map(function(i){return i.count}), STATS.yearly.map(function(i){return i.count}), 'rgba(26,115,232,0.7)');
  renderBar('ch_monthly', STATS.monthly.map(function(i){return (i.month||'').substring(4)+'月'}), STATS.monthly.map(function(i){return i.count}), STATS.monthly.map(function(i){return i.count}), 'rgba(230,126,34,0.7)');
  renderBar('ch_ctop', STATS.ctop.map(function(i){return i.name}), STATS.ctop.map(function(i){return i.count}), STATS.ctop.map(function(i){return i.count}), 'rgba(26,115,232,0.7)');
  renderBar('ch_srv', STATS.srv.map(function(i){return i.name}), STATS.srv.map(function(i){return i.count}), STATS.srv.map(function(i){return i.count}), 'rgba(39,174,96,0.7)');
  renderBar('ch_prod', STATS.prod.map(function(i){return i.name}), STATS.prod.map(function(i){return i.count}), STATS.prod.map(function(i){return i.count}), 'rgba(142,68,173,0.7)');
  renderBar('ch_sales', STATS.sales.map(function(i){return i.name}), STATS.sales.map(function(i){return i.count}), STATS.sales.map(function(i){return i.count}), 'rgba(26,188,156,0.7)');
  renderBar('ch_status', STATS.status.map(function(i){return i.name}), STATS.status.map(function(i){return i.count}), STATS.status.map(function(i){return i.count}), 'rgba(231,76,60,0.7)');
  
  // 最近派单
  var html='';
  for(var i=0;i<STATS.recent.length;i++){
    var r=STATS.recent[i];
    html+='<tr><td><b>'+r.c+'</b></td><td>'+(r.s||'-')+'</td><td>'+(r.m||'-')+'</td><td>'+(r.d||'-')+'</td></tr>';
  }
  document.getElementById('recent_tb').innerHTML=html;
}

function renderBar(elId, labels, values, displayValues, color){
  var el=document.getElementById(elId);
  if(!el) return;
  var max=Math.max.apply(null,values)||1;
  var html='';
  for(var i=0;i<labels.length;i++){
    var w=(values[i]/max*100).toFixed(1);
    html+='<div class="bar"><span class="n" title="'+labels[i]+'">'+labels[i]+'</span><span class="b"><span class="f" style="width:'+w+'%;background:'+color+'">'+values[i]+'</span></span></div>';
  }
  el.innerHTML=html;
}

// 明细筛选
var filtered=[];
var currentPage=1;

function doFilter(){
  var y=document.getElementById('fy').value;
  var kw=(document.getElementById('sq').value||'').toLowerCase();
  filtered=RECORDS.filter(function(r){
    if(y!=='all' && r.y!=parseInt(y)) return false;
    if(!kw) return true;
    var txt=(r.c||'')+' '+(r.o||'')+' '+(r.pm||'')+' '+(r.sv||'')+' '+(r.sl||'')+' '+(r.ct||'');
    return txt.toLowerCase().indexOf(kw)>=0;
  });
  currentPage=1;
  renderTable();
}

function renderTable(){
  var total=filtered.length;
  var pages=Math.ceil(total/PER_PAGE)||1;
  if(currentPage>pages) currentPage=pages;
  var start=(currentPage-1)*PER_PAGE;
  var page=filtered.slice(start,start+PER_PAGE);
  document.getElementById('info').textContent='共 '+total+' 条，第 '+(total?start+1:0)+'-'+Math.min(start+PER_PAGE,total)+' 条';
  
  var h='<tr>'+COLS.map(function(t){return '<th>'+t+'</th>'}).join('')+'<th>操作</th></tr>';
  document.getElementById('tbh').innerHTML=h;
  
  var html='';
  for(var i=0;i<page.length;i++){
    var r=page[i];
    var gIdx=start+i;
    var tc=r.t==='派单'?'tag-p':r.t==='巡检'?'tag-i':r.t==='值守'?'tag-d':'tag-m';
    html+='<tr>';
    html+='<td><span class="tag '+tc+'">'+r.t+'</span></td>';
    for(var j=1;j<F.length;j++){
      var v=r[F[j]]||'-';
      html+='<td title="'+v+'">'+v+'</td>';
    }
    html+='<td><button onclick="editRec('+gIdx+')" style="padding:2px 8px;font-size:10px;border:1px solid #1a73e8;background:#fff;color:#1a73e8;border-radius:3px;cursor:pointer">✎</button></td>';
    html+='</tr>';
  }
  document.getElementById('tbb').innerHTML=html||'<tr><td colspan="17" style="text-align:center;padding:20px;color:#999">无匹配记录</td></tr>';
  
  // 分页
  var pg='';
  var s=Math.max(1,currentPage-3);
  var e=Math.min(pages,currentPage+3);
  pg+='<button onclick="goPage(1)" '+(currentPage<=1?'disabled':'')+'>首页</button>';
  pg+='<button onclick="goPage('+(currentPage-1)+')" '+(currentPage<=1?'disabled':'')+'>‹</button>';
  if(s>1) pg+='<span style="padding:5px 4px;color:#999">...</span>';
  for(var p=s;p<=e;p++){
    pg+='<button onclick="goPage('+p+')" class="'+(p===currentPage?'on':'')+'">'+p+'</button>';
  }
  if(e<pages) pg+='<span style="padding:5px 4px;color:#999">...</span>';
  pg+='<button onclick="goPage('+(currentPage+1)+')" '+(currentPage>=pages?'disabled':'')+'>›</button>';
  pg+='<button onclick="goPage('+pages+')" '+(currentPage>=pages?'disabled':'')+'>末页</button>';
  document.getElementById('pg').innerHTML=pg;
}

function goPage(p){currentPage=p;renderTable();}

// 新增/编辑
var EDIT_MODE='add';
function openForm(){
  EDIT_MODE='add';
  document.getElementById('mt').textContent='新增记录';
  document.getElementById('f_c').value='';
  document.getElementById('f_o').value='';
  document.getElementById('f_ct').value='';
  document.getElementById('f_ph').value='';
  document.getElementById('f_a').value='';
  document.getElementById('f_sv').value='';
  document.getElementById('f_pm').value='';
  document.getElementById('f_q').value='';
  document.getElementById('f_cn').value='';
  document.getElementById('f_sl').value='';
  document.getElementById('f_sd').value='';
  document.getElementById('f_rm').value='';
  document.getElementById('f_idx').value='';
  document.getElementById('fm').textContent='';
  document.getElementById('modal').style.display='block';
}
function editRec(idx){
  var r=filtered[idx];
  if(!r) return;
  EDIT_MODE='edit';
  document.getElementById('mt').textContent='编辑: '+(r.c||'');
  document.getElementById('f_c').value=r.c||'';
  document.getElementById('f_o').value=r.o||'';
  document.getElementById('f_ct').value=r.ct||'';
  document.getElementById('f_ph').value=r.ph||'';
  document.getElementById('f_a').value=r.a||'';
  document.getElementById('f_sv').value=r.sv||'';
  document.getElementById('f_pm').value=r.pm||'';
  document.getElementById('f_q').value=r.q||'';
  document.getElementById('f_cn').value=r.cn||'';
  document.getElementById('f_sl').value=r.sl||'';
  document.getElementById('f_sd').value=r.sd||'';
  document.getElementById('f_rm').value=r.rm||'';
  document.getElementById('f_idx').value=idx;
  document.getElementById('fm').textContent='';
  document.getElementById('modal').style.display='block';
}
function closeForm(){document.getElementById('modal').style.display='none';}
function submitForm(){
  var customer=document.getElementById('f_c').value.trim();
  if(!customer){alert('请填写客户名称');return;}
  var data={
    customer:customer,
    order_no:document.getElementById('f_o').value.trim(),
    contact:document.getElementById('f_ct').value.trim(),
    phone:document.getElementById('f_ph').value.trim(),
    address:document.getElementById('f_a').value.trim(),
    service:document.getElementById('f_sv').value.trim(),
    product:document.getElementById('f_pm').value.trim(),
    qty:document.getElementById('f_q').value.trim(),
    content:document.getElementById('f_cn').value.trim(),
    sales:document.getElementById('f_sl').value.trim(),
    start_date:document.getElementById('f_sd').value.trim(),
    remark:document.getElementById('f_rm').value.trim(),
    pcat:'CX-SV',source:'CRM'
  };
  var payload={action:EDIT_MODE,data:data};
  if(EDIT_MODE==='edit'){
    var idx=parseInt(document.getElementById('f_idx').value);
    if(idx>=0 && idx<filtered.length) payload.original_order_no=filtered[idx].o||'';
  }
  var title='数据编辑:'+(EDIT_MODE==='add'?'新增':'编辑')+':'+data.customer;
  var body='```json\\n'+JSON.stringify(payload,null,2)+'\\n```\\n\\n请直接点 Submit new issue 提交';
  var url='https://github.com/DADIAO007/SV-dispatch-dashboard/issues/new?title='+encodeURIComponent(title)+'&body='+encodeURIComponent(body);
  document.getElementById('fm').innerHTML='<a href="'+url+'" target="_blank" style="color:#1a73e8;font-weight:600">👉 点此打开 GitHub Issue 提交</a><br><span style="color:#999;font-size:11px">提交后2分钟内自动同步到看板</span>';
}
</script>
</body>
</html>'''

with open('/workspace/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ 看板生成: {os.path.getsize('/workspace/dashboard.html')/1024:.1f} KB")
print(f"   内嵌数据: {len(records)} 条记录")
