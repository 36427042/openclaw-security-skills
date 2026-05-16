#!/usr/bin/env python3
"""
🍅 [番茄] 选品全流程引擎
1. 读已有选品缓存 + EchoTik API 拉新
2. 3品类×5国筛选
3. 为每个品搜索1688供应商
4. 合并输出产品+供应商文档
"""
import json, os, sys, time, base64, re, urllib.request, urllib.parse
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(SCRIPT_DIR)

# ─── EchoTik API ─────────────────────────────────────
CRED_PATH = os.path.join(WORKSPACE, "config", "echotik.json")
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
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            if retry < 2:
                time.sleep(2)
                continue
            return None

# ─── 选品配置 ────────────────────────────────────────
COUNTRIES = [
    ("TH", "泰国"), ("MY", "马来西亚"), ("VN", "越南"),
    ("PH", "菲律宾"), ("SG", "新加坡"),
]

CATEGORIES = {
    "美妆工具": {
        "l3_ids": ["601537","601585","601586","601587","601588","601529","852752","852880","853392","853520"],
        "keywords_cn": ["美妆蛋","化妆刷","眉笔","睫毛夹","化妆镜","美妆工具","化妆工具","粉扑"],
    },
    "家居用品": {
        "l1": "600001",
        "keywords_cn": ["收纳","置物架","收纳盒","桌面收纳","厨房收纳","家居"],
    },
    "个人洗护": {
        "l3_ids": ["601469","601476","601493","601506","601516","601550","601602","601608","601609","601615","601696","601733"],
        "keywords_cn": ["洗面奶","护肤品","护发","身体乳","面膜","防晒"],
    },
}

# ─── 多国搜索关键词（EchoTik product_name → 1688搜索词） ────
def build_1688_keyword(product_name_cn, category):
    """从产品名+品类生成1688搜索词"""
    cat_words = CATEGORIES.get(category, {}).get("keywords_cn", [category])
    # 优先用产品名中的中文部分
    cn_match = re.findall(r'[\u4e00-\u9fff]+', product_name_cn or "")
    if cn_match:
        return " ".join(cn_match[:3])
    return cat_words[0] if cat_words else category

# ─── 1688供应商搜索（通过公开搜索） ──────────────────
def search_1688_suppliers(keyword):
    """搜索1688找到对应产品的供应商/链接"""
    if not keyword or len(keyword) < 2:
        return []
    
    encoded = urllib.parse.quote(keyword)
    url = f"https://s.1688.com/selloffer/offer_search.htm?keywords={encoded}&n=y&spm=a260k.22464600.searchbox.0"
    
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Accept": "text/html,application/xhtml+xml"
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", errors="replace")
        
        # 解析搜索结果中的产品链接和标题
        suppliers = []
        # 匹配1688产品链接
        links = re.findall(r'//detail\.1688\.com/offer/(\d+\.html)', html)
        titles = re.findall(r'title="([^"]{10,60})"', html)
        prices = re.findall(r'¥?([\d.]+)[-~]¥?([\d.]+)', html)
        
        for i, link in enumerate(links[:5]):
            title = titles[i] if i < len(titles) else keyword
            price_range = ""
            if i < len(prices):
                price_range = f"¥{prices[i][0]}-{prices[i][1]}"
            suppliers.append({
                "title": title.strip(),
                "url": f"https://detail.1688.com/offer/{link}",
                "price": price_range,
            })
        
        return suppliers
    except Exception as e:
        return [{"title": f"搜索失败: {e}", "url": url, "price": ""}]

