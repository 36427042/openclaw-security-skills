#!/usr/bin/env python3
"""
调试publish - 用tid代替cid
还有检查claim后实际状态
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

# 1. 看当前状态
print("=== 当前所有条目 ===")
r = client.search_collect_box_list(page_no=1, page_size=50, status="notPublished")

shop_items = {}
for item in r.get("data", {}).get("detailList", []):
    cid = item.get("commonCollectBoxDetailId")
    if cid in ["3579185120", "3579185121", 3579185120, 3579185121]:
        tid = item.get("collectBoxDetailId")
        model = item.get("editModel")
        shops = [s.get('shopId') for s in item.get('collectBoxDetailShopList',[])]
        print(f"  cid={cid} | tid={tid} | model={model} | shops={shops}")
        if model == "shop" and shops:
            shop_items[tid] = {"cid": cid, "shops": shops}

print(f"\nshop模式条目: {shop_items}")

# 2. 用tid和shopId尝试publish
# 假设publish的detailId需要是collectBoxDetailId (tid)
for tid, info in shop_items.items():
    for shop_id in info["shops"]:
        print(f"\n  publish tid={tid} shop={shop_id}...", end=" ")
        r = client.publish([shop_id], [int(tid)])
        if r.get("code") == "success":
            print(f"✅")
        else:
            print(f"❌ {r.get('message', '')}")

# 3. 再看看另一个产品的get_shop状态
print("\n=== get_shop_collect_item_info (用最新的tid) ===")
# 最新的假睫毛→TH
r = client.get_shop_collect_item_info(detail_id=2962340037, shop_id=14681455)
print(f"tid=2962340037, TH: code={r.get('code')}, data={json.dumps(r.get('data',{}), ensure_ascii=False)[:300]}")

# 4. 用tid查shop状态
# 试试collect_box的另一个API
# 看文档，也许publish需要先确认claim_to_shop是否真的创建了shop条目
print("\n=== shop claim验证 ===")
for site, shop_id in SHOPS.items():
    print(f"\n{site}(shop={shop_id}):")
    # 用公共采集箱cid查
    r = client.get_shop_collect_item_info(detail_id=3579185120, shop_id=shop_id)
    print(f"  cid=3579185120: code={r.get('code')} msg={r.get('message','')}")
    # 用tid查
    r = client.get_shop_collect_item_info(detail_id=2962340037, shop_id=shop_id)
    print(f"  tid=2962340037: code={r.get('code')} msg={r.get('message','')}")
