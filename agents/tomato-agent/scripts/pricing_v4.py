#!/usr/bin/env python3
"""
定价公式 v4.0 — 灵活混合定价脚本
天赐 2026-05-15 17:25 固化版

规则：
  - 售价 ≤ 30CNY → 35% 纯利（低价品）
  - 售价 > 30CNY → 20% 纯利（高价品）
  - 判断方式：用 35% 分母算各国 CNY 等价售价，逐站独立决策
  - 家居/厨房产品不跟 TK 比价，直接上架

使用方式：
  from pricing_v4 import calc_price, get_profit_tier, list_all_prices
"""

__version__ = "4.0"
__updated__ = "2026-05-15 17:25"

# ═══════════════════════════════════════════════
# 1. 核心参数（不可随意改，改需天赐确认）
# ═══════════════════════════════════════════════

# 35% 纯利分母（低价品）
DENOMS_35 = {
    'TH': 0.40,   # 综合扣点 20%  → 分母 = 0.60 - 0.20 = 0.40
    'MY': 0.37,   # 综合扣点 23%  → 分母 = 0.60 - 0.23 = 0.37
    'PH': 0.33,   # 综合扣点 27%  → 分母 = 0.60 - 0.27 = 0.33
    'SG': 0.43,   # 综合扣点 17%  → 分母 = 0.60 - 0.17 = 0.43
    'VN': 0.34,   # 综合扣点 26%  → 分母 = 0.60 - 0.26 = 0.34
}

# 20% 纯利分母（高价品）
DENOMS_20 = {
    'TH': 0.55,   # 综合扣点 20%  → 分母 = 0.75 - 0.20 = 0.55
    'MY': 0.52,   # 综合扣点 23%  → 分母 = 0.75 - 0.23 = 0.52
    'PH': 0.48,   # 综合扣点 27%  → 分母 = 0.75 - 0.27 = 0.48
    'SG': 0.58,   # 综合扣点 17%  → 分母 = 0.75 - 0.17 = 0.58
    'VN': 0.49,   # 综合扣点 26%  → 分母 = 0.75 - 0.26 = 0.49
}

# 各国货币信息
COUNTRIES = {
    'TH': {'name': '泰国',  'currency': 'THB', 'rate': 4.95,   'symbol': '฿'},
    'MY': {'name': '马来西亚', 'currency': 'MYR', 'rate': 0.64,   'symbol': 'RM'},
    'PH': {'name': '菲律宾', 'currency': 'PHP', 'rate': 7.85,   'symbol': '₱'},
    'SG': {'name': '新加坡', 'currency': 'SGD', 'rate': 0.19,   'symbol': 'S$'},
    'VN': {'name': '越南',   'currency': 'VND', 'rate': 3450,   'symbol': '₫'},
}

# 定价阈值
LOW_PRICE_THRESHOLD_CNY = 30.0
DOMESTIC_FREIGHT = 3.5  # 国内运费（元/kg内固定）


# ═══════════════════════════════════════════════
# 2. 核心函数
# ═══════════════════════════════════════════════

def get_profit_tier(site: str, base_cny: float, freight: float = DOMESTIC_FREIGHT) -> str:
    """
    判断某产品在某站点属于低价品(35%)还是高价品(20%)
    
    Args:
        site: 'TH'|'MY'|'PH'|'SG'|'VN'
        base_cny: 1688拿货价（CNY）
        freight: 国内运费（默认3.5元）
    
    Returns:
        '35%' 或 '20%'
    """
    cny_price = (base_cny + freight) / DENOMS_35[site]
    return '35%' if cny_price <= LOW_PRICE_THRESHOLD_CNY else '20%'


def get_denom(site: str, base_cny: float, freight: float = DOMESTIC_FREIGHT) -> float:
    """根据CNY等价售价返回对应分母"""
    cny_price = (base_cny + freight) / DENOMS_35[site]
    return DENOMS_35[site] if cny_price <= LOW_PRICE_THRESHOLD_CNY else DENOMS_20[site]


def calc_price(site: str, base_cny: float, freight: float = DOMESTIC_FREIGHT) -> float:
    """
    计算产品在某站点的上架售价（当地货币）
    
    Args:
        site: 'TH'|'MY'|'PH'|'SG'|'VN'
        base_cny: 1688拿货价（CNY）
        freight: 国内运费（默认3.5元）
    
    Returns:
        当地货币售价（保留两位小数）
    """
    d = get_denom(site, base_cny, freight)
    rate = COUNTRIES[site]['rate']
    return round(max((base_cny + freight) / d * rate, 1), 2)


