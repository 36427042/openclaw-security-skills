#!/usr/bin/env python3
"""
验证claim_to_shop的实际效果
发现claim_to_shop看似逐个成功但最终只保留了1个shop
可能是claim_to_shop覆盖了之前的认领
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

# 1. 先看看当前TK采集箱状态
print("=== 当前TK采集箱状态 ===")
r = client.search_collect_box_list(page_no=1, page_size=50, status="notPublished")
for item in r.get("data", {}).get("detailList", []):
    cid = item.get("commonCollectBoxDetailId")
    tid = item.get("collectBoxDetailId")
    title = item.get("title", "?")[:40]
    edit_model = item.get("editModel")
    shop_list = item.get("collectBoxDetailShopList", [])
    if cid in [3579185120, 3579185121]:
        shops = [s.get('shopId') for s in shop_list]
        print(f"  cid={cid} | tid={tid} | model={edit_model} | shops={shops} | {title}")

# 2. claim_to_shop可以传多个shopIds吗？看妙手API文档
# 之前报错"同个全球店铺下只能选择一个子站点店铺"说明可以传多shopIds
# 但只能选一个子的意思可能是 - 实际上TK全球店铺只允许1个site？
# 那天赐的要求是如何实现的？

# 3. 看看"美妆蛋心形盒"那个产品是怎么做到shop=['14681455']的
print("\n=== 参考产品(已认领到TH) ===")
r = client.get_shop_collect_item_info(detail_id=3509527472, shop_id=14681455)
print(json.dumps(r, ensure_ascii=False)[:500])

# 4. 重新claim到单个shop并检查
print("\n=== 重新claim到TH（只假睫毛）===")
r = client.claim_to_shop([14681455], [2962333377])  # 用老的tid试试
print(f"claim: {r.get('code', r.get('message', '?'))}")

time.sleep(1)

r = client.search_collect_box_list(page_no=1, page_size=50, status="notPublished")
for item in r.get("data", {}).get("detailList", []):
    cid = item.get("commonCollectBoxDetailId")
    tid = item.get("collectBoxDetailId")
    if cid in [3579185120, 3579185121]:
        shop_list = item.get("collectBoxDetailShopList", [])
        shops = [s.get('shopId') for s in shop_list]
        print(f"  cid={cid} | tid={tid} | model={item.get('editModel')} | shops={shops}")
