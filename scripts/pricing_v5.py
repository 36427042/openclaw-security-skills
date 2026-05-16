#!/usr/bin/env python3
"""
定价公式 v5.0 — 成本加法公式
天赐 2026-05-16 04:20 固化版

规则（天赐口述）：
  - 售价 = 1688拿货价 + ¥7硬成本(国内运费¥3.5+包装¥2+平台操作费¥1.5) + 利润¥15-25
  - 利润分三档：低价品(成本≤¥10)→¥15 / 中价品(¥10-30)→¥20 / 高价品(>¥30)→¥25
  - 最终售价需满足：公式价 ≤ TK同类商品实际售价×0.92（低于10%=恶意竞争下架）
  - 家居/厨房产品不跟TK比价，直接上架

使用方式：
  from pricing_v5 import calc_price, get_profit, list_all_prices

版本演进：
  v1.0  — (P+3.5)/分母→35%纯利
  v4.0  — 混合定价(≤30→35%, >30→20%)
  v5.0  — 成本加法(成本+7+利润15-25)
"""

__version__ = "5.0"
__updated__ = "2026-05-16 04:20"

# ═══════════════════════════════════════════════
# 1. 核心参数
# ═══════════════════════════════════════════════

HARD_COST = 7.0  # 硬成本(CNY): 国内运费¥3.5 + 包装¥2 + 平台操作费¥1.5
DOMESTIC_FREIGHT = 3.5  # 国内运费(保留兼容)

# 利润分档（按总成本）
PROFIT_TIERS = [
    (10.0, 15.0),   # 成本≤¥10 → 利润¥15
    (30.0, 20.0),   # 成本≤¥30 → 利润¥20
    (float('inf'), 25.0),  # 成本>¥30 → 利润¥25
]

# TK比价规则
TK_COMPETITOR_DISCOUNT = 0.92  # 售价比TK同类低8%
TK_MIN_RATIO = 0.90  # 不得低于TK价90%（恶意竞争）
TK_MAX_RATIO = 1.10  # 不得高于TK价110%

# 各国货币信息
COUNTRIES = {
    'TH': {'name': '泰国',  'currency': 'THB', 'rate': 4.95,   'symbol': '฿'},
    'MY': {'name': '马来西亚', 'currency': 'MYR', 'rate': 0.64,   'symbol': 'RM'},
    'PH': {'name': '菲律宾', 'currency': 'PHP', 'rate': 7.85,   'symbol': '₱'},
    'SG': {'name': '新加坡', 'currency': 'SGD', 'rate': 0.19,   'symbol': 'S$'},
    'VN': {'name': '越南',   'currency': 'VND', 'rate': 3450,   'symbol': '₫'},
}

# 不需比价的品类（直接上架）
NO_COMPARE_CATEGORIES = ['家居日用品', '厨房小件']


# ═══════════════════════════════════════════════
# 2. 核心函数
# ═══════════════════════════════════════════════

def get_profit(base_cny: float) -> float:
    """根据1688拿货价+硬成本返回应加利润"""
    total_cost = base_cny + HARD_COST
    for threshold, profit in PROFIT_TIERS:
        if total_cost <= threshold:
            return profit
    return PROFIT_TIERS[-1][1]  # 兜底


def get_profit_tier(base_cny: float) -> str:
    """返回利润档位名称"""
    total_cost = base_cny + HARD_COST
    if total_cost <= 10:
        return '低档(¥15)'
    elif total_cost <= 30:
        return '中档(¥20)'
    return '高档(¥25)'


def calc_price(site: str, base_cny: float) -> float:
    """
    计算产品在某站点的上架售价（当地货币）
    公式: CNY售价 = 拿货价 + ¥7 + 利润 → 换算当地货币
    
    Args:
        site: 'TH'|'MY'|'PH'|'SG'|'VN'
        base_cny: 1688拿货价（CNY）
    
    Returns:
        当地货币售价（保留两位小数）
    """
    profit = get_profit(base_cny)
    cny_price = base_cny + HARD_COST + profit
    rate = COUNTRIES[site]['rate']
    return round(cny_price * rate, 2)


def calc_cny_price(base_cny: float) -> float:
    """计算CNY售价（不含汇率换算）"""
    profit = get_profit(base_cny)
    return round(base_cny + HARD_COST + profit, 2)


def calc_profit_cny(base_cny: float) -> float:
    """计算单件纯利(CNY)"""
    return get_profit(base_cny)


def calc_profit_margin(base_cny: float) -> float:
    """计算纯利率"""
    cny_price = calc_cny_price(base_cny)
    profit = get_profit(base_cny)
    return round(profit / cny_price * 100, 1) if cny_price > 0 else 0


def calc_all_sites(base_cny: float) -> dict:
    """
    计算产品在所有5个站点的售价
    
    Returns:
        {site: {price, currency, symbol, profit, profit_tier, cny_price}}
    """
    cny_price = calc_cny_price(base_cny)
    profit = get_profit(base_cny)
    tier = get_profit_tier(base_cny)
    
    result = {}
    for site in COUNTRIES:
        rate = COUNTRIES[site]['rate']
        price = round(cny_price * rate, 2)
        result[site] = {
            'price': price,
            'currency': COUNTRIES[site]['currency'],
            'symbol': COUNTRIES[site]['symbol'],
            'profit': profit,
            'profit_tier': tier,
            'cny_price': cny_price,
        }
    return result


