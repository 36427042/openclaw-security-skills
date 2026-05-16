#!/usr/bin/env python3
"""
📦 妙手发布脚本 v3.0（最终版）
天赐 2026-05-16 优化

核心功能：
  ✅ 去中文图（HTTP + Serveo隧道）
  ✅ 自动翻页搜索TK采集箱（1-100页）
  ✅ 5国语标题/描述（自动加载本地化文案）
  ✅ 完善信息：类目推理、重量/尺寸自动填充
  ✅ 已发布跳过检查
  ✅ 重试机制
  ✅ 多品类支持：家居+厨房
  ✅ 新定价公式（pricing_v5: 成本+7+利润15-25）

用法:
  python3 publish_v3_optimized.py [--force]
"""
import hashlib, hmac, json, requests, time, sys, os, subprocess, atexit, signal, threading, re, glob

# ═══════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════
CONFIG = {
    'key': 'ak_680398a828ce43de832d342c8dcc89ef',
    'secret': '325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493',
    'base': 'https://openapi-erp.91miaoshou.com'
}
_COM = '/open/v1/product/common_collect_box/common_collect_box'
_TK  = '/open/v1/product/collect_box/tiktok/collect_box'

# 图片目录
CLEAN_IMG_DIR = os.path.expanduser("~/Desktop/40SKU产品图_去中文/")
HTTP_PORT = 19765
tunnel_proc = http_proc = None

# 店铺映射
SHOP_MAP = {
    '家居': {'TH': 15471357, 'MY': 15471249, 'VN': 15471504, 'SG': 15471552},
    '厨房': {'TH': 15470949, 'MY': 15471582, 'VN': 15470863, 'SG': 15470918},
}
SITE_ORDER = ['TH', 'MY', 'VN', 'SG']

# 产品→序号映射（用于匹配去中文图文件名）
PRODUCT_IMAGE_SEQ = {
    3584763710:1, 3584762266:2, 3584760370:3, 3584759088:4, 3584758568:5,
    3584757763:6, 3584756988:7, 3584756022:8, 3584755695:9, 3584755289:10,
    3584753904:11, 3584752831:12, 3584752366:13, 3584752115:14, 3584751460:15,
    3584750914:16, 3584749492:17, 3584747663:18, 3584746535:19, 3584745659:20,
    3584742324:21, 3584740705:22, 3584740425:23, 3584737391:24, 3584733256:25,
    3584732170:26, 3584731868:27, 3584730631:28, 3584727336:29, 3584725982:30,
    3584722199:31, 3584720950:32, 3584719270:33, 3584699797:34, 3584697350:35,
    3584696985:36, 3584687391:37, 3584685661:38, 3584678137:39, 3584671227:40,
}

# 5国语文案
COPY_FILE = "/tmp/kitchen_5lang_copy.json"
LOCAL_COPY = {}
if os.path.exists(COPY_FILE):
    try:
        with open(COPY_FILE) as f: LOCAL_COPY = json.load(f)
    except: pass

MAX_RETRY = 2
DOMESTIC_FREIGHT = 3.5

# 定价模块（优先 v5，回退 v4）
try:
    sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/agents/tomato-agent/scripts'))
    if os.path.exists(os.path.expanduser('~/.openclaw/workspace/agents/tomato-agent/scripts/pricing_v5.py')):
        from pricing_v5 import calc_price, get_profit_tier, COUNTRIES
    else:
        from pricing_v4 import calc_price, get_profit_tier, COUNTRIES
except ImportError as e:
    raise ImportError(f"定价模块未找到: {e}")

# ═══════════════════════════════════════════
# HTTP + Tunnel 服务
# ═══════════════════════════════════════════

