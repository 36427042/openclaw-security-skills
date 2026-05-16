#!/usr/bin/env python3
"""
妙手ERP API 深度调试 - 尝试不同的路径和参数格式
"""
import hashlib
import hmac
import json
import time
import requests

BASE_URL = "https://openapi-erp.91miaoshou.com"
APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"

def hmac_sha256_hex(key, message):
    return hmac.new(
        key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

ts = str(int(time.time() * 1000))

# 端点列表
endpoints = [
    # POST - 采集商品
    ("POST", "/open/v1/product/common_collect_box/common_collect_box/fetch_item", 
     json.dumps({"urls": ["https://detail.1688.com/offer/test123.html"]})),
    # GET - 查看采集箱列表
    ("GET", "/open/v1/product/common_collect_box/common_collect_box/get_common_collect_box_list", None),
]

# 尝试不同的sign方法
sign_methods = []

# 基础: AppKey/Secret直接作为参数
sign_methods.append(("HMAC_RAW(secret)", 
    lambda: hmac_sha256_hex(APP_SECRET, "")))

for method, path, body in endpoints:
    print(f"\n{'='*60}")
    print(f"{method} {path}")
    
    # 尝试1: GET with query params
    if method == "GET":
        params = {
            "appKey": APP_KEY,
            "timestamp": ts,
            "sign": hmac_sha256_hex(APP_SECRET, path + ts + APP_KEY)
        }
        try:
            resp = requests.get(f"{BASE_URL}{path}", params=params, timeout=10)
            print(f"  GET with params: {resp.text[:300]}")
        except Exception as e:
            print(f"  Error: {e}")
    
    # 尝试2: POST with JSON body, various header patterns
    if method == "POST":
        for hdr_sign in [
            ("AppKey+Timestamp+Sign(hex)", {"AppKey": APP_KEY, "Timestamp": ts, "Sign": hmac_sha256_hex(APP_SECRET, APP_SECRET + path + ts + APP_KEY + body + APP_SECRET)}),
            ("appKey+timestamp+sign(hex)", {"appKey": APP_KEY, "timestamp": ts, "sign": hmac_sha256_hex(APP_SECRET, path + ts + APP_KEY + body)}),
            ("X-Ca-* pattern", {"X-Ca-Key": APP_KEY, "X-Ca-Timestamp": ts, "X-Ca-Signature": hmac_sha256_hex(APP_SECRET, path + ts + APP_KEY)}),
        ]:
            label, hdrs = hdr_sign
            hdrs["Content-Type"] = "application/json"
            try:
                resp = requests.post(f"{BASE_URL}{path}", headers=hdrs, data=body, timeout=10)
                print(f"  {label}: {resp.text[:300]}")
            except Exception as e:
                print(f"  Error: {e}")
    
    # 尝试3: 传参在URL里
    if method == "POST":
        params = {
            "appKey": APP_KEY,
            "timestamp": ts,
            "sign": hmac_sha256_hex(APP_SECRET, path + ts + APP_KEY),
        }
        try:
            resp = requests.post(f"{BASE_URL}{path}", params=params, data=body, 
                               headers={"Content-Type": "application/json"}, timeout=10)
            print(f"  POST with URL params: {resp.text[:300]}")
        except Exception as e:
            print(f"  Error: {e}")

# 尝试 - 用sessionToken / login方式
print("\n\n===== 尝试API需要先登录/获取token =====")
# 尝试用GET请求看看有哪些公开接口
for test_path in [
    "/doc",
    "/docs",
    "/api-docs",
    "/swagger-resources",
    "/v2/api-docs",
    "/open/v1/product/common_collect_box/list",
    "/open/v1/product/common_collect_box/get_common_collect_box_list",
    "/test",
    "/ping",
    "/health",
]:
    try:
        resp = requests.get(f"{BASE_URL}{test_path}", timeout=10)
        print(f"  GET {test_path}: {resp.status_code} - {resp.text[:200]}")
    except Exception as e:
        print(f"  GET {test_path}: Error - {e}")