def check_tk_competitor(formula_price_cny: float, tk_price_cny: float) -> dict:
    """
    检查公式价是否在TK比价允许区间内
    
    Args:
        formula_price_cny: 公式计算出的CNY售价
        tk_price_cny: TK同类商品实际CNY售价
    
    Returns:
        {pass: bool, ratio, status, message}
    """
    if tk_price_cny <= 0:
        return {'pass': True, 'ratio': None, 'status': 'no_tk_data', 'message': '无TK比价数据，用公式价直上'}
    
    ratio = formula_price_cny / tk_price_cny
    
    if ratio < TK_MIN_RATIO:
        return {'pass': False, 'ratio': ratio, 'status': 'too_low',
                'message': f'公式价¥{formula_price_cny:.1f}/TK价¥{tk_price_cny:.1f}={ratio:.0%}，低于90%恶意竞争红线'}
    elif ratio > TK_MAX_RATIO:
        return {'pass': False, 'ratio': ratio, 'status': 'too_high',
                'message': f'公式价¥{formula_price_cny:.1f}/TK价¥{tk_price_cny:.1f}={ratio:.0%}，高于110%无竞争力'}
    elif ratio <= TK_COMPETITOR_DISCOUNT:
        return {'pass': True, 'ratio': ratio, 'status': 'competitive',
                'message': f'公式价¥{formula_price_cny:.1f}比TK低{(1-ratio):.0%}，竞争力✅'}
    else:
        return {'pass': True, 'ratio': ratio, 'status': 'acceptable',
                'message': f'公式价¥{formula_price_cny:.1f}在±10%区间内，可接受'}


def should_compare_tk(category: str) -> bool:
    """判断该品类是否需要跟TK比价"""
    return category not in NO_COMPARE_CATEGORIES


# ═══════════════════════════════════════════════
# 3. 批量计算与展示
# ═══════════════════════════════════════════════

def list_all_prices(products: list):
    """
    批量计算并格式化输出
    
    Args:
        products: [(拿货价, 产品名, 品类?), ...]
    """
    header = f"{'产品名':<20} {'拿货价':<6} {'成本':<6} {'利润':<6} {'CNY价':<7} {'TH':>10} {'MY':>8} {'PH':>10} {'SG':>6} {'VN':>10}"
    print(header)
    print("─" * len(header))
    for item in products:
        p = item[0]
        name = item[1]
        category = item[2] if len(item) > 2 else '通用'
        cny = calc_cny_price(p)
        profit = get_profit(p)
        prices = calc_all_sites(p)
        parts = []
        for s in ['TH', 'MY', 'PH', 'SG', 'VN']:
            pr = prices[s]
            parts.append(f"{pr['symbol']}{pr['price']:>7.0f}")
        nc = '*' if not should_compare_tk(category) else ' '
        print(f"{name:<20} ¥{p:<4.0f}  ¥{p+HARD_COST:<4.0f}  ¥{profit:<4.0f}  ¥{cny:<5.0f}  " + "  ".join(parts) + f"  {nc}")


# ═══════════════════════════════════════════════
# 4. 命令行测试 / 模块导入
# ═══════════════════════════════════════════════

if __name__ == '__main__':
    import sys
    
    print(f"\n💰 定价公式 v{__version__} — 成本加法策略（{__updated__}）")
    print(f"   公式: 售价 = 1688拿货价 + ¥{HARD_COST}(硬成本) + ¥15~25(利润)")
    print(f"   比价: 售价 ≤ TK价×{TK_COMPETITOR_DISCOUNT}，必须在±10%区间内")
    print(f"   免比价: {', '.join(NO_COMPARE_CATEGORIES)}")
    print()
    
    # 利润档位说明
    print("=== 利润档位 ===")
    print(f"  成本≤¥10 → 利润¥15（低档）")
    print(f"  成本¥10-30 → 利润¥20（中档）")
    print(f"  成本>¥30 → 利润¥25（高档）")
    print()
    
    # 示例产品
    test_products = [
        (1.95, "真空压缩袋", "家居日用品"),
        (5.00, "收纳盒", "家居日用品"),
        (8.00, "夹缝柜", "家居日用品"),
        (5.80, "保鲜盒316", "厨房小件"),
        (7.50, "不锈钢切丝器", "厨房小件"),
        (14.80, "纸巾袋", "家居日用品"),
        (25.93, "帽子收纳", "家居日用品"),
        (36.90, "浴室架", "家居日用品"),
        (87.10, "窄柜", "家居日用品"),
        (3.50, "美妆蛋套装", "美妆工具"),
        (15.00, "化妆刷12件套", "美妆工具"),
    ]
    
    print("=== 示例产品5国售价 ===")
    list_all_prices(test_products)
    
    # 命令行模式
    if len(sys.argv) > 1:
        try:
            base = float(sys.argv[1])
            print(f"\n💰 单产品计算：拿货价¥{base}")
            print(f"   成本 = ¥{base} + ¥{HARD_COST} = ¥{base+HARD_COST:.1f}")
            print(f"   利润 = ¥{get_profit(base)}（{get_profit_tier(base)}）")
            print(f"   CNY售价 = ¥{calc_cny_price(base)}")
            print(f"   纯利率 = {calc_profit_margin(base)}%")
            print(f"\n{'站点':<4} {'售价(当地)':<12} {'CNY等价':<8} {'利润':<6}")
            for s in COUNTRIES:
                p = calc_all_sites(base)[s]
                print(f"{s:<4} {p['symbol']}{p['price']:<10.0f} ¥{p['cny_price']:<6.0f} ¥{p['profit']:<4.0f}")
        except ValueError:
            print(f"用法: python3 pricing_v5.py [拿货价]")
    
    print()
