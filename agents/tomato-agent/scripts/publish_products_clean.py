#!/usr/bin/env python3
"""
publish_40_products_clean — 自动替换去中文图再上架
启动时自动起ngrok+HTTP服务暴露去中文图片目录
"""
import hashlib, hmac, json, requests, time, sys, os, subprocess, atexit, signal

# ── 图片去中文服务 ──
CLEAN_IMG_DIR = os.path.expanduser("~/Desktop/40SKU产品图_去中文/")
HTTP_PORT = 19765
ngrok_proc = None
http_proc = None
NGROK_URL_FILE = "/tmp/ngrok_clean_img_url.txt"

# 产品ID→序号映射
PRODUCT_IMAGE_SEQ = {
    3584763710:1,3584762266:2,3584760370:3,3584759088:4,3584758568:5,
    3584757763:6,3584756988:7,3584756022:8,3584755695:9,3584755289:10,
    3584753904:11,3584752831:12,3584752366:13,3584752115:14,3584751460:15,
    3584750914:16,3584749492:17,3584747663:18,3584746535:19,3584745659:20,
    3584742324:21,3584740705:22,3584740425:23,3584737391:24,3584733256:25,
    3584732170:26,3584731868:27,3584730631:28,3584727336:29,3584725982:30,
    3584722199:31,3584720950:32,3584719270:33,3584699797:34,3584697350:35,
    3584696985:36,3584687391:37,3584685661:38,3584678137:39,3584671227:40,
}

# ── Config ──
CONFIG = {
    'key': 'ak_680398a828ce43de832d342c8dcc89ef',
    'secret': '325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493',
    'base': 'https://openapi-erp.91miaoshou.com'
}
_COM = '/open/v1/product/common_collect_box/common_collect_box'
_TK = '/open/v1/product/collect_box/tiktok/collect_box'
SHOP_MAP = {
    '家居': {'TH': 15471357, 'MY': 15471249, 'VN': 15471504, 'SG': 15471552},
    '厨房': {'TH': 15470949, 'MY': 15471582, 'VN': 15470863, 'SG': 15470918},
}
# 定价引自 pricing_v4
import sys as _sys; _sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/agents/tomato-agent/scripts'))
from pricing_v4 import calc_price, get_profit_tier, COUNTRIES

