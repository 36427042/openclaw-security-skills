#!/usr/bin/env python3
"""
🥕 萝卜EvoMap Web Claim (午夜执行)
- 天赐说一天只能绑5个, 萝卜过了12点绑定
- 使用A2A HTTP协议完成web claim
- 只需执行一次
"""
import json, sys, os
from datetime import datetime

CONFIG_PATH = os.path.expanduser("~/.openclaw/workspace/agents/tomato-agent/config/evomap_a2a.json")

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def main():
    config = load_config()
    carrot = config.get("partners", {}).get("tts", {})
    
    print(f"🥕 萝卜EvoMap Web Claim")
    print(f"   Time: {datetime.now().isoformat()}")
    print(f"   Node ID: {carrot.get('node_id', '?')}")
    print(f"   Claim URL: {carrot.get('claim_url', '?')}")
    print(f"   Claim Code: {carrot.get('claim_code', '?')}")
    print(f"   Bound (A2A): {carrot.get('bound', '?')}")
    print()
    print("请天赐在EvoMap网站完成web claim:")
    print(f"  1. 访问: {carrot.get('claim_url', '?')}")
    print(f"  2. 登录EvoMap账号")
    print(f"  3. 确认绑定→萝卜节点上线")
    print()
    
    # Log to file
    log_path = os.path.expanduser("~/.openclaw/workspace/agents/tomato-agent/memory/midnight_claim.md")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w") as f:
        f.write(f"# 🥕 萝卜午夜Web Claim\n")
        f.write(f"- Time: {datetime.now().isoformat()}\n")
        f.write(f"- Node ID: {carrot.get('node_id', '?')}\n")
        f.write(f"- Claim URL: {carrot.get('claim_url', '?')}\n")
        f.write(f"- Claim Code: {carrot.get('claim_code', '?')}\n")
        f.write(f"- Status: ⏳ 待天赐web确认\n")
    
    print(f"✅ 已写入日志: {log_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
