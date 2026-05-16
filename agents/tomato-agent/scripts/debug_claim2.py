#!/usr/bin/env python3
"""
调试：逐个shop认领claim_to_shop
之前"同个全球店铺下只能选择一个子站点店铺" - 逐个试
"""
import sys, json
sys.path.insert(0, "/Users/a1234/.openclaw/workspace/agents/tomato-agent/scripts")
from miaoshou_client import MiaoshouClient

APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"

client = MiaoshouClient(APP_KEY, APP_SECRET)

SHOPS = {
    "TH": 14681455,
    "MY": 14772485,
    "VN": 14681328,
    "PH": 14772551,
    "SG": 14772775,
}

# TK采集箱中的collectBoxDetailId（需要拿最新的）
print("=== 获取TK采集箱最新版本 ===")
r = client.search_collect_box_list(page_no=1, page_size=20, status="notPublished")
items = {}
for item in r.get("data", {}).get("detailList", []):
    cid = item.get("commonCollectBoxDetailId")
    tid = item.get("collectBoxDetailId")
    title = item.get("title", "?")[:30]
    if cid not in items and item.get("editModel") == "site":
        items[cid] = {"collectBoxDetailId": tid, "title": title}
        print(f"  commonCollectBoxDetailId={cid} → collectBoxDetailId={tid} | {title}")

# 只取最新版本的
our_items = {"3579185120": None, "3579185121": None}
for cid_str in our_items:
    if cid_str in items:
        our_items[cid_str] = items[cid_str]
        print(f"  ✅ 找到 {cid_str}: {items[cid_str]['title']} → dict={items[cid_str]['collectBoxDetailId']}")

print(f"\n=== 逐个shop认领 ===")
product_mapping = [
    ("假睫毛", 3579185120, our_items["3579185120"]["collectBoxDetailId"]),
    ("美妆蛋", 3579185121, our_items["3579185121"]["collectBoxDetailId"]),
]

for pname, cid, tid in product_mapping:
    print(f"\n--- {pname} (commonCid={cid}, tkCid={tid}) ---")
    for site, shop_id in SHOPS.items():
        print(f"  认领到{site} (shop={shop_id})...", end=" ")
        r = client.claim_to_shop([shop_id], [int(tid)])
        if r.get("code") == "success":
            print(f"✅")
        else:
            print(f"❌ {r.get('message', r)}")
