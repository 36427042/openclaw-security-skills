#!/usr/bin/env python3
"""
🥔 土豆主动推送器
通过飞书Bot API向天赐发消息
用法: python3 scripts/feishu_push.py "消息内容"
"""
import requests, json, sys, os

APP_ID = "cli_a937a620bcb99cc2"
APP_SECRET = "1QWVtHAg7aXrPNKwKe19sgRiJwObNS57"
USER_OPEN_ID = "ou_71152d1258a3112babdbcd1e2523b785"

def get_token():
    r = requests.post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal", 
        json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10)
    data = r.json()
    if data.get("code") != 0:
        raise Exception(f"获取token失败: {data.get('msg')}")
    return data["tenant_access_token"]

def send_text(token, text):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "receive_id": USER_OPEN_ID,
        "msg_type": "text",
        "content": json.dumps({"text": text})
    }
    r = requests.post(
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
        headers=headers, json=payload, timeout=10
    )
    data = r.json()
    if data.get("code") != 0:
        raise Exception(f"发送失败: {data.get('msg')}")
    return data

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 feishu_push.py '消息内容'")
        sys.exit(1)
    
    msg = sys.argv[1]
    try:
        token = get_token()
        result = send_text(token, msg)
        print(f"✅ 推送成功: {msg[:50]}...")
        print(f"   消息ID: {result.get('data',{}).get('message_id','?')}")
    except Exception as e:
        print(f"❌ 推送失败: {e}")
        sys.exit(1)
