#!/usr/bin/env python3
"""
booster_matrix.py — 🍅 番茄·爆单矩阵 v2.0
功能：
  1. EchoTik API 选品：3品类×5国×TOP100 SKU（02_选品核心标准筛选）
  2. 5国定价计算（25店矩阵）
  3. 今日新品清单
  4. GEP进化记录
  5. 1688供应商链接搜索（精选TOP30）
  6. 综合报告 → 桌面 + data/booster/
"""
import json, os, sys, time, base64, re, urllib.request, urllib.parse
from datetime import datetime
from gep_engine import GEP

gep = GEP("番茄")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
DATA_DIR = os.path.join(WORKSPACE, "data")
BOOSTER_DIR = os.path.join(DATA_DIR, "booster")
LOG_DIR = os.path.join(DATA_DIR, "logs")
os.makedirs(BOOSTER_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ─── EchoTik API ─────────────────────────────────────
ECHOTIK_CRED = os.path.expanduser("~/.openclaw/workspace/agents/tomato-agent/config/echotik.json")
if os.path.exists(ECHOTIK_CRED):
    with open(ECHOTIK_CRED) as f:
        _creds = json.load(f)
    _BASE = _creds["base_url"].rstrip("/")
    _AUTH = base64.b64encode((_creds["username"] + ":" + _creds["password"]).encode()).decode()
    _HEADERS = {"Authorization": "Basic " + _AUTH, "Content-Type": "application/json"}
else:
    _BASE = "https://open.echotik.live/api/v2"
    _HEADERS = {}

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] [{level}] {msg}"
    with open(os.path.join(LOG_DIR, "booster.log"), "a", encoding="utf-8") as f:
        f.write(entry + "\n")
    print(f"  {entry}")

