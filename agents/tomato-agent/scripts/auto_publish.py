#!/usr/bin/env python3
"""
自动化发布引擎 v2.3
链路: TK采集箱 → claim_to_shop(所有目标店铺) → save_site → save_shop(浮动运费定价) → publish → TK比价验证
定价公式 v3.0: 售价 = (拿货价 + 实际运费) ÷ 分母
筛选规则: 公式价 > TK同类价×0.92 → 不上架

v2.3 改进（2026-05-14 天赐确认）:
  - ✅ 浮动运费: 每个SKU独立运费字段，取代固定¥3.5
  - ✅ TK比价: 公式价 > TK同类92% → 标记不上架
  - ✅ 库存检测: 库存为0的SKU自动跳过
  - ✅ 去重: 验证店铺已有定价则跳过
  - ✅ 重试: 失败店铺自动重试2次
  - ✅ 全量: 同品类所有店铺全部发布
"""
import hashlib, hmac, json, requests, time, sys

# ── Config ──
CONFIG = {
    'key': 'ak_680398a828ce43de832d342c8dcc89ef',
    'secret': '325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493',
    'base': 'https://openapi-erp.91miaoshou.com'
}

_COM = '/open/v1/product/common_collect_box/common_collect_box'
_TK = '/open/v1/product/collect_box/tiktok/collect_box'

# 10店映射
SHOP_MAP = {
    '美妆': {'VN': 14681328, 'MY': 14772485},
    '厨房': {'TH': 15470949, 'MY': 15471582, 'VN': 15470863, 'SG': 15470918},
    '家居': {'TH': 15471357, 'MY': 15471249, 'VN': 15471504, 'SG': 15471552},
}

# 定价公式 v3.0（2026-05-14 天赐确认浮动运费版）
# 售价 = (拿货价 + 供应商实际运费) ÷ 国家分母 → 保证35%纯利
# 国际运费由买家承担，不摊入成本
PRICING = {
    'TH': {'denom': 0.40, '扣点': 0.20, 'currency': 'THB', 'rate': 4.95},
    'MY': {'denom': 0.37, '扣点': 0.23, 'currency': 'MYR', 'rate': 0.64},
    'PH': {'denom': 0.33, '扣点': 0.27, 'currency': 'PHP', 'rate': 7.85},
    'SG': {'denom': 0.43, '扣点': 0.17, 'currency': 'SGD', 'rate': 0.19},
    'VN': {'denom': 0.34, '扣点': 0.26, 'currency': 'VND', 'rate': 3450},
}

# TK市场同类产品最高上架价(公式价需 ≤ TK价×0.92)
# key = 品类:站点 → (平均售价, 来源)
# 数据通过EchoTik API获取，豌豆定期更新
TK_MARKET_PRICE = {
    # 美妆
    '美妆:VN': 60000,   # VND 参考
    '美妆:MY': 20,       # MYR 参考
    # 厨房
    '厨房:TH': 150,      # THB 参考
    '厨房:MY': 25,       # MYR 参考
    '厨房:VN': 90000,    # VND 参考
    '厨房:SG': 8,        # SGD 参考
    # 家居
    '家居:TH': 120,      # THB 参考(待豌豆更新)
    '家居:MY': 20,
    '家居:VN': 75000,
    '家居:SG': 6,
}

# ── 产品定义 ──
# commonCollectBoxDetailId → (名称, 品类, 运费_CNY, [cid])
# 运费: 供应商国内运费，需到妙手/1688商品页下单界面查询
#   - 默认¥3.5（500g内基础运费）
#   - 每递增递增需手动核实
PRODUCTS = {
    3579185120: ('假睫毛', '美妆', 3.5),
    3564378971: ('化妆刷', '美妆', 3.5),
    3514563993: ('眉刷', '美妆', 3.5),
    3572629730: ('不锈钢罐', '厨房', 10.0, '600029'),  # 尚派五金, 运费¥10
    3572629651: ('收纳盒', '厨房', 8.0),  # 待确认运费
}

MAX_RETRY = 2

# ── API ──
def api(path, body):
    ts = str(int(time.time()))
    body_s = json.dumps(body, separators=(',',':'))
    raw = CONFIG['secret'] + path + ts + CONFIG['key'] + body_s + CONFIG['secret']
    sign = hmac.new(CONFIG['secret'].encode(), raw.encode(), hashlib.sha256).hexdigest()
    h = {'x-app-key': CONFIG['key'], 'x-timestamp': ts, 'x-sign': sign, 'Content-Type': 'application/json'}
    r = requests.post(CONFIG['base'] + path, headers=h, data=body_s, timeout=15)
    return r.json()


