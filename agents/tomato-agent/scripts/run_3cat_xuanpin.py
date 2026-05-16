#!/usr/bin/env python3
"""3品类×5国 选品脚本 — 美妆工具/家居用品/个人洗护"""
import json, os, time, base64, urllib.request
from datetime import datetime

CRED_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "echotik.json")
with open(CRED_PATH) as f:
    creds = json.load(f)
BASE = creds["base_url"].rstrip("/")
AUTH = base64.b64encode((creds["username"] + ":" + creds["password"]).encode()).decode()
HEADERS = {"Authorization": "Basic " + AUTH, "Content-Type": "application/json"}

def api_get(path):
    url = BASE + "/" + path.lstrip("/")
    for retry in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read())
        except Exception as e:
            if retry < 2:
                time.sleep(1)
                continue
            return None

CATEGORIES = {
    "美妆工具": {"l3": ["601537","601585","601586","601587","601588","601529","852752","852880","853392","853520"]},
    "家居用品": {"l1": "600001"},
    "个人洗护": {"l3": ["601469","601476","601493","601506","601516","601550","601602","601608","601609","601615","601696","601733","853512","873480","981512"]},
}
REGIONS = {"TH": "泰国", "MY": "马来西亚", "VN": "越南", "PH": "菲律宾", "SG": "新加坡"}
RATES = {"TH": 0.028, "MY": 0.22, "VN": 4.1e-5, "PH": 0.018, "SG": 0.74}

def score(p, rate):
    sale = int(p.get("total_sale_cnt", 0) or 0)
    gmv = float(p.get("total_sale_gmv_amt", 0) or 0)
    rating = float(p.get("product_rating", 0) or 0)
    spu = float(p.get("spu_avg_price", 0) or 0)
    price = spu * rate
    w_s = min(100, (sale ** 0.3) * 8)
    w_g = min(100, (gmv ** 0.25) * 5)
    w_r = (rating / 5.0) * 100
    return round(w_s * 0.5 + w_g * 0.3 + w_r * 0.2, 2), price

results = []
api_calls = 0

for cat_name, cfg in CATEGORIES.items():
    print(f"\n{'='*50}")
    print(f"📦 {cat_name}")
    print(f"{'='*50}")
    for rc, rname in REGIONS.items():
        rate = RATES[rc]
        print(f"  🌏 {rname}({rc})...", end=" ", flush=True)
        all_items = []
        seen = set()
        total = 0

        if "l3" in cfg:
            for l3_id in cfg["l3"]:
                r = api_get(f"product/list?region={rc}&category_l3_id={l3_id}&page_num=1&page_size=10&product_sort_field=1&sort_type=1")
                api_calls += 1
                if r and r.get("code") == 0:
                    items = r.get("data", [])
                    for p in items:
                        pid = p.get("product_id", "")
                        if pid and pid not in seen:
                            seen.add(pid)
                            s, price = score(p, rate)
                            if 0.05 <= price <= 20 and int(p.get("total_sale_cnt", 0) or 0) > 0:
                                p["_s"] = s
                                p["_p"] = round(price, 2)
                                p["_r"] = rc
                                p["_c"] = cat_name
                                all_items.append(p)
                    total += len(items)
                time.sleep(0.1)
        elif "l1" in cfg:
            r = api_get(f"product/list?region={rc}&category_id={cfg['l1']}&page_num=1&page_size=10&product_sort_field=1&sort_type=1")
            api_calls += 1
            if r and r.get("code") == 0:
                items = r.get("data", [])
                for p in items:
                    s, price = score(p, rate)
                    if 0.05 <= price <= 20 and int(p.get("total_sale_cnt", 0) or 0) > 0:
                        p["_s"] = s
                        p["_p"] = round(price, 2)
                        p["_r"] = rc
                        p["_c"] = cat_name
                        all_items.append(p)
                total = len(items)

        all_items.sort(key=lambda x: x["_s"], reverse=True)
        top20 = all_items[:20]
        if top20:
            p0 = top20[0]
            print(f"OK! api={api_calls} 总{total} 合格{len(all_items)} TOP1:${p0['_p']} {p0.get('product_name','')[:30]}")
        else:
            print(f"OK! api={api_calls} 总{total} 合格{len(all_items)} (无合格)")
        results.extend(top20)

# 生成报告
ts = datetime.now().strftime("%Y-%m-%d %H:%M")
lines = [f"# 3品类×5国 选品报告 ({ts})\n\n"]
lines.append(f"**总采集: {len(results)}件 | API调用: {api_calls}次**\n\n---\n")

for cat_name in CATEGORIES:
    cat_items = [r for r in results if r.get("_c") == cat_name]
    cat_items.sort(key=lambda x: x["_s"], reverse=True)
    lines.append(f"## 📦 {cat_name} (共{len(cat_items)}件)\n\n")
    lines.append("| # | 国家 | 商品 | 价格$ | 评分 | 销量 | 商品评分 |\n")
    lines.append("|---|:----:|------|:----:|:----:|:----:|:----:|\n")
    for i, p in enumerate(cat_items[:5], 1):
        n = p.get("product_name", "")[:35]
        lines.append(f"| {i} | {p['_r']} | {n} | ${p['_p']} | {p['_s']} | {p.get('total_sale_cnt',0):,} | {p.get('product_rating',0)} |\n")
    best = cat_items[0]
    lines.append(f"\n**🏆 推荐 -> [{best['_r']}] {best.get('product_name','')[:40]} | ${best['_p']} | 评分{best['_s']} | 销量{best.get('total_sale_cnt',0):,}**\n\n---\n")

rpath = os.path.expanduser("~/选品报告_3品类_5国.md")
with open(rpath, "w") as f:
    f.write("".join(lines))
print(f"\n✅ 报告已保存: {rpath}")
print(f"\n🏆 3品类推荐产品:")
for cat_name in CATEGORIES:
    cat_items = [r for r in results if r.get("_c") == cat_name]
    cat_items.sort(key=lambda x: x["_s"], reverse=True)
    if cat_items:
        b = cat_items[0]
        print(f"  {cat_name}: [{b['_r']}] {b.get('product_name','')[:40]} | ${b['_p']} | 评分{b['_s']} | 销量{b.get('total_sale_cnt',0):,}")

print(f"\n📊 API总调用: {api_calls}次 | 总合格商品: {len(results)}件")
