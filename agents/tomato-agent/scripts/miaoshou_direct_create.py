#!/usr/bin/env python3
"""
妙手直接创建产品引擎 — 绕过1688链接需求
基于 生菜TOP20文案 + 豌豆选品数据 → 直接创建妙手采集箱 → 发布到TK
"""
import hashlib, hmac, json, requests, time, sys
from pathlib import Path

CONFIG = {
    'key': 'ak_680398a828ce43de832d342c8dcc89ef',
    'secret': '325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493',
    'base': 'https://openapi-erp.91miaoshou.com'
}

# 5国定价分母
DENOM = {'TH': 0.40, 'MY': 0.37, 'VN': 0.34, 'SG': 0.43, 'PH': 0.33}
RATE = {'TH': 4.95, 'MY': 0.64, 'VN': 3450, 'SG': 0.19, 'PH': 7.85}

# 10店映射
SHOP_MAP = {
    '美妆': {'VN': 14681328, 'MY': 14772485},
    '厨房': {'TH': 15470949, 'MY': 15471582, 'VN': 15470863, 'SG': 15470918},
    '家居': {'TH': 15471357, 'MY': 15471249, 'VN': 15471504, 'SG': 15471552},
}

def api(path, body):
    ts = str(int(time.time()))
    body_s = json.dumps(body, separators=(',',':'))
    raw = CONFIG['secret'] + path + ts + CONFIG['key'] + body_s + CONFIG['secret']
    sign = hmac.new(CONFIG['secret'].encode(), raw.encode(), hashlib.sha256).hexdigest()
    h = {'x-app-key': CONFIG['key'], 'x-timestamp': ts, 'x-sign': sign, 'Content-Type': 'application/json'}
    r = requests.post(CONFIG['base'] + path, headers=h, data=body_s, timeout=30)
    return r.json()

def create_product(title, category, cost_cny, freight_cny, descriptions, images=None):
    """
    直接创建妙手采集箱产品
    descriptions: dict of country_code -> description text
    """
    # 计算5国售价
    base_price = cost_cny + freight_cny
    prices = {cc: round(base_price / DENOM[cc], 2) for cc in DENOM}
    
    payload = {
        'title': title[:120],  # 妙手标题上限
        'price': round(prices['SG'], 2),  # 基准价用SG
        'stock': 999,
        'imgUrls': images or [],
        'weight': 0.3,  # 默认300g
        'notesText': descriptions.get('SG', title),
        'sourceAttrs': [
            {'name': 'Category', 'value': category},
            {'name': 'Origin', 'value': 'China'},
        ],
    }
    
    result = api('/open/v1/product/common_collect_box/common_collect_box/add_common_collect_box_detail', payload)
    if result.get('result') == 'success':
        common_id = result['data']['commonCollectBoxDetailId']
        print(f"✅ 创建成功: {title[:40]}... → common_id={common_id}")
        return common_id
    else:
        print(f"❌ 创建失败: {title[:40]}... → {result}")
        return None

def parse_copywriting(filepath):
    """解析生菜文案文件，提取产品数据"""
    products = []
    content = Path(filepath).read_text()
    
    # 按 Product #N 分割
    import re
    chunks = re.split(r'\n## Product #(\d+): ', content)[1:]  # 跳过标题
    
    for i in range(0, len(chunks), 2):
        if i+1 >= len(chunks):
            break
        num = chunks[i]
        chunk = chunks[i+1]
        
        # 提取产品名（第一行）
        name = chunk.split('\n')[0].strip()
        
        # 提取各国描述
        descs = {}
        for line in chunk.split('\n'):
            if '🇹🇭 TH:' in line:
                descs['TH'] = line.split('🇹🇭 TH:')[1].strip()
            elif '🇲🇾 MY:' in line:
                descs['MY'] = line.split('🇲🇾 MY:')[1].strip()
            elif '🇻 VN:' in line:
                descs['VN'] = line.split('🇻🇳 VN:')[1].strip()
            elif '🇸🇬 SG:' in line:
                descs['SG'] = line.split('🇸🇬 SG:')[1].strip()
            elif '🇵🇭 PH:' in line:
                descs['PH'] = line.split('🇵🇭 PH:')[1].strip()
        
        products.append({'num': int(num), 'name': name, 'descs': descs})
    
    return products

def main():
    print("🥔 妙手直接发布引擎 v1.0")
    print("=" * 50)
    
    # 解析美妆TOP20文案
    beauty_products = parse_copywriting('/Users/a1234/.openclaw/workspace/agents/lettuce-agent/output/top20_copywriting_2026-05-14.md')
    print(f"📝 解析美妆文案: {len(beauty_products)} 个产品")
    
    # 演示：创建前3个产品
    for prod in beauty_products[:3]:
        # 估算成本（美妆工具约¥3-8）
        cost = 5.0
        freight = 3.5
        common_id = create_product(
            title=prod['name'],
            category='美妆工具',
            cost_cny=cost,
            freight_cny=freight,
            descriptions=prod['descs'],
            images=[]  # 暂时无图，后续可加
        )
        if common_id:
            print(f"   → 下一步：claim_to_shop + save_shop + publish")
    
    print("\n" + "=" * 50)
    print("演示完成。全量60产品发布需确认成本数据。")

if __name__ == '__main__':
    main()