def start_http():
    global http_proc
    http_proc = subprocess.Popen(["python3","-m","http.server",str(HTTP_PORT),
        "--directory",CLEAN_IMG_DIR,"--bind","127.0.0.1"],
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(1)
    for _ in range(5):
        try:
            if requests.get(f"http://127.0.0.1:{HTTP_PORT}/", timeout=3).status_code == 200:
                print(f"  📂 HTTP ✅ http://127.0.0.1:{HTTP_PORT}")
                return
        except: pass
        time.sleep(1)
    raise RuntimeError("❌ HTTP启动失败")

def start_tunnel():
    """Serveo SSH隧道"""
    global tunnel_proc
    url_found = [None]
    def reader(stream):
        for line in iter(stream.readline, ''):
            ls = line.strip()[:100]
            m = re.search(r'https://[^\s]+serveousercontent\.com', line)
            if m and not url_found[0]:
                url_found[0] = m.group(0) + '/'
        stream.close()
    tunnel_proc = subprocess.Popen(
        ['ssh','-o','StrictHostKeyChecking=no','-R',f'80:localhost:{HTTP_PORT}','serveo.net'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    t = threading.Thread(target=reader, args=(tunnel_proc.stdout,), daemon=True); t.start()
    for _ in range(30):
        if url_found[0]:
            print(f'  🔗 Serveo → {url_found[0]}'); return url_found[0]
        if tunnel_proc.poll() is not None: break
        time.sleep(1)
    raise RuntimeError("❌ Serveo隧道启动失败")

def cleanup():
    for p in [tunnel_proc, http_proc]:
        if p:
            try: p.terminate()
            except: pass
    subprocess.run("pkill -f 'serveo.net' 2>/dev/null", shell=True)
    subprocess.run("pkill -f 'http.server.*19765' 2>/dev/null", shell=True)
atexit.register(cleanup)

def get_clean_urls(url, product_id):
    """返回去中文图的公网URL列表"""
    seq = PRODUCT_IMAGE_SEQ.get(product_id)
    if not seq: return []
    urls = []
    if not os.path.isdir(CLEAN_IMG_DIR): return urls
    # 尝试双数字前缀 (01_,02_)
    prefix = f"{seq:02d}_"
    for f in sorted(os.listdir(CLEAN_IMG_DIR)):
        if f.startswith(prefix) and (f.endswith('.jpg') or f.endswith('.png')):
            urls.append(url + f)
    if not urls:
        # 尝试单数字前缀
        prefix2 = f"{seq}_"
        for f in sorted(os.listdir(CLEAN_IMG_DIR)):
            if f.startswith(prefix2) and (f.endswith('.jpg') or f.endswith('.png')):
                urls.append(url + f)
    return urls

# ═══════════════════════════════════════════
# 妙手 API
# ═══════════════════════════════════════════

def api(path, body):
    ts = str(int(time.time()))
    body_s = json.dumps(body, separators=(',',':'))
    raw = CONFIG['secret'] + path + ts + CONFIG['key'] + body_s + CONFIG['secret']
    sign = hmac.new(CONFIG['secret'].encode(), raw.encode(), hashlib.sha256).hexdigest()
    h = {'x-app-key': CONFIG['key'], 'x-timestamp': ts, 'x-sign': sign, 'Content-Type': 'application/json'}
    r = requests.post(CONFIG['base'] + path, headers=h, data=body_s, timeout=15)
    return r.json()

def get_base_price_and_stock(common_id):
    r = api(f'{_COM}/get_common_collect_box_detail', {'commonCollectBoxDetailId': common_id})
    if r.get('code') != 'success': return None, False, 0, 0
    d = r['data']
    detail = d.get('editCommonCollectBoxDetail', d.get('collectDetail', {}))
    sku_map = detail.get('skuMap', {})
    if isinstance(sku_map, list):
        skus = [v for v in sku_map if isinstance(v, dict) and v.get('price', 0) > 0]
    else:
        skus = [v for v in sku_map.values() if isinstance(v, dict) and v.get('price', 0) > 0]
    prices = [v.get('price', 0) for v in skus]
    stocks = [int(v.get('stock', 0) or 0) for v in skus]
    if not prices: return None, False, 0, 0
    base = min(prices)
    if base < 0.5:
        valid = [p for p in prices if p > 0.5]
        if valid: base = min(valid)
    return round(base, 2), sum(stocks) > 0, sum(stocks), len(skus)

def search_tk_all():
    """全量搜索TK采集箱（自动翻页1-100页）"""
    result = {}
    for page in range(1, 101):
        r = api(f'{_TK}/search_collect_box_detail_list', {'pageNo': page, 'pageSize': 50})
        items = r.get('data',{}).get('detailList',[]) or r.get('data',{}).get('list',[])
        if not items: break
        for item in items:
            result[str(item.get('commonCollectBoxDetailId',''))] = item.get('collectBoxDetailId')
    print(f"  📋 TK采集箱搜索完成: {len(result)}项 ({page-1}页)")
    return result

def is_already_published(tk_did, shop_id):
    r = api(f'{_TK}/get_shop_collect_item_info', {'detailId': tk_did, 'shopId': shop_id})
    if r.get('code') != 'success': return False
    si = r['data'].get('shopCollectItemInfo', {})
    sku_map = si.get('skuMap', {})
    if isinstance(sku_map, dict):
        prices = [v.get('priceIncludeVat', 0) or 0 for v in sku_map.values() if isinstance(v, dict)]
    else:
        prices = [v.get('priceIncludeVat', 0) or 0 for v in sku_map if isinstance(v, dict)]
    return any(p > 1 for p in prices)

def claim_to_shop(tk_did, shop_id):
    r = api(f'{_TK}/claim_to_shop', {'shopIds': [shop_id], 'detailIds': [tk_did]})
    return r.get('code') == 'success', r.get('message', '')

def infer_cid(name):
    """基于中文品名推理类目ID"""
    n = name.lower()
    if any(k in n for k in ['保鲜','饭盒','密封','盒','米桶','储物罐']): return '600029'
    if any(k in n for k in ['筷子','锅铲','厨具','勺']): return '600030'
    if any(k in n for k in ['榨汁','封口','打蒜','机']): return '600031'
    if any(k in n for k in ['水龙头','过滤']): return '600032'
    if any(k in n for k in ['收纳','置物','架','整理','挂','压缩袋']): return '600001'
    if any(k in n for k in ['真空','袋','压缩']): return '600002'
    if any(k in n for k in ['抹布','清洁','刷']): return '600003'
    if any(k in n for k in ['化妆','美容','刷','眉']): return '600004'
    return None

# ═══════════════════════════════════════════
# 发布核心
# ═══════════════════════════════════════════

def publish_one(tk_did, shop_id, site, did, name, base_cny, freight, base_url):
    """发布单个产品到单个站点"""
    target_price = calc_price(site, base_cny, freight)
    tier = get_profit_tier(site, base_cny, freight)
    print(f"  💰 ¥{base_cny}+¥{freight} → {COUNTRIES[site]['symbol']}{target_price:,.0f} ({tier})")

    # ❶ 认领到店铺
    api(f'{_TK}/claim_to_shop', {'shopIds':[shop_id],'detailIds':[tk_did]})
    time.sleep(0.3)

    # ❷ 获取站点信息
    r = api(f'{_TK}/get_site_collect_item_info', {'detailId': tk_did, 'site': site})
    if r.get('code') != 'success': return False, f'get_site: {r.get("message","")[:60]}'
    info = r['data']['siteCollectItemInfo']
    oss = r['data']['ossMd5']

    # 去中文图
    clean_urls = get_clean_urls(base_url, did)
    if clean_urls:
        info['imgUrls'] = clean_urls[:15]
        print(f"    🖼️ 去中文图 {len(clean_urls)}张")
    else:
        imgs = info.get('imgUrls', [])
        if len(imgs) > 15: info['imgUrls'] = imgs[:15]

    # 5国语标题+描述
    copy = LOCAL_COPY.get(str(did), {}).get('sites', {}).get(site, {})
    if copy.get('title'):
        info['title'] = copy['title']
        print(f"    📝 {site}标题: {copy['title'][:40]}")
    if copy.get('description'):
        info['notesText'] = info.get('notesText', '') + '\n' + copy['description']
        info['detail'] = copy['description']

    # 类目推理
    if not info.get('cid'):
        cid = infer_cid(name)
        if cid: info['cid'] = cid

    # 完善信息（重量/尺寸）
    info.setdefault('weight', 0.05)
    info.setdefault('packageLength', 15)
    info.setdefault('packageWidth', 10)
    info.setdefault('packageHeight', 2)
    info['deliveryOptionSetType'] = 'default'
    info['sizeChartType'] = ''

    # 若无标题则回填
    if not info.get('title'):
        rc = api(f'{_COM}/get_common_collect_box_detail', {'commonCollectBoxDetailId': did})
        if rc.get('code') == 'success':
            cd = rc['data'].get('editCommonCollectBoxDetail', rc['data'].get('collectDetail', {}))
            info['title'] = cd.get('title', name)

    # ❸ 保存站点信息
    r2 = api(f'{_TK}/save_site_collect_item_info', {'ossMd5':oss,'site':site,'detailId':tk_did,'siteCollectItemInfo':info})
    if r2.get('code') != 'success': return False, f'save_site: {r2.get("message","")[:60]}'
    time.sleep(0.5)

    # ❹ 获取店铺信息 → 设置价格
    r3 = api(f'{_TK}/get_shop_collect_item_info', {'detailId':tk_did,'shopId':shop_id})
    if r3.get('code') != 'success': return False, f'get_shop: {r3.get("message","")[:60]}'
    shop_info = r3['data']['shopCollectItemInfo']
    shop_oss = r3['data']['ossMd5']

    # 过滤零库存SKU + 设价
    sku_map = shop_info.get('skuMap', {})
    if isinstance(sku_map, dict):
        filtered = {}
        for k, v in sku_map.items():
            stock = int(v.get('stock', 0) or 0)
            if stock == 0: continue
            v['priceIncludeVat'] = target_price
            v['price'] = round(target_price / 1.1, 2)
            if stock > 99999: v['stock'] = 99999
            filtered[k] = v
        sku_map.clear()
        sku_map.update(filtered)

    shop_info['deliveryOptionSetType'] = 'default'
    shop_info['sizeChartType'] = ''
    shop_info.setdefault('weight',0.05)
    shop_info.setdefault('packageLength',15)
    shop_info.setdefault('packageWidth',10)
    shop_info.setdefault('packageHeight',2)

    r4 = api(f'{_TK}/save_shop_collect_item_info', {'ossMd5':shop_oss,'detailId':tk_did,'shopId':shop_id,'shopCollectItemInfo':shop_info})
    if r4.get('code') != 'success': return False, f'save_shop: {r4.get("message","")[:60]}'
    time.sleep(0.5)

    # ❺ 最后提交发布
    for attempt in range(1, MAX_RETRY+2):
        r5 = api(f'{_TK}/save_move_collect_task', {'shopIds':[shop_id],'detailIds':[tk_did]})
        if r5.get('code') == 'success':
            return True, f'{COUNTRIES[site]["currency"]} {target_price:,.0f} {tier}'
        if attempt < MAX_RETRY+1:
            time.sleep(2)
        else:
            if r5.get('message'):
                return False, f'publish({attempt}次): {r5.get("message","")[:60]}'

    return False, 'publish: 重试全部失败'

# ═══════════════════════════════════════════
# 产品列表
# ═══════════════════════════════════════════

# 家居 + 厨房 全部40个
ALL_PRODUCTS = {
    3584763710: ('抽气真空压缩袋', '家居', 3.5),
    3584762266: ('夹缝抽屉式收纳窄柜', '家居', 8.0),
    3584760370: ('家用浴室卫生间置物架', '家居', 8.0),
    3584759088: ('可爱猫咪纸巾袋', '家居', 3.5),
    3584758568: ('美当家无纺布十层帽子收纳', '家居', 3.5),
    3584757763: ('棉被被子收纳袋', '家居', 3.5),
    3584756988: ('保鲜膜收纳盒壁挂式', '家居', 3.5),
    3584756022: ('宿舍床底下收纳箱', '家居', 8.0),
    3584755695: ('跨境可折叠无盖收纳盒', '家居', 3.5),
    3584755289: ('橱柜收纳盒抽屉式', '家居', 3.5),
    3584753904: ('厨房吸盘抹布架', '厨房', 3.5),
    3584752831: ('大容量带灯化妆包', '家居', 5.0),
    3584752366: ('厨房下水槽置物架', '厨房', 5.0),
    3584752115: ('保鲜盒316不锈钢', '厨房', 3.5),
    3584751460: ('带盖衣服收纳箱', '家居', 5.0),
    3584750914: ('花泥定制多个包', '家居', 3.5),
    3584749492: ('环保可降解纸浆盒', '家居', 3.5),
    3584747663: ('跨境清洁抹布', '家居', 3.5),
    3584746535: ('现货加厚侧拉门式磁扣', '家居', 3.5),
    3584745659: ('桌面置物架多层收纳', '家居', 3.5),
    3584742324: ('CEOOL总裁小姐迷你榨汁杯', '厨房', 3.5),
    3584740705: ('通用型0.01微米水龙头', '厨房', 3.5),
    3584740425: ('鸿俊达纯钛筷子', '厨房', 3.5),
    3584737391: ('微波炉可加热玻璃饭盒', '厨房', 3.5),
    3584733256: ('铝箔保温膜餐桌', '厨房', 3.5),
    3584732170: ('316不锈钢保鲜盒', '厨房', 3.5),
    3584731868: ('电动打蒜机充电款', '厨房', 3.5),
    3584730631: ('304印尼不锈钢餐盒', '厨房', 3.5),
    3584727336: ('跨境一体硅胶厨具', '厨房', 5.0),
    3584725982: ('米桶家用2025新款', '厨房', 3.5),
    3584722199: ('批发二合一体喷倒油壶', '厨房', 3.5),
    3584720950: ('专利现货不倒翁削皮刀', '厨房', 3.5),
    3584719270: ('现货真空压缩袋立体', '厨房', 3.5),
    3584699797: ('硅胶饭勺耐高温', '厨房', 3.5),
    3584697350: ('塑料安扣储物罐', '厨房', 3.5),
    3584696985: ('塑料安扣储物罐2', '厨房', 3.5),
    3584687391: ('跨境新款厨房碗碟架', '厨房', 8.0),
    3584685661: ('保鲜盒食品级PP', '厨房', 3.5),
    3584678137: ('全自动真空封口机', '厨房', 3.5),
    3584671227: ('一次性保鲜袋食品级', '厨房', 3.5),
}

# ═══════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description='妙手发布 v3.0')
    parser.add_argument('--force', action='store_true', help='跳过已发布检查，强制发布')
    parser.add_argument('--products', type=str, default='all',
                        help='产品范围: all/home/kitchen 或逗号分隔ID列表')
    args = parser.parse_args()

    print("=" * 55)
    print("📦 妙手发布 v3.0（最终优化版）")
    print("   去中文图 + 自动翻页 + 5国语 + 已发布检查")
    print("=" * 55)

    # 筛选产品
    if args.products == 'kitchen':
        products = {k:v for k,v in ALL_PRODUCTS.items() if v[1] == '厨房'}
    elif args.products == 'home':
        products = {k:v for k,v in ALL_PRODUCTS.items() if v[1] == '家居'}
    elif args.products != 'all':
        ids = [int(x.strip()) for x in args.products.split(',') if x.strip().isdigit()]
        products = {k:ALL_PRODUCTS[k] for k in ids if k in ALL_PRODUCTS}
    else:
        products = ALL_PRODUCTS
    print(f"  📦 待处理: {len(products)}个产品 ({args.products})")

    # 启动图片服务
    print("\n🔌 启动图片服务...")
    start_http()
    base_url = start_tunnel()
    print(f"  ✅ tunnel就绪")

    # 全量搜索TK采集箱
    print("\n🔍 搜索TK采集箱（自动翻页）...")
    tk_index = search_tk_all()

    results = []
    for did, (name, category, freight) in products.items():
        base_cny, has_stock, total_stock, sku_count = get_base_price_and_stock(did)
        if not base_cny:
            results.append((did, name, '—', '⏭️', '无拿货价'))
            print(f'\n⏭️ {name}: 无拿货价')
            continue
        if not has_stock:
            results.append((did, name, '—', '⏭️', '库存0'))
            print(f'\n⏭️ {name}: 库存0')
            continue
        print(f'\n📍 {name} | ¥{base_cny}+运费¥{freight} | 库存{total_stock}({sku_count}SKU) | {category}')

        tk_did = tk_index.get(str(did))
        if not tk_did:
            results.append((did, name, '—', '⏭️', 'TK采集箱未找到'))
            print(f'  ⏭️ TK采集箱未找到')
            continue

        target_shops = SHOP_MAP[category]
        for site in SITE_ORDER:
            shop_id = target_shops.get(site)
            if not shop_id: continue
            # 已发布检查
            if not args.force and is_already_published(tk_did, shop_id):
                results.append((did, name, f'{site}:{shop_id}', '⏭️', '已存在'))
                print(f'  ⏭️ {site}:{shop_id} → 已发布，跳过')
                continue
            # 认领+发布
            ok, msg = False, ''
            for attempt in range(1, MAX_RETRY+2):
                if attempt > 1: time.sleep(2)
                claim_to_shop(tk_did, shop_id)
                time.sleep(0.3)
                ok, msg = publish_one(tk_did, shop_id, site, did, name, base_cny, freight, base_url)
                if ok: break
                time.sleep(0.5)
            emoji = '✅' if ok else '❌'
            print(f'    {emoji} {site}:{shop_id} {msg}')
            results.append((did, name, f'{site}:{shop_id}', emoji, msg))
            time.sleep(1)

    # 汇总
    stats = {'✅': 0, '❌': 0, '⏭️': 0}
    for r in results:
        stats[r[3]] = stats.get(r[3], 0) + 1
    print(f'\n{"="*55}')
    print(f'📊 发布汇总 ✅{stats.get("✅",0)} ❌{stats.get("❌",0)} ⏭️{stats.get("⏭️",0)}')
    fails = [r for r in results if r[3] == '❌']
    if fails:
        print(f'\n❌ 失败 {len(fails)}项:')
        for r in fails:
            print(f'  ❌ {r[1]} → {r[2]}: {r[4][:60]}')

if __name__ == '__main__':
    try:
        main()
    finally:
        cleanup()
