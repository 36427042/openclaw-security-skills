#!/usr/bin/env python3
"""
妙手上架TOP60脚本
基于EchoTik原始JSON → 定价v3.0 → 比价过滤 → 按GMV排序TOP20/品类 → 妙手API上架
"""
import hashlib, hmac, json, requests, time, sys, re
from pathlib import Path

# ========== 配置 ==========

CONFIG = {
    'key': 'ak_680398a828ce43de832d342c8dcc89ef',
    'secret': '325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493',
    'base': 'https://openapi-erp.91miaoshou.com'
}

# 定价公式v3.0: 售价 = (spu_avg_price * 0.25 + 运费) / 分母
FREIGHT = {'TH': 0.50, 'MY': 0.80, 'PH': 0.80, 'SG': 0.50, 'VN': 0.60}
DENOM = {'TH': 0.40, 'MY': 0.37, 'PH': 0.33, 'SG': 0.43, 'VN': 0.34}

# 店铺映射
SHOP_MAP = {
    'beauty': {'VN': 14681328, 'MY': 14772485},
    'kitchen': {'TH': 15470949, 'MY': 15471582, 'VN': 15470863, 'SG': 15470918},
    'home': {'TH': 15471357, 'MY': 15471249, 'VN': 15471504, 'SG': 15471552},
}
# PH: 暂无店铺

DATA_DIR = '/Users/a1234/.openclaw/workspace/agents/pea-agent/output/echotik_raw'

# ========== API 工具 ==========

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

def extract_cover_urls(cover_url_str, max_images=9):
    """提取封面图URL列表，过滤掉非JPG/JPEG/PNG格式"""
    allowed_exts = ('.jpg', '.jpeg', '.png')
    try:
        urls = json.loads(cover_url_str)
        filtered = []
        for u in urls:
            url = u['url']
            # 检查扩展名
            path_part = url.split('?')[0].lower()
            if path_part.endswith(allowed_exts):
                filtered.append(url)
            if len(filtered) >= max_images:
                break
        return filtered
    except:
        return []

# ========== 数据加载 & 比价过滤 ==========

def load_and_filter(category, region):
    """
    加载一个品类×国家的数据，针对该国家做比价过滤
    返回按GMV排序的通过比价商品列表
    """
    filepath = f'{DATA_DIR}/{category}_{region}.json'
    try:
        with open(filepath) as f:
            data = json.load(f)
    except:
        return []

    items = data.get('items', [])
    freight = FREIGHT[region]
    denom = DENOM[region]
    
    passed = []
    for item in items:
        product_id = item.get('product_id')
        product_name = item.get('product_name', '')
        spu_avg_price = item.get('spu_avg_price', 0)
        min_price = item.get('min_price', 0)
        sale_30d_cnt = item.get('total_sale_30d_cnt', 0)
        gmv_30d = item.get('total_sale_gmv_30d_amt', 0)
        rating = item.get('product_rating', 0)
        review_cnt = item.get('review_count', 0)
        ifl_cnt = item.get('total_ifl_cnt', 0)
        cover_urls = extract_cover_urls(item.get('cover_url', '[]'))
        
        if not spu_avg_price or not min_price:
            continue
        
        # 定价公式v3.0: 售价 = (spu_avg_price * 0.25 + 运费) / 分母
        # spu_avg_price 是USD，计算售价直接得出USD
        our_price = (spu_avg_price * 0.25 + freight) / denom
        
        # 比价过滤: 计算售价 ≤ TK价×0.92
        tk_price = min_price
        if our_price <= tk_price * 0.92:
            passed.append({
                'product_id': product_id,
                'product_name': product_name,
                'category': category,
                'region': region,
                'spu_avg_price': spu_avg_price,
                'tk_price': tk_price,
                'our_price': round(our_price, 2),
                'gmv_30d': gmv_30d,
                'sale_30d_cnt': sale_30d_cnt,
                'rating': rating,
                'review_count': review_cnt,
                'ifl_cnt': ifl_cnt,
                'cover_urls': cover_urls,
            })
    
    # 按GMV降序排列
    passed.sort(key=lambda x: x['gmv_30d'], reverse=True)
    return passed

# ========== 妙手上架流程 ==========

