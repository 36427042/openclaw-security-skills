#!/usr/bin/env python3
"""
豌豆数据·妙手上架63产品脚本
链路: add_common_collect_box_detail → claimed → claim_to_shop → save_site → save_shop → save_move_collect_task

依据:
- WORKFLOW_LOCK.md 第5条 (妙手上架脚本锁)
- WORKFLOW_LOCK.md 第7条 (10店品类映射)
- 数据源: /tmp/publish_final.json (63个产品,含title/description/shop_id/country/cat)
"""
import hashlib, hmac, json, requests, time, sys, os, re
from pathlib import Path

CONFIG = {
    'key': 'ak_680398a828ce43de832d342c8dcc89ef',
    'secret': '325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493',
    'base': 'https://openapi-erp.91miaoshou.com'
}

# ========== 品类→中文映射 ==========
CAT_CN = {
    'beauty': '美妆',
    'kitchen': '厨房',
    'home': '家居',
}

# ========== 10店映射 (WORKFLOW_LOCK.md 第7条) ==========
SHOP_MAP = {
    'beauty': {
        'MY': {'shop_id': 14772485, 'brand': 'Bloom Lane'},
    },
    'kitchen': {
        'TH': {'shop_id': 15470949, 'brand': 'Smart Kitchen Life'},
        'MY': {'shop_id': 15471582, 'brand': 'Smart Kitchen Life'},
        'VN': {'shop_id': 15470863, 'brand': 'Smart Kitchen Life'},
        'SG': {'shop_id': 15470918, 'brand': 'Smart Kitchen Life'},
    },
    'home': {
        'TH': {'shop_id': 15471357, 'brand': 'Daily Home'},
        'MY': {'shop_id': 15471249, 'brand': 'Daily Home'},
        'VN': {'shop_id': 15471504, 'brand': 'Daily Home'},
        'SG': {'shop_id': 15471552, 'brand': 'Daily Home'},
    },
}

SITE_NAMES = {
    'TH': 'Thailand', 'MY': 'Malaysia', 'VN': 'Vietnam',
    'SG': 'Singapore', 'PH': 'Philippines', 'ID': 'Indonesia',
}

# ========== API工具 ==========

def api(path, body, retry=3, delay=1.0):
    """安全API调用,重试+限流"""
    for attempt in range(retry):
        try:
            ts = str(int(time.time()))
            body_s = json.dumps(body, separators=(',',':'), ensure_ascii=False)
            raw = CONFIG['secret'] + path + ts + CONFIG['key'] + body_s + CONFIG['secret']
            sign = hmac.new(CONFIG['secret'].encode(), raw.encode(), hashlib.sha256).hexdigest()
            headers = {
                'x-app-key': CONFIG['key'],
                'x-timestamp': ts,
                'x-sign': sign,
                'Content-Type': 'application/json'
            }
            r = requests.post(CONFIG['base'] + path, headers=headers, data=body_s.encode('utf-8'), timeout=30)
            result = r.json()

            if result.get('code') == 'rateLimitExceeded' or result.get('result') == 'rateLimitExceeded':
                wait = min(2 ** attempt * 2, 15)
                print("    ⏳ API限流,等待{}秒...".format(wait))
                time.sleep(wait)
                continue

            return result
        except Exception as e:
            if attempt < retry - 1:
                print("    ⚠️ API调用失败(尝试{}): {},重试中...".format(attempt+1, e))
                time.sleep(2 ** attempt)
            else:
                return {'result': 'fail', 'error': str(e)}


# ========== 步骤1: 创建采集箱产品 ==========

def create_common_product(prod, product_index, total):
    """
    创建产品到妙手公共采集箱
    返回: commonCollectBoxDetailId 或 None
    """
    title = prod['title'][:120] if prod['title'] else prod['name'][:120]
    desc = prod['desc']

    payload = {
        'title': title,
        'price': 9.99,
        'stock': 999,
        'weight': 0.2,
        'notesText': desc[:500] if desc else title,
        'sourceAttrs': [
            {'name': 'Category', 'value': CAT_CN.get(prod['cat'], prod['cat']).title()},
            {'name': 'Origin', 'value': 'China'},
        ],
        'imgUrls': [],
    }

    result = api('/open/v1/product/common_collect_box/common_collect_box/add_common_collect_box_detail', payload)

    if result.get('result') == 'success' or result.get('code') == 'success':
        common_id = result.get('data', {}).get('commonCollectBoxDetailId')
        if not common_id:
            common_id = result.get('data', {}).get('id')
        if common_id:
            return int(common_id)

    return None


