#!/usr/bin/env python3
"""
妙手ERP 1688商品采集 - 测试脚本

Credentials:
  AppKey: ak_680398a828ce43de832d342c8dcc89ef
  AppSecret: 325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493
  Base URL: https://openapi-erp.91miaoshou.com
  Auth: HmacSHA256

Endpoints:
  POST /open/v1/product/common_collect_box/common_collect_box/fetch_item
    Body: {"urls": ["https://detail.1688.com/offer/xxx.html", ...]}

  GET/POST /open/v1/product/common_collect_box/common_collect_box/get_common_collect_box_list

多种签名方法测试 + 最终成品函数
"""
import hashlib
import hmac
import json
import time
import requests
import uuid
import base64
from urllib.parse import urlencode

APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"
BASE_URL = "https://openapi-erp.91miaoshou.com"

def hmac_sha256_hex(key, msg):
    return hmac.new(key.encode(), msg.encode(), hashlib.sha256).hexdigest()

def hmac_sha256_b64(key, msg):
    return base64.b64encode(
        hmac.new(key.encode(), msg.encode(), hashlib.sha256).digest()
    ).decode()

def md5(s):
    return hashlib.md5(s.encode()).hexdigest()

# ============ 测试所有可能的签名方法 ============

PATH = "/open/v1/product/common_collect_box/common_collect_box/fetch_item"
BODY = json.dumps({"urls": ["https://detail.1688.com/offer/1234567890.html"]}, ensure_ascii=False, separators=(',', ':'))
TS_MS = str(int(time.time() * 1000))
TS_S = str(int(time.time()))
NONCE = str(uuid.uuid4()).replace('-', '')
NONCE_SHORT = NONCE[:16]

signatures = []

# 根据用户说明: sign = HmacSHA256(secret, secret+path+timestamp+key+body+secret)
msg_a = APP_SECRET + PATH + TS_MS + APP_KEY + BODY + APP_SECRET
s_a = hmac_sha256_hex(APP_SECRET, msg_a)
signatures.append(("secret+path+ts+key+body+secret (hex)", s_a, {"AppKey": APP_KEY, "Timestamp": TS_MS, "Sign": s_a}))

# HmacSHA256 Base64 variant
s_a_b64 = hmac_sha256_b64(APP_SECRET, msg_a)
signatures.append(("secret+path+ts+key+body+secret (b64)", s_a_b64, {"AppKey": APP_KEY, "Timestamp": TS_MS, "Sign": s_a_b64}))

# Path + Timestamp + Key + Body (no secret wrapping)
msg_b = PATH + TS_MS + APP_KEY + BODY
s_b = hmac_sha256_hex(APP_SECRET, msg_b)
signatures.append(("path+ts+key+body", s_b, {"AppKey": APP_KEY, "Timestamp": TS_MS, "Sign": s_b}))

# Secret + path + ts + key (no body)
msg_c = APP_SECRET + PATH + TS_MS + APP_KEY + APP_SECRET
s_c = hmac_sha256_hex(APP_SECRET, msg_c)
signatures.append(("secret+path+ts+key+secret", s_c, {"AppKey": APP_KEY, "Timestamp": TS_MS, "Sign": s_c}))

# Body MD5 + Path + Key
msg_d = md5(BODY) + PATH + APP_KEY + TS_MS
s_d = hmac_sha256_hex(APP_SECRET, msg_d)
signatures.append(("md5(body)+path+key+ts", s_d, {"AppKey": APP_KEY, "Timestamp": TS_MS, "Sign": s_d}))

# 参数拼接格式: appKey=xxx&timestamp=xxx&body=xxx (sorted alphabetically)
param_str = f"body={BODY}&timestamp={TS_MS}&appKey={APP_KEY}"
msg_e = param_str + APP_SECRET
s_e = hmac_sha256_hex(APP_SECRET, msg_e)
signatures.append(("sorted params (key=val) + secret", s_e, {"AppKey": APP_KEY, "Timestamp": TS_MS, "Sign": s_e}))

# appKey + appSecret + nonce + timestamp 排序拼接
params_f = {
    "appKey": APP_KEY,
    "appSecret": APP_SECRET,
    "nonce": NONCE_SHORT,
    "timestamp": TS_MS,
}
sorted_f = "&".join(f"{k}={v}" for k, v in sorted(params_f.items()))
s_f = hmac_sha256_hex(APP_SECRET, sorted_f)
signatures.append(("sorted(appKey,appSecret,nonce,ts)", s_f, {"AppKey": APP_KEY, "Timestamp": TS_MS, "Nonce": NONCE_SHORT, "Sign": s_f}))

# appKey + timestamp + nonce + body + appSecret 
msg_g = f"appKey={APP_KEY}&timestamp={TS_MS}&nonce={NONCE_SHORT}&body={BODY}&appSecret={APP_SECRET}"
s_g = hmac_sha256_hex(APP_SECRET, msg_g.replace("&appSecret=" + APP_SECRET, ""))
signatures.append(("key=val&... (no secret in msg)", s_g, {"AppKey": APP_KEY, "Timestamp": TS_MS, "Nonce": NONCE_SHORT, "Sign": s_g}))

# Try with different header naming
signatures.append(("path+ts+key (lowercase headers)", s_b, {"appKey": APP_KEY, "timestamp": TS_MS, "sign": s_b}))
signatures.append(("path+ts+key (X-Ca-* headers)", s_b, {"X-Ca-Key": APP_KEY, "X-Ca-Timestamp": TS_MS, "X-Ca-Signature": s_b}))

# ============ Execute all tests ============
print(f"Testing {len(signatures)} signature variants against {PATH}")
print(f"Body: {BODY}")
print(f"Timestamp: {TS_MS}")
print(f"Nonce: {NONCE_SHORT}")
print("=" * 70)

success = False
for label, sign, headers in signatures:
    h = {"Content-Type": "application/json", **headers}
    try:
        resp = requests.post(f"{BASE_URL}{PATH}", headers=h, data=BODY, timeout=10)
        result = resp.json()
        code = result.get("code", "?")
        msg = result.get("message", "?")
        if code == "systemError":
            status = "❌ AUTH_FAIL"
        elif code == "success" or result.get("result") == "success":
            status = "✅ SUCCESS!"
            success = True
        else:
            status = f"⚠️ {code}: {msg}"
        print(f"[{status}] {label}")
        print(f"  sign[0:40]: {sign[:40]}...")
        if code != "systemError":
            print(f"  response: {resp.text[:300]}")
    except Exception as e:
        print(f"[ERROR] {label}: {e}")

if success:
    print("\n✅ FOUND WORKING SIGNATURE METHOD!")
else:
    print("\n❌ None of the signature methods worked with the current header pattern.")
    print("Possibilities:")
    print("  1. API requires first calling an auth endpoint for a session token")
    print("  2. AppKey/AppSecret is a different credential format (base64 decoded?)")
    print("  3. API requires specific format for path/body")
    print("  4. The openapi-erp.91miaoshou.com endpoint is not the correct API gateway")
    print("  5. Need to contact Miaoshou directly for API documentation")