def add_to_collection_box(product, shop_id):
    """
    步骤4: 添加产品到妙手公共采集箱 (add_common_collect_box_detail)
    """
    cover_urls = product['cover_urls'][:9] if product['cover_urls'] else []
    
    payload = {
        'title': product['product_name'][:120],
        'price': round(product['our_price'] * 1.3, 2),  # 统一用SG价格/加一些利润空间
        'stock': 999,
        'imgUrls': cover_urls,
        'weight': 0.2,
        'sourceAttrs': [
            {'name': 'Category', 'value': product['category'].title()},
            {'name': 'Origin', 'value': 'China'},
            {'name': 'Source', 'value': 'EchoTik'},
        ],
    }
    
    result = api('/open/v1/product/common_collect_box/common_collect_box/add_common_collect_box_detail', payload)
    return result

def claim_platform(common_ids):
    """
    步骤5: 认领平台 (claimed)
    """
    result = api('/open/v1/product/collect_box/tiktok/collect_box/claim_to_platform', {
        'commonCollectBoxDetailIds': common_ids,
    })
    return result

def claim_to_shop(common_ids, shop_id):
    """
    步骤6: 认领到具体店铺
    """
    result = api('/open/v1/product/collect_box/tiktok/collect_box/claim_to_shop', {
        'detailIds': common_ids,
        'shopIds': [shop_id],
    })
    return result

def publish_items(common_ids, shop_id):
    """
    步骤7: 发布上架 (save_move_collect_task)
    注意：需要 shopIds 参数
    """
    result = api('/open/v1/product/collect_box/tiktok/collect_box/save_move_collect_task', {
        'detailIds': common_ids,
        'shopIds': [shop_id],
    })
    return result

# ========== 主流程 ==========

