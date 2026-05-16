# PRODUCTS dict draft - 2026-05-14
# Source: pea-agent/output/selection_analysis_2026-05-14.md
# Format: common_id: ('product_name', 'category', freight_CNY, ['cid'])
# NOTE: This is a DRAFT - requires 天赐 approval before publishing

PRODUCTS = {
    # 🪞 美妆工具 (Bloom Lane: VN+MY)
    1001: ('Waterdrop Beauty Blender 4pcs', '美妆', 3.5, ['600001']),
    1002: ('Air Cushion Puff Black Pineapple', '美妆', 3.5, ['600002']),
    1003: ('Air Cushion Puff Cotton Candy', '美妆', 3.5, ['600003']),
    1004: ('Silicone Puff 2pcs', '美妆', 3.5, ['600004']),
    1005: ('Beauty Blender 12pcs', '美妆', 3.5, ['600005']),
    1006: ('Triangle Puff 50pcs', '美妆', 3.5, ['600006']),
    1007: ('Cushion Puff Set 3 Types', '美妆', 3.5, ['600007']),
    1008: ('Diamond Beauty Blender 4 Colors', '美妆', 3.5, ['600008']),
    1009: ('Beauty Blender Cleaner 100ml', '美妆', 3.5, ['600009']),
    1010: ('Brush Cleaner Box + Silicone Pad', '美妆', 3.5, ['600010']),
    1011: ('Setting Spray Bottle 50ml', '美妆', 3.5, ['600011']),
    1012: ('Brush Cleaning Spray 100ml', '美妆', 3.5, ['600012']),
    1013: ('Blush Brush Angled', '美妆', 3.5, ['600013']),
    1014: ('Highlighter Brush Tapered', '美妆', 3.5, ['600014']),
}

# Pricing (from selection_analysis, formula v3.0)
PRICING = {
    'TH': {'denom': 0.40, 'currency': 'THB', 'rate': 4.95},
    'MY': {'denom': 0.37, 'currency': 'MYR', 'rate': 0.64},
    'VN': {'denom': 0.34, 'currency': 'VND', 'rate': 3450},
    'SG': {'denom': 0.43, 'currency': 'SGD', 'rate': 0.19},
    'PH': {'denom': 0.34, 'currency': 'PHP', 'rate': 7.85},
}

# Shop mapping
SHOP_MAP = {
    '美妆': {'VN': 14681328, 'MY': 14772485},
    '厨房': {'TH': 15470949, 'MY': 15471582, 'VN': 15470863, 'SG': 15470918},
    '家居': {'TH': 15471357, 'MY': 15471249, 'VN': 15471504, 'SG': 15471552},
}

print(f"✅ PRODUCTS draft ready: {len(PRODUCTS)} products")
print(f"✅ Pricing configured for {len(PRICING)} countries")
print(f"✅ Shop mapping: {sum(len(v) for v in SHOP_MAP.values())} shops")