PRODUCTS = {
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

MAX_RETRY = 2

# ═══════════════════════════════════════════════
# 1. NGROK + HTTP 服务管理
# ═══════════════════════════════════════════════

def start_http_server():
    """起Python HTTP服务器托管去中文图"""
    global http_proc
    http_proc = subprocess.Popen(
        ["python3", "-m", "http.server", str(HTTP_PORT), "--directory", CLEAN_IMG_DIR,
         "--bind", "127.0.0.1"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(1)
    print(f"  📂 HTTP 服务 → http://127.0.0.1:{HTTP_PORT}")

def start_ngrok():
    """起ngrok暴露HTTP端口"""
    global ngrok_proc
    # 先杀旧ngrok
    subprocess.run("pkill -f 'ngrok.*19765' 2>/dev/null", shell=True)
    time.sleep(0.5)
    ngrok_proc = subprocess.Popen(
        ["ngrok", "http", str(HTTP_PORT), "--log=stdout"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(3)
    # 获取ngrok公网URL
    for _ in range(10):
        try:
            r = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=3)
            tunnels = r.json().get("tunnels", [])
            for t in tunnels:
                if t.get("public_url", "").startswith("https://"):
                    url = t["public_url"] + "/"
                    print(f"  🔗 ngrok → {url}")
                    with open(NGROK_URL_FILE, "w") as f:
                        f.write(url)
                    return url
        except: pass
        time.sleep(1)
    raise RuntimeError("❌ ngrok启动失败，无法获取公网URL")

def cleanup():
    """清理子进程"""
    global ngrok_proc, http_proc
    for p in [ngrok_proc, http_proc]:
        if p:
            try: p.terminate()
            except: pass
    subprocess.run("pkill -f 'ngrok.*19765' 2>/dev/null", shell=True)
    subprocess.run("pkill -f 'python3.*http.*19765' 2>/dev/null", shell=True)

atexit.register(cleanup)
signal.signal(signal.SIGTERM, lambda *_: cleanup())

def get_clean_img_urls(ngrok_base_url, product_id):
    """
    返回去中文图的ngrok URL列表
    """
    seq = PRODUCT_IMAGE_SEQ.get(product_id)
    if not seq:
        return []
    prefix = f"{seq:02d}_"
    urls = []
    if not os.path.isdir(CLEAN_IMG_DIR):
        return []
    for f in sorted(os.listdir(CLEAN_IMG_DIR)):
        if f.startswith(prefix) and (f.endswith('.jpg') or f.endswith('.png')):
            urls.append(ngrok_base_url + f)
    if not urls:
        # 也试单数字前缀
        prefix2 = f"{seq}_"
        for f in sorted(os.listdir(CLEAN_IMG_DIR)):
            if f.startswith(prefix2) and (f.endswith('.jpg') or f.endswith('.png')):
                urls.append(ngrok_base_url + f)
    return urls

# ═══════════════════════════════════════════════
# 2. 妙手API函数
# ═══════════════════════════════════════════════

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
    if not prices: return None, False, 0, 0
    base = min(prices)
    if base < 0.5:
        valid = [p for p in prices if p > 0.5]
        if valid: base = min(valid)
    stocks = [int(v.get('stock', 0) or 0) for v in skus]
    return round(base, 2), sum(stocks) > 0, sum(stocks), len(skus)

def get_tk_detail_id(common_id):
    r = api(f'{_TK}/search_collect_box_detail_list', {'pageNo': 1, 'pageSize': 50})
    items = r.get('data', {}).get('detailList', []) or r.get('data', {}).get('list', [])
    for item in items:
        if str(item.get('commonCollectBoxDetailId', '')) == str(common_id):
            return item.get('collectBoxDetailId')
    return None

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

def publish_one(did, name, tk_did, shop_id, site, base_cny, freight, ngrok_base, cid=None):
    target_price = calc_price(site, base_cny, freight)
    tier = get_profit_tier(site, base_cny, freight)
    print(f'    💰 拿货¥{base_cny}+运费¥{freight} → {COUNTRIES[site]["symbol"]}{target_price:,.0f} ({tier})')

    r1 = api(f'{_TK}/get_site_collect_item_info', {'detailId': tk_did, 'site': site})
    if r1.get('code') != 'success': return False, f'get_site fail: {r1.get("message")}'
    info = r1['data']['siteCollectItemInfo']
    site_oss = r1['data']['ossMd5']

    # 🔥 核心修复：替换imgUrls为去中文图
    clean_urls = get_clean_img_urls(ngrok_base, did)
    if clean_urls:
        info['imgUrls'] = clean_urls[:15]
        print(f'    🖼️ 替换为去中文图: {len(clean_urls)}张')
    else:
        img_urls = info.get('imgUrls', [])
        if img_urls and len(img_urls) > 15: info['imgUrls'] = img_urls[:15]
        print(f'    ⚠️ 无去中文图, 使用原始图 {len(info.get("imgUrls",[]))}张')

    if not info.get('cid'):
        if cid: info['cid'] = cid
        else:
            title = info.get('title', '').lower()
            if any(k in title for k in ['保鲜','饭盒','密封']): info['cid'] = '600029'
            elif any(k in title for k in ['筷子','锅铲','厨具']): info['cid'] = '600030'
            elif any(k in title for k in ['榨汁','封口','打蒜']): info['cid'] = '600031'
            elif any(k in title for k in ['水龙头','过滤']): info['cid'] = '600032'
            elif any(k in title for k in ['收纳','置物','架']): info['cid'] = '600001'
            elif '压缩袋' in title: info['cid'] = '600002'
    info['weight'] = 0.05; info['packageLength'] = 15; info['packageWidth'] = 10; info['packageHeight'] = 2
    info['deliveryOptionSetType'] = 'default'; info['sizeChartType'] = ''
    if not info.get('title'):
        rc = api(f'{_COM}/get_common_collect_box_detail', {'commonCollectBoxDetailId': did})
        if rc.get('code') == 'success':
            cd = rc['data'].get('editCommonCollectBoxDetail', rc['data'].get('collectDetail', {}))
            info['title'] = cd.get('title', '')

    r2 = api(f'{_TK}/save_site_collect_item_info', {'ossMd5': site_oss, 'site': site, 'detailId': tk_did, 'siteCollectItemInfo': info})
    if r2.get('code') != 'success': return False, f'save_site: {r2.get("message","")[:80]}'
    time.sleep(0.5)

    r3 = api(f'{_TK}/get_shop_collect_item_info', {'detailId': tk_did, 'shopId': shop_id})
    if r3.get('code') != 'success': return False, f'get_shop fail: {r3.get("message")}'
    shop_info = r3['data']['shopCollectItemInfo']
    shop_oss = r3['data']['ossMd5']
    sku_map = shop_info.get('skuMap', {})
    if isinstance(sku_map, dict):
        filtered = {}; skipped = 0
        for k, v in sku_map.items():
            stock = int(v.get('stock', 0) or 0)
            if stock == 0: skipped += 1; continue
            v['priceIncludeVat'] = target_price
            v['price'] = round(target_price / 1.1, 2)
            if stock > 99999: v['stock'] = 99999
            filtered[k] = v
        sku_map.clear(); sku_map.update(filtered)
    shop_info['deliveryOptionSetType'] = 'default'; shop_info['sizeChartType'] = ''
    if not shop_info.get('weight'): shop_info['weight'] = 0.05; shop_info['packageLength'] = 15; shop_info['packageWidth'] = 10; shop_info['packageHeight'] = 2
    r4 = api(f'{_TK}/save_shop_collect_item_info', {'ossMd5': shop_oss, 'detailId': tk_did, 'shopId': shop_id, 'shopCollectItemInfo': shop_info})
    if r4.get('code') != 'success': return False, f'save_shop: {r4.get("message","")[:80]}'
    time.sleep(0.5)
    r5 = api(f'{_TK}/save_move_collect_task', {'shopIds': [shop_id], 'detailIds': [tk_did]})
    if r5.get('code') != 'success': return False, f'publish: {r5.get("message","")[:80]}'
    return True, f'{COUNTRIES[site]["currency"]} {target_price:,.0f}'

def main():
    import glob
    print("=" * 50)
    print("📦 40产品上架 — 去中文图版")
    print("=" * 50)
    
    # 启动HTTP+ngrok
    print("\n🔌 启动图片服务...")
    start_http_server()
    ngrok_base = start_ngrok()
    print(f"  ✅ 图片服务就绪: {ngrok_base}")

    results = []
    for did, (name, category, freight) in PRODUCTS.items():
        base_cny, has_stock, total_stock, sku_count = get_base_price_and_stock(did)
        if not base_cny: results.append((did, name, '—', '❌', '无拿货价')); continue
        if not has_stock: results.append((did, name, '—', '⏭️', f'库存0')); continue
        print(f'\n📍 {name} | ¥{base_cny}+运费¥{freight} | 库存{total_stock}({sku_count}SKU) | {category}')
        tk_did = get_tk_detail_id(did)
        if not tk_did: results.append((did, name, '—', '❌', 'TK采集箱未找到')); continue
        target_shops = SHOP_MAP[category]
        for site, shop_id in target_shops.items():
            if is_already_published(tk_did, shop_id):
                results.append((did, name, f'{site}:{shop_id}', '⏭️', '已存在')); continue
            ok, msg = False, ''
            for attempt in range(1, MAX_RETRY+2):
                if attempt > 1: time.sleep(2)
                claim_to_shop(tk_did, shop_id); time.sleep(0.3)
                ok, msg = publish_one(did, name, tk_did, shop_id, site, base_cny, freight, ngrok_base)
                if ok: break
                time.sleep(0.5)
            status = '✅' if ok else '❌'
            results.append((did, name, f'{site}:{shop_id}', status, msg))
        time.sleep(0.5)

    summaries = {}
    for r in results:
        summaries.setdefault(r[3], []).append(r)
    print(f'\n{"="*50}\n📊 汇总: (共{len(results)}项)')
    for emoji in ['✅', '⏭️', '❌']:
        items = summaries.get(emoji, [])
        if items: print(f'  {emoji} {len(items)}项')

if __name__ == '__main__':
    try:
        main()
    finally:
        cleanup()
