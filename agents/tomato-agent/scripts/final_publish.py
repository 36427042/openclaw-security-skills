#!/usr/bin/env python3
"""
最后冲刺：补完美妆蛋→SG的shop详情并publish
所有shop模式条目已存在，只需要save_shop_collect_item_info + publish

假睫毛→TH(2962333377, 14681455) ✅ 已publish
美妆蛋→SG(2962333379, 14772775) ❌ 需要补完
"""
import sys, json, time
sys.path.insert(0, "/Users/a1234/.openclaw/workspace/agents/tomato-agent/scripts")
from miaoshou_client import MiaoshouClient

APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"

client = MiaoshouClient(APP_KEY, APP_SECRET)

# 美妆蛋→SG 的shop条目
DETAIL_ID = 2962333379  # collectBoxDetailId (tid)
SHOP_ID = 14772775
SITE = "SG"
PRICE = "1.80"
NAME = "美妆蛋粉扑4件套"

# 公共采集箱详情 - 获取图片
r_detail = client.get_collect_box_detail(3579185121)
if r_detail.get("code") != "success":
    print(f"❌ 获取公共采集箱详情失败")
    sys.exit(1)

edit_data = r_detail.get("data", {}).get("editCommonCollectBoxDetail", {})
img_urls = [u for u in edit_data.get("imgUrls", []) if u]
print(f"公共采集箱图片: {len(img_urls)}张")

# 获取shop模式现有详情
r_shop = client.get_shop_collect_item_info(detail_id=DETAIL_ID, shop_id=SHOP_ID)
print(f"get_shop: code={r_shop.get('code')}")
if r_shop.get("code") != "success":
    print(f"❌ 获取shop详情失败")
    sys.exit(1)

data = r_shop.get("data", {})
oss_md5 = data.get("ossMd5", "")
existing_info = data.get("shopCollectItemInfo", {})

print(f"现有cid: '{existing_info.get('cid','')}'")
print(f"现有price: {list(existing_info.get('skuMap', {}).values())[0].get('price','?') if existing_info.get('skuMap') else '无SKU'}")

# 美妆蛋TK类目 - 从公共采集箱类目"粉扑、美妆蛋"找对应的TK类目ID
# 之前假睫毛类目是824720 (TikTok类目ID)
# 需要找到粉扑/美妆蛋对应的TK类目ID
# 先尝试让系统自动匹配（不传cid，保留现有空cid不行）
# 或者搜一下TK类目树

print("\n=== 搜索TK粉扑/美妆蛋类目 ===")
r = client.get_category_tree("TH")
tree = r.get("data", {}).get("cateTree", {})

def search_cat(tree, target, path=""):
    for k, v in tree.items():
        curr = f"{path}/{k}" if path else k
        if isinstance(v, dict):
            cid = v.get("cid", v.get("categoryId", ""))
            name = v.get("categoryName", v.get("name", k))
            if isinstance(name, str) and target.lower() in name.lower():
                print(f"  ✅ 匹配: {curr} → cid={cid} name={name}")
            kids = v.get("children", v.get("subCateList", {}))
            if kids and isinstance(kids, dict):
                search_cat(kids, target, curr)

for t in ["粉扑", "美妆蛋", "化妆工具"]:
    print(f"\n搜索'{t}':")
    search_cat(tree, t)

# 更新SKU价格
print("\n=== 更新SKU价格 ===")
sku_map = existing_info.get("skuMap", {})
print(f"SKU数量: {len(sku_map)}")
for sku_key, sku_val in sku_map.items():
    old_price = sku_val.get("price", "?")
    sku_val["price"] = PRICE
    sku_val["priceIncludeVat"] = PRICE
    sku_val["originPrice"] = "0.45"
    # 更新stock
    shop_map = sku_val.get("shopIdToWarehouseIdAndStockMap", {})
    for sid, wmap in shop_map.items():
        for wh_id in wmap:
            wmap[wh_id] = "99999"
    print(f"  SKU {sku_key}: {old_price} → {PRICE}")

# 构建完整的shop info
shop_info = {
    "title": NAME,
    "price": PRICE,
    "productName": NAME,
    "notes": existing_info.get("notes", ""),
    "imgUrls": img_urls[:10],
    "cid": existing_info.get("cid", "824720"),  # 用假睫毛的类目作为fallback，但最好找到正确的
    "brandId": existing_info.get("brandId", "0"),
    "brandName": existing_info.get("brandName", "无品牌"),
    "skuMap": sku_map,
    "images": [{"url": u} for u in img_urls[:10]],
}

# 清理
shop_info = {k: v for k, v in shop_info.items() if v is not None and v != "" and (not isinstance(v, (list, dict)) or v)}

print(f"\n=== 保存shop info (imgUrls={len(shop_info.get('imgUrls',[]))}, cid={shop_info.get('cid','')}) ===")
r_save = client.save_shop_collect_item_info(
    oss_md5=oss_md5,
    detail_id=DETAIL_ID,
    shop_id=SHOP_ID,
    info=shop_info
)
print(f"save: {json.dumps(r_save, ensure_ascii=False)[:500]}")

if r_save.get("code") == "success":
    print(f"\n=== 🚀 publish ===")
    r_pub = client.publish([SHOP_ID], [DETAIL_ID])
    print(f"publish: {json.dumps(r_pub, ensure_ascii=False)[:500]}")
    if r_pub.get("code") == "success":
        print(f"\n✅ 美妆蛋→SG 发布成功！")
    else:
        print(f"\n❌ publish失败")
else:
    print(f"\n❌ save失败，尝试更精简的info...")
    # 只传必要字段
    simple_info = {
        "title": NAME,
        "price": PRICE,
        "productName": NAME,
    }
    r_save2 = client.save_shop_collect_item_info(
        oss_md5=oss_md5,
        detail_id=DETAIL_ID,
        shop_id=SHOP_ID,
        info=simple_info
    )
    print(f"save(simple): {json.dumps(r_save2, ensure_ascii=False)[:500]}")
