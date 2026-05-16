#!/usr/bin/env python3
"""
🥬 生菜·TK Shop认领+发布全流程 - 修正版

正确流程（从记忆中的全链路流程）:
1. claimed → TK采集箱（site模式）
2. save_site_collect_item_info → 设置定价（在site模式时做）
3. claim_to_shop → 认领到具体店铺
4. publish

注意：TK global店铺下，每个产品只能认领到1个shop（因为site模式的tid在claim_to_shop后变成shop模式）
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

ALL_SHOP_IDS = list(SHOPS.values())

PRODUCT_INFO = [
    {"cid": 3579185120, "name": "假睫毛", "prices": {"TH": "63", "MY": "9", "VN": "52000", "PH": "123", "SG": "2.30"}},
    {"cid": 3579185121, "name": "美妆蛋", "prices": {"TH": "50", "MY": "7", "VN": "41000", "PH": "97", "SG": "1.80"}},
]

def print_state():
    r = client.search_collect_box_list(page_no=1, page_size=50, status="notPublished")
    for item in r.get("data", {}).get("detailList", []):
        cid = item.get("commonCollectBoxDetailId")
        if cid in ["3579185120", "3579185121", 3579185120, 3579185121]:
            tid = item.get("collectBoxDetailId")
            model = item.get("editModel")
            shops = [s.get('shopId') for s in item.get('collectBoxDetailShopList',[])]
            print(f"  cid={cid} | tid={tid} | model={model} | shops={shops}")

# =========================================
# STEP 0: 检查当前状态
# =========================================
print("="*60)
print("[Step 0] 当前TK采集箱状态 (只显示我们的产品)")
print("="*60)
print_state()

# =========================================
# STEP 1: 重新claimed到TK采集箱
# 先看有没有site模式的，如果没有就重新claim
# =========================================
print("\n" + "="*60)
print("[Step 1] 检查/重建site模式条目")
print("="*60)

# 找出已有的site模式
r = client.search_collect_box_list(page_no=1, page_size=50, status="notPublished")
existing_site_cids = set()
for item in r.get("data", {}).get("detailList", []):
    cid = item.get("commonCollectBoxDetailId")
    model = item.get("editModel")
    if cid in ["3579185120", "3579185121", 3579185120, 3579185121] and model == "site":
        existing_site_cids.add(int(cid) if isinstance(cid, str) else cid)
        print(f"  ✅ 已有site模式: cid={cid}")

for p in PRODUCT_INFO:
    cid = p["cid"]
    if cid not in existing_site_cids:
        print(f"  假睫毛(cid={cid}) 没有site模式，重新claimed...")
        r = client.claimed([{"detailId": cid, "platform": "tiktok", "serialNumber": 1}])
        if r.get("code") == "success":
            print(f"  ✅ claimed成功")
        else:
            print(f"  ❌ claimed失败: {r.get('message','')}")

time.sleep(2)

print("\n=== claimed后状态 ===")
print_state()

# =========================================
# STEP 2: save_site_collect_item_info → 定价
# =========================================
print("\n" + "="*60)
print("[Step 2] 💰 save_site_collect_item_info — 设置站点模式定价")
print("="*60)

# 重新获取site模式的tid
r = client.search_collect_box_list(page_no=1, page_size=50, status="notPublished")
site_tids = {}
for item in r.get("data", {}).get("detailList", []):
    cid = item.get("commonCollectBoxDetailId")
    if cid in ["3579185120", "3579185121", 3579185120, 3579185121] and item.get("editModel") == "site":
        site_tids[int(cid) if isinstance(cid, str) else cid] = item.get("collectBoxDetailId")

for p in PRODUCT_INFO:
    cid = p["cid"]
    if cid not in site_tids:
        print(f"  ❌ {p['name']} 没有site模式，跳过定价")
        continue
    tid = site_tids[cid]
    
    for site in SHOPS:
        price = p["prices"][site]
        print(f"  {p['name']} → {site} (cid={cid}, tid={tid}) 定价={price}")
        
        # 获取site模式详情
        r_info = client.get_site_collect_item_info(detail_id=cid, site=site)
        if r_info.get("code") == "success":
            data = r_info.get("data", {})
            oss_md5 = data.get("ossMd5", "")
            print(f"    ossMd5={'有' if oss_md5 else '空'}, get_site成功")
            
            price_info = {
                "price": price,
                "productName": p["name"],
            }
            r_save = client.save_site_collect_item_info(
                oss_md5=oss_md5,
                detail_id=cid,
                site=site,
                info=price_info
            )
            if r_save.get("code") == "success":
                print(f"    ✅ 定价成功")
            else:
                print(f"    ❌ 定价失败: {r_save.get('message', json.dumps(r_save, ensure_ascii=False)[:200])}")
        else:
            print(f"    ⚠️  获取site详情失败: {r_info.get('message', json.dumps(r_info, ensure_ascii=False)[:200])}")
        
        time.sleep(0.3)

# =========================================
# STEP 3: claim_to_shop
# =========================================
print("\n" + "="*60)
print("[Step 3] 📦 claim_to_shop (用site模式的tid)")
print("="*60)

# 用site模式的tid claim
for p in PRODUCT_INFO:
    cid = p["cid"]
    if cid not in site_tids:
        print(f"  ❌ {p['name']} 没有site模式的tid，跳过claim")
        continue
    tid = int(site_tids[cid])
    
    # 逐个shop claim
    for site, shop_id in SHOPS.items():
        print(f"  {p['name']} → {site} (shop={shop_id}, tid={tid})...", end=" ")
        r = client.claim_to_shop([shop_id], [tid])
        if r.get("code") == "success":
            print(f"✅")
        else:
            print(f"❌ {r.get('message','')}")
        time.sleep(0.5)

time.sleep(2)

# =========================================
# STEP 4: publish (用公共采集箱的cid)
# =========================================
print("\n" + "="*60)
print("[Step 4] 🚀 publish")
print("="*60)

# 注意：publish用的detailIds是公共采集箱的commonCollectBoxDetailId
# shopIds是所有要发布的shop
print("  尝试publish到所有5国...")
r = client.publish(ALL_SHOP_IDS, [3579185120, 3579185121])
if r.get("code") == "success":
    print(f"  ✅ publish成功: {json.dumps(r, ensure_ascii=False)[:500]}")
else:
    print(f"  ❌ publish失败: {r.get('message', json.dumps(r, ensure_ascii=False)[:500])}")
    # 如果全部不行，尝试逐个shop publish
    print("\n  尝试逐个shop publish...")
    for site, shop_id in SHOPS.items():
        print(f"  publish到{site}(shop={shop_id})...", end=" ")
        r = client.publish([shop_id], [3579185120, 3579185121])
        if r.get("code") == "success":
            print(f"✅")
        else:
            print(f"❌ {r.get('message','')}")
        time.sleep(1)

print("\n" + "="*60)
print("📋 完成")
print("="*60)
