#!/usr/bin/env python3
"""
假睫毛→TH publish成功了！现在检查实际状态，并补完美妆蛋→SG。

还有：publish后产品从"notPublished"消失了但不在"published"里，
可能已经在TK Shop后台了。
需要验证是否真的发布成功。

同时：尝试让美妆蛋→SG也publish。
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

# 1. 验证假睫毛→TH publish结果 - 用get_shop_collect_item_info
print("="*60)
print("验证假睫毛→TH publish结果")
print("="*60)

r = client.get_shop_collect_item_info(detail_id=2962333377, shop_id=14681455)
if r.get("code") == "success":
    data = r.get("data", {})
    info = data.get("shopCollectItemInfo", {})
    print(f"  title: {info.get('title', 'N/A')}")
    print(f"  cid (类目): {info.get('cid', 'N/A')}")
    print(f"  price: {info.get('skuMap', {}).get(list(info.get('skuMap', {}).keys() or [''])[0], {}).get('price', 'N/A')}")
    print(f"  site: {info.get('site', 'N/A')}")
    print(f"  shopId: {info.get('shopId', 'N/A')}")
    print(f"  完整info: {json.dumps(info, ensure_ascii=False)[:800]}")

# 2. 现在补完美妆蛋→SG 
# 需要先设置好shopCollectItemInfo再publish
print("\n" + "="*60)
print("美妆蛋→SG - 设置shop详情")
print("="*60)

# 用假睫毛→TH的info做参考，构建美妆蛋的info
# 假睫毛已经有的字段: site, shopId, detailId, title, notes, cid, brandId, 
#   brandName, productAttributes, skuMap, images
# 对应类目: cid=824720

# 先获取当前的详情（拿到现有的数据）
r = client.get_shop_collect_item_info(detail_id=2962333379, shop_id=14772775)
if r.get("code") == "success":
    data = r.get("data", {})
    oss_md5 = data.get("ossMd5", "")
    existing_info = data.get("shopCollectItemInfo", {})
    print(f"  现有ossMd5: {oss_md5[:20]}...")
    print(f"  现有info: {json.dumps(existing_info, ensure_ascii=False)[:500]}")
    
    # 构建完整的shopCollectItemInfo
    # 用公共采集箱中已有的数据
    info = {
        "title": "美妆蛋粉扑4件套 葫芦/水滴/斜切 干湿两用 化妆海绵",
        "price": "1.80",
        "productName": "美妆蛋粉扑4件套",
    }
    # 添加其他已有字段保留
    if existing_info.get("cid"):
        info["cid"] = existing_info.get("cid")
    if existing_info.get("notes"):
        info["notes"] = existing_info.get("notes")
    if existing_info.get("skuMap"):
        info["skuMap"] = existing_info.get("skuMap")
    if existing_info.get("images"):
        info["images"] = existing_info.get("images")
    
    print(f"\n  保存info: {json.dumps(info, ensure_ascii=False)[:500]}")
    
    r_save = client.save_shop_collect_item_info(
        oss_md5=oss_md5,
        detail_id=2962333379,
        shop_id=14772775,
        info=info
    )
    print(f"  save结果: {json.dumps(r_save, ensure_ascii=False)[:300]}")
    
    if r_save.get("code") == "success":
        print("\n  ✅ shop详情保存成功，尝试publish...")
        r_pub = client.publish([14772775], [2962333379])
        print(f"  publish结果: {json.dumps(r_pub, ensure_ascii=False)[:300]}")
    else:
        print(f"\n  ❌ 保存失败，需要更完整的数据")
        # 尝试用site模式的cid来获取公共采集箱详情
        r_detail = client.get_collect_box_detail(3579185121)
        if r_detail.get("code") == "success":
            edit_data = r_detail.get("data", {}).get("editCommonCollectBoxDetail", {})
            print(f"  公共采集箱类目: {edit_data.get('cateList', ['?'])}")
            
            # 尝试用save_site模式先设置类目
            # ... 但可能已经在shop模式了
