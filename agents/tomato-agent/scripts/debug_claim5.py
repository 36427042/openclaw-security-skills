#!/usr/bin/env python3
"""
用正确的collectBoxDetailId(tid)来操作
发现get_shop_collect_item_info需要用tid而不是cid
而且claim_to_shop后的shop模式条目需要分别处理

关键问题：
1. claim_to_shop只认领到1个shop（覆盖之前的）
2. 需要生成多个shop模式条目 → 或许需要多次claim_to_shop

策略：
- 先重新claim假睫毛到TH → 生成TH shop条目
- 再重新claim假睫毛到MY → 再生成MY shop条目
- 以此类推
"""
import sys, json, time
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

PRODUCT_NAMES = {
    3579185120: "假睫毛",
    3579185121: "美妆蛋",
}

# 1. 当前TK采集箱中我们的产品
print("=== 当前所有我们的TK产品 ===")
r = client.search_collect_box_list(page_no=1, page_size=50, status="all")
cid_to_tids = {}
for item in r.get("data", {}).get("detailList", []):
    cid = item.get("commonCollectBoxDetailId")
    if cid in ["3579185120", "3579185121", 3579185120, 3579185121]:
        tid = item.get("collectBoxDetailId")
        model = item.get("editModel")
        shops = [s.get('shopId') for s in item.get('collectBoxDetailShopList',[])]
        print(f"  cid={cid} | tid={tid} | model={model} | shops={shops}")
        if cid not in cid_to_tids:
            cid_to_tids[cid] = []
        cid_to_tids[cid].append({"tid": tid, "model": model, "shops": shops})

# 2. 分析：每次claim_to_shop会用site模式的tid生成shop模式条目
# 但之前的claim每次传同一个tid会被覆盖
# 只有site模式的条目才能被认领到新shop
# site模式的tid: 3579185121→2962330294

print("\n=== site模式条目 ===")
site_tids = {}
for cid, entries in cid_to_tids.items():
    for e in entries:
        if e["model"] == "site":
            site_tids[cid] = e["tid"]
            print(f"  cid={cid} → site_tid={e['tid']}")

# 3. 用site模式的tid逐个shop认领
# 先清空旧的shop条目（？），直接重新认领
print("\n=== 逐个shop认领假睫毛 ===")
# 需要用最新的site模式的tid
for site, shop_id in SHOPS.items():
    print(f"  认领假睫毛 → {site} (shop={shop_id})...", end=" ")
    if 3579185120 in site_tids:
        r = client.claim_to_shop([shop_id], [int(site_tids[3579185120])])
        print(f"{'✅' if r.get('code')=='success' else '❌'} {r.get('message','')}")
    else:
        print("❌ 没有site模式的tid")
    time.sleep(0.5)

# 4. 查看结果
print("\n=== 认领后状态 ===")
r = client.search_collect_box_list(page_no=1, page_size=50, status="all")
for item in r.get("data", {}).get("detailList", []):
    cid = item.get("commonCollectBoxDetailId")
    if cid in ["3579185120", "3579185121", 3579185120, 3579185121]:
        tid = item.get("collectBoxDetailId")
        model = item.get("editModel")
        shops = [s.get('shopId') for s in item.get('collectBoxDetailShopList',[])]
        print(f"  cid={cid} | tid={tid} | model={model} | shops={shops}")
