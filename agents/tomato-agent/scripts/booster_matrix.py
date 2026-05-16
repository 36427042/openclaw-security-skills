#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🍅 番茄·EchoTik v2 选品引擎 (2026-05-13)
===========================================
使用EchoTik v2 API，关键词搜索代替类目过滤
新定价公式：售价 = (P + 3.5) ÷ 国家分母 → 保证35%纯利

Output:
- ~/Desktop/番茄选品报告_v2_EchoTik重选_20260513.md
- ~/Desktop/选品数据_v2_20260513.json
"""

import json, os, sys, time
from datetime import datetime

# 使用统一API客户端
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_client import EchoTikAPI

# ── 路径 ──
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESKTOP = os.path.expanduser("~/Desktop")

# ── 初始化API客户端 ──
api = EchoTikAPI(os.path.join(BASE, "config", "echotik.json"))


# ============================================================
# 🏷️ 各国税率/扣点/分母 定价公式
# ============================================================
PRICING = {
    "TH": {"commission": 0.20, "denom": 0.40, "min_price": 20,   "symbol": "฿",   "rate": 0.028, "local_per_usd": 35.8},
    "MY": {"commission": 0.23, "denom": 0.37, "min_price": 3,    "symbol": "RM",  "rate": 0.22,  "local_per_usd": 4.55},
    "PH": {"commission": 0.27, "denom": 0.33, "min_price": 50,   "symbol": "₱",   "rate": 0.018, "local_per_usd": 55.5},
    "SG": {"commission": 0.17, "denom": 0.43, "min_price": 1,    "symbol": "S$",  "rate": 0.74,  "local_per_usd": 1.35},
    "VN": {"commission": 0.26, "denom": 0.34, "min_price": 10000,"symbol": "₫",   "rate": 0.000041, "local_per_usd": 24380},
}

REGION_NAMES = {"TH": "🇹🇭泰国", "MY": "🇲🇾马来西亚", "VN": "🇻🇳越南", "PH": "🇵🇭菲律宾", "SG": "🇸🇬新加坡"}
REGION_SHORT = {"TH": "泰国", "MY": "马来西亚", "VN": "越南", "PH": "菲律宾", "SG": "新加坡"}

# 各国本地语言关键词（美妆工具/家居日用品/厨房小件）
KEYWORDS = {
    "美妆工具": {
        "TH": ["เครื่องสำอาง", "แปรงแต่งหน้า", "ที่เขียนคิ้ว", "มาสคาร่า", "อายไลเนอร์"],
        "MY": ["alat solek", "berus solek", "pensil kening", "maskara", "eyeliner"],
        "VN": ["dụng cụ trang điểm", "cọ trang điểm", "chì kẻ mày", "mascara", "kẻ mắt"],
        "PH": ["makeup tools", "makeup brush", "eyebrow pencil", "mascara", "eyeliner"],
        "SG": ["makeup tools", "makeup brush", "eyebrow pencil", "mascara", "eyeliner"],
    },
    "家居日用品": {
        "TH": ["ของใช้ในบ้าน", "ที่เก็บของ", "อุปกรณ์ทำความสะอาด", "ของใช้ประจำวัน"],
        "MY": ["barang rumah", "penyimpanan", "alat pembersih", "keperluan harian"],
        "VN": ["đồ gia dụng", "đồ dùng nhà bếp", "đồ dọn dẹp", "đồ dùng hàng ngày"],
        "PH": ["home essentials", "storage organizer", "cleaning tools", "household items"],
        "SG": ["home essentials", "storage organizer", "cleaning tools", "household items"],
    },
    "厨房小件": {
        "TH": ["เครื่องครัว", "อุปกรณ์ทำครัว", "มีดครัว", "ภาชนะใส่อาหาร"],
        "MY": ["peralatan dapur", "alat masak", "pisau dapur", "bekas makanan"],
        "VN": ["dụng cụ nhà bếp", "đồ dùng bếp", "dao bếp", "hộp đựng thực phẩm"],
        "PH": ["kitchen tools", "kitchen gadgets", "kitchen knife", "food container"],
        "SG": ["kitchen tools", "kitchen gadgets", "kitchen knife", "food container"],
    },
}


# ============================================================
# 💰 定价公式计算
# ============================================================
def calc_price(cost_rmb, region):
    """
    新定价公式：售价 = (1688拿货价P + ¥3.5国内运费) ÷ 国家分母
    分母已包含：平台扣点 + 跨境物流 + 尾程运费 + 退货损耗 + 营销成本
    保证纯利35%
    """
    cfg = PRICING[region]
    p = cost_rmb
    freight_cn = 3.5

    formula_price_rmb = (p + freight_cn) / cfg["denom"]
    local_price = formula_price_rmb / cfg["rate"]
    usd_price = formula_price_rmb / 7.2

    total_cost_rmb = p + freight_cn
    commission_amt = formula_price_rmb * cfg["commission"]
    net_revenue_rmb = formula_price_rmb - commission_amt
    profit_rmb = net_revenue_rmb - total_cost_rmb
    profit_margin = (profit_rmb / formula_price_rmb) * 100 if formula_price_rmb > 0 else 0

    is_viable = local_price >= cfg["min_price"]

    # 当地显示格式
    if local_price >= 100:
        local_display = f'{cfg["symbol"]}{local_price:,.0f}'
    else:
        local_display = f'{cfg["symbol"]}{local_price:.2f}'

    return {
        "local_price": round(local_price, 2),
        "local_price_display": local_display,
        "usd_price": round(usd_price, 2),
        "formula_rmb": round(formula_price_rmb, 2),
        "profit_margin": round(profit_margin, 1),
        "total_cost_rmb": round(total_cost_rmb, 2),
        "is_viable": is_viable,
    }


def calc_all_countries(cost_rmb, tk_price_usd=None):
    """对5个国家计算定价，检查排除规则"""
    results = {}

    for region in ["TH", "MY", "VN", "PH", "SG"]:
        r = calc_price(cost_rmb, region)
        flags = []

        # 规则1: 低价排除（<¥0.5）
        if cost_rmb < 0.5:
            flags.append("❌低价<¥0.5")

        # 规则2+3: 与TK实际售价对比
        if tk_price_usd is not None and tk_price_usd > 0:
            must_lower_than = tk_price_usd * 0.92
            lower_bound = tk_price_usd * 0.90

            if r["usd_price"] > must_lower_than:
                flags.append(f"❌公式价${r['usd_price']:.2f}>TK的92%:${must_lower_than:.2f}")
                r["_price_violation"] = "too_high"
            elif r["usd_price"] < lower_bound:
                flags.append(f"⚠️公式价${r['usd_price']:.2f}<TK的90%:${lower_bound:.2f}")
                r["_price_violation"] = "too_low"
            else:
                r["_price_violation"] = "ok"

        # 规则4: 最低售价阈值
        if not r["is_viable"]:
            flags.append(f"❌售价{r['local_price_display']}<最低{PRICING[region]['symbol']}{PRICING[region]['min_price']}")

        r["flags"] = flags

        # 状态判定
        fail_flags = [f for f in flags if f.startswith("❌")]
        warn_flags = [f for f in flags if f.startswith("⚠️")]

        if len(fail_flags) > 0:
            r["status"] = "❌不可做"
        elif len(warn_flags) > 0:
            r["status"] = "⚠️需精查"
        else:
            r["status"] = "✅可做"

        results[region] = r

    # 整体状态
    fail_count = sum(1 for r in results.values() if r["status"] == "❌不可做")
    warn_count = sum(1 for r in results.values() if r["status"] == "⚠️需精查")

    if fail_count >= 3:
        overall = "❌不可做"
    elif warn_count >= 1 or fail_count > 0:
        overall = "⚠️需精查"
    else:
        overall = "✅可做"

    return results, overall


# ============================================================
# 📥 数据采集
# ============================================================
def fetch_by_keyword(cat_name, keywords_list, region, pages=10, page_size=10):
    """用关键词列表搜索产品，合并去重"""
    rname = REGION_SHORT[region]
    print(f"  🔍 {rname} ({keywords_list[0]})...", end=" ", flush=True)

    all_items = []
    seen_ids = set()

    for kw in keywords_list:
        for page in range(1, pages + 1):
            products = api.search_products(
                region=region,
                keyword=kw,
                page_num=page,
                page_size=page_size,
                sort_field=5,
                sort_type=1
            )
            if not products:
                break
            for p in products:
                pid = p.get("product_id", "")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    all_items.append(p)
            time.sleep(0.1)

    print(f"{len(all_items)}条", end=" ", flush=True)
    return all_items


# ============================================================
# 📊 评分 + 定价 + 过滤
# ============================================================
def filter_and_score(products, region, cat_name):
    """筛选评分，取TOP100"""
    cfg = PRICING[region]
    scored = []

    for p in products:
        # 当地货币价格
        local_price_raw = float(p.get("spu_avg_price", 0) or 0)
        price_usd = local_price_raw * cfg["rate"]

        # 估算1688拿货价（从零售价倒推）
        est_cost_rmb = price_usd * 7.2 * 0.35
        if est_cost_rmb < 0.5:
            est_cost_rmb = 0.5

        # 指标
        sale_7d = int(p.get("total_sale_7d_cnt", 0) or 0)
        sale_30d = int(p.get("total_sale_30d_cnt", 0) or 0)
        sale_total = int(p.get("total_sale_cnt", 0) or 0)
        rating = float(p.get("product_rating", 0) or 0)
        review_cnt = int(p.get("review_count", 0) or 0)
        gmv_30d = float(p.get("total_sale_gmv_30d_amt", 0) or 0)
        gpm = (gmv_30d / sale_30d * 100) if sale_30d > 0 else 0
        ifl_cnt = int(p.get("total_ifl_cnt", 0) or 0)
        product_name = p.get("product_name", "") or ""
        product_id = p.get("product_id", "")

        # TK实际售价作为对比基准
        tk_actual_usd = price_usd

        # 5国定价
        countries_pricing, overall_status = calc_all_countries(est_cost_rmb, tk_actual_usd)

        # 综合评分
        growth_rate = (sale_7d / sale_30d * 100) if sale_30d > 0 else 0
        gpm_score = min(1.0, gpm / 150)
        sale_score = min(1.0, (sale_7d ** 0.3) / 15)
        rating_score = min(1.0, rating / 5.0)
        blue_score = max(0, 1 - min(ifl_cnt, 200) / 200)

        score = (gpm_score * 0.30 + sale_score * 0.25 + rating_score * 0.20 +
                 blue_score * 0.15 + min(1.0, growth_rate / 100) * 0.10)

        # 多国可行性加分
        viable_countries = sum(1 for r in ["TH", "MY", "VN", "PH", "SG"]
                              if countries_pricing.get(r, {}).get("is_viable", False))
        if viable_countries >= 3:
            score *= 1.15
        elif viable_countries <= 1:
            score *= 0.80

        # 评级
        if score >= 0.55:
            level = "🔥S"
        elif score >= 0.40:
            level = "⭐A"
        elif score >= 0.25:
            level = "👀B"
        else:
            level = "C"

        scored.append({
            "product_id": product_id,
            "product_name": product_name,
            "local_price": local_price_raw,
            "price_usd": round(price_usd, 2),
            "est_cost_rmb": round(est_cost_rmb, 2),
            "sale_7d": sale_7d,
            "sale_30d": sale_30d,
            "sale_total": sale_total,
            "growth_30d": round(growth_rate, 1),
            "gpm": round(gpm, 1),
            "rating": rating,
            "review_cnt": review_cnt,
            "ifl_cnt": ifl_cnt,
            "score": round(score, 3),
            "level": level,
            "overall_status": overall_status,
            "countries_pricing": countries_pricing,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    top100 = scored[:100]
    viable = [p for p in top100 if p["overall_status"] == "✅可做"]

    print(f"→ TOP100: ✅{len(viable)}可做 "
          f"⚠️{sum(1 for p in top100 if p['overall_status']=='⚠️需精查')}待查 "
          f"❌{sum(1 for p in top100 if p['overall_status']=='❌不可做')}排除")
    return top100


# ============================================================
# 📝 报告生成
# ============================================================
def generate_report(all_results, ts):
    lines = []

    lines.append(f"# 🍅 番茄选品报告·EchoTik v2重选 ({ts})")
    lines.append("")
    lines.append("> **数据源**: EchoTik v2 API | **筛选**: 新定价公式(35%纯利) | **搜索**: 关键词代替类目过滤")
    lines.append("> **定价公式**: 售价 = (1688拿货价P + ¥3.5运费) ÷ 国家分母")
    lines.append("")

    # ── 采集总览 ──
    lines.append("## 📊 采集总览")
    lines.append("")
    lines.append("| 品类 | 国家 | 关键词 | 获取数 | TOP100 | ✅可做 | ⚠️精查 | ❌排除 |")
    lines.append("|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|")

    totals = {"retrieved": 0, "top100": 0, "viable": 0, "warn": 0, "fail": 0}

    for cat_name in ["美妆工具", "家居日用品", "厨房小件"]:
        for region in ["TH", "MY", "VN", "PH", "SG"]:
            d = all_results.get(cat_name, {}).get(region, {})
            if d:
                kw_used = KEYWORDS[cat_name][region][0]
                retrieved = d.get("retrieved", 0)
                top100 = d.get("top100", [])
                viables = sum(1 for p in top100 if p["overall_status"] == "✅可做")
                warns = sum(1 for p in top100 if p["overall_status"] == "⚠️需精查")
                fails = sum(1 for p in top100 if p["overall_status"] == "❌不可做")
                totals["retrieved"] += retrieved
                totals["top100"] += len(top100)
                totals["viable"] += viables
                totals["warn"] += warns
                totals["fail"] += fails
                lines.append(f"| {cat_name} | {REGION_NAMES[region]} | {kw_used} | {retrieved} | {len(top100)} | {viables} | {warns} | {fails} |")

    lines.append("")
    lines.append(f"**总计**: 采集{totals['retrieved']}条 | TOP100共{totals['top100']} SKU | ✅{totals['viable']}可做 | ⚠️{totals['warn']}精查 | ❌{totals['fail']}排除")
    lines.append("")

    # ── 定价公式表 ──
    lines.append("## 💰 定价公式速查表")
    lines.append("")
    lines.append("| 国家 | 综合扣点 | 分母 | 最低可行售价 |")
    lines.append("|:---|:---:|:---:|:---|")
    for region in ["TH", "MY", "PH", "SG", "VN"]:
        cfg = PRICING[region]
        lines.append(f"| {REGION_NAMES[region]} | {cfg['commission']*100:.0f}% | {cfg['denom']:.2f} | {cfg['symbol']}{cfg['min_price']} |")
    lines.append("")

    # ── 各品类详情 ──
    for cat_name in ["美妆工具", "家居日用品", "厨房小件"]:
        lines.append(f"---")
        lines.append(f"")
        lines.append(f"# 📦 {cat_name}")
        lines.append("")

        for region in ["TH", "MY", "VN", "PH", "SG"]:
            d = all_results.get(cat_name, {}).get(region, {})
            if not d or not d.get("top100"):
                continue

            top100 = d["top100"]
            viables = [p for p in top100 if p["overall_status"] == "✅可做"]
            warns = [p for p in top100 if p["overall_status"] == "⚠️需精查"]
            fails = [p for p in top100 if p["overall_status"] == "❌不可做"]

            lines.append(f"")
            lines.append(f"## 🌏 {REGION_NAMES[region]}")
            lines.append(f"获取{d['retrieved']}条 → TOP100: ✅{len(viables)}可做 ⚠️{len(warns)}需精查 ❌{len(fails)}不可做")
            lines.append("")

            # 按利润排序（取5国中最好的利润）
            def best_profit(p):
                scores = []
                for r in ["TH", "MY", "VN", "PH", "SG"]:
                    cp = p["countries_pricing"].get(r, {})
                    if cp.get("is_viable"):
                        scores.append(cp["profit_margin"])
                return max(scores) if scores else -1

            ranked = sorted(top100, key=best_profit, reverse=True)

            # 表头
            headers = ["#", "商品名", f"售价({region})", "售价$", "估RMB", "7天销", "30天销", "评分", "分数", "评级", "5国定价详情", "整体"]
            lines.append(f"| {' | '.join(headers)} |")

            # Use markdown row separators matching header count
            lines.append(f"|{ '|'.join([':---'] * len(headers)) }|")

            for i, p in enumerate(ranked, 1):
                name_short = (p["product_name"][:24] if p["product_name"] else "N/A")
                local_price_display = p["countries_pricing"].get(region, {}).get("local_price_display", "N/A")

                # 5国定价摘要
                country_summaries = []
                for r_code in ["TH", "MY", "VN", "PH", "SG"]:
                    cp = p["countries_pricing"].get(r_code, {})
                    if cp.get("is_viable"):
                        country_summaries.append(f"{r_code}:{cp.get('profit_margin',0):.0f}%")
                    else:
                        country_summaries.append(f"{r_code}:❌")

                row = [
                    str(i),
                    name_short,
                    local_price_display,
                    f"${p['price_usd']:.2f}",
                    f"¥{p['est_cost_rmb']:.2f}",
                    str(p["sale_7d"]),
                    str(p["sale_30d"]),
                    str(p["rating"]),
                    f"{p['score']:.2f}",
                    p["level"],
                    " | ".join(country_summaries),
                    p["overall_status"],
                ]
                lines.append(f"| {' | '.join(row)} |")

            lines.append("")
            lines.append("**图例**: ✅=可做 ❌=不可做 | 利润% = 纯利率（需≥35%）")
            lines.append("")

    # ── S级推荐 ──
    lines.append(f"---")
    lines.append(f"# 🏆 精选推荐·S级产品")
    lines.append("")
    lines.append("| # | 品类 | 国家 | 商品名 | 售价$ | 估RMB | 评分 | 评级 | 7天销 | 多国利润 |")
    lines.append("|---|:---:|:---:|------|:---:|:---:|:---:|:---:|:---:|------|")

    s_products = []
    for cat_name in ["美妆工具", "家居日用品", "厨房小件"]:
        for region in ["TH", "MY", "VN", "PH", "SG"]:
            for p in all_results.get(cat_name, {}).get(region, {}).get("top100", []):
                if p["level"] in ("🔥S",) and p["overall_status"] in ("✅可做", "⚠️需精查"):
                    profit_details = []
                    for r in ["TH", "MY", "VN", "PH", "SG"]:
                        cp = p["countries_pricing"].get(r, {})
                        if cp.get("is_viable"):
                            profit_details.append(f"{REGION_SHORT[r]}:{cp.get('profit_margin',0):.0f}%")
                    s_products.append((cat_name, region, p, " | ".join(profit_details)))

    s_products.sort(key=lambda x: x[2]["score"], reverse=True)

    for i, (cat, region, p, profit_str) in enumerate(s_products[:30], 1):
        lines.append(f"| {i} | {cat[:6]} | {region} | {p['product_name'][:28]} | ${p['price_usd']:.2f} | ¥{p['est_cost_rmb']:.2f} | {p['rating']} | {p['level']} | {p['sale_7d']:,} | {profit_str[:50]} |")

    lines.append("")

    # ── 各国最佳 ──
    lines.append(f"---")
    lines.append(f"# 🌍 各国最佳选品")
    lines.append("")
    lines.append("| 国家 | 品类 | 商品名 | 售价Local | 估RMB | 评分 | 评级 | 7天销 | 纯利% |")
    lines.append("|:---:|:---:|------|:---:|:---:|:---:|:---:|:---:|:---:|")

    for region in ["TH", "MY", "VN", "PH", "SG"]:
        best = None
        best_score = -1
        for cat_name in ["美妆工具", "家居日用品", "厨房小件"]:
            for p in all_results.get(cat_name, {}).get(region, {}).get("top100", []):
                if p["score"] > best_score and p["overall_status"] == "✅可做":
                    best = (cat_name, p)
                    best_score = p["score"]
        if best:
            cat, p = best
            cp = p["countries_pricing"][region]
            lines.append(f"| {REGION_NAMES[region]} | {cat[:8]} | {p['product_name'][:28]} | {cp['local_price_display']} | ¥{p['est_cost_rmb']:.2f} | {p['rating']} | {p['level']} | {p['sale_7d']:,} | {cp.get('profit_margin',0):.1f}% |")

    lines.append("")

    # ── 综合评估 ──
    lines.append(f"---")
    lines.append(f"# 📋 综合评估")
    lines.append("")
    lines.append(f"| 维度 | 数值 |")
    lines.append(f"|:---|:---:|")
    lines.append(f"| 总TOP100合计 | {totals['top100']} SKU |")
    lines.append(f"| ✅可直接上架 | {totals['viable']} SKU |")
    lines.append(f"| ⚠️需精查定价 | {totals['warn']} SKU |")
    lines.append(f"| ❌不可做 | {totals['fail']} SKU |")
    lines.append(f"| 推荐优先 | {len(s_products)} 个S级产品 |")
    lines.append("")
    lines.append("**下步行动**:")
    lines.append("1. ✅ 优先从S级中选5-10个做精查（1688比价+竞品分析）")
    lines.append("2. ⚠️ ⚠️标记产品需AdsPower查TK实际库存和认证")
    lines.append("3. 🎬 选3-5个首批品→生菜文案→玉米视频→萝卜配音")
    lines.append("")

    lines.append(f"---")
    lines.append(f"*生成时间: {ts}*")
    lines.append(f"*工具: 🍅 番茄·EchoTik v2选品引擎 (2026-05-13版)*")

    return "\n".join(lines)


# ============================================================
# 🏁 主函数
# ============================================================
def main():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    today = datetime.now().strftime("%Y%m%d")
    print(f"\n{'='*60}")
    print(f"🍅 番茄·EchoTik v2选品 {ts}")
    print(f"{'='*60}")
    print(f"品类: 美妆工具 / 家居日用品 / 厨房小件")
    print(f"国家: TH / MY / VN / PH / SG")
    print(f"搜索: 关键词代替类目过滤")
    print(f"定价: 新公式 售价=(P+3.5)÷分母 → 35%纯利")
    print(f"{'='*60}\n")

    all_results = {}

    for cat_name in ["美妆工具", "家居日用品", "厨房小件"]:
        print(f"\n{'─'*50}")
        print(f"📦 {cat_name}")
        print(f"{'─'*50}")
        cat_results = {}

        for region in ["TH", "MY", "VN", "PH", "SG"]:
            keywords = KEYWORDS[cat_name][region]
            print(f"\n  🌏 {REGION_NAMES[region]} [{cat_name}]")

            products = fetch_by_keyword(cat_name, keywords, region, pages=10, page_size=10)

            if products:
                top100 = filter_and_score(products, region, cat_name)
            else:
                top100 = []
                print("  ⚠️ 无数据")

            cat_results[region] = {
                "retrieved": len(products),
                "top100": top100,
            }
            time.sleep(0.3)  # 国家间间隔

        all_results[cat_name] = cat_results

        # 品类统计
        total_for_cat = sum(len(v.get("top100", [])) for v in cat_results.values())
        viable_for_cat = sum(
            sum(1 for p in v.get("top100", []) if p["overall_status"] == "✅可做")
            for v in cat_results.values()
        )
        print(f"\n📊 {cat_name} 汇总: {total_for_cat} SKU | ✅{viable_for_cat}可做")

    # ── 生成报告 ──
    report = generate_report(all_results, ts)
    report_path = os.path.join(DESKTOP, f"番茄选品报告_v2_EchoTik重选_{today}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n✅ 选品报告 → {report_path}")

    # ── 保存数据 ──
    raw_data_path = os.path.join(DESKTOP, f"选品数据_v2_{today}.json")
    raw_export = {}
    for cat_name in ["美妆工具", "家居日用品", "厨房小件"]:
        raw_export[cat_name] = {}
        for region in ["TH", "MY", "VN", "PH", "SG"]:
            d = all_results.get(cat_name, {}).get(region, {})
            if d:
                raw_export[cat_name][region] = {
                    "retrieved": d.get("retrieved", 0),
                    "products": [{
                        "product_id": p["product_id"],
                        "product_name": p["product_name"],
                        "price_usd": p["price_usd"],
                        "est_cost_rmb": p["est_cost_rmb"],
                        "sale_7d": p["sale_7d"],
                        "sale_30d": p["sale_30d"],
                        "sale_total": p["sale_total"],
                        "growth_30d": p["growth_30d"],
                        "gpm": p["gpm"],
                        "rating": p["rating"],
                        "score": p["score"],
                        "level": p["level"],
                        "overall_status": p["overall_status"],
                        "pricing": {r: {
                            "local_price": cp["local_price_display"],
                            "profit_margin": cp["profit_margin"],
                            "is_viable": cp["is_viable"],
                        } for r, cp in p["countries_pricing"].items()},
                    } for p in d.get("top100", [])]
                }

    with open(raw_data_path, "w", encoding="utf-8") as f:
        json.dump(raw_export, f, ensure_ascii=False, indent=2)
    print(f"✅ 原始数据 → {raw_data_path} ({os.path.getsize(raw_data_path)/1024:.0f}KB)")

    # ── 汇总 ──
    total_top = sum(len(v.get("top100", [])) for cat in all_results.values() for v in cat.values())
    total_viable = sum(
        sum(1 for p in v.get("top100", []) if p["overall_status"] == "✅可做")
        for cat in all_results.values() for v in cat.values()
    )
    total_warn = sum(
        sum(1 for p in v.get("top100", []) if p["overall_status"] == "⚠️需精查")
        for cat in all_results.values() for v in cat.values()
    )
    total_fail = sum(
        sum(1 for p in v.get("top100", []) if p["overall_status"] == "❌不可做")
        for cat in all_results.values() for v in cat.values()
    )

    print(f"\n{'='*60}")
    print(f"📊 汇总统计")
    print(f"  总TOP100: {total_top}")
    print(f"  ✅ 可做: {total_viable}")
    print(f"  ⚠️ 精查: {total_warn}")
    print(f"  ❌ 排除: {total_fail}")
    print(f"  报告: {report_path}")
    print(f"  数据: {raw_data_path}")
    print(f"{'='*60}\n")

    return all_results


if __name__ == "__main__":
    main()
