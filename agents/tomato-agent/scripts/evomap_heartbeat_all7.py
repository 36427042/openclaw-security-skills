#!/usr/bin/env python3
"""
🫀 EvoMap A2A Heartbeat — All 7 Nodes v2 (2026-05-16)
每5分钟向所有7个节点发送心跳
"""
import json, time, uuid, os, sys
from datetime import datetime, timezone
from urllib import request as ureq

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "evomap_a2a.json")

def load_nodes():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    
    nodes = [{
        'name': '🥔 土豆·统筹',
        'key': 'hub',
        'node_id': cfg['node_id'],
        'secret': cfg['node_secret'],
    }]
    
    partner_map = {
        'booster': '🍅 番茄·选品',
        'copy': '🥬 生菜·文案',
        'video': '🌽 玉米·视频',
        'tts': '🥕 萝卜·配音',
        'risk': '🥒 苦瓜·风控',
        'data': '🫘 豌豆·数据',
    }
    
    for key, name in partner_map.items():
        p = cfg['partners'].get(key, {})
        if p.get('node_id'):
            nodes.append({
                'name': name,
                'key': key,
                'node_id': p['node_id'],
                'secret': p.get('secret', ''),
            })
    
    return nodes

def send_heartbeat(node):
    msg = {
        'protocol': 'gep-a2a',
        'protocol_version': '1.0.0',
        'message_type': 'heartbeat',
        'message_id': f'hb_{int(time.time())}_{uuid.uuid4().hex[:6]}',
        'sender_id': node['node_id'],
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'payload': {
            'status': 'alive',
            'load_avg': os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0,
            'uptime_seconds': 0,
        }
    }
    
    req = ureq.Request(
        'https://evomap.ai/a2a/heartbeat',
        data=json.dumps(msg).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {node["secret"]}'},
        method='POST',
    )
    
    with ureq.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())

if __name__ == '__main__':
    nodes = load_nodes()
    ok = 0
    fail = 0
    for node in nodes:
        try:
            r = send_heartbeat(node)
            status = r.get('status', r.get('node_status', '?'))
            claimed = r.get('claimed', '?')
            ok += 1
            print(f'  ✅ {node["name"]:12s} {status:4s} claimed={claimed}')
        except Exception as e:
            fail += 1
            print(f'  ❌ {node["name"]:12s} {str(e)[:80]}')
        time.sleep(0.2)
    
    print(f'\n📊 {ok}/{len(nodes)} OK | {fail} fail')
    sys.exit(0 if fail == 0 else 1)