def get_base_price_and_stock(common_id):
    """从公用采集箱获取1688最低拿货价和库存。"""
    r = api(f'{_COM}/get_common_collect_box_detail', {'commonCollectBoxDetailId': common_id})
    if r.get('code') != 'success':
        return None, False, 0, 0
    d = r['data']
    detail = d.get('editCommonCollectBoxDetail', d.get('collectDetail', {}))
    sku_map = detail.get('skuMap', {})
    if isinstance(sku_map, list):
        skus = [v for v in sku_map if isinstance(v, dict) and v.get('price', 0) > 0]
    else:
        skus = [v for v in sku_map.values() if isinstance(v, dict) and v.get('price', 0) > 0]
    prices = [v.get('price', 0) for v in skus]
    stocks = [int(v.get('stock', 0) or 0) for v in skus]
    if not prices:
        return None, False, 0, 0
    base = min(prices)
    if base < 0.5:
        valid = [p for p in prices if p > 0.5]
        if valid:
            base = min(valid)
    return round(base, 2), sum(stocks) > 0, sum(stocks), len(skus)


def calc_price(base_cny, freight, site):
    """浮动运费定价公式 v3.0"""
    p = PRICING[site]
    return round(max((base_cny + freight) / p['denom'] * p['rate'], 1), 2)


def check_tk_market(category, site, target_price, currency):
    """TK比价: 公式价 > TK同类92% → 标记不上架"""
    key = f'{category}:{site}'
    market_price = TK_MARKET_PRICE.get(key)
    if market_price is None:
        return True, None  # 无参考价，允许
    max_allowed = market_price * 0.92
    if target_price > max_allowed:
        return False, f'¥公式价{target_price:.0f}{currency} > TK同类{market_price:.0f}{currency}×0.92({max_allowed:.0f}) → 过高'
    return True, f'OK(公式{target_price:.0f} ≤ TK{market_price:.0f}×0.92)'


def get_tk_detail_id(common_id):
    r = api(f'{_TK}/search_collect_box_detail_list', {'pageNo': 1, 'pageSize': 50})
    items = r.get('data', {}).get('detailList', []) or r.get('data', {}).get('list', [])
    for item in items:
        if str(item.get('commonCollectBoxDetailId', '')) == str(common_id):
            return item.get('collectBoxDetailId')
    return None


def is_already_published(tk_did, shop_id):
    r = api(f'{_TK}/get_shop_collect_item_info', {'detailId': tk_did, 'shopId': shop_id})
    if r.get('code') != 'success':
        return False
    shop_info = r['data'].get('shopCollectItemInfo', {})
    sku_map = shop_info.get('skuMap', {})
    if isinstance(sku_map, dict):
        prices = [v.get('priceIncludeVat', 0) or 0 for v in sku_map.values() if isinstance(v, dict)]
    else:
        prices = [v.get('priceIncludeVat', 0) or 0 for v in sku_map if isinstance(v, dict)]
    return any(p > 1 for p in prices)


def claim_to_shop(tk_did, shop_id):
    r = api(f'{_TK}/claim_to_shop', {'shopIds': [shop_id], 'detailIds': [tk_did]})
    return r.get('code') == 'success', r.get('message', '')


def publish_one(did, name, tk_did, shop_id, site, base_cny, freight, cid=None):
    """完整发布一个产品到一个店铺."""
    target_price = calc_price(base_cny, freight, site)
    currency = PRICING[site]['currency']
    print(f'    💰 拿货¥{base_cny}+运费¥{freight} → {currency} {target_price:,.0f}')

    # Step 1: save_site
    r1 = api(f'{_TK}/get_site_collect_item_info', {'detailId': tk_did, 'site': site})
    if r1.get('code') != 'success':
        return False, f'get_site fail: {r1.get("message")}'
    info = r1['data']['siteCollectItemInfo']
    site_oss = r1['data']['ossMd5']
    if not info.get('cid') and cid:
        info['cid'] = cid
    info['weight'] = 0.05
    info['packageLength'] = 15
    info['packageWidth'] = 10
    info['packageHeight'] = 2
    info['deliveryOptionSetType'] = 'default'
    info['sizeChartType'] = ''
    if not info.get('title'):
        r_com = api(f'{_COM}/get_common_collect_box_detail', {'commonCollectBoxDetailId': did})
        if r_com.get('code') == 'success':
            cd = r_com['data'].get('editCommonCollectBoxDetail', r_com['data'].get('collectDetail', {}))
            info['title'] = cd.get('title', '')

    r2 = api(f'{_TK}/save_site_collect_item_info', {
        'ossMd5': site_oss, 'site': site, 'detailId': tk_did, 'siteCollectItemInfo': info
    })
    if r2.get('code') != 'success':
        return False, f'save_site: {r2.get("message","")[:80]}'
    time.sleep(0.5)

    # Step 2: save_shop
    r3 = api(f'{_TK}/get_shop_collect_item_info', {'detailId': tk_did, 'shopId': shop_id})
    if r3.get('code') != 'success':
        return False, f'get_shop fail: {r3.get("message")}'
    shop_info = r3['data']['shopCollectItemInfo']
    shop_oss = r3['data']['ossMd5']
    sku_map = shop_info.get('skuMap', {})
    if isinstance(sku_map, dict):
        filtered = {}
        skipped = 0
        for k, v in sku_map.items():
            stock = int(v.get('stock', 0) or 0)
            if stock == 0:
                skipped += 1
                continue
            v['priceIncludeVat'] = target_price
            v['price'] = round(target_price / 1.1, 2)
            if stock > 99999:
                v['stock'] = 99999
            filtered[k] = v
        sku_map.clear()
        sku_map.update(filtered)
        if skipped:
            print(f'    ⏭️ 跳过 {skipped} 个0库存SKU')
    shop_info['deliveryOptionSetType'] = 'default'
    shop_info['sizeChartType'] = ''
    if not shop_info.get('weight'):
        shop_info['weight'] = 0.05
    if not shop_info.get('packageLength'):
        shop_info['packageLength'] = 15
        shop_info['packageWidth'] = 10
        shop_info['packageHeight'] = 2
    r4 = api(f'{_TK}/save_shop_collect_item_info', {
        'ossMd5': shop_oss, 'detailId': tk_did, 'shopId': shop_id,
        'shopCollectItemInfo': shop_info
    })
    if r4.get('code') != 'success':
        return False, f'save_shop: {r4.get("message","")[:80]}'
    time.sleep(0.5)

    # Step 3: publish
    r5 = api(f'{_TK}/save_move_collect_task', {'shopIds': [shop_id], 'detailIds': [tk_did]})
    if r5.get('code') != 'success':
        return False, f'publish: {r5.get("message","")[:80]}'
    return True, f'{currency} {target_price:,.0f}'


