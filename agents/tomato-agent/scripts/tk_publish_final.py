#!/usr/bin/env python3
"""
🥬 生菜·最终版 TK Shop 认领+发布全流程

完整正确的流程:
1. claimed → TK采集箱(site模式)
2. get_site_collect_item_info 获取site模式详情
3. save_site_collect_item_info 设置定价+类目
4. claim_to_shop 认领到shop → 转为shop模式
5. get_shop_collect_item_info 获取shop模式详情
6. save_shop_collect_item_info 补完shop模式数据（价格+图片+类目）
7. publish (用tid)

一个产品只能claim到一个shop（TK全球店铺限制）。
所以先搞定假睫毛→TH, 美妆蛋→SG。
"""
import sys, json, time, re
sys.path.insert(0, "/Users/a1234/.openclaw/workspace/agents/tomato-agent/scripts")
from miaoshou_client import MiaoshouClient

APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"

client = MiaoshouClient(APP_KEY, APP_SECRET)

# ======= 配置 =======
PRODUCTS = [
    {
        "cid": 3579185120,
        "name": "假睫毛",
        "public_cid": "824720",  # 公共采集箱中的类目ID(假睫毛)
        "site": "TH",
        "shop_id": 14681455,
        "price": "63",
        "prices_sku": [  # 根据假睫毛的实际SKU
            {"originPrice": "1.50", "price": "63", "stock": "99999"},
            {"originPrice": "3.50", "price": "147", "stock": "1000"},
        ]
    },
    {
        "cid": 3579185121,
        "name": "美妆蛋", 
        "public_cid": "",  # 需要查找美妆蛋在TK的类目
        "site": "SG",
        "shop_id": 14772775,
        "price": "1.80",
        "prices_sku": [
            {"originPrice": "0.45", "price": "1.80", "stock": "99999"},
        ]
    },
]

def extract_img_urls(public_box_detail):
    """从公共采集箱详情中提取图片URL列表"""
    img_urls = []
    edit = public_box_detail.get("data", {}).get("editCommonCollectBoxDetail", {})
    for url in edit.get("imgUrls", []):
        if isinstance(url, str) and url:
            img_urls.append(url)
    return img_urls

def find_tk_category(public_box_detail):
    """从公共采集箱中获取类目信息"""
    edit = public_box_detail.get("data", {}).get("editCommonCollectBoxDetail", {})
    cate_list = edit.get("cateList", [])
    # 返回第一个类目名称
    return cate_list[0] if cate_list else ""

def get_sku_price(sku_key, prices_config):
    """根据SKU key确定定价"""
    # 简单定价：所有SKU统一价格
    return prices_config[0]["price"] if prices_config else "0"

def get_oss_md5(data_item):
    """获取ossMd5"""
    if isinstance(data_item, str):
        return data_item
    return data_item.get("ossMd5", "")

def update_sku_prices(existing_info, prices_config):
    """更新SKU价格"""
    sku_map = existing_info.get("skuMap", {})
    if not sku_map:
        return sku_map
    
    updated = {}
    for i, (sku_key, sku_val) in enumerate(sku_map.items()):
        pc = prices_config[min(i, len(prices_config) - 1)]
        new_price = pc["price"]
        origin_price = pc.get("originPrice", sku_val.get("originPrice", "0"))
        
        sku_val["price"] = new_price
        sku_val["priceIncludeVat"] = new_price
        sku_val["originPrice"] = origin_price
        sku_val["stock"] = pc.get("stock", "99999")
        
        # 更新shop warehouse stock
        shop_map = sku_val.get("shopIdToWarehouseIdAndStockMap", {})
        for shop_id, warehouse_map in shop_map.items():
            for wh_id in warehouse_map:
                warehouse_map[wh_id] = pc.get("stock", "99999")
        
        updated[sku_key] = sku_val
    
    return updated

# ======= 流程 =======
print("="*60)
print("🥬 TK Shop认领+发布全流程 (最终版)")
print("="*60)

# Step 0: 获取公共采集箱详情（图片、类目等）
print("\n[Step 0] 获取公共采集箱详情")
details = {}
for p in PRODUCTS:
    r = client.get_collect_box_detail(p["cid"])
    if r.get("code") == "success":
        edit = r.get("data", {}).get("editCommonCollectBoxDetail", {})
        img_urls = [u for u in edit.get("imgUrls", []) if u]
        print(f"  ✅ {p['name']}: {len(img_urls)}张图片, 类目={edit.get('cateList',[])}")
        details[p["cid"]] = r
    else:
        print(f"  ❌ {p['name']}: 获取详情失败 {r.get('message','')}")
        details[p["cid"]] = None

# Step 1: 获取TK站点类目（美妆蛋需要类目）
print("\n[Step 1] 获取TK类目树")
# 先找粉扑/美妆蛋的类目
r = client.get_category_tree("TH")
if r.get("code") == "success":
    tree = r.get("data", {}).get("cateTree", {})
    print(f"  类目树根节点: {list(tree.keys())[:5] if tree else '空'}")
    # 搜索粉扑类目
    def find_cat(tree, target, path=""):
        for k, v in tree.items():
            curr_path = f"{path}/{k}" if path else k
            if target.lower() in k.lower():
                print(f"  🔍 找到类目: {curr_path} = {v.get('cid', '?')}")
            if isinstance(v, dict):
                kids = v.get("children", v.get("subCateList", {}))
                if kids:
                    find_cat(kids if isinstance(kids, dict) else {}, target, curr_path)
    find_cat(tree, "粉扑")
    find_cat(tree, "美妆蛋")

