#!/usr/bin/env python3
"""
美妆蛋packageLength必填 - 设默认值
"""
import sys, json
sys.path.insert(0, "/Users/a1234/.openclaw/workspace/agents/tomato-agent/scripts")
from miaoshou_client import MiaoshouClient

APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"

client = MiaoshouClient(APP_KEY, APP_SECRET)

# 获取当前
r = client.get_shop_collect_item_info(detail_id=2962333379, shop_id=14772775)
data = r.get("data", {})
info = data.get("shopCollectItemInfo", {})
oss_md5 = data.get("ossMd5", "")

# 获取图片
r_detail = client.get_collect_box_detail(3579185121)
edit = r_detail.get("data", {}).get("editCommonCollectBoxDetail", {})
img_urls = [u for u in edit.get("imgUrls", []) if u]

# 更新SKU
sku_map = info.get("skuMap", {})
for sku_key, sku_val in sku_map.items():
    sku_val["price"] = "1.80"
    sku_val["priceIncludeVat"] = "1.80"
    sku_val["originPrice"] = "0.45"
    sku_val["weight"] = "0.01"
    shop_map = sku_val.get("shopIdToWarehouseIdAndStockMap", {})
    for sid, wmap in shop_map.items():
        for wh_id in wmap:
            wmap[wh_id] = "99999"

# 关键：设packageLength有值
full_info = {
    "title": "美妆蛋粉扑4件套 葫芦/水滴/斜切 干湿两用 化妆海绵",
    "price": "1.80",
    "productName": "美妆蛋粉扑4件套",
    "notes": info.get("notes", ""),
    "imgUrls": img_urls[:10],
    "cid": "853008",
    "brandId": info.get("brandId", "0"),
    "brandName": info.get("brandName", "无品牌"),
    "productAttributes": [],
    "skuMap": sku_map,
    "weight": "0.01",
    "packageLength": "15",
    "packageWidth": "10",
    "packageHeight": "3",
    "isCodOpen": "1",
    "productCertifications": [],
    "mainImgPlatformVideoId": "",
    "mainImgVideoUrl": "",
    "sizeChart": "",
    "manufacturerIds": [],
    "responsiblePersonIds": [],
}

print("保存完整info...")
r_save = client.save_shop_collect_item_info(
    oss_md5=oss_md5,
    detail_id=2962333379,
    shop_id=14772775,
    info=full_info
)
print(f"save: code={r_save.get('code')} msg={r_save.get('message','')}")
print(json.dumps(r_save, ensure_ascii=False)[:500])

if r_save.get("code") == "success":
    print(f"\n🚀 publish...")
    r_pub = client.publish([14772775], [2962333379])
    print(f"publish: code={r_pub.get('code')} msg={r_pub.get('message','')}")
    if r_pub.get("code") == "success":
        print(f"\n✅ 美妆蛋→SG 发布成功！")
    else:
        print(f"\n❌ publish失败")
else:
    # 试去掉一些字段
    print(f"\n尝试精简info...")
    simple = {
        "title": "美妆蛋粉扑4件套 葫芦/水滴/斜切 干湿两用 化妆海绵",
        "price": "1.80",
        "productName": "美妆蛋粉扑4件套",
        "cid": "853008",
        "weight": "0.01",
        "packageLength": "15",
        "packageWidth": "10",
        "packageHeight": "3",
    }
    r_save2 = client.save_shop_collect_item_info(
        oss_md5=oss_md5,
        detail_id=2962333379,
        shop_id=14772775,
        info=simple
    )
    print(f"save(simple): code={r_save2.get('code')} msg={r_save2.get('message','')}")
    print(json.dumps(r_save2, ensure_ascii=False)[:300])
