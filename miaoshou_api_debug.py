#!/usr/bin/env python3
"""
妙手ERP API 签名测试脚本
测试多种常见的签名/header格式
"""
import hashlib
import hmac
import json
import time
import requests
import uuid

BASE_URL = "https://openapi-erp.91miaoshou.com"
APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"

def hmac_sha256_hex(key, message):
    """HMAC-SHA256 返回十六进制小写"""
    return hmac.new(
        key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def hmac_sha256_base64(key, message):
    """HMAC-SHA256 返回 Base64"""
    return hmac.new(
        key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest().hex()  # 先试hex

PATH = "/open/v1/product/common_collect_box/common_collect_box/fetch_item"
BODY = json.dumps({"urls": ["https://detail.1688.com/offer/test123.html"]}, ensure_ascii=False)
TIMESTAMP_MS = str(int(time.time() * 1000))
TIMESTAMP_S = str(int(time.time()))
NONCE = str(uuid.uuid4()).replace('-', '')

results = []

# 测试方法1: sign = HmacSHA256(secret, secret+path+timestamp+key+body+secret)
msg1 = APP_SECRET + PATH + TIMESTAMP_MS + APP_KEY + BODY + APP_SECRET
sign1 = hmac_sha256_hex(APP_SECRET, msg1)
results.append(("方法1: secret+path+ts+key+body+secret", sign1, msg1))

# 测试方法2: sign = HmacSHA256(secret, path+timestamp+key+body)
msg2 = PATH + TIMESTAMP_MS + APP_KEY + BODY
sign2 = hmac_sha256_hex(APP_SECRET, msg2)
results.append(("方法2: path+ts+key+body", sign2, msg2))

# 测试方法3: 参数拼接排序
params3 = f"appKey={APP_KEY}&timestamp={TIMESTAMP_MS}&body={BODY}"
msg3 = params3 + "&secret=" + APP_SECRET
sign3 = hmac_sha256_hex(APP_SECRET, msg3)
results.append(("方法3: key=value排序+secret", sign3, msg3))

# 测试方法4: 阿里云API网关风格
msg4 = f"POST\n\napplication/json\n\n\n\n{PATH}"
sign4 = hmac_sha256_hex(APP_SECRET, msg4)
results.append(("方法4: 阿里云API网关风格", sign4, msg4))

# 测试方法5: 纯body HMAC-SHA256
sign5 = hmac_sha256_hex(APP_SECRET, BODY)
results.append(("方法5: HMAC(secret, body)", sign5, BODY))

# 测试方法6: timestamp+secret
msg6 = TIMESTAMP_MS + APP_SECRET
sign6 = hmac_sha256_hex(APP_SECRET, msg6)
results.append(("方法6: timestamp+secret", sign6, msg6))

# 测试方法7: secret+timestamp
msg7 = APP_SECRET + TIMESTAMP_MS
sign7 = hmac_sha256_hex(APP_SECRET, msg7)
results.append(("方法7: secret+timestamp", sign7, msg7))

# 测试方法8: path+timestamp+key (不带body)
msg8 = PATH + TIMESTAMP_S + APP_KEY
sign8 = hmac_sha256_hex(APP_SECRET, msg8)
results.append(("方法8: path+ts(s)+key", sign8, msg8))

# 测试方法9: MD5(body) 拼接
body_md5 = hashlib.md5(BODY.encode('utf-8')).hexdigest()
msg9 = APP_SECRET + PATH + TIMESTAMP_MS + APP_KEY + body_md5 + APP_SECRET
sign9 = hmac_sha256_hex(APP_SECRET, msg9)
results.append(("方法9: secret+path+ts+key+md5(body)+secret", sign9, msg9))

# Header 命名变体
header_variants = [
    {"AppKey": APP_KEY, "Timestamp": TIMESTAMP_MS, "Sign": sign1},
    {"appKey": APP_KEY, "timestamp": TIMESTAMP_MS, "sign": sign1},
    {"X-Ca-Key": APP_KEY, "X-Ca-Timestamp": TIMESTAMP_MS, "X-Ca-Signature": sign1},
    {"app_key": APP_KEY, "timestamp": TIMESTAMP_MS, "sign": sign1},
    {"App-Key": APP_KEY, "Timestamp": TIMESTAMP_MS, "Sign": sign1},
]

# 每种签名方法 + 每种header变体 尝试一次
for label, sign, msg in results:
    print(f"\n=== {label} ===")
    print(f"  sign(前40): {sign[:40]}...")
    print(f"  msg(前80): {msg[:80]}...")
    
    # Use "AppKey" "Timestamp" "Sign" headers (most common in ERP APIs)
    headers = {
        "Content-Type": "application/json",
        "AppKey": APP_KEY,
        "Timestamp": TIMESTAMP_MS,
        "Sign": sign,
    }
    try:
        resp = requests.post(
            f"{BASE_URL}{PATH}",
            headers=headers,
            data=BODY,
            timeout=10
        )
        data = resp.json()
        print(f"  响应: {json.dumps(data, ensure_ascii=False)[:200]}")
        if data.get("result") == "fail" and "sign" not in json.dumps(data).lower() and "auth" not in json.dumps(data).lower():
            # 如果是其他错误，可能说明签名通过了
            pass
    except Exception as e:
        print(f"  错误: {e}")

print("\n\n===== 额外测试其他header命名 =====")
# 只用方法1尝试不同的header命名
sign = sign1
for hdr in header_variants:
    headers = {"Content-Type": "application/json", **hdr}
    print(f"\n  Headers: {hdr}")
    try:
        resp = requests.post(
            f"{BASE_URL}{PATH}",
            headers=headers,
            data=BODY,
            timeout=10
        )
        print(f"  响应: {resp.text[:200]}")
    except Exception as e:
        print(f"  错误: {e}")

