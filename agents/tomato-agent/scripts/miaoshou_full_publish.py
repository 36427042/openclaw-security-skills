#!/usr/bin/env python3
"""
妙手全量发布引擎 v2.0
基于 生菜TOP20文案 + 豌豆选品数据 → 直接创建妙手采集箱 → 发布到TK
"""
import hashlib, hmac, json, requests, time, sys, re
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

# 成本估算（基于品类）
COST_ESTIMATES = {
    '美妆': {'cost': 5.0, 'freight': 3.5, 'weight': 0.2},
    '家居': {'cost': 12.0, 'freight': 3.5, 'weight': 0.5},
    '厨房': {'cost': 15.0, 'freight': 3.5, 'weight': 0.8},
}

def api(path, body, retry=3):
    for attempt in range(retry):
        try:
            ts = str(int(time.time()))
            body_s = json.dumps(body, separators=(',',':'))
            raw = CONFIG['secret'] + path + ts + CONFIG['key'] + body_s + CONFIG['secret']
            sign = hmac.new(CONFIG['secret'].encode(), raw.encode(), hashlib.sha256).hexdigest()
            h = {'x-app-key': CONFIG['key'], 'x-timestamp': ts, 'x-sign': sign, 'Content-Type': 'application/json'}
            r = requests.post(CONFIG['base'] + path, headers=h, data=body_s, timeout=30)
            result = r.json()
            if result.get('result') == 'success':
                return result
            elif result.get('code') == 'rateLimitExceeded':
                print(f"  ⏳ API限流，等待{2**attempt}秒...")
                time.sleep(2**attempt)
                continue
            else:
                return result
        except Exception as e:
            print(f"  ⚠️ 尝试{attempt+1}失败: {e}")
            time.sleep(2**attempt)
    return {'result': 'fail', 'code': 'maxRetriesExceeded'}

def create_product(title, category, cost_cny, freight_cny, descriptions, images=None):
    """直接创建妙手采集箱产品"""
    base_price = cost_cny + freight_cny
    prices = {cc: round(base_price / DENOM[cc], 2) for cc in DENOM}
    
    payload = {
        'title': title[:120],
        'price': round(prices['SG'], 2),
        'stock': 999,
        'imgUrls': images or [],
        'weight': COST_ESTIMATES[category]['weight'],
        'notesText': descriptions.get('SG', title),
        'sourceAttrs': [
            {'name': 'Category', 'value': category},
            {'name': 'Origin', 'value': 'China'},
        ],
    }
    
    result = api('/open/v1/product/common_collect_box/common_collect_box/add_common_collect_box_detail', payload)
    if result.get('result') == 'success':
        common_id = result['data']['commonCollectBoxDetailId']
        print(f"✅ {title[:40]}... → common_id={common_id}")
        return common_id
    else:
        print(f"❌ {title[:40]}... → {result}")
        return None

def parse_copywriting(filepath, category):
    """解析生菜文案文件"""
    products = []
    content = Path(filepath).read_text()
    
    chunks = re.split(r'\n## Product #(\d+): ', content)[1:]
    
    for i in range(0, len(chunks), 2):
        if i+1 >= len(chunks):
            break
        num = chunks[i]
        chunk = chunks[i+1]
        
        name = chunk.split('\n')[0].strip()
        
        descs = {}
        for line in chunk.split('\n'):
            if '🇹🇭 TH:' in line:
                descs['TH'] = line.split('🇹🇭 TH:')[1].strip()
            elif '🇲🇾 MY:' in line:
                descs['MY'] = line.split('🇲🇾 MY:')[1].strip()
            elif '🇻🇳 VN:' in line:
                descs['VN'] = line.split('🇻🇳 VN:')[1].strip()
            elif '🇸🇬 SG:' in line:
                descs['SG'] = line.split('🇸🇬 SG:')[1].strip()
            elif '🇵🇭 PH:' in line:
                descs['PH'] = line.split('🇵🇭 PH:')[1].strip()
        
        products.append({'num': int(num), 'name': name, 'descs': descs})
    
    return products

def claim_to_shop(common_ids, shop_id):
    """认领到店铺"""
    result = api('/open/v1/product/collect_box/tiktok/collect_box/claim_to_shop', {
        'commonCollectBoxDetailIds': common_ids,
        'shopId': shop_id,
    })
    return result

def save_shop(common_id, descriptions, category):
    """保存店铺产品信息"""
    base_price = COST_ESTIMATES[category]['cost'] + COST_ESTIMATES[category]['freight']
    prices = {cc: round(base_price / DENOM[cc], 2) for cc in DENOM}
    
    result = api('/open/v1/product/collect_box/tiktok/collect_box/save_shop_collect_item_info', {
        'commonCollectBoxDetailId': common_id,
        'title': descriptions.get('SG', ''),
        'description': descriptions.get('SG', ''),
        'price': prices['SG'],
        'stock': 999,
    })
    return result

def publish(common_id):
    """发布产品"""
    result = api('/open/v1/product/collect_box/tiktok/collect_box/save_move_collect_task', {
        'commonCollectBoxDetailIds': [common_id],
    })
    return result

def main():
    print("🥔 妙手全量发布引擎 v2.0")
    print("=" * 60)
    
    all_products = []
    
    # 解析3品类文案
    files = [
        ('美妆', '/Users/a1234/.openclaw/workspace/agents/lettuce-agent/output/top20_copywriting_2026-05-14.md'),
        ('家居', '/Users/a1234/.openclaw/workspace/agents/lettuce-agent/output/home_top20_copywriting_2026-05-14.md'),
        ('厨房', '/Users/a1234/.openclaw/workspace/agents/lettuce-agent/output/kitchen_top20_copywriting_2026-05-14.md'),
    ]
    
    for category, filepath in files:
        products = parse_copywriting(filepath, category)
        all_products.extend([(category, p) for p in products])
        print(f"📝 {category}: {len(products)} 个产品")
    
    print(f"\n🚀 开始创建 {len(all_products)} 个产品...")
    
    created_ids = []
    for category, prod in all_products:
        cost_info = COST_ESTIMATES[category]
        common_id = create_product(
            title=prod['name'],
            category=category,
            cost_cny=cost_info['cost'],
            freight_cny=cost_info['freight'],
            descriptions=prod['descs'],
        )
        if common_id:
            created_ids.append((category, common_id, prod['name']))
        time.sleep(0.5)  # 避免API限流
    
    print(f"\n✅ 成功创建 {len(created_ids)} 个产品")
    
    # 按品类分组发布
    for category in ['美妆', '家居', '厨房']:
        category_ids = [(c, cid, n) for c, cid, n in created_ids if c == category]
        if not category_ids:
            continue
            
        print(f"\n📦 {category} 发布流程:")
        shops = SHOP_MAP[category]
        
        for shop_name, shop_id in shops.items():
            print(f"  🏪 {shop_name} (ID: {shop_id})")
            
            # 认领
            ids = [cid for _, cid, _ in category_ids]
            claim_result = claim_to_shop(ids, shop_id)
            print(f"    认领: {claim_result.get('result', 'unknown')}")
            
            # 保存并发布
            for _, cid, name in category_ids:
                save_result = save_shop(cid, {}, category)
                publish_result = publish(cid)
                print(f"    {name[:30]}: save={save_result.get('result','?')}, publish={publish_result.get('result','?')}")
            
            time.sleep(1)
    
    print("\n" + "=" * 60)
    print("🎉 发布完成！")

if __name__ == '__main__':
    main()