# ========== 步骤2: 认领到TK平台 ==========

def claim_to_platform(common_ids):
    """将公共采集箱产品认领到TikTok平台采集箱"""
    items = [{'detailId': cid, 'platform': 'tiktok', 'serialNumber': 1} for cid in common_ids]

    batch_size = 50
    all_tk_ids = {}

    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        result = api('/open/v1/product/common_collect_box/common_collect_box/claimed', {
            'detailSerialNumberPlatformList': batch
        })

        if result.get('result') == 'success' or result.get('code') == 'success':
            id_map = result.get('data', {}).get('platformCollectBoxDetailIdMap', {})
            if id_map and 'tiktok' in id_map:
                tk_info = id_map['tiktok']
                for orig_id, tk_data in tk_info.items():
                    try:
                        cid = int(orig_id)
                    except:
                        continue
                    if isinstance(tk_data, dict):
                        tid = tk_data.get('collectBoxDetailId', tk_data.get('detailId', ''))
                    else:
                        tid = str(tk_data)
                    all_tk_ids[cid] = tid

        time.sleep(0.5)

    return all_tk_ids


# ========== 步骤3: 认领到店铺 ==========

def claim_to_shop_batch(tk_ids_list, shop_id):
    """认领到指定店铺"""
    result = api('/open/v1/product/collect_box/tiktok/collect_box/claim_to_shop', {
        'shopIds': [shop_id],
        'detailIds': tk_ids_list
    })
    return result.get('code') == 'success', result


# ========== 步骤4: 从TK采集箱查找detail ID ==========

def search_tk_collect_box_batch(common_ids):
    """批量查找TK detail ID"""
    result = {}

    for status in ['notPublished', 'all']:
        page = 1
        while page <= 5:
            r = api('/open/v1/product/collect_box/tiktok/collect_box/search_collect_box_detail_list', {
                'pageNo': page,
                'pageSize': 500,
                'filter': {'status': status}
            })
            if r.get('code') != 'success':
                break

            items = r.get('data', {}).get('detailList', []) or r.get('data', {}).get('list', [])
            if not items:
                break

            for item in items:
                cid = item.get('commonCollectBoxDetailId')
                if cid and cid in common_ids and cid not in result:
                    tk_id = item.get('collectBoxDetailId')
                    if tk_id:
                        result[cid] = tk_id

            page += 1
            time.sleep(0.3)

    return result


# ========== 步骤5: 保存站点模式 + 店铺模式 + 发布 ==========

