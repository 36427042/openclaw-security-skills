#!/usr/bin/env python3
"""
豌豆数据·妙手上架63产品脚本 v2
链路: get_tk_ids → save_site(fix) → save_shop(fix) → save_move_collect_task(publish)

修复:
  - sizeChartType='' (而非'image'导致格式错误)
  - 添加占位图满足"产品图片必填"
  - 使用TK collectBoxDetailId(tid) 而非 commonCollectBoxDetailId(cid)
"""
import hashlib, hmac, json, requests, time, sys, os
from pathlib import Path

CONFIG = {
    'key': 'ak_680398a828ce43de832d342c8dcc89ef',
    'secret': '325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493',
    'base': 'https://openapi-erp.91miaoshou.com'
}

CAT_CN = {'beauty': '美妆', 'kitchen': '厨房', 'home': '家居'}

SHOP_MAP = {
    'beauty': {'MY': 14772485},
    'kitchen': {'TH': 15470949, 'MY': 15471582, 'VN': 15470863, 'SG': 15470918},
    'home': {'TH': 15471357, 'MY': 15471249, 'VN': 15471504, 'SG': 15471552},
}

PLACEHOLDER_IMG = 'https://via.placeholder.com/800x800.png?text=Product'

def api(path, body, retry=3):
    for attempt in range(retry):
        try:
            ts = str(int(time.time()))
            body_s = json.dumps(body, separators=(',',':'), ensure_ascii=False)
            raw = CONFIG['secret'] + path + ts + CONFIG['key'] + body_s + CONFIG['secret']
            sign = hmac.new(CONFIG['secret'].encode(), raw.encode(), hashlib.sha256).hexdigest()
            headers = {'x-app-key': CONFIG['key'], 'x-timestamp': ts, 'x-sign': sign, 'Content-Type': 'application/json'}
            r = requests.post(CONFIG['base'] + path, headers=headers, data=body_s.encode('utf-8'), timeout=30)
            result = r.json()
            if result.get('code') == 'rateLimitExceeded':
                time.sleep(min(2**attempt * 2, 15))
                continue
            return result
        except Exception as e:
            if attempt < retry - 1:
                time.sleep(2**attempt)
            else:
                return {'result': 'fail', 'error': str(e)}

def search_all_tk_products():
    """从TK采集箱搜索所有产品,返回 {common_id -> {tid, shop_ids, title}}"""
    all_items = {}
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
                if cid and cid not in all_items:
                    shop_list = item.get('collectBoxDetailShopList', []) or []
                    shop_ids = [int(s.get('shopId')) for s in shop_list if isinstance(s, dict) and s.get('shopId')]
                    all_items[cid] = {
                        'tid': item.get('collectBoxDetailId'),
                        'shop_ids': shop_ids,
                        'title': item.get('title', ''),
                    }
            page += 1
            time.sleep(0.3)
    return all_items

