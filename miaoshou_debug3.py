#!/usr/bin/env python3
"""
妙手ERP API - 尝试form-urlencoded格式 和 不同的body格式
"""
import hashlib
import hmac
import json
import time
import requests
import uuid
import urllib.parse

BASE_URL = "https://openapi-erp.91miaoshou.com"
APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"
PATH = "/open/v1/product/common_collect_box/common_collect_box/fetch_item"

def hmac_sha256(key, msg):
    return hmac.new(key.encode(), msg.encode(), hashlib.sha256).hexdigest()

ts = str(int(time.time() * 1000))

# 1. Try form-urlencoded body with nonce
body_data = json.dumps({"urls": ["https://detail.1688.com/offer/test123.html"]})
params = {
    "appKey": APP_KEY,
    "timestamp": ts,
    "nonce": str(uuid.uuid4()).replace('-', '')[:16],
    "signType": "HmacSHA256",
}
# Sort params alphabetically
sorted_items = sorted(params.items())
# Build string: key1=val1&key2=val2...secret
param_str = "&".join(f"{k}={v}" for k, v in sorted_items)
sign_str = param_str + APP_SECRET
sign = hmac_sha256(APP_SECRET, sign_str)

print(f"param_str: {param_str}")
print(f"sign_str: {sign_str[:80]}...")
print(f"sign: {sign}")

headers = {
    "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
}
form_data = {**params, "sign": sign}

try:
    resp = requests.post(f"{BASE_URL}{PATH}", headers=headers, data=form_data, timeout=10)
    print(f"Form-encoded: {resp.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

# 2. Try JSON body combined with URL params
try:
    resp = requests.post(f"{BASE_URL}{PATH}", params=params, 
                        json={"urls": ["https://detail.1688.com/offer/test123.html"]},
                        timeout=10)
    print(f"URL params + JSON body: {resp.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

# 3. Try with AppKey in URL path
try:
    resp = requests.post(f"{BASE_URL}/open/v1/product/common_collect_box/fetch_item",
                        json={"urls": ["test"]},
                        headers={"Content-Type": "application/json", "AppKey": APP_KEY},
                        timeout=10)
    print(f"Shorter path: {resp.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

# 4. Try pass appKey in JSON body
for body_variant in [
    {"appKey": APP_KEY, "urls": ["https://detail.1688.com/offer/test.html"]},
    {"app_key": APP_KEY, "urls": ["https://detail.1688.com/offer/test.html"]},
]:
    try:
        resp = requests.post(f"{BASE_URL}{PATH}", 
                            json=body_variant,
                            headers={"Content-Type": "application/json"},
                            timeout=10)
        print(f"Body with key: {json.dumps(body_variant)[:80]} => {resp.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

# 5. Try GET on fetch_item
try:
    resp = requests.get(f"{BASE_URL}{PATH}", params={"urls": "https://detail.1688.com/offer/test.html"}, timeout=10)
    print(f"GET fetch_item: {resp.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

# 6. Check if there's a V2 endpoint
for v2_path in [
    "/open/v2/product/common_collect_box/fetch_item",
    "/open/api/product/common_collect_box/fetch_item",
    "/api/open/v1/product/common_collect_box/fetch_item",
]:
    try:
        resp = requests.post(f"{BASE_URL}{v2_path}", 
                            json={"urls": ["test"]},
                            headers={"Content-Type": "application/json"},
                            timeout=10)
        print(f"{v2_path}: {resp.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