def main():
    print("=" * 70)
    print("  🌽 玉米 - 妙手上架TOP60引擎 v1.0")
    print("  数据: EchoTik原始JSON → 定价v3.0 → 比价过滤 → GMV排序TOP20/品类")
    print("=" * 70)
    
    categories = ['beauty', 'kitchen', 'home']
    all_results = {}
    
    # 步骤1-3: 加载数据 → 定价 → 比价过滤 → 排序取TOP20
    for cat in categories:
        print(f"\n📊 品类: {cat.capitalize()}")
        cat_results = {}
        
        for region in ['VN', 'TH', 'MY', 'PH', 'SG']:
            # 跳过PH (无店铺) 或无shop映射
            shops = SHOP_MAP.get(cat, {})
            if region not in shops:
                continue
                
            items = load_and_filter(cat, region)
            if not items:
                print(f"  {region}: 0个通过比价")
                continue
            
            top20 = items[:20]
            print(f"  {region}: {len(items)}个通过比价 → TOP20 (GMV: {top20[0]['gmv_30d']:.0f}~{top20[-1]['gmv_30d']:.0f})")
            
            shop_id = shops[region]
            cat_results[region] = {'shop_id': shop_id, 'products': top20}
            
            # 打印产品概要
            for i, p in enumerate(top20, 1):
                print(f"    {i:2d}. {p['product_name'][:40]:40s} | TK价={p['tk_price']:.2f} → 售价={p['our_price']:.2f} | GMV={p['gmv_30d']:.0f}")
        
        all_results[cat] = cat_results
    
    # 确认
    print(f"\n" + "=" * 70)
    print("  已通过比价过滤，按GMV排序选出TOP20/店铺")
    print("  准备调用妙手API上架...")
    print("=" * 70)
    
    # ===== 步骤4: 创建采集箱产品 =====
    print("\n\n🚀 步骤4: 创建产品到妙手公共采集箱 (add_common_collect_box_detail)")
    created_map = {}  # cat -> region -> {product_id -> common_id}
    
    for cat, regions in all_results.items():
        created_map[cat] = {}
        for region, data in regions.items():
            created_map[cat][region] = {}
            print(f"\n  [{cat.capitalize()} - {region}] 创建{len(data['products'])}个产品:")
            
            for p in data['products']:
                # 设置正确的售价 - 我们需要为该产品的源国家设置售价
                # 但由于 add_common_collect_box_detail 只需要一个price字段
                # 我们用该国家的定价
                result = add_to_collection_box(p, data['shop_id'])
                
                if result.get('result') == 'success':
                    common_id = result['data']['commonCollectBoxDetailId']
                    created_map[cat][region][p['product_id']] = common_id
                    print(f"    ✅ {p['product_name'][:30]:30s} → common_id={common_id}")
                else:
                    print(f"    ❌ {p['product_name'][:30]:30s} → {result}")
                
                time.sleep(0.5)  # 限流控制
    
    # 统计创建结果
    total_created = sum(len(r) for cat_reg in created_map.values() for r in cat_reg.values())
    print(f"\n  总计创建: {total_created} 个产品到采集箱")
    
    if total_created == 0:
        print("❌ 没有产品创建成功，中止流程")
        return
    
    # ===== 步骤5: 认领平台 (claimed) =====
    print("\n\n🚀 步骤5: 认领平台 (claim_to_platform)")
    
    for cat, regions in created_map.items():
        for region, products in regions.items():
            if not products:
                continue
            common_ids = list(products.values())
            shop_id = all_results[cat][region]['shop_id']
            
            print(f"  [{cat.capitalize()} - {region}] 认领{len(common_ids)}个产品...")
            result = claim_platform(common_ids)
            
            if result.get('result') == 'success':
                print(f"    ✅ 平台认领成功: {result.get('message', '')}")
            else:
                print(f"    ⚠️ 平台认领结果: {result}")
            
            time.sleep(1)
    
    # ===== 步骤6: 认领到店铺 =====
    print("\n\n🚀 步骤6: 认领到店铺 (claim_to_shop)")
    
    all_claim_results = {}
    for cat, regions in created_map.items():
        all_claim_results[cat] = {}
        for region, products in regions.items():
            if not products:
                continue
            common_ids = list(products.values())
            shop_id = SHOP_MAP[cat][region]
            
            print(f"  [{cat.capitalize()} - {region}] 认领到店铺 {shop_id}...")
            result = claim_to_shop(common_ids, shop_id)
            
            if result.get('result') == 'success':
                print(f"    ✅ 店铺认领成功: {result.get('message', '')}")
                all_claim_results[cat][region] = True
            else:
                print(f"    ⚠️ 店铺认领结果: {result}")
                all_claim_results[cat][region] = False
            
            time.sleep(1)
    
    # ===== 步骤7: 发布上架 =====
    print("\n\n🚀 步骤7: 发布上架 (save_move_collect_task)")
    
    publish_results = []
    for cat, regions in created_map.items():
        for region, products in regions.items():
            if not products:
                continue
            if not all_claim_results.get(cat, {}).get(region, False):
                print(f"  ⏭️ [{cat.capitalize()} - {region}] 店铺认领未成功，跳过发布")
                continue
            
            common_ids = list(products.values())
            shop_id = SHOP_MAP[cat][region]
            # 批量发布一次
            print(f"  [{cat.capitalize()} - {region}] 发布 {len(common_ids)} 个产品...")
            result = publish_items(common_ids, shop_id)
            
            if result.get('result') == 'success':
                print(f"    ✅ 批量发布成功")
                for cid in common_ids:
                    publish_results.append({'cat': cat, 'region': region, 'common_id': cid, 'status': 'success'})
            else:
                print(f"    ⚠️ 批量发布结果: {result}")
                # 尝试单品发布
                for cid in common_ids:
                    print(f"     单品发布 common_id={cid}...")
                    single_result = publish_items([cid], shop_id)
                    if single_result.get('result') == 'success':
                        print(f"      ✅ 发布成功")
                        publish_results.append({'cat': cat, 'region': region, 'common_id': cid, 'status': 'success'})
                    else:
                        print(f"      ⚠️ 发布结果: {single_result}")
                        publish_results.append({'cat': cat, 'region': region, 'common_id': cid, 'status': 'failed', 'error': str(single_result)})
                    time.sleep(0.5)
    
    # ===== 输出报告 =====
    print("\n\n" + "=" * 70)
    print("  📋 上架结果报告")
    print("=" * 70)
    
    for cat in categories:
        regions = created_map.get(cat, {})
        if not regions:
            continue
            
        print(f"\n  📁 {cat.capitalize()}:")
        for region, products in regions.items():
            success_count = sum(1 for r in publish_results if r['cat'] == cat and r['region'] == region and r['status'] == 'success')
            print(f"    {region}: {len(products)}个创建 → {success_count}个成功发布")
    
    success_total = sum(1 for r in publish_results if r['status'] == 'success')
    fail_total = sum(1 for r in publish_results if r['status'] == 'failed')
    
    print(f"\n  📊 总计: {total_created}个创建 → {success_total}个发布成功, {fail_total}个发布失败")
    
    # 保存结果到文件
    output = {
        'created_count': total_created,
        'published_success': success_total,
        'published_failed': fail_total,
        'details': publish_results,
        'created_map': {cat: {reg: {pid: cid for pid, cid in prods.items()} for reg, prods in regs.items()} for cat, regs in created_map.items()}
    }
    output_path = '/Users/a1234/.openclaw/workspace/agents/corn-agent/output/miaoshou_top60_result.json'
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n  📝 详细结果已保存: {output_path}")
    print("=" * 70)

if __name__ == '__main__':
    main()
