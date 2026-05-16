#!/usr/bin/env python3
"""
Apply SOP selection criteria to echotik raw data
Outputs filtered products and scoring
"""
import json, re, sys

with open("echotik_selection_raw.json") as f:
    raw = json.load(f)

# Price bands per country (in USD)
PRICE_BANDS = {
    "TH": {"l": 2.80, "opt_l": 4.20, "opt_h": 11.30, "h": 14.15},  # 99/149-399/499 THB
    "MY": {"l": 2.00, "opt_l": 4.30, "opt_h": 11.10, "h": 15.70},  # 9/19-49/69 MYR
    "VN": {"l": 0.80, "opt_l": 1.20, "opt_h": 3.30, "h": 4.90},   # 20k/30k-80k/120k VND
    "PH": {"l": 0.90, "opt_l": 1.40, "opt_h": 4.50, "h": 6.30},   # 50/80-250/350 PHP
}

def in_optimal_price(price, region):
    pb = PRICE_BANDS.get(region, PRICE_BANDS["TH"])
    return pb["opt_l"] <= price <= pb["opt_h"]

def in_price_range(price, region):
    pb = PRICE_BANDS.get(region, PRICE_BANDS["TH"])
    return pb["l"] <= price <= pb["h"]

def price_fit_score(price, region):
    pb = PRICE_BANDS.get(region, PRICE_BANDS["TH"])
    if pb["opt_l"] <= price <= pb["opt_h"]:
        return 1.0
    if pb["l"] <= price <= pb["h"]:
        return 0.6
    return 0.2

def score_product(p):
    region = p["region"]
    
    gpm_score = min(1.0, p["gpm"] / 150)
    growth_score = min(1.0, p["growth_7d_pct"] / 50) if p["sale_7d"] > 0 else 0
    blue_ocean = max(0, 1 - (p.get("total_ifl_cnt", 100) or 100) / 200)
    pfit = price_fit_score(p["price_usd"], region)
    
    def spow(v, e): return max(0, v) ** max(0, e) if v > 0 else 0.0
    base = spow(gpm_score, 1.2) * spow(growth_score, 0.8) * spow(blue_ocean, 0.6) * spow(pfit, 0.4)
    
    country_weight = {"TH": 1.0, "MY": 0.95, "VN": 0.85, "PH": 0.80}
    final = base * country_weight.get(region, 0.8)
    
    if final >= 0.50:
        grade = "🔥 S级"
    elif final >= 0.35:
        grade = "⭐ A级"
    elif final >= 0.20:
        grade = "👀 B级"
    else:
        grade = "❌ C级"
    
    return round(final, 3), grade

def matches_basic_filter(p):
    """Check 8 basic filters"""
    region = p["region"]
    checks = {}
    
    # 1. 7d growth >= 30%
    if p["sale_7d"] > 0 and p["growth_7d_pct"] >= 30:
        checks["growth"] = True
    else:
        checks["growth"] = False
    
    # 2. GPM >= threshold
    threshold = 100 if region == "TH" else 80
    checks["gpm"] = p["gpm"] >= threshold
    
    # 3. Reviews 100-3000
    checks["reviews"] = 100 <= p["reviews"] <= 3000
    
    # 4. Rating >= 4.5 (proxy for low negative rate ≤ 3%)
    checks["rating"] = p["rating"] >= 4.5
    
    # 5. Price in reasonable range
    checks["price"] = in_price_range(p["price_usd"], region)
    
    # 6. Not super hot (s30 < 5000)
    checks["not_too_hot"] = p["sale_30d"] < 5000
    
    # 7. Check if likely brand/name brand
    name = p["name"].lower()
    brand_kws = ['official', 'store', 'loreal', 'l\'oreal', 'neutrogena', 'nivea', 'olay',
                 'vaseline', 'garnier', 'maybelline', 'lancome', 'estee lauder', 'clinique',
                 'sk-ii', 'shiseido', 'sulwhasoo', 'laneige', 'innisfree', 'the face shop',
                 'etude house', 'nature republic', 'missha', 'banila co', 'cosrx']
    checks["no_brand"] = not any(kw in name for kw in brand_kws)
    
    passed_count = sum(1 for v in checks.values() if v)
    all_passed = all(checks.values())
    
    return checks, all_passed, passed_count

# Additional exclusion checks
def has_exclusion(kw, name):
    name_lower = name.lower()
    liquid_kw = ['liquid', 'lotion', 'oil', 'spray', 'toner', 'serum', 'essence',
                 'sunscreen', 'cream', 'shampoo', 'conditioner', 'soap']
    fragile_kw = ['glass', 'ceramic', 'bottle', 'jar', 'mirror']
    
    if any(w in name_lower for w in fragile_kw):
        return "易碎品"
    return None