def calc_all_sites(base_cny: float, freight: float = DOMESTIC_FREIGHT) -> dict:
    """
    计算产品在所有5个站点的售价
    
    Returns:
        {site: {price, profit%, denom, currency}}
    """
    result = {}
    for site in ['TH', 'MY', 'PH', 'SG', 'VN']:
        d = get_denom(site, base_cny, freight)
        rate = COUNTRIES[site]['rate']
        price = round(max((base_cny + freight) / d * rate, 1), 2)
        profit = '35%' if d == DENOMS_35[site] else '20%'
        # CNY等价售价
        cny_eq = round((base_cny + freight) / d, 2)
        result[site] = {
            'price': price,
            'currency': COUNTRIES[site]['currency'],
            'profit_tier': profit,
            'denom_used': d,
            'cny_equivalent': cny_eq,
            'symbol': COUNTRIES[site]['symbol'],
        }
    return result


def calc_profit_margin(site: str, base_cny: float, freight: float = DOMESTIC_FREIGHT) -> float:
    """
    计算实际纯利百分比
    """
    d = get_denom(site, base_cny, freight)
    rate = COUNTRIES[site]['rate']
    local_price = (base_cny + freight) / d * rate
    cny_price = local_price / rate
    
    # 纯利 = (CNY售价 - 成本 - 运费) / CNY售价
    cost_ratio = 1.0  # 实际扣点+损耗在分母上已体现
    
    if d in (DENOMS_35[site],):
        return 0.35
    return 0.20


def get_threshold_purchase_price(site: str) -> float:
    """
    计算某站的拿货价阈值（低于此值为低价35%，高于此值为高价20%）
    CNY售价 = (P + 3.5) / 分母_35
    当CNY售价 = 30时：P = 30 * 分母_35 - 3.5
    """
    return round(30 * DENOMS_35[site] - DOMESTIC_FREIGHT, 1)


# ═══════════════════════════════════════════════
# 3. 批量计算与展示
# ═══════════════════════════════════════════════

def list_all_prices(products: list):
    """
    批量计算并格式化输出
    
    Args:
        products: [(拿货价, 产品名, 运费?), ...]
    """
    header = f"{'产品名':<20} {'拿货价':<6} {'TH':>10} {'MY':>8} {'PH':>10} {'SG':>6} {'VN':>10}"
    print(header)
    print("─" * len(header))
    for item in products:
        p = item[0]
        name = item[1]
        freight = item[2] if len(item) > 2 else DOMESTIC_FREIGHT
        prices = calc_all_sites(p, freight)
        parts = []
        for s in ['TH', 'MY', 'PH', 'SG', 'VN']:
            pr = prices[s]
            t = '▲' if pr['profit_tier'] == '20%' else ' '
            parts.append(f"{t}{pr['symbol']}{pr['price']:>7.0f}")
        print(f"{name:<20} ¥{p:<4.0f}  " + "  ".join(parts))


# ═══════════════════════════════════════════════
# 4. 命令行测试
# ═══════════════════════════════════════════════

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--thresholds':
        # 显示各站阈值
        print("=== 拿货价阈值（CNY售价=30倒推） ===")
        print(f"{'站点':<4} {'35%纯利':<10} {'20%纯利':<10} {'阈值拿货价':<10}")
        for s in ['TH', 'MY', 'PH', 'SG', 'VN']:
            t = get_threshold_purchase_price(s)
            print(f"{s:<4} {'¥'+str(DENOMS_35[s]):<10} {'¥'+str(DENOMS_20[s]):<10} {'¥'+str(t):<10}")
        sys.exit(0)
    
    # 展示阈值
    print(f"\n⚡ 定价公式 v{__version__} — 混合策略（{__updated__}）")
    print(f"   低价: ≤30CNY → 35%纯利")
    print(f"   高价: >30CNY → 20%纯利")
    print()
    
    for s in ['TH', 'MY', 'PH', 'SG', 'VN']:
        t = get_threshold_purchase_price(s)
        print(f"  {s}: 拿货价≤¥{t} → 35%  |  拿货价>¥{t} → 20%")
    
    # 展示示例产品
    test_products = [
        (1.95, "真空压缩袋"),
        (5.00, "收纳盒"),
        (8.00, "夹缝柜"),
        (14.80, "纸巾袋"),
        (25.93, "帽子收纳"),
        (36.90, "浴室架"),
        (87.10, "窄柜"),
    ]
    
    print("\n=== 示例产品5国售价 ===")
    list_all_prices(test_products)
    
    # 交互模式
    if len(sys.argv) > 1:
        try:
            base = float(sys.argv[1])
            freight = float(sys.argv[2]) if len(sys.argv) > 2 else DOMESTIC_FREIGHT
            print(f"\n💰 批量计算：拿货价¥{base}，运费¥{freight}")
            print(f"{'站点':<4} {'售价(当地)':<12} {'纯利':<6} {'CNY等价':<8} {'分母':<6}")
            for s in ['TH', 'MY', 'PH', 'SG', 'VN']:
                p = calc_all_sites(base, freight)[s]
                print(f"{s:<4} {p['symbol']}{p['price']:<10.0f} {p['profit_tier']:<6} ¥{p['cny_equivalent']:<6.0f} {p['denom_used']:<.2f}")
        except ValueError:
            pass
