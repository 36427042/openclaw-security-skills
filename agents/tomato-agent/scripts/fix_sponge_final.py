#!/usr/bin/env python3
"""
先查清get_shop_collect_item_info的具体返回结构，
然后按假睫毛→TH的结构构建美妆蛋→SG的save。
也确认packageLength这些字段在假睫毛的edit中是否为null。

关键：假睫毛的save可能是在第一次publish时自动补全的。
美妆蛋是first save，可能需要对所有必填字段。
"""
import sys, json
sys.path.insert(0, "/Users/a1234/.openclaw/workspace/agents/tomato-agent/scripts")
from miaoshou_client import MiaoshouClient

APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"

client = MiaoshouClient(APP_KEY, APP_SECRET)

# 完整的假睫毛→TH data结构
r = client.get_shop_collect_item_info(detail_id=2962333377, shop_id=14681455)
print("=== 假睫毛→TH 完整data ===")
data = r.get("data", {})
for k, v in data.items():
    if k == "shopCollectItemInfo":
        continue
    print(f"  {k}: {str(v)[:300]}")

print("\n  shopCollectItemInfo的packageX:")
info = data.get("shopCollectItemInfo", {})
for pk in ["packageLength", "packageWidth", "packageHeight", "weight"]:
    print(f"    {pk}: {info.get(pk, 'NOT_FOUND')}")

# 美妆蛋→SG完整data
print("\n=== 美妆蛋→SG 完整data ===")
r2 = client.get_shop_collect_item_info(detail_id=2962333379, shop_id=14772775)
data2 = r2.get("data", {})
for k, v in data2.items():
    if k == "shopCollectItemInfo":
        continue
    print(f"  {k}: {str(v)[:300]}")

info2 = data2.get("shopCollectItemInfo", {})
for pk in ["packageLength", "packageWidth", "packageHeight", "weight", "cid"]:
    print(f"    {pk}: {info2.get(pk, 'NOT_FOUND')}")

# 试试传完整字段
print("\n=== 尝试传完整字段(包括null) ===")
img_urls = []
r_detail = client.get_collect_box_detail(3579185121)
edit = r_detail.get("data", {}).get("editCommonCollectBoxDetail", {})
img_urls = [u for u in edit.get("imgUrls", []) if u]

sku_map = info2.get("skuMap", {})
for sku_key, sku_val in sku_map.items():
    sku_val["price"] = "1.80"
    sku_val["priceIncludeVat"] = "1.80"
    sku_val["originPrice"] = "0.45"
    sku_val["weight"] = "0.01"
    # Update warehouse stock
    shop_map = sku_val.get("shopIdToWarehouseIdAndStockMap", {})
    for sid, wmap in shop_map.items():
        for wh_id in wmap:
            wmap[wh_id] = "99999"

# 完整结构
full_info = {
    "title": "美妆蛋粉扑4件套 葫芦/水滴/斜切 干湿两用 化妆海绵",
    "price": "1.80",
    "productName": "美妆蛋粉扑4件套",
    "notes": info2.get("notes", ""),
    "imgUrls": img_urls[:10],
    "cid": "853008",
    "brandId": info2.get("brandId", "0"),
    "brandName": info2.get("brandName", "无品牌"),
    "productAttributes": [],
    "skuMap": sku_map,
    "weight": "0.01",
    "packageLength": "",
    "packageWidth": "",
    "packageHeight": "",
    "isCodOpen": "1",
    "productCertifications": [],
    "mainImgPlatformVideoId": "",
    "mainImgVideoUrl": "",
    "sizeChart": "",
    "manufacturerIds": [],
    "responsiblePersonIds": [],
}

r_save = client.save_shop_collect_item_info(
    oss_md5="NcZiXrbNpFrPnv5ADXf1",
    detail_id=2962333379,
    shop_id=14772775,
    info=full_info
)
print(f"save: code={r_save.get('code')} msg={r_save.get('message','')}")
print(json.dumps(r_save, ensure_ascii=False)[:300])

if r_save.get("code") == "success":
    print(f"\n✅ save成功！尝试publish...")
    r_pub = client.publish([14772775], [2962333379])
    print(f"publish: code={r_pub.get('code')} msg={r_pub.get('message','')}")