# ─── 已有选品缓存 ────────────────────────────────────
def load_cached():
    """加载昨天的选品缓存"""
    cache_paths = [
        os.path.expanduser("~/Desktop/EchoTik_5国美妆工具选品.json"),
        os.path.expanduser("~/Desktop/EchoTik_泰国美妆工具选品.json"),
    ]
    all_products = []
    seen_ids = set()
    
    for cp in cache_paths:
        if os.path.exists(cp):
            with open(cp) as f:
                data = json.load(f)
            # 遍历所有国家
            results = data.get("results", {}) if "results" in data else data
            if isinstance(results, dict):
                for cc, items in results.items():
                    if isinstance(items, list):
                        for p in items:
                            pid = p.get("product_id", "") if isinstance(p, dict) else str(p)
                            if pid and pid not in seen_ids:
                                seen_ids.add(pid)
                                all_products.append({
                                    "source": "缓存",
                                    "country": cc,
                                    "product_id": pid,
                                    "name": p.get("product_name", "") if isinstance(p, dict) else str(p),
                                    "price": p.get("min_price", 0) if isinstance(p, dict) else 0,
                                    "sales_30d": p.get("total_sale_30d_cnt", 0) if isinstance(p, dict) else 0,
                                    "rating": p.get("product_rating", 0) if isinstance(p, dict) else 0,
                                    "category": "美妆工具",
                                })
    
    return all_products

# ─── EchoTik API拉新 ─────────────────────────────────
def fetch_new_products():
    """从EchoTik拉取新品"""
    products = []
    seen_ids = set()
    
    for cat_name, cat_cfg in CATEGORIES.items():
        print(f"\n📦 {cat_name}")
        for cc, cn_name in COUNTRIES:
            # 构建查询参数
            if "l3_ids" in cat_cfg:
                for l3_id in cat_cfg["l3_ids"][:5]:  # 每个品类最多前5个子类
                    r = api_get(
                        f"product/list?region={cc}&category_l3_id={l3_id}"
                        f"&page_num=1&page_size=5&product_sort_field=1&sort_type=1"
                    )
                    if r and r.get("code") == 0 and r.get("data"):
                        for p in r["data"]:
                            pid = p.get("product_id", "")
                            if pid and pid not in seen_ids:
                                seen_ids.add(pid)
                                products.append({
                                    "source": "新拉",
                                    "country": cc,
                                    "product_id": pid,
                                    "name": p.get("product_name", ""),
                                    "price": p.get("min_price", 0),
                                    "sales_30d": p.get("total_sale_30d_cnt", 0),
                                    "rating": p.get("product_rating", 0),
                                    "category": cat_name,
                                })
            elif "l1" in cat_cfg:
                r = api_get(
                    f"product/list?region={cc}&category_id={cat_cfg['l1']}"
                    f"&page_num=1&page_size=10&product_sort_field=1&sort_type=1"
                )
                if r and r.get("code") == 0 and r.get("data"):
                    for p in r["data"]:
                        pid = p.get("product_id", "")
                        if pid and pid not in seen_ids:
                            seen_ids.add(pid)
                            products.append({
                                "source": "新拉",
                                "country": cc,
                                "product_id": pid,
                                "name": p.get("product_name", ""),
                                "price": p.get("min_price", 0),
                                "sales_30d": p.get("total_sale_30d_cnt", 0),
                                "rating": p.get("product_rating", 0),
                                "category": cat_name,
                            })
            print(f"  {cn_name}({cc})... ✅", end=" ", flush=True)
        print()
    
    return products

# ─── 筛选逻辑 ────────────────────────────────────────
def filter_products(all_products):
    """筛选条件：高销量+高评分+合理价格"""
    filtered = []
    for p in all_products:
        score = 0
        sales = p.get("sales_30d", 0) or 0
        rating = p.get("rating", 0) or 0
        price = p.get("price", 0) or 0
        
        # 销量分
        if sales > 10000:
            score += 40
        elif sales > 5000:
            score += 30
        elif sales > 1000:
            score += 20
        elif sales > 100:
            score += 10
        
        # 评分分
        if rating >= 4.5:
            score += 30
        elif rating >= 4.0:
            score += 20
        elif rating >= 3.5:
            score += 10
        
        # 价格合理性（$2-$15区间为美妆工具黄金带）
        if 2 <= price <= 15:
            score += 20
        elif price < 2 and price > 0:
            score += 10
        
        p["score"] = score
        if score >= 20:  # 最低门槛
            filtered.append(p)
    
    filtered.sort(key=lambda x: x["score"], reverse=True)
    return filtered