def process_save_and_publish(tk_id, shop_id, site, title, desc):
    """
    完整上架流程: save_site → save_shop → publish
    返回: (success, message)
    """
    tk_id_int = int(tk_id)

    # --- 5a: 获取站点详情 ---
    r_site = api('/open/v1/product/collect_box/tiktok/collect_box/get_site_collect_item_info', {
        'detailId': tk_id_int, 'site': site
    })
    if r_site.get('code') != 'success':
        return False, "get_site失败: {}".format(r_site.get('message', '')[:60])

    site_info = r_site['data']['siteCollectItemInfo']
    site_oss = r_site['data']['ossMd5']

    site_info['title'] = site_info.get('title', '') or title
    site_info['notes'] = site_info.get('notes', '') or desc
    site_info['weight'] = site_info.get('weight', 0.2)
    site_info['packageLength'] = site_info.get('packageLength', 15)
    site_info['packageWidth'] = site_info.get('packageWidth', 10)
    site_info['packageHeight'] = site_info.get('packageHeight', 5)
    site_info['deliveryOptionSetType'] = site_info.get('deliveryOptionSetType', 'default')
    site_info['sizeChartType'] = site_info.get('sizeChartType', '')
    site_info['isCodOpen'] = site_info.get('isCodOpen', '1')

    r_save_site = api('/open/v1/product/collect_box/tiktok/collect_box/save_site_collect_item_info', {
        'ossMd5': site_oss,
        'site': site,
        'detailId': tk_id_int,
        'siteCollectItemInfo': site_info
    })
    if r_save_site.get('code') != 'success':
        return False, "save_site: {}".format(r_save_site.get('message', '')[:60])

    time.sleep(0.5)

    # --- 5b: 获取店铺详情 ---
    r_shop = api('/open/v1/product/collect_box/tiktok/collect_box/get_shop_collect_item_info', {
        'detailId': tk_id_int, 'shopId': shop_id
    })
    if r_shop.get('code') != 'success':
        return False, "get_shop失败: {}".format(r_shop.get('message', '')[:60])

    shop_info = r_shop['data']['shopCollectItemInfo']
    shop_oss = r_shop['data']['ossMd5']

    sku_map = shop_info.get('skuMap', {})
    if isinstance(sku_map, dict):
        for k, v in sku_map.items():
            if isinstance(v, dict):
                v['price'] = v.get('price', 9.99)
                v['priceIncludeVat'] = v.get('priceIncludeVat', 9.99)
                v['stock'] = max(int(v.get('stock', 0) or 0), 999)
    shop_info['deliveryOptionSetType'] = shop_info.get('deliveryOptionSetType', 'default')
    shop_info['sizeChartType'] = shop_info.get('sizeChartType', '')
    shop_info['title'] = shop_info.get('title', '') or title

    if not shop_info.get('weight'):
        shop_info['weight'] = 0.2
    if not shop_info.get('packageLength'):
        shop_info['packageLength'] = 15
        shop_info['packageWidth'] = 10
        shop_info['packageHeight'] = 5

    r_save_shop = api('/open/v1/product/collect_box/tiktok/collect_box/save_shop_collect_item_info', {
        'ossMd5': shop_oss,
        'detailId': tk_id_int,
        'shopId': shop_id,
        'shopCollectItemInfo': shop_info
    })
    if r_save_shop.get('code') != 'success':
        return False, "save_shop: {}".format(r_save_shop.get('message', '')[:60])

    time.sleep(0.5)

    # --- 5c: 发布 ---
    r_pub = api('/open/v1/product/collect_box/tiktok/collect_box/save_move_collect_task', {
        'shopIds': [shop_id],
        'detailIds': [tk_id_int]
    })
    if r_pub.get('code') == 'success':
        return True, "发布成功"
    else:
        return False, "publish: {}".format(r_pub.get('message', '')[:60])


# ========== 主流程 ==========