# Step 2: 用site模式的tid操作（获取当前site条目）
print("\n[Step 2] 处理site模式条目")
r = client.search_collect_box_list(page_no=1, page_size=50, status="notPublished")
site_tids = {}
for item in r.get("data", {}).get("detailList", []):
    cid = item.get("commonCollectBoxDetailId")
    if cid in ["3579185120", "3579185121", 3579185120, 3579185121] and item.get("editModel") == "site":
        site_tids[int(cid)] = item.get("collectBoxDetailId")
        print(f"  ✅ {PRODUCTS[0 if int(cid)==3579185120 else 1]['name']}: site_tid={item.get('collectBoxDetailId')}")

# Step 3: 为每个产品设置site模式定价+类目 → claim → publish
for p in PRODUCTS:
    cid = p["cid"]
    name = p["name"]
    site = p["site"]
    shop_id = p["shop_id"]
    price = p["price"]
    
    print(f"\n{'='*50}")
    print(f"处理: {name} → {site} (shop={shop_id})")
    print(f"{'='*50}")
    
    # 3a: 先获取site模式的详情
    r_site = client.get_site_collect_item_info(detail_id=cid, site=site)
    print(f"  get_site模式: code={r_site.get('code')} msg={r_site.get('message','')}")
    
    if r_site.get("code") == "success":
        data = r_site.get("data", {})
        oss_md5 = get_oss_md5(data)
        print(f"  ossMd5={'有' if oss_md5 else '空'}")
        
        # 构建site模式的info - 设置价格
        site_info = {
            "price": price,
            "productName": name,
        }
        
        r_save = client.save_site_collect_item_info(
            oss_md5=oss_md5,
            detail_id=cid if site_tids.get(cid) is not None else cid,
            site=site,
            info=site_info
        )
        print(f"  save_site定价: {r_save.get('code', '?')} {r_save.get('message','')}")
    
    # 3b: claim_to_shop
    if cid in site_tids:
        tid = int(site_tids[cid])
        r_claim = client.claim_to_shop([shop_id], [tid])
        print(f"  claim_to_shop: {r_claim.get('code','?')} {r_claim.get('message','')}")
    else:
        print(f"  ⚠️  没有site模式的tid，无法claim")
        continue
    
    time.sleep(1)
    
    # 3c: 获取shop模式详情
    # 找到claim后生成的shop模式条目的tid
    r_list = client.search_collect_box_list(page_no=1, page_size=50, status="notPublished")
    shop_tid = None
    for item in r_list.get("data", {}).get("detailList", []):
        icid = item.get("commonCollectBoxDetailId")
        if icid in ["3579185120", "3579185121", 3579185120, 3579185121] \
           and item.get("editModel") == "shop" \
           and shop_id in [int(s.get("shopId")) for s in item.get("collectBoxDetailShopList", [])]:
            shop_tid = item.get("collectBoxDetailId")
            print(f"  ✅ 找到shop模式: tid={shop_tid}")
            break
    
    if not shop_tid:
        print(f"  ❌ 找不到shop模式条目")
        continue
    
    # 3d: 获取并补完shop详情
    r_shop = client.get_shop_collect_item_info(detail_id=shop_tid, shop_id=shop_id)
    if r_shop.get("code") == "success":
        data = r_shop.get("data", {})
        shop_oss = get_oss_md5(data)
        existing_info = data.get("shopCollectItemInfo", {})
        print(f"  shop ossMd5={'有' if shop_oss else '空'}")
        
        # 从公共采集箱取图片
        detail = details.get(cid, {})
        edit_data = detail.get("data", {}).get("editCommonCollectBoxDetail", {}) if detail else {}
        img_urls = [u for u in edit_data.get("imgUrls", []) if u]
        
        # 构建完整的shop info
        shop_info = {
            "title": existing_info.get("title", name),
            "price": price,
            "productName": name,
            "notes": existing_info.get("notes", ""),
            "imgUrls": img_urls[:10],  # 最多10张
            "cid": p["public_cid"] if p["public_cid"] else existing_info.get("cid", ""),
            "brandId": existing_info.get("brandId", "0"),
            "brandName": existing_info.get("brandName", "无品牌"),
            "skuMap": update_sku_prices(existing_info, p["prices_sku"]),
            "images": existing_info.get("images", img_urls[:10]),
        }
        
        # 清理空值
        shop_info = {k: v for k, v in shop_info.items() if v}
        
        print(f"  保存shop info (cid={shop_info.get('cid','')}, price={price})...")
        r_save2 = client.save_shop_collect_item_info(
            oss_md5=shop_oss,
            detail_id=shop_tid,
            shop_id=shop_id,
            info=shop_info
        )
        print(f"  save_shop: {r_save2.get('code','?')} {r_save2.get('message','')}")
        
        if r_save2.get("code") == "success":
            # 3e: publish
            print(f"  🚀 publishing...")
            r_pub = client.publish([shop_id], [shop_tid])
            print(f"  publish: {r_pub.get('code','?')} {r_pub.get('message','')}")
            if r_pub.get("code") == "success":
                print(f"  ✅ {name}→{site} 发布成功！")
        else:
            print(f"  ❌ 保存shop详情失败，需要补全信息")
    else:
        print(f"  ❌ get_shop失败: {r_shop.get('message','')}")

print("\n" + "="*60)
print("📋 流程完成")
print("="*60)