# ─── 主流程 ──────────────────────────────────────────
def main():
    print("=" * 50)
    print("🍅 [番茄] 选品全流程启动")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    
    # Step 1: 加载缓存
    print("\n📂 加载已有选品缓存...")
    cached = load_cached()
    print(f"   缓存中有 {len(cached)} 个产品")
    
    # Step 2: 拉新
    print("\n🔄 EchoTik API 拉新...")
    news = fetch_new_products()
    print(f"\n   新拉 {len(news)} 个产品")
    
    # Step 3: 合并去重
    all_products = cached + news
    print(f"\n📊 合并后共 {len(all_products)} 个产品")
    
    # Step 4: 筛选
    filtered = filter_products(all_products)
    print(f"\n🔍 筛选后 {len(filtered)} 个产品进入供应商搜索")
    
    # Step 5: 搜索1688供应商（取前30个）
    top30 = filtered[:30]
    print(f"\n🏭 搜索1688供应商链接...")
    enriched = []
    for i, p in enumerate(top30):
        name = p.get("name", "")
        cat = p.get("category", "美妆工具")
        keyword = build_1688_keyword(name, cat)
        suppliers = search_1688_suppliers(keyword)
        p["suppliers"] = suppliers
        enriched.append(p)
        progress = f"[{i+1}/{len(top30)}]"
        short_name = name[:25] if name else "?"
        sup_count = len(suppliers)
        print(f"  {progress} {short_name:<28} → {sup_count}个供应商", flush=True)
        time.sleep(0.5)  # 避免被封
    
    # Step 6: 生成文档
    print(f"\n📄 生成最终文档...")
    
    output = []
    output.append(f"# 🍅 番茄选品报告（含1688供应商）")
    output.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    output.append(f"**数据源**: EchoTik API + 1688搜索")
    output.append(f"**产品数**: 缓存{len(cached)}件 + 新拉{len(news)}件 = 总计{len(all_products)}件 | 精选{len(filtered)}件\n")
    
    # 按品类分组
    for cat_name in CATEGORIES:
        cat_products = [p for p in enriched if p.get("category") == cat_name]
        if not cat_products:
            continue
        output.append(f"\n---\n## 📦 {cat_name}（精选{len(cat_products)}款）\n")
        
        for p in cat_products:
            country_code = p.get("country", "?")
            name = p.get("name", "?")
            price = p.get("price", 0)
            sales = p.get("sales_30d", 0)
            rating = p.get("rating", 0)
            score = p.get("score", 0)
            suppliers = p.get("suppliers", [])
            
            output.append(f"### {name}")
            output.append(f"- **地区**: {country_code} | **价格**: ${price} | **月销**: {sales}件 | **评分**: {rating}⭐ | **综合分**: {score}")
            
            if suppliers:
                output.append(f"- **1688供应商**:")
                for s in suppliers[:3]:
                    title = s.get("title", "?")[:40]
                    url = s.get("url", "")
                    price_range = s.get("price", "")
                    output.append(f"  - [{title}]({url}) {price_range}")
            else:
                output.append(f"- **1688供应商**: 暂未找到")
            output.append("")
    
    # 完整清单
    output.append(f"\n---\n## 📋 完整清单\n")
    output.append("| # | 产品 | 品类 | 地区 | 价格$ | 月销 | 评分 | 供应商数 |")
    output.append("|---|------|:----:|:----:|:----:|:----:|:----:|:--------:|")
    for i, p in enumerate(enriched, 1):
        output.append(
            f"| {i} | {p.get('name','?')[:25]} "
            f"| {p.get('category','?')[:4]} "
            f"| {p.get('country','?')} "
            f"| ${p.get('price',0)} "
            f"| {p.get('sales_30d',0)} "
            f"| {p.get('rating',0)} "
            f"| {len(p.get('suppliers',[]))} |"
        )
    
    # 保存到桌面
    report = "\n".join(output)
    report_path = os.path.expanduser("~/Desktop/番茄选品报告_含供应商.md")
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\n✅ 文档已保存: {report_path}")
    print(f"   文档长度: {len(report)} 字符")
    
    return report_path

if __name__ == "__main__":
    main()
