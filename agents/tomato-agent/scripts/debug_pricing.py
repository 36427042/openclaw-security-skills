#!/usr/bin/env python3
"""
STEP 3.5: 查claim_to_shop后的TK采集箱状态
STEP 4:   save_shop_collect_item_info (定价)
STEP 5:   publish
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
    3579185120: "10对硬梗假睫毛一整条",
    3579185121: "美妆蛋粉扑4件套",
}

PRICES = {
    3579185120: {"TH": "63", "MY": "9", "VN": "52000", "PH": "123", "SG": "2.30"},
    3579185121: {"TH": "50", "MY": "7", "VN": "41000", "PH": "97", "SG": "1.80"},
}

# =========================================
# STEP 3.5: 确认claim后状态
# =========================================
print("="*60)
print("[Step 3.5] 确认claim后TK采集箱状态")
print("="*60)

r = client.search_collect_box_list(page_no=1, page_size=50, status="notPublished")
items = {}
for item in r.get("data", {}).get("detailList", []):
    cid = item.get("commonCollectBoxDetailId")
    tid = item.get("collectBoxDetailId")
    title = item.get("title", "?")[:40]
    edit_model = item.get("editModel")
    shop_list = item.get("collectBoxDetailShopList", [])
    print(f"  cid={cid} | tid={tid} | model={edit_model} | shops={[s.get('shopId') for s in shop_list]} | {title}")
    items[cid] = {"tid": tid, "editModel": edit_model, "shopList": shop_list}

# 等待系统处理
time.sleep(1)

# =========================================
# STEP 4: save_shop_collect_item_info (定价)
# =========================================
print("\n" + "="*60)
print("[Step 4] 💰 save_shop_collect_item_info — 设置定价")
print("="*60)

for did in [3579185120, 3579185121]:
    print(f"\n--- {PRODUCT_NAMES[did]} ---")
    for site, shop_id in SHOPS.items():
        price = PRICES[did][site]
        print(f"  {site} (shop={shop_id}) 定价={price}")
        
        # 获取详情（拿ossMd5）
        r_info = client.get_shop_collect_item_info(detail_id=did, shop_id=shop_id)
        
        if r_info.get("code") == "success":
            data = r_info.get("data", {})
            oss_md5 = data.get("ossMd5", "")
            print(f"    ossMd5={'有' if oss_md5 else '空'}, get_shop成功")
            
            # 构建定价信息 - 按妙手API要求
            price_info = {
                "price": price,
                "productName": PRODUCT_NAMES[did],
            }
            
            r_save = client.save_shop_collect_item_info(
                oss_md5=oss_md5,
                detail_id=did,
                shop_id=shop_id,
                info=price_info
            )
            if r_save.get("code") == "success":
                print(f"    ✅ 定价成功")
            else:
                print(f"    ❌ 定价失败: {r_save.get('message', json.dumps(r_save, ensure_ascii=False)[:200])}")
        else:
            # 尝试站点模式
            print(f"    ⚠️  店铺模式失败({r_info.get('message','?')}), 试站点模式...")
            r_site = client.get_site_collect_item_info(detail_id=did, site=site)
            if r_site.get("code") == "success":
                data = r_site.get("data", {})
                oss_md5 = data.get("ossMd5", "")
                price_info = {
                    "price": price,
                    "productName": PRODUCT_NAMES[did],
                }
                r_save = client.save_site_collect_item_info(
                    oss_md5=oss_md5,
                    detail_id=did,
                    site=site,
                    info=price_info
                )
                if r_save.get("code") == "success":
                    print(f"    ✅ 站点模式定价成功")
                else:
                    print(f"    ❌ 站点模式定价失败: {r_save.get('message', json.dumps(r_save, ensure_ascii=False)[:200])}")
            else:
                print(f"    ❌ {site} 两种模式都失败: {json.dumps(r_info, ensure_ascii=False)[:200]}")
        
        time.sleep(0.5)

time.sleep(2)

# =========================================
# STEP 5: publish
# =========================================
print("\n" + "="*60)
print("[Step 5] 🚀 publish 到全部5国→7条")
print("="*60)

# publish需要detailId = 公共采集箱的commonCollectBoxDetailId
r5 = client.publish(list(SHOPS.values()), [3579185120, 3579185121])
if r5.get("code") == "success":
    print(f"  ✅ publish成功: {json.dumps(r5, ensure_ascii=False)[:500]}")
else:
    print(f"  ❌ publish失败: {r5.get('message', json.dumps(r5, ensure_ascii=False)[:500])}")

print("\n" + "="*60)
print("📋 完成")
print("="*60)