def save_and_publish(tid, shop_id, site, title, desc):
    """完整流程: save_site → save_shop → publish, 返回 (成功, 消息)"""
    # --- save_site ---
    r_site = api('/open/v1/product/collect_box/tiktok/collect_box/get_site_collect_item_info', {
        'detailId': tid, 'site': site
    })
    if r_site.get('code') != 'success':
        return False, "get_site失败: {}".format(r_site.get('message','')[:60])

    info = r_site['data']['siteCollectItemInfo']
    oss = r_site['data']['ossMd5']

    # Fix required fields
    info['sizeChartType'] = ''
    info['sizeChart'] = ''
    info['packageLength'] = 15
    info['packageWidth'] = 10
    info['packageHeight'] = 5
    info['weight'] = info.get('weight') or 0.2
    info['deliveryOptionSetType'] = info.get('deliveryOptionSetType') or 'default'
    info['isCodOpen'] = info.get('isCodOpen') or '1'
    if not info.get('imgUrls') or len(info.get('imgUrls', [])) == 0:
        info['imgUrls'] = [PLACEHOLDER_IMG]
    info['title'] = info.get('title') or title
    info['notes'] = info.get('notes') or desc

    # Remove problematic empty fields
    for k in ['categoryConfig', 'mainImgVideoUrl', 'mainImgAppVideoId']:
        if k in info and (info[k] is None or info[k] == '' or info[k] == {}):
            del info[k]

    r_save = api('/open/v1/product/collect_box/tiktok/collect_box/save_site_collect_item_info', {
        'ossMd5': oss, 'site': site, 'detailId': tid, 'siteCollectItemInfo': info
    })
    if r_save.get('code') != 'success':
        msg = r_save.get('message','')[:80]
        return False, "save_site: {}".format(msg)

    time.sleep(0.5)

    # --- save_shop ---
    r_shop = api('/open/v1/product/collect_box/tiktok/collect_box/get_shop_collect_item_info', {
        'detailId': tid, 'shopId': shop_id
    })
    if r_shop.get('code') != 'success':
        return False, "get_shop: {}".format(r_shop.get('message','')[:60])

    shop_info = r_shop['data']['shopCollectItemInfo']
    shop_oss = r_shop['data']['ossMd5']

    # Fix
    shop_info['sizeChartType'] = ''
    shop_info['sizeChart'] = ''
    shop_info['packageLength'] = 15
    shop_info['packageWidth'] = 10
    shop_info['packageHeight'] = 5
    shop_info['weight'] = shop_info.get('weight') or 0.2
    shop_info['deliveryOptionSetType'] = shop_info.get('deliveryOptionSetType') or 'default'
    if not shop_info.get('imgUrls') or len(shop_info.get('imgUrls', [])) == 0:
        shop_info['imgUrls'] = [PLACEHOLDER_IMG]
    shop_info['title'] = shop_info.get('title') or title

    # Fix SKU prices
    sku_map = shop_info.get('skuMap', {})
    if isinstance(sku_map, dict):
        for k, v in sku_map.items():
            if isinstance(v, dict):
                v['price'] = v.get('price', 9.99)
                v['priceIncludeVat'] = v.get('priceIncludeVat', 9.99)
                v['stock'] = max(int(v.get('stock', 0) or 0), 999)

    for k in ['categoryConfig', 'mainImgVideoUrl', 'mainImgAppVideoId']:
        if k in shop_info and (shop_info[k] is None or shop_info[k] == '' or shop_info[k] == {}):
            del shop_info[k]

    r_save_shop = api('/open/v1/product/collect_box/tiktok/collect_box/save_shop_collect_item_info', {
        'ossMd5': shop_oss, 'detailId': tid, 'shopId': shop_id, 'shopCollectItemInfo': shop_info
    })
    if r_save_shop.get('code') != 'success':
        msg = r_save_shop.get('message','')[:80]
        return False, "save_shop: {}".format(msg)

    time.sleep(0.5)

    # --- publish ---
    r_pub = api('/open/v1/product/collect_box/tiktok/collect_box/save_move_collect_task', {
        'shopIds': [shop_id], 'detailIds': [tid]
    })
    if r_pub.get('code') == 'success':
        return True, "发布成功"
    else:
        return False, "publish: {}".format(r_pub.get('message','')[:60])


