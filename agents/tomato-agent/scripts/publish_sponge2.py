#!/usr/bin/env python3
"""
美妆蛋→SG publish - 加上weight
"""
import sys, json
sys.path.insert(0, "/Users/a1234/.openclaw/workspace/agents/tomato-agent/scripts")
from miaoshou_client import MiaoshouClient

APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"

client = MiaoshouClient(APP_KEY, APP_SECRET)

DETAIL_ID = 2962333379
SHOP_ID = 14772775
PRICE = "1.80"
NAME = "美妆蛋粉扑4件套 葫芦/水滴/斜切 干湿两用 化妆海绵"

r = client.get_shop_collect_item_info(detail_id=DETAIL_ID, shop_id=SHOP_ID)
if r.get("code") != "success":
    print(f"❌ 获取shop详情失败")
    sys.exit(1)

data = r.get("data", {})
oss_md5 = data.get("ossMd5", "")
existing = data.get("shopCollectItemInfo", {})

# 从公共采集箱获取图片和weight
r_detail = client.get_collect_box_detail(3579185121)
edit_data = r_detail.get("data", {}).get("editCommonCollectBoxDetail", {})
img_urls = [u for u in edit_data.get("imgUrls", []) if u]
weight = edit_data.get("weight", 0.01)  # 0.01kg = 10g

# 更新SKU价格
sku_map = existing.get("skuMap", {})
for sku_key, sku_val in sku_map.items():
    sku_val["price"] = PRICE
    sku_val["priceIncludeVat"] = PRICE
    sku_val["originPrice"] = "0.45"
    sku_val["weight"] = str(weight)
    shop_map = sku_val.get("shopIdToWarehouseIdAndStockMap", {})
    for sid, wmap in shop_map.items():
        for wh_id in wmap:
            wmap[wh_id] = "99999"

# 构建shop info
shop_info = {
    "title": NAME,
    "price": PRICE,
    "productName": "美妆蛋粉扑4件套",
    "imgUrls": img_urls[:10],
    "cid": "853008",
    "weight": str(weight),
    "brandId": existing.get("brandId", "0"),
    "brandName": existing.get("brandName", "无品牌"),
    "skuMap": sku_map,
    "notes": existing.get("notes", ""),
}

print(f"保存shop info...")
print(f"  title: {shop_info['title']} ({len(shop_info['title'])}字符)")
print(f"  price: {PRICE}")
print(f"  cid: 853008")
print(f"  weight: {weight}kg")
print(f"  imgUrls: {len(shop_info['imgUrls'])}张")
print(f"  SKUs: {len(sku_map)}个")

r_save = client.save_shop_collect_item_info(
    oss_md5=oss_md5,
    detail_id=DETAIL_ID,
    shop_id=SHOP_ID,
    info=shop_info
)
print(f"\nsave: code={r_save.get('code')} msg={r_save.get('message','')}")
print(json.dumps(r_save, ensure_ascii=False)[:500])

if r_save.get("code") == "success":
    print(f"\n🚀 publish...")
    r_pub = client.publish([SHOP_ID], [DETAIL_ID])
    print(f"publish: code={r_pub.get('code')} msg={r_pub.get('message','')}")
    if r_pub.get("code") == "success":
        print(f"\n✅ 美妆蛋→SG 发布成功！")
    else:
        print(f"\n❌ publish失败: {r_pub.get('message','')}")
else:
    print(f"\n❌ save失败")
