#!/usr/bin/env python3
"""
🫀 EvoMap Heartbeat — 每5分钟保活
发送心跳到 EvoMap Hub，维持节点在线状态
"""
import json, time, uuid, sys, os
from datetime import datetime, timezone
from urllib import request as ureq, error

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(WORKSPACE, "config", "evomap_a2a.json")

def load_creds():
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ 凭证未找到: {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)

def save_creds(creds):
    with open(CONFIG_PATH, "w") as f:
        json.dump(creds, f, indent=2)

def send_heartbeat(creds):
    """发送心跳"""
    node_id = creds["node_id"]
    secret = creds["node_secret"]

    msg = {
        "protocol": "gep-a2a",
        "protocol_version": "1.0.0",
        "message_type": "heartbeat",
        "message_id": f"hb_{int(time.time())}_{uuid.uuid4().hex[:6]}",
        "sender_id": node_id,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "payload": {
            "status": "alive",
            "load_avg": os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0,
            "memory_free_gb": 0,
            "uptime_seconds": int(time.time() - creds.get("started_at", time.time())),
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {secret}",
    }

    req = ureq.Request(
        "https://evomap.ai/a2a/heartbeat",
        data=json.dumps(msg).encode(),
        headers=headers,
        method="POST",
    )

    with ureq.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
        return data

def gep_engine_post_record(task, context=None, outcome="unknown", problem="", solution=""):
    """Record GEP evolution node for heartbeat tracking."""
    try:
        sys.path.insert(0, "/Users/a1234/.openclaw/workspace/scripts")
        from gep_engine import GEP
        engine = GEP(partner="土豆")
        engine.post_record(
            task=task,
            context=context or {},
            outcome=outcome,
            problem=problem,
            solution=solution,
            note=f"EvoMap心跳-{outcome}" if not problem else f"EvoMap心跳-{problem[:50]}"
        )
    except Exception as e:
        print(f"⚠️ GEP记录失败: {e}")

if __name__ == "__main__":
    try:
        creds = load_creds()
        if "started_at" not in creds:
            creds["started_at"] = time.time()
            save_creds(creds)

        response = send_heartbeat(creds)
        status = response.get("payload", response).get("status", "unknown")
        credits = response.get("payload", response).get("credit_balance", creds.get("credit_balance", 0))

        # 更新凭证
        if creds.get("credit_balance") != credits:
            creds["credit_balance"] = credits
            save_creds(creds)

        if status in ("acknowledged", "ok", "active"):
            print(f"✅ 心跳成功 | node:{response.get('your_node_id','?')} | status:{status} | credits:{credits}")
            gep_engine_post_record("evomap_heartbeat", {"node_id": creds["node_id"], "node_status": "active"}, outcome="success")
        else:
            print(f"⚠ 心跳响应: {status}")
            print(f"   完整响应: {json.dumps(response, ensure_ascii=False)[:200]}")
            gep_engine_post_record("evomap_heartbeat", {"node_id": creds["node_id"], "raw": str(response)[:100]}, outcome="unexpected", problem=f"unknown status:{status}")

    except Exception as e:
        print(f"❌ 心跳失败: {e}")
        gep_engine_post_record("evomap_heartbeat", {}, outcome="error", problem=str(e))
        sys.exit(1)

# ══════════════════════════════════════
# GEP统计快照（每次心跳检查并记录）
# ══════════════════════════════════════
try:
    sys.path.insert(0, "/Users/a1234/.openclaw/workspace/scripts")
    from gep_engine import GEPRegistry

    registry = GEPRegistry()
    stats = registry.get_stats()
    print(f"🧬 GEP: 总{stats.get('total',0)}节点 | 土豆{stats.get('by_partner',{}).get('土豆',0)}条")
except Exception as e:
    print(f"⚠️ GEP统计失败: {e}")