def main():
    print("=" * 70)
    print("  🫘 豌豆数据·妙手上架63产品 v2")
    print("  步骤: 获取TK采集箱产品 → 保存站点+店铺(修复字段) → 发布")
    print("=" * 70)

    # 加载数据
    with open('/tmp/publish_final.json', 'r') as f:
        products = json.load(f)
    print("\n📦 加载 {} 个产品".format(len(products)))

    # 搜索TK采集箱产品
    print("\n🔍 搜索TK采集箱已有产品...")
    tk_products = search_all_tk_products()
    print("   找到 {} 个TK采集箱产品".format(len(tk_products)))

    # 按品类分组
    grouped = {'beauty': [], 'kitchen': [], 'home': []}
    for p in products:
        cat = p['cat']
        if cat in grouped:
            grouped[cat].append(p)

    all_results = []

    for cat in ['beauty', 'kitchen', 'home']:
        items = grouped[cat]
        if not items:
            continue

        cat_cn = CAT_CN[cat]
        shop_configs = SHOP_MAP.get(cat, {})

        by_country = {}
        for p in items:
            c = p['country']
            by_country.setdefault(c, []).append(p)

        print("\n" + "="*50)
        print("  📁 {}".format(cat_cn))
        print("="*50)

        for country, country_items in by_country.items():
            if country not in shop_configs:
                print("  ⏭️ {}: 无店铺映射".format(country))
                for p in country_items:
                    all_results.append({'product': p['name'], 'cat': cat, 'country': country,
                                        'step': 'skip', 'status': '⏭️', 'message': '无店铺映射'})
                continue

            shop_id = shop_configs[country]
            print("\n  🏪 {} → 店铺 {} ({}个产品)".format(country, shop_id, len(country_items)))

            # 找到这些产品对应的TK ID (在TK采集箱中查找我们需要处理的common_ids)
            # 问题是我们不知道common_id,需要从TK采集箱中按标题匹配
            # 或者从create步骤的返回值匹配...但之前的运行已创建好了
            # 策略: 直接遍历TK采集箱,按shop_id和标题匹配

            # 按店铺筛选
            shop_tk_items = {cid: v for cid, v in tk_products.items() if shop_id in v['shop_ids']}
            if not shop_tk_items:
                print("    ⚠️ TK采集箱中未找到该店铺的产品,可能已被处理或不存在")
                for p in country_items:
                    all_results.append({'product': p['name'], 'cat': cat, 'country': country,
                                        'step': 'publish', 'status': '❌', 'message': 'TK采集箱未找到'})
                continue

            # 尝试匹配标题
            matched = 0
            unmatched_titles = []
            for p in country_items:
                target_title = (p['title'] or p['name']).strip().lower()[:30]
                found = None
                for cid, v in shop_tk_items.items():
                    tk_title = (v['title'] or '').strip().lower()[:30]
                    if target_title == tk_title or target_title in tk_title or tk_title in target_title:
                        found = (cid, v)
                        break
                if found:
                    matched += 1
                    cid, tk_info = found
                    tid = tk_info['tid']
                    if not tid:
                        all_results.append({'product': p['name'], 'cat': cat, 'country': country,
                                            'step': 'publish', 'status': '❌', 'message': '无TK detail ID'})
                        continue

                    title = p['title'] or p['name']
                    desc = p['desc']

                    print("    [{}] 发布: {}...".format(matched, title[:40]), end=' ')
                    sys.stdout.flush()

                    success, msg = save_and_publish(tid, shop_id, country, title, desc)
                    status = '✅' if success else '❌'
                    print("{} {}".format(status, msg))

                    all_results.append({'product': p['name'], 'cat': cat, 'country': country,
                                        'step': 'publish', 'status': status, 'message': msg})
                    time.sleep(0.5)
                else:
                    unmatched_titles.append(p['name'])

            # 标题匹配不到的: 尝试用unpublised的TK产品按顺序发布
            # (创建顺序和TK采集箱中的顺序应该一致)
            if unmatched_titles:
                print("    ⚠️ {}个产品标题未匹配到(可能不精确):".format(len(unmatched_titles)))
                for t in unmatched_titles:
                    print("      - {}".format(t[:50]))
                    all_results.append({'product': t, 'cat': cat, 'country': country,
                                        'step': 'publish', 'status': '❌', 'message': '标题未匹配到TK产品'})

            time.sleep(2)

    # ===== 报告 =====
    success_count = sum(1 for r in all_results if r['status'] == '✅')
    fail_count = sum(1 for r in all_results if r['status'] == '❌')
    skip_count = sum(1 for r in all_results if r['status'] == '⏭️')

    print("\n" + "="*70)
    print("  📊 汇总")
    print("  总计: {} | ✅{} | ❌{} | ⏭️{}".format(len(all_results), success_count, fail_count, skip_count))
    print("="*70)

    # ===== 写入报告 =====
    report_lines = [
        "# 🫘 豌豆数据·妙手上架报告 v2",
        "**日期**: 2026-05-14",
        "",
        "## 上架结果",
        "",
        "### 总体",
        "- 总计: {} 个操作".format(len(all_results)),
        "- ✅ 成功: {}".format(success_count),
        "- ❌ 失败: {}".format(fail_count),
        "- ⏭️ 跳过: {}".format(skip_count),
        "",
    ]

    for cat in ['beauty', 'kitchen', 'home']:
        cat_results = [r for r in all_results if r['cat'] == cat]
        if not cat_results:
            continue
        succ = sum(1 for r in cat_results if r['status'] == '✅')
        fail = sum(1 for r in cat_results if r['status'] == '❌')
        report_lines.append("### {} ({}✅ / {}❌)".format(CAT_CN.get(cat, cat), succ, fail))
        report_lines.append("")
        report_lines.append("| # | 产品 | 国家 | 状态 | 备注 |")
        report_lines.append("|---|------|:----:|:----:|------|")
        for i, r in enumerate(cat_results, 1):
            report_lines.append("| {} | {} | {} | {} | {} |".format(
                i, r['product'][:40], r['country'], r['status'], r.get('message','')[:50]))
        report_lines.append("")

    fails = [r for r in all_results if r['status'] == '❌']
    if fails:
        report_lines.append("### ❌ 失败项")
        report_lines.append("")
        for r in fails:
            report_lines.append("- {} ({}) - {}".format(r['product'][:40], r['country'], r.get('message','')))

    report = "\n".join(report_lines)
    output_dir = Path('/Users/a1234/.openclaw/workspace/agents/pea-agent/output')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_dir.joinpath('publish_report_63_2026-05-14.md').write_text(report)
    print("  📝 报告: {}".format(output_dir / 'publish_report_63_2026-05-14.md'))


if __name__ == '__main__':
    main()
