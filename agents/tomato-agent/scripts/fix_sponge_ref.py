#!/usr/bin/env python3
"""
一次性传所有假睫毛→TH的字段给美妆蛋
但更新价格和类目
"""
import sys, json, copy
sys.path.insert(0, "/Users/a1234/.openclaw/workspace/agents/tomato-agent/scripts")
from miaoshou_client import MiaoshouClient

APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"

client = MiaoshouClient(APP_KEY, APP_SECRET)

# 获取假睫毛→TH的完整info作为模板
r_ref = client.get_shop_collect_item_info(detail_id=2962333377, shop_id=14681455)
ref_info = copy.deepcopy(r_ref.get("data", {}).get("shopCollectItemInfo", {}))

# 获取美妆蛋→SG的当前info（用来取已有的skuMap、notes等）
r_sponge = client.get_shop_collect_item_info(detail_id=2962333379, shop_id=14772775)
sponge_info = r_sponge.get("data", {}).get("shopCollectItemInfo", {})
sponge_oss = r_sponge.get("data", {}).get("ossMd5", "")

# 获取美妆蛋图片
r_detail = client.get_collect_box_detail(3579185121)
edit = r_detail.get("data", {}).get("editCommonCollectBoxDetail", {})
img_urls = [u for u in edit.get("imgUrls", []) if u]

# 用ref_info作为模板，替换美妆蛋的值
new_info = copy.deepcopy(ref_info)
new_info["title"] = "美妆蛋粉扑4件套 葫芦/水滴/斜切 干湿两用 化妆海绵"
new_info["price"] = "1.80"
new_info["productName"] = "美妆蛋粉扑4件套"
new_info["notes"] = sponge_info.get("notes", ref_info.get("notes", ""))
new_info["cid"] = "853008"
new_info["weight"] = "0.01"
new_info["packageLength"] = "15"
new_info["packageWidth"] = "10"
new_info["packageHeight"] = "3"
new_info["imgUrls"] = img_urls[:10]

# 更新SKU价格
sku_map = sponge_info.get("skuMap", {})
for sku_key, sku_val in sku_map.items():
    sku_val["price"] = "1.80"
    sku_val["priceIncludeVat"] = "1.80"
    sku_val["originPrice"] = "0.45"
    sku_val["weight"] = "0.01"
    shop_map = sku_val.get("shopIdToWarehouseIdAndStockMap", {})
    for sid, wmap in shop_map.items():
        for wh_id in wmap:
            wmap[wh_id] = "99999"

new_info["skuMap"] = sku_map
new_info["brandId"] = sponge_info.get("brandId", "0")
new_info["brandName"] = sponge_info.get("brandName", "无品牌")

# 检查假睫毛ref中的额外字段
extra_keys = [k for k in ref_info.keys() if k not in sponge_info or not sponge_info.get(k)]
print(f"额外字段(美妆蛋缺失): {extra_keys}")
for ek in extra_keys:
    print(f"  {ek}: {str(ref_info.get(ek))[:100]}")

print(f"\n保存完整info...")
print(f"  字段数: {len(new_info)}")
print(f"  deliveryOptionSetType: {new_info.get('deliveryOptionSetType', 'NOT_SET')}")
print(f"  skuPropertyList: {bool(new_info.get('skuPropertyList'))}")

r_save = client.save_shop_collect_item_info(
    oss_md5=sponge_oss,
    detail_id=2962333379,
    shop_id=14772775,
    info=new_info
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
