#!/usr/bin/env python3
"""3品类各TOP20选品快速运行器"""
import json, os, sys, time, base64, urllib.request
from datetime import datetime

# 配置
CRED_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "echotik.json")
with open(CRED_PATH) as f:
    creds = json.load(f)
BASE = creds["base_url"].rstrip("/")
AUTH = base64.b64encode(f'{creds["username"]}:{creds["password"]}'.encode()).decode()
HEADERS = {"Authorization": f"Basic {AUTH}", "Content-Type": "application/json"}

def api_get(path):
    url = f"{BASE}/{path.lstrip('/')}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  ❌ HTTP错误: {e}")
        return None

# ========== 品类定义 ==========
CATEGORIES = {
    "美妆工具": {
        "type": "l3_list",
        "ids": ["601537","601585","601586","601587","601588",
                "601529","852752","852880","853392","853520"],
        "max_price_usd": 20, "min_price_usd": 0.05,
    },
    "家具用品": {
        "type": "l1",
        "ids": ["600001"],
        "max_price_usd": 20, "min_price_usd": 0.3,
    },
    "个人洗护": {
        "type": "l3_list",
        "ids": ["601469","601476","601493","601506","601516",
                "601550","601602","601608","601609","601615",
                "601696","601733","853512","873480","981512"],
        "max_price_usd": 20, "min_price_usd": 0.1,
    },
}

REGIONS = {
    "TH": {"name":"泰国","rate":0.028},
    "MY": {"name":"马来西亚","rate":0.22},
    "VN": {"name":"越南","rate":0.000041},
    "PH": {"name":"菲律宾","rate":0.018},
    "SG": {"name":"新加坡","rate":0.74},
}

def search_category(region, l3_id, page_size=10):
    params = f"region={region}&category_l3_id={l3_id}&page_num=1&page_size={page_size}&product_sort_field=1&sort_type=1"
    return api_get(f"product/list?{params}")

def search_l1_category(region, cat_id, page_size=20):
    params = f"region={region}&category_id={cat_id}&page_num=1&page_size={page_size}&product_sort_field=1&sort_type=1"
    return api_get(f"product/list?{params}")

def main():
    os.makedirs("reports", exist_ok=True)
    results = {cat_name: {} for cat_name in CATEGORIES}
    
    for cat_name, cat_cfg in CATEGORIES.items():
        print(f"\n{'='*50}")
        print(f"📦 品类: {cat_name}")
        print(f"{'='*50}")
        
        for rcode, rinfo in REGIONS.items():
            print(f"\n  🌏 {rinfo['name']}({rcode})...")
            all_products = []
            seen = set()
            
            if cat_cfg["type"] == "l3_list":
                for l3_id in cat_cfg["ids"]:
                    data = search_category(rcode, l3_id, page_size=10)
                    if data and data.get("code") == 0:
                        items = data.get("data", [])
                        for p in items:
                            pid = p.get("product_id","")
                            if pid and pid not in seen:
                                seen.add(pid)
                                all_products.append(p)
                    time.sleep(0.2)
            elif cat_cfg["type"] == "l1":
                data = search_l1_category(rcode, cat_cfg["ids"][0], page_size=20)
                if data and data.get("code") == 0:
                    items = data.get("data", [])
                    for p in items:
                        all_products.append(p)
            
            # 评分筛选
            scored = []
            for p in all_products:
                spu = float(p.get("spu_avg_price",0) or 0)
                price = spu * rinfo["rate"]
                if price < cat_cfg["min_price_usd"] or price > cat_cfg["max_price_usd"]:
                    continue
                sale = int(p.get("total_sale_cnt",0) or 0)
                if sale <= 0: continue
                
                # 评分
                w_sale = min(100, (sale**0.3)*8)
                gmv = float(p.get("total_sale_gmv_amt",0) or 0)
                w_gmv = min(100, (gmv**0.25)*5)
                score = round(w_sale*0.5 + w_gmv*0.3 + float(p.get("product_rating",0) or 0)/5*100*0.2, 2)
                p["_score"] = score
                p["_price_usd"] = round(price, 2)
                scored.append(p)
            
            scored.sort(key=lambda x: x["_score"], reverse=True)
            top20 = scored[:20]
            
            print(f"    总采集:{len(all_products)} 合格:{len(scored)} {'TOP20首件:${} {}'.format(top20[0].get('_price_usd','?'), top20[0].get('product_name','')[:30]) if top20 else '无合格商品'}")
            results[cat_name][rcode] = top20
            if not top20:
                continue
    
    # ======== 生成报告 ========
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"# 3品类选品报告 ({ts})\n"]
    
    for cat_name, region_data in results.items():
        total_products = sum(len(v) for v in region_data.values())
        lines.append(f"\n## 📦 {cat_name} (共{total_products}件)\n")
        lines.append("| 国家 | 合格数 | TOP1 | 价格$ | 销量 | 评分 |")
        lines.append("|------|:------:|------|:-----:|:----:|:----:|")
        
        for rcode, products in region_data.items():
            if products:
                p0 = products[0]
                lines.append(f"| {rcode} | {len(products)} | {p0.get('product_name','')[:25]} | {p0.get('_price_usd','')} | {p0.get('total_sale_cnt',0)} | {p0.get('_score','')} |")
            else:
                lines.append(f"| {rcode} | 0 | - | - | - | - |")
    
    report = "\n".join(lines)
    rpath = f"reports/3cat_top20_{datetime.now().strftime('%H%M')}.md"
    with open(rpath, "w") as f:
        f.write(report)
    
    print(f"\n\n✅ 报告已生成: {rpath}")
    
    # 挑最佳产品
    print("\n\n🏆 各品类最佳产品:")
    for cat_name, region_data in results.items():
        best = None
        for rcode, products in region_data.items():
            if products:
                for p in products:
                    if best is None or p["_score"] > best["_score"]:
                        best = p
                        best["_region"] = rcode
        if best:
            print(f"  {cat_name}: [{best['_region']}] ${best['_price_usd']} | {best.get('product_name','')[:40]} | 销量{best.get('total_sale_cnt',0)} | 评分{best.get('_score','')}")
    
    return results

if __name__ == "__main__":
    main()
