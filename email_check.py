#!/usr/bin/env python3
"""
邮件监控脚本（GitHub Actions 版）
IMAP 增量扫描 foxmail 邮箱，只处理 zhouxiangkun@inspur.com 的邮件
解析实施需求并通过 kdocs-cli 追加到金山文档表格
"""
import imaplib
import email
import json
import os
import re
import subprocess
from email.header import decode_header
from datetime import datetime

EMAIL_ADDR = 'xkzhou7936@foxmail.com'
EMAIL_PASS = os.environ.get('FOXMAIL_PASS', '')
IMAP_SERVER = 'imap.qq.com'
FILE_ID = 'nZL1azhGc1MphojViCR2rxeDwtT16Wmce'
WORKSHEET_ID = 27  # 2026派单记录
STATE_FILE = 'email_state.json'
LOG_FILE = 'email_log.json'

def decode_str(s):
    if not s: return ''
    parts = decode_header(s)
    result = []
    for part, charset in parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or 'utf-8', errors='replace'))
        else:
            result.append(part)
    return ''.join(result)

def get_text_body(msg):
    body = ''
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == 'text/plain':
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='replace')
                break
        if not body:
            for part in msg.walk():
                if part.get_content_type() == 'text/html':
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='replace')
                        body = re.sub(r'<[^>]+>', '', body)
                        break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or 'utf-8'
            body = payload.decode(charset, errors='replace')
    return body.strip()

def parse_dispatch(subject, body):
    """从邮件内容解析派单字段"""
    dispatch = {
        'customer': '',
        'contact': '',
        'phone': '',
        'order_no': '',
        'service_type': '',
        'product_model': '',
        'quantity': '',
        'service_content': '',
        'address': '',
        'sales': '',
        'start_date': '',
    }
    
    # 客户名称
    m = re.search(r'客户名称[：:]\s*(.+?)(?:\n|$)', body)
    if m: dispatch['customer'] = m.group(1).strip()
    if not dispatch['customer']:
        m = re.search(r'客户[：:]\s*(.+?)(?:\n|$)', body)
        if m: dispatch['customer'] = m.group(1).strip()
    
    # 联系人
    m = re.search(r'联系人[：:]\s*(.+?)(?:\n|$)', body)
    if m:
        contact_info = m.group(1).strip()
        # 尝试分离姓名和电话
        phone_match = re.search(r'1[3-9]\d{9}', contact_info)
        if phone_match:
            dispatch['phone'] = phone_match.group()
            dispatch['contact'] = contact_info[:phone_match.start()].strip().rstrip(',，、 ')
        else:
            dispatch['contact'] = contact_info
    
    # 电话（单独搜索）
    if not dispatch['phone']:
        m = re.search(r'(?:联系电话|联系方式|电话)[：:]\s*(1[3-9]\d{9})', body)
        if m: dispatch['phone'] = m.group(1)
    if not dispatch['phone']:
        m = re.search(r'(1[3-9]\d{9})', body)
        if m: dispatch['phone'] = m.group(1)
    
    # 单号
    m = re.search(r'(?:特价单号|单号|工单编号)[：:]\s*(CX-SV\d+|JSJTSFW[\w-]+)', body)
    if m: dispatch['order_no'] = m.group(1)
    if not dispatch['order_no']:
        m = re.search(r'(CX-SV\d+)', body)
        if m: dispatch['order_no'] = m.group(1)
    
    # 服务类型（从标题推断）
    if '开箱' in subject or '开箱' in body:
        dispatch['service_type'] = '开箱督导'
    elif '上架' in body:
        dispatch['service_type'] = '硬件安装'
    elif '集成化' in body:
        dispatch['service_type'] = '集成化交付'
    elif '巡检' in subject or '巡检' in body:
        dispatch['service_type'] = '巡检'
    elif '值守' in subject or '值守' in body:
        dispatch['service_type'] = '值守'
    elif '操作系统' in body:
        dispatch['service_type'] = '操作系统安装'
    
    # 实施内容
    m = re.search(r'(?:实施内容|服务内容|需求)[：:]\s*(.+?)(?:\n|$)', body)
    if m: dispatch['service_content'] = m.group(1).strip()
    else:
        # 从标题提取
        if '申请' in subject:
            dispatch['service_content'] = subject.split('申请')[-1].strip()
    
    # 数量
    m = re.search(r'(\d+)\s*台', body)
    if m: dispatch['quantity'] = m.group(1)
    
    # 地址
    m = re.search(r'(?:地址|地点|服务地点)[：:]\s*(.+?)(?:\n|$)', body)
    if m: dispatch['address'] = m.group(1).strip()
    
    # 销售人员
    m = re.search(r'(?:销售|大客户经理|发起人)[：:]\s*(.+?)(?:\n|$)', body)
    if m: dispatch['sales'] = m.group(1).strip()
    
    # 开始时间
    m = re.search(r'(?:要求时间|开始时间|时间)[：:]\s*(.+?)(?:\n|$)', body)
    if m:
        time_str = m.group(1).strip()
        # 尝试转换为 YYYYMMDD
        date_match = re.search(r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})', time_str)
        if date_match:
            dispatch['start_date'] = date_match.group(1) + date_match.group(2).zfill(2) + date_match.group(3).zfill(2)
    
    return dispatch