# Apply filters
results = []
for p in raw:
    checks, all_passed, passed_count = matches_basic_filter(p)
    score, grade = score_product(p)
    exclusion = has_exclusion(p.get("name"), p.get("name"))
    
    p["filter_checks"] = checks
    p["filter_passed"] = passed_count
    p["all_passed"] = all_passed
    p["score"] = score
    p["grade"] = grade
    p["exclusion"] = exclusion
    
    results.append(p)

# Sort by score desc
results.sort(key=lambda p: (-p["score"], -p["gpm"]))

# Save filtered results
filtered = [p for p in results if p["all_passed"]]
with open("echotik_selection_filtered.json", "w") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

with open("echotik_selection_passed.json", "w") as f:
    json.dump(filtered, f, ensure_ascii=False, indent=2)

# Print report
print("=" * 80)
print("📊 ECHOTIK 选品扫描 — SOP筛选评估报告")
print("=" * 80)
print(f"\n📦 扫描数据总量: {len(results)} 条")
print(f"   ✅ 全部通过8项筛选: {len(filtered)} 条 ({len(filtered)/len(results)*100:.1f}%)" if filtered else "   ✅ 全部通过8项筛选: 0 条")
print(f"   🔥 S级 (score≥0.50): {sum(1 for r in results if r['grade']=='🔥 S级')}")
print(f"   ⭐ A级 (0.35-0.49): {sum(1 for r in results if r['grade']=='⭐ A级')}")
print(f"   👀 B级 (0.20-0.34): {sum(1 for r in results if r['grade']=='👀 B级')}")
print(f"   ❌ C级 (<0.20): {sum(1 for r in results if r['grade']=='❌ C级')}")

for cat_name in ["美妆洗护", "家居用品"]:
    print(f"\n{'─'*70}")
    print(f"  ── {cat_name} ──")
    print(f"{'─'*70}")
    
    for region, country in [("TH","泰国"),("MY","马来西亚"),("ID","印尼"),("PH","菲律宾"),("VN","越南")]:
        items = [r for r in results if r['category']==cat_name and r['region']==region]
        if not items: continue
        
        passed = [r for r in items if r["all_passed"]]
        s_grade = [r for r in items if r['grade']=='🔥 S级']
        a_grade = [r for r in items if r['grade']=='⭐ A级']
        
        if not passed:
            print(f"\n  📍 {country} ({region}) — {len(items)}条, {len(passed)}条通过筛选, S/A级={len(s_grade)}/{len(a_grade)}")
            # Show top 3 even if not all passed
            print(f"     (未通过筛选 Top 3—供参考):")
            for r in sorted(items, key=lambda x: -x['score'])[:3]:
                print(f"     {r['name'][:35]:35s} | score:{r['score']:.3f} | {r['grade']} | "
                      f"gpm:{r['gpm']:.0f} | s7:{r['sale_7d']} | s30:{r['sale_30d']} | "
                      f"r:{r['rating']} rev:{r['reviews']} | ${r['price_usd']:.2f}")
            continue
        
        print(f"\n  📍 {country} ({region}) — {len(items)}条, {len(passed)}条通过筛选, S/A级={len(s_grade)}/{len(a_grade)}")
        
        # Show all passed items
        for i, r in enumerate(sorted(passed, key=lambda x: -x['score']), 1):
            print(f"  {i:2d}. {r['grade']} {r['name'][:35]:35s} | score:{r['score']:.3f} | "
                  f"gpm:{r['gpm']:.0f} | s7:{r['sale_7d']:>4} | s30:{r['sale_30d']:>5} | "
                  f"g:{r['growth_7d_pct']:.0f}% | r:{r['rating']} | rev:{r['reviews']:>4} | "
                  f"${r['price_usd']:.2f}")
        
        if not passed and s_grade:
            print(f"     (S级 Top 3):")
            for r in sorted(s_grade, key=lambda x: -x['score'])[:3]:
                print(f"     {r['name'][:35]:35s} | score:{r['score']:.3f} | "
                      f"gpm:{r['gpm']:.0f} | s7:{r['sale_7d']} | s30:{r['sale_30d']}")

print(f"\n{'='*80}")
print(f"📁 输出文件:")
print(f"   echotik_selection_raw.json — 原始829条数据")
print(f"   echotik_selection_filtered.json — 加权评分全部数据")
print(f"   echotik_selection_passed.json — 仅通过筛选的")
print(f"{'='*80}")