def echotik_api(path):
    """EchoTik API GET 请求（自动重试3次）"""
    url = _BASE + "/" + path.lstrip("/")
    for retry in range(3):
        try:
            req = urllib.request.Request(url, headers=_HEADERS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            log(f"EchoTik HTTP {e.code} for {path[:60]}", "WARN")
            if retry < 2:
                time.sleep(2)
        except Exception as e:
            log(f"EchoTik error: {e}", "WARN")
            if retry < 2:
                time.sleep(2)
            else:
                return None
    return None

# ═══════════════════════════════════════════════════
#  选品配置（3品类 × 5国）
# ═══════════════════════════════════════════════════

COUNTRIES = [
    ("TH", "泰国"), ("MY", "马来西亚"), ("VN", "越南"),
    ("PH", "菲律宾"), ("SG", "新加坡"),
]

# 品类关键词拼音映射（用于搜索）
COUNTRY_KEYWORDS = {
    "TH": {"美妆工具": "เครื่องสำอาง", "家居日用品": "ของใช้", "厨房小件": "เครื่องครัว"},
    "MY": {"美妆工具": "alat solek", "家居日用品": "barangan", "厨房小件": "alat dapur"},
    "VN": {"美妆工具": "mỹ phẩm", "家居日用品": "đồ gia dụng", "厨房小件": "dụng cụ bếp"},
    "PH": {"美妆工具": "makeup", "家居日用品": "bahay", "厨房小件": "kusina"},
    "SG": {"美妆工具": "makeup", "家居日用品": "household", "厨房小件": "kitchen"},
}

# 3品类 EchoTik L3 类目 ID（根据 cron 任务要求：美妆工具/家居日用品/厨房小件）
CATEGORIES = {
    "美妆工具": {
        "keywords_cn": ["makeup","beauty","cosmetic","eyelash","sponge",
                        "brush","mascara","eyebrow","lipstick","powder"],
    },
    "家居日用品": {
        "keywords_cn": ["storage","organizer","household","home","kitchen",
                        "rack","shelf","hook","bathroom","cleaning"],
    },
    "厨房小件": {
        "keywords_cn": ["kitchen","peeler","grater","container","utensil",
                        "opener","strainer","sharpener","spatula","tongs"],
    },
}

# ─── 筛选标准（02_选品核心标准） ────────────────────
# 销量权重40% + 评分权重30% + 价格合理性20% + 视频数10%
def apply_selection_criteria(p):
    """全面筛选打分"""
    score = 0
    sales = p.get("sales_30d", 0) or 0
    rating = p.get("rating", 0) or 0
    price = p.get("price", 0) or 0
    videos = p.get("video_count", 0) or 0

    # 销量标准：>=300月销为合格
    if sales >= 10000: score += 40
    elif sales >= 5000: score += 35
    elif sales >= 2000: score += 30
    elif sales >= 500: score += 20
    elif sales >= 100: score += 10

    # 评分标准：>=4.0为合格
    if rating >= 4.8: score += 30
    elif rating >= 4.5: score += 25
    elif rating >= 4.0: score += 20
    elif rating >= 3.5: score += 10

    # 价格合理性：不同品类价格不同
    cat = p.get("category", "")
    if cat == "美妆工具":
        if 1.5 <= price <= 20: score += 20
        elif price > 0: score += 10
    elif cat == "家居日用品":
        if 3 <= price <= 30: score += 20
        elif price > 0: score += 10
    elif cat == "厨房小件":
        if 2 <= price <= 25: score += 20
        elif price > 0: score += 10
    else:
        if 2 <= price <= 15: score += 20

    # 视频数/内容热度
    if videos >= 100: score += 10
    elif videos >= 50: score += 8
    elif videos >= 10: score += 5

    p["score"] = score
    return p

# ─── 新品判断（销售天数<=30天 或 上架 < 15天） ──────
def is_new_product(p):
    sales = p.get("sales_30d", 0) or 0
    rating = p.get("rating", 0) or 0
    return sales < 100 and rating >= 4.0

# ═══════════════════════════════════════════════════
#  定价公式v2.0（2026-05-13 天赐固化）
# 售价 = (1688拿货价P + ¥3.5) ÷ 国家分母 → 35%纯利
# EchoTik v2 返回USD价，需 ×7.2 转CNY比较
# ═══════════════════════════════════════════════════
PRICING = {
    "TH": {"denom": 0.40, "min_local": 20,   "cur": "฿", "rate": 5.0},
    "MY": {"denom": 0.37, "min_local": 3,    "cur": "RM", "rate": 1.5},
    "VN": {"denom": 0.34, "min_local": 10000,"cur": "₫", "rate": 3500},
    "PH": {"denom": 0.33, "min_local": 50,   "cur": "₱", "rate": 8.0},
    "SG": {"denom": 0.43, "min_local": 1,    "cur": "S$", "rate": 5.5},
}
DOMESTIC_SHIPPING = 3.5
USD_TO_CNY = 7.2
MIN_1688_COST = 0.5
TARGET_RATIO = 0.92  # 比TK竞品低8%

def apply_pricing_filter(price_usd, region):
    """定价过滤: 返回 (status, reason, formula_price_local)"""
    price_cny = round(price_usd * USD_TO_CNY, 2)
    cfg = PRICING.get(region)
    if not cfg:
        return "warn", "未知国家", 0
    # 估算1688成本 (TK售价×0.15)
    cost = round(price_cny * 0.15, 2)
    if cost < MIN_1688_COST:
        return "reject", f"成本¥{cost}<¥{MIN_1688_COST}", 0
    # 公式价(当地货币)
    formula = round((cost + DOMESTIC_SHIPPING) / cfg["denom"] * cfg["rate"], 0)
    if formula < cfg["min_local"]:
        return "reject", f"公式价{formula}{cfg['cur']}<最低{cfg['min_local']}", formula
    # 目标价: TK当地价×0.92
    price_local = round(price_cny * cfg["rate"], 2)
    target = round(price_local * TARGET_RATIO, 2)
    if formula > target:
        return "reject", f"公式价{formula}>{target}，竞争不过", formula
    return "ok", "", formula

# ═══════════════════════════════════════════════════
#  Feed 搜索函数（按品类+国家组合）
# ═══════════════════════════════════════════════════

def search_category_country(cat_name, cat_cfg, cc):
    """按品类+国家搜索 EchoTik，返回产品列表"""
    products = []
    seen_ids = set()
    page_count = 2  # 每关键词2页，每页10 → 5关键词×2页×10=100品
    
    # v2 API: 类目过滤不可靠，改用英文关键词搜索
    kw_list = cat_cfg.get("keywords_cn", [])
    for kw in kw_list[:3]:  # 每品类拿前3个关键词
        for page in range(1, page_count + 1):
            r = echotik_api(
                f"product/list?region={cc}&keyword={urllib.parse.quote(kw)}"
                f"&page_num={page}&page_size=10&product_sort_field=1&sort_type=1"
            )
            if r and r.get("code") == 0 and r.get("data"):
                for p in r["data"]:
                    pid = p.get("product_id", "")
                    if pid and pid not in seen_ids:
                        seen_ids.add(pid)
                        # 定价过滤
                        price_usd = p.get("min_price", 0) or p.get("spu_avg_price", 0) or 0
                        ps, reason, fprice = apply_pricing_filter(price_usd, cc)
                        if ps == "reject":
                            continue  # 排除不可做产品
                        products.append({
                            "source": "EchoTik",
                            "country": cc,
                            "product_id": pid,
                            "name": p.get("product_name", ""),
                            "price": p.get("min_price", 0) or p.get("spu_avg_price", 0),
                            "sales_30d": p.get("total_sale_30d_cnt", 0),
                            "rating": p.get("product_rating", 0),
                            "video_count": p.get("video_count", 0),
                            "category": cat_name,
                            "pricing_status": ps,
                            "pricing_reason": reason,
                            "formula_price": fprice,
                        })
            elif r:
                break  # 无更多数据
            elif r:
                break
    return products

# ═══════════════════════════════════════════════════
#  定价计算（5国 × 5店 = 25店矩阵）
# ═══════════════════════════════════════════════════

PRICING_CONFIG = {
    "TH": {"name": "泰国", "multiplier": 5.8, "currency": "THB", "min_profit_pct": 480},
    "MY": {"name": "马来西亚", "multiplier": 6.2, "currency": "MYR", "min_profit_pct": 520},
    "VN": {"name": "越南", "multiplier": 6.0, "currency": "VND", "min_profit_pct": 500},
    "ID": {"name": "印尼", "multiplier": 5.5, "currency": "IDR", "min_profit_pct": 450},
    "PH": {"name": "菲律宾", "multiplier": 5.5, "currency": "PHP", "min_profit_pct": 450},
    "SG": {"name": "新加坡", "multiplier": 6.5, "currency": "SGD", "min_profit_pct": 550},
}

def calculate_pricing(cost_rmb):
    """根据人民币成本价计算5国售价"""
    results = {}
    for cc, cfg in PRICING_CONFIG.items():
        local_price = round(cost_rmb * cfg["multiplier"], 2)
        profit_margin = round((local_price - cost_rmb) / cost_rmb * 100, 1)
        results[cc] = {
            "cost_rmb": cost_rmb,
            "local_price": local_price,
            "currency": cfg["currency"],
            "profit_margin": profit_margin,
            "status": "✅" if profit_margin >= cfg["min_profit_pct"] else "⚠️"
        }
    return results

def estimate_cost_from_echotik(price_usd, category):
    """从EchoTik售价($)估算人民币成本价（经验公式）"""
    # 美妆工具: 售价=成本×5~6, 家居: ×4~5, 厨房小件: ×4~6
    margin = {"美妆工具": 5.5, "家居日用品": 4.5, "厨房小件": 5.0}
    m = margin.get(category, 5.0)
    # $1 ≈ 7.2 RMB
    cost_rmb = round((price_usd * 7.2) / m, 2)
    return cost_rmb if cost_rmb > 0 else 3.0

# ═══════════════════════════════════════════════════
#  1688 供应商搜索
# ═══════════════════════════════════════════════════

def search_1688(keyword):
    """搜索1688供应商"""
    if not keyword or len(keyword) < 2:
        return []
    encoded = urllib.parse.quote(keyword)
    url = f"https://s.1688.com/selloffer/offer_search.htm?keywords={encoded}&n=y"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html"
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", errors="replace")
        links = re.findall(r'//detail\.1688\.com/offer/(\d+\.html)', html)
        titles = re.findall(r'title="([^"]{10,60})"', html)
        prices = re.findall(r'¥([\d.]+)[-~]¥?([\d.]+)', html)
        suppliers = []
        for i, link in enumerate(links[:5]):
            title = titles[i] if i < len(titles) else keyword
            pr = f"¥{prices[i][0]}-{prices[i][1]}" if i < len(prices) else ""
            suppliers.append({"title": title.strip()[:40], "url": f"https://detail.1688.com/offer/{link}", "price": pr})
        return suppliers
    except Exception as e:
        return [{"title": f"搜索失败", "url": url[:60], "price": "?"}]

# ═══════════════════════════════════════════════════
#  主流程
# ═══════════════════════════════════════════════════

def do_full_run():
    log("=" * 50)
    log("🍅 爆单矩阵 v2.0 启动")
    log(f"模式: EchoTik选品 + 25店定价 + 供应商搜索")

    ctx = {"started_at": datetime.now().isoformat()}
    advice = gep.pre_check("booster_daily_run", ctx)
    if advice and advice.get("cautious"):
        log(f"📖 GEP经验: {advice.get('advice','')[:80]}", "GEP")

    # ═══ Phase 1: EchoTik 选品 ═══════════════════
    log("─" * 40)
    log("Phase 1: EchoTik 选品（3品类×5国×TOP100 SKU）")
    
    all_products = []
    for cat_name, cat_cfg in CATEGORIES.items():
        log(f"  📦 {cat_name}")
        for cc, cn_name in COUNTRIES:
            prods = search_category_country(cat_name, cat_cfg, cc)
            all_products.extend(prods)
            kw = COUNTRY_KEYWORDS.get(cc, {}).get(cat_name, "")
            log(f"    {cn_name}({cc}) → {len(prods)}品", "DATA")
        log("")

    log(f"📊 EchoTik 原始数据: {len(all_products)} 品")

    # ═══ Phase 2: 筛选（02_选品核心标准） ═══════
    log("─" * 40)
    log("Phase 2: 选品标准筛选")
    
    scored = [apply_selection_criteria(p) for p in all_products]
    passed = [p for p in scored if p["score"] >= 20]
    passed.sort(key=lambda p: p["score"], reverse=True)
    
    # TOP 100
    top100 = passed[:100] if len(passed) > 100 else passed
    
    new_products = [p for p in top100 if is_new_product(p)]
    
    log(f"  合格品: {len(passed)} | TOP100: {len(top100)} | 今日新品: {len(new_products)}")

    # ═══ Phase 3: 定价计算 ═══════════════════════
    log("─" * 40)
    log("Phase 3: 定价计算（5国×5店=25店矩阵）")
    
    pricing_report = {}
    for p in top100[:50]:  # 前50个做定价
        name = p.get("name", "?")[:20]
        cat = p.get("category", "美妆工具")
        cost = estimate_cost_from_echotik(p.get("price", 0), cat)
        pricing = calculate_pricing(cost)
        pricing_report[name] = {"cost_rmb": cost, "pricing": pricing}

    # ═══ Phase 4: 1688供应商搜索（TOP30） ════════
    log("─" * 40)
    log("Phase 4: 1688供应商搜索（精选TOP30）")
    
    enriched_top30 = []
    for i, p in enumerate(top100[:30]):
        time.sleep(0.3)  # 防封
        name = p.get("name", "")
        cat = p.get("category", "美妆工具")
        kw = CATEGORIES.get(cat, {}).get("keywords_cn", [cat])[0]
        cn_match = re.findall(r'[\u4e00-\u9fff]+', name or "")
        search_kw = " ".join(cn_match[:3]) if cn_match else kw
        suppliers = search_1688(search_kw)
        p["suppliers"] = suppliers
        p["_search_keyword"] = search_kw
        enriched_top30.append(p)
        log(f"  [{i+1:2d}/{30}] {name[:25]:<28} → {len(suppliers)}供应商", "DATA")

    # ═══ Phase 5: 生成报告 ═══════════════════════
    log("─" * 40)
    log("Phase 5: 生成综合报告")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    today = datetime.now().strftime("%Y%m%d")
    
    # ── 品类分布统计 ──
    cat_stats = {}
    for cat_name in CATEGORIES:
        count = sum(1 for p in top100 if p.get("category") == cat_name)
        avg_score = round(sum(p["score"] for p in top100 if p.get("category") == cat_name) / max(count, 1), 1)
        cat_stats[cat_name] = {"count": count, "avg_score": avg_score}

    # ── 各国分布统计 ──
    country_stats = {}
    for cc, cn_name in COUNTRIES:
        count = sum(1 for p in top100 if p.get("country") == cc)
        country_stats[cc] = count

    lines = []
    lines.append(f"# 🍅 每日爆单矩阵报告")
    lines.append(f"**生成时间**: {now}")
    lines.append(f"**数据源**: EchoTik API + 1688搜索")
    lines.append("")
    lines.append(f"## 📊 概览")
    lines.append(f"- 全部采集: {len(all_products)} 品")
    lines.append(f"- 合格通过: {len(passed)} 品")
    lines.append(f"- 🏆 TOP 100: {len(top100)} 品")
    lines.append(f"- 🆕 今日新品: {len(new_products)} 品（低销量高评分趋势品）")
    lines.append("")
    
    # ── 品类分布 ──
    lines.append(f"### 品类分布")
    lines.append(f"| 品类 | 数量 | 均分 |")
    lines.append(f"|:----|:----:|:----:|")
    for cat_name, stats in cat_stats.items():
        bar = "█" * (stats["count"] // 5)
        lines.append(f"| {cat_name} | {stats['count']} {bar} | {stats['avg_score']} |")
    lines.append("")
    
    # ── 国家分布 ──
    lines.append(f"### 国家分布")
    lines.append(f"| 国家 | 数量 |")
    lines.append(f"|:----|:----:|")
    for cc, cn_name in COUNTRIES:
        count = country_stats.get(cc, 0)
        bar = "█" * (count // 4)
        lines.append(f"| {cn_name}({cc}) | {count} {bar} |")
    lines.append("")

    # ── 定价报告 ──
    lines.append(f"## 💰 25店矩阵定价")
    lines.append(f"| 代表品 | 成本¥ | THB | MYR | VND | IDR | PHP | SGD |")
    lines.append(f"|:------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for i, (name, pd) in enumerate(list(pricing_report.items())[:10]):
        lines.append(
            f"| {name[:15]} | ¥{pd['cost_rmb']} "
            f"| {pd['pricing'].get('TH',{}).get('local_price','?')} "
            f"| {pd['pricing'].get('MY',{}).get('local_price','?')} "
            f"| {pd['pricing'].get('VN',{}).get('local_price','?')} "
            f"| {pd['pricing'].get('ID',{}).get('local_price','?')} "
            f"| {pd['pricing'].get('PH',{}).get('local_price','?')} "
            f"| {pd['pricing'].get('SG',{}).get('local_price','?')} |"
        )
    lines.append("")

    # ── 今日新品清单 ──
    lines.append(f"## 🆕 今日新品清单（{len(new_products)}件）")
    if new_products:
        lines.append(f"| # | 产品 | 品类 | 地区 | 价格$ | 评分 | 综合分 |")
        lines.append(f"|---|------|:----:|:----:|:----:|:----:|:----:|")
        for i, p in enumerate(new_products[:20], 1):
            lines.append(
                f"| {i} | {p.get('name','?')[:30]} "
                f"| {p.get('category','?')[:6]} "
                f"| {p.get('country','?')} "
                f"| ${p.get('price',0)} "
                f"| {p.get('rating',0)}⭐ "
                f"| {p.get('score',0)} |"
            )
    else:
        lines.append("暂无新品趋势")
    lines.append("")

    # ── TOP 100 完整清单 ──
    lines.append(f"## 🏆 TOP 100 选品清单")
    lines.append(f"| # | 产品 | 品类 | 地区 | 价格$ | 月销 | 评分 | 视频 | 分 |")
    lines.append(f"|---|------|:----:|:----:|:----:|:----:|:----:|:----:|:--:|")
    for i, p in enumerate(top100, 1):
        lines.append(
            f"| {i:3d} | {p.get('name','?')[:28]} "
            f"| {p.get('category','?')[:6]} "
            f"| {p.get('country','?')} "
            f"| ${p.get('price',0)} "
            f"| {p.get('sales_30d',0)} "
            f"| {p.get('rating',0)} "
            f"| {p.get('video_count',0)} "
            f"| {p['score']} |"
        )
    lines.append("")

    # ── 供应商清单（TOP30） ──
    lines.append(f"## 🏭 1688供应商（精选TOP30）")
    for i, p in enumerate(enriched_top30, 1):
        lines.append(f"### {i}. {p.get('name','?')[:40]}")
        lines.append(f"- **品类**: {p.get('category','?')} | **地区**: {p.get('country','?')} | **价格**: ${p.get('price',0)}")
        lines.append(f"- **月销**: {p.get('sales_30d',0)} | **评分**: {p.get('rating',0)}⭐ | **综合分**: {p['score']}")
        suppliers = p.get("suppliers", [])
        if suppliers:
            lines.append(f"- **1688供应商**:")
            for s in suppliers[:3]:
                lines.append(f"  - [{s['title']}]({s['url']}) {s['price']}")
        else:
            lines.append(f"- **1688供应商**: 暂未找到")
        lines.append("")

    report = "\n".join(lines)

    # ── 保存 ──
    # 桌面报告
    desktop_report = os.path.expanduser(f"~/Desktop/番茄_每日爆单矩阵_{today}.md")
    with open(desktop_report, "w", encoding="utf-8") as f:
        f.write(report)

    # 结构化JSON
    json_path = os.path.join(BOOSTER_DIR, f"booster_full_{today}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": now,
            "total_collected": len(all_products),
            "passed": len(passed),
            "top100": len(top100),
            "new_products": len(new_products),
            "categories": cat_stats,
            "countries": country_stats,
            "top100_list": [{k: p.get(k) for k in ("product_id","name","category","country","price","sales_30d","rating","score")} for p in top100],
        }, f, ensure_ascii=False, indent=2)

    # ── 定价JSON ──
    pricing_path = os.path.join(BOOSTER_DIR, f"pricing_{today}.json")
    with open(pricing_path, "w", encoding="utf-8") as f:
        json.dump({"generated_at": now, "matrix_25stores": pricing_report}, f, ensure_ascii=False, indent=2)

    # ── 输出摘要 ──
    log("=" * 50)
    log(f"✅ 爆单矩阵完成")
    log(f"   采集: {len(all_products)}品 | 合格: {len(passed)} | TOP100: {len(top100)} | 新品: {len(new_products)}")
    log(f"   定价: 25店矩阵（5国×5店）")
    log(f"   供应商: TOP30已搜")
    log(f"   报告: {desktop_report}")
    log(f"   JSON: {json_path}")
    log(f"   GEP: {gep.get_stats().get('total',0)}条")
    log("=" * 50)

    # GEP 记录
    try:
        gep.post_record("booster_daily_run", {
            "total": len(all_products),
            "passed": len(passed),
            "top100": len(top100),
            "new": len(new_products),
        }, "success")
    except Exception:
        pass

    # JSON stdout — 框架捕获
    summary_output = {
        "status": "completed",
        "total_collected": len(all_products),
        "passed": len(passed),
        "top100": len(top100),
        "new_products": len(new_products),
        "categories": cat_stats,
        "countries": country_stats,
        "reports": {
            "markdown": desktop_report,
            "json": json_path,
            "pricing": pricing_path,
        },
    }
    print(json.dumps(summary_output, ensure_ascii=False))
    return summary_output


def main():
    """CLI入口（兼容框架argparse调用）"""
    return do_full_run()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="🍅 番茄·爆单矩阵 - EchoTik选品+25店定价+1688供应商")
    parser.add_argument("--full-run", action="store_true", default=True, help="执行全流程选品(默认)")
    parser.add_argument("--no-1688", action="store_true", help="跳过1688供应商搜索")
    parser.add_argument("--max-products", type=int, default=50, help="定价计算最大产品数")
    args = parser.parse_args()
    result = main()
    sys.exit(0 if result else 1)
