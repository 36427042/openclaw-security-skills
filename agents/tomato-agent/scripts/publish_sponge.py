#!/usr/bin/env python3
"""
美妆蛋→SG publish
类目ID: 853008 (Makeup Sponge)
Title需要25+字符
"""
import sys, json
sys.path.insert(0, "/Users/a1234/.openclaw/workspace/agents/tomato-agent/scripts")
from miaoshou_client import MiaoshouClient

APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"

client = MiaoshouClient(APP_KEY, APP_SECRET)

# 美妆蛋→SG
DETAIL_ID = 2962333379
SHOP_ID = 14772775
PRICE = "1.80"
NAME = "美妆蛋粉扑4件套 葫芦/水滴/斜切 干湿两用 化妆海绵"

# 获取shop详情
r = client.get_shop_collect_item_info(detail_id=DETAIL_ID, shop_id=SHOP_ID)
if r.get("code") != "success":
    print(f"❌ 获取shop详情失败")
    sys.exit(1)

data = r.get("data", {})
oss_md5 = data.get("ossMd5", "")
existing = data.get("shopCollectItemInfo", {})
print(f"ossMd5: {oss_md5[:20] if oss_md5 else '空'}")
print(f"现有cid: '{existing.get('cid','')}'")
print(f"现有title: '{existing.get('title','')}' ({len(existing.get('title',''))}字符)")

# 从公共采集箱获取图片
r_detail = client.get_collect_box_detail(3579185121)
edit_data = r_detail.get("data", {}).get("editCommonCollectBoxDetail", {})
img_urls = [u for u in edit_data.get("imgUrls", []) if u]
print(f"图片: {len(img_urls)}张")

# 更新SKU价格
sku_map = existing.get("skuMap", {})
for sku_key, sku_val in sku_map.items():
    sku_val["price"] = PRICE
    sku_val["priceIncludeVat"] = PRICE
    sku_val["originPrice"] = "0.45"
    # Update warehouse stock
    shop_map = sku_val.get("shopIdToWarehouseIdAndStockMap", {})
    for sid, wmap in shop_map.items():
        for wh_id in wmap:
            wmap[wh_id] = "99999"

# 构建shop info - 最少必要字段
shop_info = {
    "title": NAME,  # 30字符 > 25
    "price": PRICE,
    "productName": "美妆蛋粉扑4件套",
    "imgUrls": img_urls[:10],
    "cid": "853008",  # Makeup Sponge!
    "brandId": existing.get("brandId", "0"),
    "brandName": existing.get("brandName", "无品牌"),
    "skuMap": sku_map,
    "notes": existing.get("notes", ""),
}

print(f"\n保存shop info...")
print(f"  title: {shop_info['title']} ({len(shop_info['title'])}字符)")
print(f"  price: {shop_info['price']}")
print(f"  cid: {shop_info['cid']}")
print(f"  imgUrls: {len(shop_info['imgUrls'])}")

r_save = client.save_shop_collect_item_info(
    oss_md5=oss_md5,
    detail_id=DETAIL_ID,
    shop_id=SHOP_ID,
    info=shop_info
)
print(f"\nsave: code={r_save.get('code')} msg={r_save.get('message','')}")
print(json.dumps(r_save, ensure_ascii=False)[:300])

if r_save.get("code") == "success":
    print(f"\n🚀 publish...")
    r_pub = client.publish([SHOP_ID], [DETAIL_ID])
    print(f"publish: code={r_pub.get('code')} msg={r_pub.get('message','')}")
    if r_pub.get("code") == "success":
        print(f"\n✅ 美妆蛋→SG 发布成功！")
    else:
        print(f"\n❌ publish失败")
else:
    print(f"\n❌ save失败")