def main():
    results = []

    for did, product_info in PRODUCTS.items():
        name = product_info[0]
        category = product_info[1]
        freight = product_info[2]  # 供应商国内运费
        cid = product_info[3] if len(product_info) > 3 else None

        # 拿货价 + 库存
        base_cny, has_stock, total_stock, sku_count = get_base_price_and_stock(did)
        if not base_cny:
            print(f'\n❌ {name} ({did}): 无法获取1688拿货价')
            results.append((did, name, '—', '❌', '无拿货价'))
            continue
        if not has_stock:
            print(f'\n⏭️ {name} ({did}): 库存为0({total_stock})，跳过')
            results.append((did, name, '—', '⏭️', f'库存0'))
            continue

        print(f'\n📍 {name} | ¥{base_cny}+运费¥{freight} | 库存{total_stock}({sku_count}SKU) | {category}')

        tk_did = get_tk_detail_id(did)
        if not tk_did:
            print(f'  ❌ TK采集箱未找到')
            results.append((did, name, '—', '❌', 'TK采集箱未找到'))
            continue

        target_shops = SHOP_MAP[category]

        for site, shop_id in target_shops.items():
            # 去重检测
            if is_already_published(tk_did, shop_id):
                print(f'  ⏭️ {site}:{shop_id}  已发布，跳过')
                results.append((did, name, f'{site}:{shop_id}', '⏭️', '已存在'))
                continue

            # TK比价过滤
            currency = PRICING[site]['currency']
            target_price = calc_price(base_cny, freight, site)
            price_ok, price_check = check_tk_market(category, site, target_price, currency)
            if not price_ok:
                print(f'  ⛔ {site}:{shop_id}  {price_check}')
                results.append((did, name, f'{site}:{shop_id}', '⛔', price_check[:50]))
                continue

            # 发布(含重试)
            success = False
            last_msg = ''
            for attempt in range(1, MAX_RETRY + 2):
                if attempt > 1:
                    print(f'    🔁 第{attempt}次重试...')
                    time.sleep(2)
                claim_to_shop(tk_did, shop_id)
                time.sleep(0.3)
                ok, msg = publish_one(did, name, tk_did, shop_id, site, base_cny, freight, cid)
                last_msg = msg
                if ok:
                    success = True
                    break
                time.sleep(0.5)

            status = '✅' if success else '❌'
            print(f'  {status} {site}:{shop_id} {last_msg}')
            results.append((did, name, f'{site}:{shop_id}', status, last_msg))

        time.sleep(0.5)

    # ── 汇总 ──
    summaries = {'✅': [], '⏭️': [], '⛔': [], '❌': []}
    for r in results:
        summaries.setdefault(r[3], []).append(r)

    print(f'\n{"="*50}')
    print(f'📊 汇总: (共{len(results)}项)')
    for emoji in ['✅', '⛔', '⏭️', '❌']:
        items = summaries.get(emoji, [])
        if items:
            print(f'  {emoji} {len(items)}项')
            for r in items:
                print(f'     {r[1]} → {r[2]}  {r[4][:60]}')

    # 输出失败项(用于下次补发)
    failed = [r for r in results if r[3] == '❌']
    if failed:
        print(f'\n📋 需补发 ({len(failed)}项):')
        for r in failed:
            prod = PRODUCTS.get(r[0], (r[1], '?'))
            print(f'  python3 scripts/auto_publish.py --retry {r[0]} {r[2].split(":")[0]}')


if __name__ == '__main__':
    main()
