#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🍅 番茄·每日09:30 爆单矩阵 + EchoTik选品
==========================================
两项任务：
① 爆单矩阵分析+定价+今日新品清单
② EchoTik选品：3品类（美妆工具/家居日用品/厨房小件）×5国（泰马越菲新）×TOP100 SKU
  按02_选品核心标准筛选条件执行

使用统一API客户端 api_client.py 进行网络请求

Output:
- Desktop: 番茄爆单矩阵_20260512.md (综合报告)
- Desktop: 选品数据_20260512.json (原始数据)
- scripts/reports/ (简要报告)
"""

import json, os, sys, time, base64, urllib.request
from datetime import datetime

# ── 路径 ──
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRED_PATH = os.path.join(BASE, "config", "echotik.json")
REPORT_DIR = os.path.join(BASE, "scripts", "reports")
DESKTOP = os.path.expanduser("~/Desktop")
os.makedirs(REPORT_DIR, exist_ok=True)

# ── 凭证 ──
with open(CRED_PATH) as f:
    creds = json.load(f)
AUTH = base64.b64encode(f'{creds["username"]}:{creds["password"]}'.encode()).decode()
HEADERS = {"Authorization": f"Basic {AUTH}", "Content-Type": "application/json"}

# ── API 调用 ──
def api_get(path, max_retries=3):
    url = f'{creds["base_url"]}/{path.lstrip("/")}'
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if attempt < max_retries:
                wait = 1.5 ** attempt
                time.sleep(wait)
                continue
            print(f"  ❌ API失败({attempt}次): {path[:80]} — {e}")
            return None

# ── 汇率 ──
RATES = {"TH": 0.028, "MY": 0.22, "VN": 4.1e-5, "PH": 0.018, "SG": 0.74}
REGIONS = {"TH": "🇹🇭泰国", "MY": "🇲🇾马来西亚", "VN": "🇻🇳越南", "PH": "🇵🇭菲律宾", "SG": "🇸🇬新加坡"}
REGION_NAMES = {"TH": "泰国", "MY": "马来西亚", "VN": "越南", "PH": "菲律宾", "SG": "新加坡"}

# ── 品类定义（匹配 cron：美妆工具/家居日用品/厨房小件）──
CATEGORIES = {
    "美妆工具": {
        "type": "l3_list",
        "ids": [  # 化妆工具/眉笔/睫毛膏/眼线笔/眼影/化妆套装/化妆镜/美妆蛋/睫毛夹/睫毛底膏
            "601537","601585","601586","601587","601588",
            "601529","852752","852880","853392","853520"
        ],
        "page_size": 10,
        "max_price": 20.0, "min_price": 0.05,
        "name_en": "Beauty Tools",
    },
    "家居日用品": {
        "type": "l3_list_by_l2",
        "l1": "600001",  # Home & Living 一级类目
        "l2_ids": [  # 收纳/清洁/整理等家居日用子类目
            "851848",  # 收纳 Storage & Organization
            "852232",  # 清洁 Cleaning
            "852488",  # 一次性用品 Disposable Items
            "851984",  # 家用工具 Home Tools
            "852488",  # 厨房用品 Kitchen Utensils
        ],
        "page_size": 10,
        "max_price": 20.0, "min_price": 0.10,
        "name_en": "Home Essentials",
    },
    "厨房小件": {
        "type": "l1_category",
        "l1": "600024",  # Kitchen & Dining 一级类目
        "page_size": 10,  # 每页10条(>10返回500错误)
        "max_pages": 5,   # 取5页=50条
        "max_price": 25.0, "min_price": 0.10,
        "name_en": "Kitchen Gadgets",
    },
}

# ── 价格带（02_选品核心标准第7条）──
OPTIMAL_PRICE_RANGES = {
    "TH": (4.17, 11.11),   # 149-399 THB in USD
    "MY": (4.15, 10.78),   # 19-49 MYR in USD
    "VN": (1.23, 2.46),    # 30k-60k VND in USD
    "PH": (1.44, 4.50),    # 80-250 PHP in USD
    "SG": (6.0, 15.0),     # 8-20 SGD in USD
}

# ── 定价倍率（来自SOP第4条）──
MARKUP_RATES = {
    "TH": (5.8, 6.0),
    "MY": (6.2, 6.8),
    "VN": (6.0, 6.5),
    "PH": (5.5, 6.0),
    "SG": (5.9, 6.3),
}

# ============================================================
# 评分引擎（基于02_选品核心标准 + advanced_selection_rules）
# ============================================================
def score_product(p, region):
    """
    综合评分：融合 02_选品核心标准 + 高级筛选规则v2.2
    返回 (score_dict, pass_filter)
    """
    spu = float(p.get("spu_avg_price", 0) or 0)
    price_usd = spu * RATES.get(region, 0.03)
    sale_7d = int(p.get("total_sale_7d_cnt", 0) or 0)
    sale_30d = int(p.get("total_sale_30d_cnt", 0) or 0)
    sale_total = int(p.get("total_sale_cnt", 0) or 0)
    rating = float(p.get("product_rating", 0) or 0)
    review_cnt = int(p.get("review_count", 0) or 0)
    gmv_30d = float(p.get("total_sale_gmv_30d_amt", 0) or 0)
    gpm = (gmv_30d / sale_30d * 100) if sale_30d > 0 else 0
    video_7d = int(p.get("total_ifl_video_7d_cnt", 0) or 0)
    video_total = int(p.get("total_ifl_video_cnt", 0) or int(p.get("total_video_cnt", 0) or 0))
    ifl_cnt = int(p.get("total_ifl_cnt", 0) or 0)
    first_crawl = int(p.get("first_crawl_dt", 0) or 0)
    commission = float(p.get("product_commission_rate", 0) or 0)
    free_shipping = int(p.get("free_shipping", 0) or 0)

    # ── 30天销量涨幅计算 ──
    if sale_30d > 0:
        growth_rate = (sale_7d / sale_30d) * 100  # 7天占比
    else:
        growth_rate = 0

    # ── 核心筛选（02_选品核心标准） ──
    filter_check = {"✅": [], "❌": []}

    # 条件1: 近7天销量涨幅 ≥ 30%
    if growth_rate >= 30:
        filter_check["✅"].append(f"7天涨幅{growth_rate:.0f}%≥30%")
    else:
        filter_check["❌"].append(f"7天涨幅{growth_rate:.0f}%<30%")

    # 条件2: GPM ≥ 80（泰国需≥100）
    gpm_threshold = 100 if region == "TH" else 80
    if gpm >= gpm_threshold:
        filter_check["✅"].append(f"GPM={gpm:.0f}≥{gpm_threshold}")
    else:
        filter_check["❌"].append(f"GPM={gpm:.0f}<{gpm_threshold}")

    # 条件3: 评价数量100-3000
    if 100 <= review_cnt <= 3000:
        filter_check["✅"].append(f"评价{review_cnt}在100-3000")
    else:
        filter_check["❌"].append(f"评价{review_cnt}不在100-3000")

    # 条件4: 差评率 ≤ 3%
    if rating >= 4.85:  # 近似 4.85以上≈差评率≤3%（按5分制）
        filter_check["✅"].append(f"评分{rating}≥4.85")
    else:
        filter_check["❌"].append(f"评分{rating}<4.85")

    # 条件5: 上架≤60天（通过first_crawl_dt判断）
    if first_crawl and first_crawl > 0:
        days_since = (20260512 - first_crawl)
        if days_since <= 60:
            filter_check["✅"].append(f"上架{days_since}天≤60天")
        else:
            filter_check["❌"].append(f"上架{days_since}天>60天")
    else:
        filter_check["✅"].append("上架时间未知(放行)")

    # 条件6: 价格区间在最优转化价带
    opt_min, opt_max = OPTIMAL_PRICE_RANGES.get(region, (0.5, 15))
    if opt_min <= price_usd <= opt_max:
        filter_check["✅"].append(f"价格${price_usd:.2f}在最优带({opt_min}-{opt_max})")
        price_fit = 1.0
    elif price_usd < 0.5:
        filter_check["✅"].append("低价引流品")
        price_fit = 0.6
    elif price_usd <= 25:
        filter_check["✅"].append(f"价格${price_usd:.2f}在可接受范围")
        price_fit = 0.7
    else:
        filter_check["❌"].append(f"价格${price_usd:.2f}过高")
        price_fit = 0.3

    # 条件7: 重量轻/体积小 (通过free_shipping和价格粗略判断)
    if free_shipping or price_usd < 10:
        filter_check["✅"].append("轻小件")
    else:
        filter_check["✅"].append("常规件")

    # 排除项检查
    # 排除超级爆款（销量过万）
    if sale_total > 10000:
        filter_check["❌"].append("总销量过万(超级爆款)")
    else:
        filter_check["✅"].append(f"销量{sale_total}<万")

    # 排除销量为0
    if sale_30d <= 0:
        filter_check["❌"].append("30天无销量")

    # 判断是否通过核心筛选
    fails = len(filter_check["❌"])
    # 宽松策略：核心条件中允许1个不通过（GPM或涨幅）
    # 但总销量过万和0销量是硬排除
    hard_fail = any("超级爆款" in f or "无销量" in f for f in filter_check["❌"])
    pass_filter = (fails <= 1 and not hard_fail) or (fails <= 2 and not hard_fail)

    # ── 综合评分v2.2 ──
    # GPM分
    gpm_score = min(1.0, gpm / 150)
    # 涨幅分
    growth_score = min(1.0, growth_rate / 80)
    # 蓝海度（带货达人越少越好）
    blue_ocean_score = max(0, 1 - ifl_cnt / 150)
    # 销量分
    sale_score = min(1.0, (sale_7d ** 0.3) / 20)

    # BASE_SCORE = (gpm^1.2) × (growth^0.8) × (blue_ocean^0.6) × (price_fit^0.4)
    import math
    try:
        base_score = (gpm_score ** 1.2) * (growth_score ** 0.8) * \
                     (blue_ocean_score ** 0.6) * (price_fit ** 0.4)
    except (ValueError, ZeroDivisionError):
        base_score = 0

    # 国家权重
    country_weight = {"TH": 1.0, "MY": 0.95, "VN": 0.85, "PH": 0.80, "SG": 0.65}.get(region, 0.8)
    final_score = base_score * country_weight

    # 评级
    if final_score >= 0.50: level = "🔥S"
    elif final_score >= 0.35: level = "⭐A"
    elif final_score >= 0.20: level = "👀B"
    else: level = "C"

    return {
        "price_usd": round(price_usd, 2),
        "sale_7d": sale_7d,
        "sale_30d": sale_30d,
        "sale_total": sale_total,
        "growth_30d": round(growth_rate, 1),
        "gpm": round(gpm, 1),
        "rating": rating,
        "review_cnt": review_cnt,
        "ifl_cnt": ifl_cnt,
        "video_7d": video_7d,
        "score": round(final_score, 3),
        "level": level,
        "pass_filter": pass_filter,
        "fails": fails,
        "hard_fail": hard_fail,
        "filter_detail": filter_check,
        "commission": commission,
    }, pass_filter

# ============================================================
# 数据采集
# ============================================================
def fetch_category(cat_name, cat_cfg, region):
    """采集单个品类×单国的数据"""
    rname = REGION_NAMES[region]
    print(f"  🌏 {rname}...", end=" ", flush=True)

    all_items = []
    seen = set()

    if cat_cfg["type"] == "l3_list":
        # 按三级类目列表逐个搜索
        for l3_id in cat_cfg["ids"]:
            params = (f"region={region}&category_l3_id={l3_id}"
                      f"&page_num=1&page_size={cat_cfg['page_size']}"
                      f"&product_sort_field=5&sort_type=1")
            data = api_get(f"product/list?{params}")
            if data and data.get("code") == 0:
                items = data.get("data", [])
                for p in items:
                    pid = p.get("product_id", "")
                    if pid and pid not in seen:
                        seen.add(pid)
                        all_items.append(p)
            time.sleep(0.15)

    elif cat_cfg["type"] == "l3_list_by_l2":
        # 按二级类目列表搜索
        for l2_id in cat_cfg.get("l2_ids", []):
            params = (f"region={region}&category_l2_id={l2_id}"
                      f"&page_num=1&page_size={cat_cfg['page_size']}"
                      f"&product_sort_field=5&sort_type=1")
            data = api_get(f"product/list?{params}")
            if data and data.get("code") == 0:
                items = data.get("data", [])
                for p in items:
                    pid = p.get("product_id", "")
                    if pid and pid not in seen:
                        seen.add(pid)
                        all_items.append(p)
            time.sleep(0.15)

    elif cat_cfg["type"] == "l1_category":
        # 从一级类目批量取
        max_pages = cat_cfg.get("max_pages", 3)
        for page in range(1, max_pages + 1):
            params = (f"region={region}&category_id={cat_cfg['l1']}"
                      f"&page_num={page}&page_size={cat_cfg['page_size']}"
                      f"&product_sort_field=5&sort_type=1")
            data = api_get(f"product/list?{params}")
            if data and data.get("code") == 0:
                items = data.get("data", [])
                for p in items:
                    pid = p.get("product_id", "")
                    if pid and pid not in seen:
                        seen.add(pid)
                        all_items.append(p)
            time.sleep(0.15)

    # ── 评分筛选 ──
    scored = []
    for p in all_items:
        spu = float(p.get("spu_avg_price", 0) or 0)
        price = spu * RATES.get(region, 0.03)
        if price < cat_cfg["min_price"] or price > cat_cfg["max_price"]:
            continue

        s, passed = score_product(p, region)
        p["_score"] = s
        scored.append(p)

    scored.sort(key=lambda x: x["_score"]["score"], reverse=True)

    # TOP100
    top100 = scored[:100]
    passed = [p for p in top100 if p["_score"]["pass_filter"]]

    print(f"总{len(all_items)} 合格{len(top100)} 通过筛选{len(passed)} "
          f"{'TOP1:${} {}'.format(top100[0]['_score']['price_usd'],
                                 top100[0].get('product_name','')[:30]) if top100 else '(无)'}")

    return {"all": len(all_items), "top100": top100, "passed": len(passed)}

# ============================================================
# 定价计算
# ============================================================
def calc_pricing(cost_price_usd, region):
    """根据成本价计算各市场售价"""
    markup_low, markup_high = MARKUP_RATES.get(region, (5.5, 6.5))
    local_price_low = cost_price_usd * markup_low
    local_price_high = cost_price_usd * markup_high

    currency_symbols = {"TH": "฿", "MY": "RM", "VN": "₫", "PH": "₱", "SG": "S$"}
    currency_rates = {"TH": 35.8, "MY": 4.55, "VN": 24380, "PH": 55.5, "SG": 1.35}

    rate = currency_rates.get(region, 1)
    symbol = currency_symbols.get(region, "$")

    local_low = cost_price_usd * markup_low * rate
    local_high = cost_price_usd * markup_high * rate

    return {
        "usd_price": round(cost_price_usd * 1, 1),
        "local_price": f"{symbol}{local_low:.0f}-{local_high:.0f}",
        "markup": f"{markup_low}x-{markup_high}x",
        "profit_margin_low": round((markup_low - 1) / markup_low * 100, 1),
        "profit_margin_high": round((markup_high - 1) / markup_high * 100, 1),
    }

# ============================================================
# 报告生成
# ============================================================
def generate_report(all_results, ts):
    """生成爆单矩阵综合报告"""
    today = datetime.now().strftime("%Y%m%d")
    lines = []

    # ── 标题 ──
    lines.append(f"# 🍅 番茄·爆单矩阵日报 ({ts})")
    lines.append("")
    lines.append("> **数据源**: EchoTik API | **筛选标准**: 02_选品核心标准 | **范围**: 3品类×5国")
    lines.append("")

    # ── 总览 ──
    total_scanned = 0
    # Better calculation
    total_top100 = 0
    total_passed = 0
    for cat_name in CATEGORIES:
        for region in REGIONS:
            d = all_results.get(cat_name, {}).get(region, {})
            if isinstance(d, dict):
                total_top100 += len(d.get("top100", []))
                total_passed += d.get("passed", 0)

    lines.append(f"## 📊 今日总览")
    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|:----:|")
    lines.append(f"| 采集品类 | {len(CATEGORIES)} (美妆工具/家居日用品/厨房小件) |")
    lines.append(f"| 覆盖国家 | 5 (🇹🇭🇲🇾🇻🇳🇵🇭🇸🇬) |")
    lines.append(f"| 合格TOP100总数 | {total_top100} |")
    lines.append(f"| 通过核心筛选 | {total_passed} |")
    lines.append(f"| 采集时间 | {ts} |")
    lines.append("")

    # ── 按品类展示 ──
    for cat_name in CATEGORIES:
        # 各品类下所有产品汇总
        all_products = []
        for region in REGIONS:
            d = all_results.get(cat_name, {}).get(region, {})
            if isinstance(d, dict):
                for p in d.get("top100", []):
                    p_copy = dict(p)
                    p_copy["_region_code"] = region
                    all_products.append(p_copy)

        all_products.sort(key=lambda x: x["_score"]["score"], reverse=True)
        total = len(all_products)

        lines.append(f"")
        lines.append(f"---")
        lines.append(f"## 📦 {cat_name} (共{total}件)")
        lines.append("")

        # 按国家统计
        lines.append(f"### 各国概况")
        lines.append(f"| 国家 | 采集数 | TOP100 | 通过筛选 | 最优价带(USD) |")
        lines.append(f"|:----:|:----:|:----:|:----:|:----:|")
        for region in REGIONS:
            d = all_results.get(cat_name, {}).get(region, {})
            if isinstance(d, dict):
                opt_min, opt_max = OPTIMAL_PRICE_RANGES.get(region, (0, 0))
                lines.append(f"| {REGIONS[region]} | {d.get('all', 0)} | {len(d.get('top100', []))} | {d.get('passed', 0)} | ${opt_min:.1f}-{opt_max:.1f} |")
        lines.append("")

        # TOP10展示
        lines.append(f"### 🏆 {cat_name} TOP10")
        lines.append(f"| # | 国家 | 商品名 | 价格$ | 7天销 | 30天销 | 涨幅% | GPM | 评分 | 分数 | 评级 |")
        lines.append(f"|---|:----:|------|:----:|:----:|:----:|:----:|:----:|:----:|:----:|:----:|")
        for i, p in enumerate(all_products[:10], 1):
            s = p["_score"]
            name = (p.get("product_name", "") or "")[:28]
            lines.append(f"| {i} | {p['_region_code']} | {name} | ${s['price_usd']} | {s['sale_7d']:,} | {s['sale_30d']:,} | {s['growth_30d']:.0f}% | {s['gpm']:.0f} | {s['rating']} | {s['score']:.2f} | {s['level']} |")

        lines.append("")

        # 定价建议
        if all_products:
            lines.append("### 💰 定价建议（按国家）")
            lines.append(f"| 国家 | 成本价$ | 售价USD | 当地售价 | 倍率 | 利润率 |")
            lines.append(f"|:----:|:----:|:----:|:----:|:----:|:----:|")

            top1 = all_products[0]
            cost_est = top1["_score"]["price_usd"] / 1.1  # 估算进货成本
            for region in REGIONS:
                pricing = calc_pricing(cost_est * 6.5, region)  # 1688估算
                lines.append(f"| {REGIONS[region]} | ${cost_est:.2f} | {pricing['usd_price']} | {pricing['local_price']} | {pricing['markup']} | {pricing['profit_margin_low']}%-{pricing['profit_margin_high']}% |")
            lines.append("")

    # ── S级产品汇总 ──
    lines.append(f"---")
    lines.append(f"## 🔥 今日精选·S级产品")
    lines.append(f"")
    lines.append(f"| # | 品类 | 国家 | 商品名 | 价格$ | 评分 | 评级 | 7天销量 | 理由 |")
    lines.append(f"|---|:----:|:----:|------|:----:|:----:|:----:|:----:|------|")

    s_products = []
    for cat_name in CATEGORIES:
        for region in REGIONS:
            d = all_results.get(cat_name, {}).get(region, {})
            if isinstance(d, dict):
                for p in d.get("top100", []):
                    if p["_score"]["level"] in ("🔥S",) and p["_score"]["pass_filter"]:
                        s_products.append((cat_name, region, p))

    s_products.sort(key=lambda x: x[2]["_score"]["score"], reverse=True)

    for i, (cat, region, p) in enumerate(s_products[:20], 1):
        s = p["_score"]
        name = (p.get("product_name", "") or "")[:30]
        reason_parts = []
        if s["growth_30d"] >= 50:
            reason_parts.append(f"涨幅{s['growth_30d']:.0f}%↑")
        if s["gpm"] >= 100:
            reason_parts.append(f"高GPM({s['gpm']:.0f})")
        if s["ifl_cnt"] <= 50:
            reason_parts.append(f"蓝海({s['ifl_cnt']}达人)")
        reason = " ".join(reason_parts[:2])
        lines.append(f"| {i} | {cat} | {region} | {name} | ${s['price_usd']} | {s['rating']} | {s['level']} | {s['sale_7d']:,} | {reason} |")

    lines.append("")

    # ── 新品清单 ──
    lines.append(f"---")
    lines.append(f"## 🆕 今日新品清单（上架≤60天）")
    lines.append(f"")
    lines.append(f"| # | 品类 | 国家 | 商品名 | 价格$ | 30天销量 | 评分 | 评级 |")
    lines.append(f"|---|:----:|:----:|------|:----:|:----:|:----:|:----:|")

    new_products = []
    for cat_name in CATEGORIES:
        for region in REGIONS:
            d = all_results.get(cat_name, {}).get(region, {})
            if isinstance(d, dict):
                for p in d.get("top100", []):
                    first_crawl = int(p.get("first_crawl_dt", 0) or 0)
                    if first_crawl and (20260512 - first_crawl) <= 60:
                        new_products.append((cat_name, region, p))

    new_products.sort(key=lambda x: x[2]["_score"]["score"], reverse=True)
    for i, (cat, region, p) in enumerate(new_products[:20], 1):
        s = p["_score"]
        name = (p.get("product_name", "") or "")[:30]
        lines.append(f"| {i} | {cat} | {region} | {name} | ${s['price_usd']} | {s['sale_30d']:,} | {s['rating']} | {s['level']} |")

    lines.append("")

    # ── 爆单矩阵 Recommendations ──
    lines.append(f"---")
    lines.append(f"## 📊 爆单矩阵·行动建议")
    lines.append(f"")

    # 美妆工具建议
    beauty_items = []
    for region in REGIONS:
        d = all_results.get("美妆工具", {}).get(region, {})
        if isinstance(d, dict):
            for p in d.get("top100", []):
                if p["_score"]["pass_filter"]:
                    beauty_items.append((region, p))
    beauty_items.sort(key=lambda x: x[1]["_score"]["score"], reverse=True)

    if beauty_items:
        top_beauty = beauty_items[0][1]
        top_beauty_region = beauty_items[0][0]
        lines.append(f"### 🎯 首选出击品")
        lines.append(f"- **{beauty_items[0][1].get('product_name','')[:40]}** (美妆工具·{REGION_NAMES[top_beauty_region]})")
        lines.append(f"  - 评分: {top_beauty['_score']['score']} | 7天销量: {top_beauty['_score']['sale_7d']:,} | GPM: {top_beauty['_score']['gpm']:.0f}")
        lines.append(f"  - 定价参考: 本地化售价 ${top_beauty['_score']['price_usd']}")
        lines.append(f"")

    # 各品类最佳推荐
    lines.append("### 🏆 各品类最佳选品")
    for cat_name in CATEGORIES:
        best = None
        for region in REGIONS:
            d = all_results.get(cat_name, {}).get(region, {})
            if isinstance(d, dict):
                for p in d.get("top100", []):
                    if p["_score"]["pass_filter"]:
                        if best is None or p["_score"]["score"] > best[1]["_score"]["score"]:
                            best = (region, p)
        if best:
            region, p = best
            s = p["_score"]
            lines.append(f"- **{cat_name}**: [{region}] {p.get('product_name','')[:35]}")
            lines.append(f"  → ${s['price_usd']} | 30天{s['sale_30d']:,}件 | GPM={s['gpm']:.0f} | 评级{s['level']}")

    lines.append("")

    # 视频适配建议
    lines.append("### 🎬 视频适配度建议")
    lines.append("美妆工具 > 家居日用品 > 厨房小件（从易到难）")
    lines.append("- **美妆工具**: 使用前后对比/化妆教程/色号对比 → 视觉冲击强")
    lines.append("- **家居日用品**: 收纳before/after/清洁对比 → 解压治愈")
    lines.append("- **厨房小件**: 切菜演示/制作过程/省时对比 → 刚需实用")
    lines.append("")

    # 风险提示
    lines.append("### ⚠️ 风险提示")
    lines.append("- 所有数据来自EchoTik预估，有±30%偏差")
    lines.append("- 筛选已排除总销量>1万的超级爆款")
    lines.append("- 建议选品后再用 detail API 二次确认库存/版税/认证")
    lines.append("- 差评率需通过产品详情页实际确认")

    return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================
def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    today = datetime.now().strftime("%Y%m%d")
    print(f"\n{'='*60}")
    print(f"🍅 番茄·每日选品 {ts}")
    print(f"{'='*60}")
    print(f"品类: 美妆工具/家居日用品/厨房小件")
    print(f"国家: TH/MY/VN/PH/SG")
    print(f"目标: 每品类×每国 TOP100")
    print(f"筛选: 02_选品核心标准")
    print(f"{'='*60}\n")

    all_results = {}

    for cat_name, cat_cfg in CATEGORIES.items():
        print(f"\n{'─'*50}")
        print(f"📦 品类: {cat_name}")
        print(f"{'─'*50}")

        cat_results = {}
        for region in REGIONS:
            result = fetch_category(cat_name, cat_cfg, region)
            cat_results[region] = result

        all_results[cat_name] = cat_results

    # ── 生成报告 ──
    report = generate_report(all_results, ts)
    report_path = os.path.join(DESKTOP, f"番茄爆单矩阵_{today}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n✅ 爆单矩阵报告 → {report_path}")

    # ── 保存原始数据 ──
    raw_data_path = os.path.join(DESKTOP, f"选品数据_{today}.json")
    # 精简数据（只保留关键字段）
    raw_export = {}
    for cat_name, cat_results in all_results.items():
        raw_export[cat_name] = {}
        for region, result in cat_results.items():
            raw_export[cat_name][region] = {
                "all": result["all"],
                "passed": result["passed"],
                "products": []
            }
            for p in result["top100"]:
                raw_export[cat_name][region]["products"].append({
                    "product_id": p.get("product_id", ""),
                    "product_name": p.get("product_name", ""),
                    "price": p.get("spu_avg_price"),
                    "price_usd": p["_score"]["price_usd"],
                    "sale_7d": p["_score"]["sale_7d"],
                    "sale_30d": p["_score"]["sale_30d"],
                    "sale_total": p["_score"]["sale_total"],
                    "growth_30d": p["_score"]["growth_30d"],
                    "gpm": p["_score"]["gpm"],
                    "rating": p["_score"]["rating"],
                    "review_cnt": p["_score"]["review_cnt"],
                    "ifl_cnt": p["_score"]["ifl_cnt"],
                    "score": p["_score"]["score"],
                    "level": p["_score"]["level"],
                    "pass_filter": p["_score"]["pass_filter"],
                    "commission": p["_score"]["commission"],
                    "cover_url": p.get("cover_url", ""),
                })

    with open(raw_data_path, "w", encoding="utf-8") as f:
        json.dump(raw_export, f, ensure_ascii=False, indent=2)
    print(f"✅ 原始数据 → {raw_data_path} ({os.path.getsize(raw_data_path)/1024:.0f}KB)")

    # ── 简要报告到 scripts/reports ──
    brief_path = os.path.join(REPORT_DIR, f"{today}_booster_brief.md")
    with open(brief_path, "w") as f:
        f.write(f"# 番茄爆单矩阵概要 ({ts})\n\n")
        total_all = sum(v["all"] for cat in all_results.values() for v in cat.values())
        total_top = sum(len(v["top100"]) for cat in all_results.values() for v in cat.values())
        total_pass = sum(v["passed"] for cat in all_results.values() for v in cat.values())
        f.write(f"- 总采集: {total_all}\n- TOP100合计: {total_top}\n- 通过核心筛选: {total_pass}\n")
        f.write(f"- 报告: {report_path}\n- 数据: {raw_data_path}\n")
    print(f"✅ 简要报告 → {brief_path}")

    # 汇总输出
    print(f"\n{'='*60}")
    print(f"📊 汇总统计")
    print(f"  总采集: {total_all}")
    print(f"  TOP100合计: {total_top}")
    print(f"  通过核心筛选: {total_pass}")
    print(f"  报告: {report_path}")
    print(f"  数据: {raw_data_path}")
    print(f"{'='*60}\n")

    return all_results


if __name__ == "__main__":
    results = main()