def main():
    print("=" * 70)
    print("  🫘 豌豆数据·妙手上架63产品引擎")
    print("  数据: /tmp/publish_final.json (63个产品)")
    print("  链路: 创建采集箱 → 认领平台 → 认领店铺 → 保存站点+店铺 → 发布")
    print("=" * 70)

    # 加载数据
    with open('/tmp/publish_final.json', 'r') as f:
        products = json.load(f)

    print("\n📦 加载 {} 个产品".format(len(products)))

    # 按品类分组
    grouped = {'beauty': [], 'kitchen': [], 'home': []}
    for p in products:
        cat = p['cat']
        if cat in grouped:
            grouped[cat].append(p)
    for cat, items in grouped.items():
        print("  {}: {} 个".format(CAT_CN.get(cat, cat), len(items)))

    # ===== 报告输出 =====
    report_lines = [
        "# 🫘 豌豆数据·妙手上架报告",
        "**日期**: 2026-05-14",
        "**数据源**: /tmp/publish_final.json ({}个产品)".format(len(products)),
        "",
        "## 数据概览",
    ]
    for cat, items in grouped.items():
        countries = {}
        for p in items:
            c = p['country']
            countries[c] = countries.get(c, 0) + 1
        country_strs = ["{}({})".format(c, n) for c, n in countries.items()]
        report_lines.append("- **{}**: {}个产品 → {}".format(
            CAT_CN.get(cat, cat), len(items), ', '.join(country_strs)))

    report_lines.extend(["", "---", "## 上架结果", ""])

    all_results = []

    # ===== 按品类处理 =====
    for cat in ['beauty', 'kitchen', 'home']:
        items = grouped[cat]
        if not items:
            continue

        cat_cn = CAT_CN[cat]
        shop_configs = SHOP_MAP.get(cat, {})

        shop_targets = ', '.join("{} (ID:{})".format(c, v['shop_id']) for c, v in shop_configs.items())
        print("\n" + "="*60)
        print("  📁 品类: {}".format(cat_cn))
        print("  → 目标店铺: {}".format(shop_targets))
        print("="*60)

        by_country = {}
        for p in items:
            c = p['country']
            if c not in by_country:
                by_country[c] = []
            by_country[c].append(p)

        for country, country_items in by_country.items():
            if country not in shop_configs:
                print("\n  ⏭️ {}: 无对应店铺映射,跳过".format(country))
                for p in country_items:
                    all_results.append({
                        'product': p['name'],
                        'cat': cat,
                        'country': country,
                        'step': 'skip',
                        'status': '⏭️',
                        'message': '无店铺映射'
                    })
                continue

            shop_info = shop_configs[country]
            shop_id = shop_info['shop_id']

            print("\n  🏪 {} → 店铺 {} ({}) - {}个产品".format(
                country, shop_id, shop_info['brand'], len(country_items)))

            # ----- 步骤1: 创建采集箱产品 -----
            print("\n    📌 步骤1: 创建采集箱产品...")
            created_ids = {}

            for idx, p in enumerate(country_items):
                progress = "[{}/{}]".format(idx+1, len(country_items))
                title = p['title'][:60] if p['title'] else p['name'][:60]
                print("    {} 创建: {}...".format(progress, title), end=' ')
                sys.stdout.flush()

                common_id = create_common_product(p, idx, len(country_items))
                if common_id:
                    created_ids[idx] = common_id
                    print("✅ common_id={}".format(common_id))
                    time.sleep(0.5)
                else:
                    print("❌ 创建失败")
                    all_results.append({
                        'product': p['name'],
                        'cat': cat,
                        'country': country,
                        'step': 'create',
                        'status': '❌',
                        'message': '创建采集箱产品失败'
                    })

            if not created_ids:
                print("    ❌ {}: 所有产品创建失败,跳过后续".format(country))
                continue

            print("    ✅ 已创建 {}/{} 个产品到采集箱".format(
                len(created_ids), len(country_items)))

            # ----- 步骤2: 认领到TK平台 -----
            common_ids_list = list(created_ids.values())
            print("\n    📌 步骤2: 认领{}个产品到TK平台...".format(len(common_ids_list)))

            tk_id_map = claim_to_platform(common_ids_list)

            if not tk_id_map:
                print("    ⚠️ 平台认领返回为空,尝试搜索TK采集箱...")

            print("    ✅ 平台认领: {}/{} 个匹配".format(
                len(tk_id_map), len(common_ids_list)))

            # ----- 步骤3-5: 获取tid → 认领到店铺 → 保存 → 发布 -----
            tk_ids_found = list(tk_id_map.values()) if tk_id_map else []

            if not tk_ids_found:
                print("\n    📌 搜索TK采集箱获取detail ID...")
                tk_map_from_search = search_tk_collect_box_batch(set(common_ids_list))
                for cid, tid in tk_map_from_search.items():
                    tk_id_map[cid] = tid
                tk_ids_found = list(tk_id_map.values())
                print("    ✅ 搜索到 {} 个TK detail ID".format(len(tk_ids_found)))

            if tk_ids_found:
                print("\n    📌 步骤3: 认领到店铺 {}...".format(shop_id))
                ok, claim_result = claim_to_shop_batch(
                    [int(tid) for tid in tk_ids_found if tid],
                    shop_id
                )
                if ok:
                    print("    ✅ 店铺认领成功")
                else:
                    print("    ⚠️ 店铺认领结果: {}".format(
                        json.dumps(claim_result, ensure_ascii=False)[:150]))

                time.sleep(1)

                # 逐个产品: save_site → save_shop → publish
                print("\n    📌 步骤4-6: 保存站点/店铺 → 发布")

                for idx, product_info in enumerate(country_items):
                    if idx not in created_ids:
                        all_results.append({
                            'product': product_info['name'],
                            'cat': cat,
                            'country': country,
                            'step': 'publish',
                            'status': '❌',
                            'message': '前序步骤失败(未创建)'
                        })
                        continue

                    common_id = created_ids[idx]
                    tk_id = tk_id_map.get(common_id)

                    if not tk_id:
                        all_results.append({
                            'product': product_info['name'],
                            'cat': cat,
                            'country': country,
                            'step': 'publish',
                            'status': '❌',
                            'message': '未获取到TK detail ID'
                        })
                        continue

                    title = product_info['title'] or product_info['name']
                    desc = product_info['desc']
                    progress = "[{}/{}]".format(idx+1, len(country_items))

                    print("    {} 发布: {}...".format(progress, title[:50]), end=' ')
                    sys.stdout.flush()

                    success, msg = process_save_and_publish(
                        tk_id, shop_id, country, title, desc
                    )

                    status = '✅' if success else '❌'
                    print("{} {}".format(status, msg))

                    all_results.append({
                        'product': product_info['name'],
                        'cat': cat,
                        'country': country,
                        'step': 'publish',
                        'status': status,
                        'message': msg
                    })

                    time.sleep(0.5)

            time.sleep(2)

    # ===== 汇总报告 =====
    print("\n" + "="*70)
    print("  📊 汇总报告")
    print("="*70)

    success_count = sum(1 for r in all_results if r['status'] == '✅')
    fail_count = sum(1 for r in all_results if r['status'] == '❌')
    skip_count = sum(1 for r in all_results if r['status'] == '⏭️')

    print("\n  总计: {} 个操作".format(len(all_results)))
    print("  ✅ 成功: {}".format(success_count))
    print("  ❌ 失败: {}".format(fail_count))
    print("  ⏭️ 跳过: {}".format(skip_count))

    print("\n  📊 按品类:")
    for cat in ['beauty', 'kitchen', 'home']:
        cat_results = [r for r in all_results if r['cat'] == cat]
        if cat_results:
            succ = sum(1 for r in cat_results if r['status'] == '✅')
            fail = sum(1 for r in cat_results if r['status'] == '❌')
            skip = sum(1 for r in cat_results if r['status'] == '⏭️')
            print("    {}: {}✅ / {}❌ / {}⏭️".format(
                CAT_CN.get(cat, cat), succ, fail, skip))

    # ===== 写入报告 =====
    report_lines.append("### 总体")
    report_lines.append("- 总计: {} 个操作".format(len(all_results)))
    report_lines.append("- ✅ 成功: {}".format(success_count))
    report_lines.append("- ❌ 失败: {}".format(fail_count))
    report_lines.append("- ⏭️ 跳过: {}".format(skip_count))
    report_lines.append("")

    for cat in ['beauty', 'kitchen', 'home']:
        cat_results = [r for r in all_results if r['cat'] == cat]
        if not cat_results:
            continue
        succ = sum(1 for r in cat_results if r['status'] == '✅')
        fail = sum(1 for r in cat_results if r['status'] == '❌')
        skip = sum(1 for r in cat_results if r['status'] == '⏭️')
        report_lines.append("### {} ({}✅ / {}❌ / {}⏭️)".format(
            CAT_CN.get(cat, cat), succ, fail, skip))
        report_lines.append("")
        report_lines.append("| # | 产品 | 国家 | 状态 | 备注 |")
        report_lines.append("|---|------|:----:|:----:|------|")
        for i, r in enumerate(cat_results, 1):
            report_lines.append("| {} | {} | {} | {} | {} |".format(
                i, r['product'][:40], r['country'], r['status'],
                r.get('message', '')[:50]))
        report_lines.append("")

    fails = [r for r in all_results if r['status'] == '❌']
    if fails:
        report_lines.append("### ❌ 失败项")
        report_lines.append("")
        for r in fails:
            report_lines.append("- {} ({}) - {}".format(
                r['product'][:40], r['country'], r.get('message', '')))

    report = "\n".join(report_lines)

    output_dir = Path('/Users/a1234/.openclaw/workspace/agents/pea-agent/output')
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / 'publish_report_63_2026-05-14.md'
    report_path.write_text(report)

    print("\n  📝 报告已保存: {}".format(report_path))
    print("="*70)


if __name__ == '__main__':
    main()