def kdocs_add_row(dispatch):
    """通过 kdocs-cli 追加一行到金山文档表格"""
    env = {**os.environ, 'PATH': os.environ.get('PATH', '') + ':' + os.path.expanduser('~/.local/bin')}
    
    # 构建行数据 - 2026派单记录的列顺序
    # 0:序号 1:客户名称 2:详细地址 3:联系人 4:联系方式 5:单号 6:服务 7:产品型号
    # 8:数量 9:服务内容 10:实施编号 11:销售 12:联系方式 13:开始时间 14:预计结束时间
    # 15:备注 16:产品类别 17:任务来源
    
    row_data = [
        "",  # 序号(自动)
        dispatch.get('customer', ''),
        dispatch.get('address', ''),
        dispatch.get('contact', ''),
        dispatch.get('phone', ''),
        dispatch.get('order_no', ''),
        dispatch.get('service_type', ''),
        dispatch.get('product_model', ''),
        dispatch.get('quantity', ''),
        dispatch.get('service_content', ''),
        "",  # 实施编号
        dispatch.get('sales', ''),
        "",  # 销售联系方式
        dispatch.get('start_date', ''),
        "",  # 预计结束时间
        "",  # 备注
        "CX-SV",  # 产品类别
        "CRM",  # 任务来源
    ]
    
    payload = {
        'file_id': FILE_ID,
        'worksheet_id': WORKSHEET_ID,
        'row_data': row_data
    }
    
    payload_file = '/tmp/kdocs_payload.json'
    with open(payload_file, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False)
    
    result = subprocess.run(
        ['kdocs-cli', 'sheet', 'add-row', '--file', payload_file, '--silent'],
        capture_output=True, text=True, env=env, timeout=30
    )
    
    return result.returncode == 0, result.stdout + result.stderr

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {'last_uid': 0, 'processed': []}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def main():
    print(f"[{datetime.now().isoformat()}] 邮件监控启动")
    
    if not EMAIL_PASS:
        print("❌ FOXMAIL_PASS 环境变量未设置")
        return
    
    try:
        imap = imaplib.IMAP4_SSL(IMAP_SERVER, 993, timeout=15)
        imap.login(EMAIL_ADDR, EMAIL_PASS)
        imap.select('INBOX')
        
        _, msgs = imap.search(None, 'ALL')
        all_ids = msgs[0].split() if msgs[0] else []
        
        state = load_state()
        new_business = []
        
        for mid in all_ids:
            mi = int(mid)
            if mi <= state['last_uid'] or mi in state['processed']:
                continue
            
            _, data = imap.fetch(mid, '(RFC822)')
            msg = email.message_from_bytes(data[0][1])
            from_addr = decode_str(msg.get('From', ''))
            subject = decode_str(msg.get('Subject', ''))
            date_str = msg.get('Date', '')
            body = get_text_body(msg)
            
            state['processed'].append(mi)
            
            if 'zhouxiangkun@inspur.com' not in from_addr.lower():
                continue
            
            print(f"\n🔔 新业务邮件: {subject}")
            dispatch = parse_dispatch(subject, body)
            print(f"   解析结果: {json.dumps(dispatch, ensure_ascii=False, indent=2)}")
            
            # 写入金山文档
            success, msg_text = kdocs_add_row(dispatch)
            if success:
                print(f"   ✅ 已写入金山文档表格")
            else:
                print(f"   ⚠️ 金山文档写入失败: {msg_text[:100]}")
            
            new_business.append({
                'subject': subject,
                'from': from_addr,
                'date': date_str,
                'dispatch': dispatch,
                'kdocs_synced': success
            })
        
        state['last_uid'] = max(int(m) for m in all_ids) if all_ids else state['last_uid']
        if len(state['processed']) > 500:
            state['processed'] = state['processed'][-500:]
        save_state(state)
        
        imap.logout()
        
        # 保存日志
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'check_time': datetime.now().isoformat(),
                'new_count': len(new_business),
                'items': new_business
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 本次新增: {len(new_business)} 封业务邮件")
        
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == '__main__':
    main()
