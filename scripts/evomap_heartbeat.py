#!/usr/bin/env python3
"""
EvoMap心跳保活脚本 v2.0
每5分钟为7个节点(土豆+6伙伴)发送心跳，保持在线状态
使用正确的伙伴目录映射
"""
import json, os, requests, time, sys
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from gep_engine import GEP
except ImportError:
    GEP = None

# 节点配置：key -> (目录名, 节点ID)
# 2026-05-16: 番茄/玉米/苦瓜因secret过期重新注册，Node ID更新
NODES = {
    "土豆": {"dir": "tomato-agent",        "id": "tudou-commander-001"},
    "番茄": {"dir": "booster-agent",        "id": "node_8dfc28e4dcda8b44"},
    "生菜": {"dir": "lettuce-agent",        "id": "lettuce-copy-001"},
    "玉米": {"dir": "corn-agent",           "id": "node_db18f355082b8e5a"},
    "萝卜": {"dir": "carrot-agent",         "id": "carrot-livestream-001"},
    "苦瓜": {"dir": "bittergourd-agent",    "id": "node_2800add54d53b759"},
    "豌豆": {"dir": "pea-agent",            "id": "pea-data-001"},
}

BASE_DIR = os.path.expanduser("~/.openclaw/workspace/agents")
LOG_FILE = os.path.expanduser("~/.openclaw/workspace/scripts/heartbeat_log.json")

def send_heartbeat(name, node_id, secret):
    """发送心跳"""
    try:
        r = requests.post(
            "https://evomap.ai/a2a/heartbeat",
            json={"node_id": node_id},
            headers={"Authorization": f"Bearer {secret}"},
            timeout=10
        )
        
        if r.status_code == 200:
            data = r.json()
            return {
                "status": "ok",
                "balance": data.get("credit_balance", 0),
                "claimed": data.get("claimed", False),
                "node_status": data.get("node_status", "unknown")
            }
        else:
            return {"status": "error", "code": r.status_code, "message": f"HTTP {r.status_code}: {r.text[:100]}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{ts}] EvoMap心跳保活...")
    
    results = {}
    
    for name, config in NODES.items():
        node_id = config["id"]
        dir_name = config["dir"]
        
        # 读取secret
        secret_file = os.path.join(BASE_DIR, dir_name, ".evomap_secret")
        if not os.path.exists(secret_file):
            print(f"❌ {name}: 未找到secret文件 ({secret_file})")
            results[name] = {"status": "missing_secret"}
            continue
        
        with open(secret_file) as f:
            secret_config = json.load(f)
            secret = secret_config["node_secret"]
        
        # 发送心跳
        result = send_heartbeat(name, node_id, secret)
        results[name] = result
        
        if result["status"] == "ok":
            print(f"✅ {name}: {result['node_status']} | {result['balance']}c")
        else:
            print(f"❌ {name}: {result.get('message', 'unknown error')}")
        
        time.sleep(0.3)
    
    # 保存日志
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results
    }
    
    with open(LOG_FILE, 'w') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    success_count = sum(1 for r in results.values() if r.get("status") == "ok")
    print(f"\n✅ 成功: {success_count}/{len(NODES)} | 日志: {LOG_FILE}")
    
    # GEP recording
    if GEP:
        try:
            outcome = "success" if success_count == len(NODES) else "partial_failure"
            gep = GEP("土豆·系统")
            gep.post_record(task="evomap_heartbeat",
                           context={"nodes": list(NODES.keys()),
                                    "success": success_count,
                                    "total": len(NODES)},
                           outcome=outcome,
                           note=f"EvoMap心跳保活: {success_count}/{len(NODES)}节点在线")
        except Exception as e:
            print(f"⚠️ GEP记录失败: {e}")
    
    return 0 if success_count == len(NODES) else 1

if __name__ == "__main__":
    sys.exit(main())
