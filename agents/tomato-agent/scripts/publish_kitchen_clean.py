#!/usr/bin/env python3
"""
🍳 厨房24品 全量重上架 — 去中文图 + 混合定价 + 5国语言详情
天赐 2026-05-15 17:48 指示：厨房品全删了要重上
"""
import hashlib, hmac, json, requests, time, sys, os, subprocess, atexit, signal

# ═══════════════════════════════════════════════
# 0. 配置
# ═══════════════════════════════════════════════

CLEAN_IMG_DIR = os.path.expanduser("~/Desktop/40SKU产品图_去中文/")
HTTP_PORT = 19765
ngrok_proc = http_proc = None

sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/agents/tomato-agent/scripts'))
from pricing_v4 import calc_price, get_profit_tier, COUNTRIES, DOMESTIC_FREIGHT

CONFIG = {
    'key': 'ak_680398a828ce43de832d342c8dcc89ef',
    'secret': '325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493',
    'base': 'https://openapi-erp.91miaoshou.com'
}
_COM = '/open/v1/product/common_collect_box/common_collect_box'
_TK = '/open/v1/product/collect_box/tiktok/collect_box'

# ═══════════════════════════════════════════════
# 1. 厨房产品清单 + 5国语言 + 图片序号
# ═══════════════════════════════════════════════

SITE_MAP = {'TH': 15470949, 'MY': 15471582, 'VN': 15470863, 'SG': 15470918}
SITE_ORDER = ['TH', 'MY', 'VN', 'SG']

PRODUCTS = [
    # (did, 短名, 运费, 序号)
    (3584753904, '厨房吸盘抹布架', 3.5, 11),
    (3584752366, '厨房下水槽置物架', 5.0, 13),
    (3584752115, '保鲜盒316不锈钢', 3.5, 14),
    (3584742324, 'CEOOL迷你榨汁杯', 3.5, 21),
    (3584740705, '通用型0.01微米水龙头', 3.5, 22),
    (3584740425, '鸿俊达纯钛筷子', 3.5, 23),
    (3584737391, '微波炉可加热玻璃饭盒', 3.5, 24),
    (3584733256, '铝箔保温膜餐桌', 3.5, 25),
    (3584732170, '316不锈钢保鲜盒', 3.5, 26),
    (3584731868, '电动打蒜机充电款', 3.5, 27),
    (3584730631, '304印尼不锈钢餐盒', 3.5, 28),
    (3584727336, '跨境一体硅胶厨具', 5.0, 29),
    (3584725982, '米桶家用2025新款', 3.5, 30),
    (3584722199, '批发二合一体喷倒油壶', 3.5, 31),
    (3584720950, '专利现货不倒翁削皮刀', 3.5, 32),
    (3584719270, '现货真空压缩袋立体', 3.5, 33),
    (3584699797, '硅胶饭勺耐高温', 3.5, 34),
    (3584697350, '塑料安扣储物罐', 3.5, 35),
    (3584696985, '塑料安扣储物罐2', 3.5, 36),
    (3584687391, '跨境新款厨房碗碟架', 8.0, 37),
    (3584685661, '保鲜盒食品级PP', 3.5, 38),
    (3584678137, '全自动真空封口机', 3.5, 39),
    (3584671227, '一次性保鲜袋食品级', 3.5, 40),
]

# 装入5国语文案
COPY_FILE = "/tmp/kitchen_5lang_copy.json"
LOCAL_COPY = {}
if os.path.exists(COPY_FILE):
    with open(COPY_FILE) as f:
        LOCAL_COPY = json.load(f)
    print(f"  📖 已加载 {len(LOCAL_COPY)} 份5国语详情")

MAX_RETRY = 2

# ═══════════════════════════════════════════════
# 2. ngrok + HTTP 服务
# ═══════════════════════════════════════════════

def start_http():
    global http_proc
    http_proc = subprocess.Popen(["python3", "-m", "http.server", str(HTTP_PORT),
        "--directory", CLEAN_IMG_DIR, "--bind", "127.0.0.1"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    # 验证HTTP可用
    for _ in range(5):
        try:
            r = requests.get(f"http://127.0.0.1:{HTTP_PORT}/", timeout=3)
            if r.status_code == 200:
                print(f"  📂 HTTP ✅ http://127.0.0.1:{HTTP_PORT}")
                return
        except: pass
        time.sleep(1)
    raise RuntimeError("❌ HTTP服务启动失败")

def start_tunnel():
    """用serveo.net代替ngrok（零认证）"""
    global ngrok_proc
    import threading, re
    url_found = [None]
    
    def reader(stream, url_found):
        for line in iter(stream.readline, ''):
            line_s = line.strip()[:100]
            print(f'    [{line_s}]')
            m = re.search(r'https://[^\s]+serveousercontent\.com', line)
            if m and not url_found[0]:
                url_found[0] = m.group(0) + '/'
        stream.close()
    
    cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ServerAliveInterval=30',
           '-R', f'80:localhost:{HTTP_PORT}', 'serveo.net']
    ngrok_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, bufsize=1)
    
    t = threading.Thread(target=reader, args=(ngrok_proc.stdout, url_found), daemon=True)
    t.start()
    
    for _ in range(20):
        if url_found[0]:
            print(f'  🔗 tunnel → {url_found[0]}')
            return url_found[0]
        if ngrok_proc.poll() is not None:
            break
        time.sleep(1)
    raise RuntimeError("❌ SSH隧道启动失败")

def cleanup():
    for p in [ngrok_proc, http_proc]:
        if p:
            try: p.terminate()
            except: pass
    subprocess.run("pkill -f 'serveo.net' 2>/dev/null", shell=True)
    subprocess.run("pkill -f 'http.server.*19765' 2>/dev/null", shell=True)

atexit.register(cleanup)
signal.signal(signal.SIGTERM, lambda *_: cleanup())

def get_clean_urls(base_url, seq):
    """获取去中文图的ngrok URL列表"""
    urls = []
    if not os.path.isdir(CLEAN_IMG_DIR): return urls
    prefix = f"{seq:02d}_"
    for f in sorted(os.listdir(CLEAN_IMG_DIR)):
        if f.startswith(prefix) and f.endswith('.jpg'):
            urls.append(base_url + f)
    # fallback: 单数字
    if not urls:
        p2 = f"{seq}_"
        for f in sorted(os.listdir(CLEAN_IMG_DIR)):
            if f.startswith(p2) and f.endswith('.jpg'):
                urls.append(base_url + f)
    return urls

# ═══════════════════════════════════════════════
# 3. 妙手API
# ═══════════════════════════════════════════════

def api(path, body):
    ts = str(int(time.time()))
    body_s = json.dumps(body, separators=(',',':'))
    raw = CONFIG['secret'] + path + ts + CONFIG['key'] + body_s + CONFIG['secret']
    sign = hmac.new(CONFIG['secret'].encode(), raw.encode(), hashlib.sha256).hexdigest()
    h = {'x-app-key': CONFIG['key'], 'x-timestamp': ts, 'x-sign': sign, 'Content-Type': 'application/json'}
    try:
        return requests.post(CONFIG['base'] + path, headers=h, data=body_s, timeout=15).json()
    except Exception as e:
        return {'code': 'error', 'message': str(e)}

def get_price_stock(did):
    r = api(f'{_COM}/get_common_collect_box_detail', {'commonCollectBoxDetailId': did})
    if r.get('code') != 'success': return None, False, 0
    d = r['data']
    detail = d.get('editCommonCollectBoxDetail', d.get('collectDetail', {}))
    sku_map = detail.get('skuMap', {})
    if isinstance(sku_map, list):
        skus = [v for v in sku_map if isinstance(v, dict) and v.get('price', 0) > 0]
    else:
        skus = [v for v in sku_map.values() if isinstance(v, dict) and v.get('price', 0) > 0]
    prices = [v.get('price', 0) for v in skus]
    if not prices: return None, False, 0
    base = min(prices)
    if base < 0.5:
        valid = [p for p in prices if p > 0.5]
        if valid: base = min(valid)
    stocks = sum(int(v.get('stock', 0) or 0) for v in skus)
    return round(base, 2), stocks > 0, stocks

def get_tk_did(common_id):
    # 搜索所有页（TK采集箱可能超过50项）
    for page in range(1, 10):
        r = api(f'{_TK}/search_collect_box_detail_list', {'pageNo': page, 'pageSize': 50})
        items = r.get('data', {}).get('detailList', []) or r.get('data', {}).get('list', [])
        if not items: break
        for item in items:
            if str(item.get('commonCollectBoxDetailId', '')) == str(common_id):
                return item.get('collectBoxDetailId')
    return None

def claim(did, shop_id):
    r = api(f'{_TK}/claim_to_shop', {'shopIds': [shop_id], 'detailIds': [did]})
    return r.get('code') == 'success'

def publish(did, name, tk_did, shop_id, site, base_cny, freight, seq, base_url):
    """核心：去中文图 + 混合定价 + 5国语"""
    
    # ── 新定价 ──
    target_price = calc_price(site, base_cny, freight)
    tier = get_profit_tier(site, base_cny, freight)
    print(f'    💰 ¥{base_cny}+¥{freight} → {COUNTRIES[site]["symbol"]}{target_price:,.0f} ({tier})')

    # ── 获取站点信息 ──
    r1 = api(f'{_TK}/get_site_collect_item_info', {'detailId': tk_did, 'site': site})
    if r1.get('code') != 'success': return False, f'get_site: {r1.get("message")}'
    info = r1['data']['siteCollectItemInfo']
    oss = r1['data']['ossMd5']

    # ── 替换图片为去中文图 ──
    clean_urls = get_clean_urls(base_url, seq)
    if clean_urls:
        info['imgUrls'] = clean_urls[:15]
        print(f'    🖼️ 去中文图 {len(clean_urls)}张')
    else:
        imgs = info.get('imgUrls', [])
        if imgs and len(imgs) > 15: info['imgUrls'] = imgs[:15]

    # ── 替换标题/描述为本地语言 ──
    copy = LOCAL_COPY.get(str(did), {})
    site_copy = copy.get('sites', {}).get(site, {})
    if site_copy.get('title'):
        info['title'] = site_copy['title']
        print(f'    📝 {site}标题: {site_copy["title"][:40]}')
    if site_copy.get('description'):
        info['notesText'] = info.get('notesText', '') + '\n' + site_copy['description']
        info['detail'] = site_copy['description']

    # ── 设置类目（厨房站点通用） ──
    if not info.get('cid'):
        n_lower = name.lower()
        if any(k in n_lower for k in ['保鲜','饭盒','密封','盒','米桶','储物罐']): info['cid'] = '600029'
        elif any(k in n_lower for k in ['筷子','锅铲','厨具','勺']): info['cid'] = '600030'
        elif any(k in n_lower for k in ['榨汁','封口','打蒜','机']): info['cid'] = '600031'
        elif any(k in n_lower for k in ['水龙头','过滤']): info['cid'] = '600032'
        elif any(k in n_lower for k in ['收纳','置物','架','整理','挂','碗碟']): info['cid'] = '600001'
        elif any(k in n_lower for k in ['压缩','袋','真空']): info['cid'] = '600002'
    info['weight'] = 0.05; info['packageLength'] = 15; info['packageWidth'] = 10; info['packageHeight'] = 2
    info['deliveryOptionSetType'] = 'default'; info['sizeChartType'] = ''

    # ── 保存站点信息 ──
    r2 = api(f'{_TK}/save_site_collect_item_info', {'ossMd5': oss, 'site': site, 'detailId': tk_did, 'siteCollectItemInfo': info})
    if r2.get('code') != 'success': return False, f'save_site: {r2.get("message","")[:60]}'
    time.sleep(0.5)

    # ── 获取店铺信息 → 设价格 → 保存 ──
    r3 = api(f'{_TK}/get_shop_collect_item_info', {'detailId': tk_did, 'shopId': shop_id})
    if r3.get('code') != 'success': return False, f'get_shop: {r3.get("message")}'
    shop_info = r3['data']['shopCollectItemInfo']
    shop_oss = r3['data']['ossMd5']
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
        sku_map.clear(); sku_map.update(filtered)
    shop_info['deliveryOptionSetType'] = 'default'; shop_info['sizeChartType'] = ''
    if not shop_info.get('weight'): shop_info['weight'] = 0.05; shop_info['packageLength'] = 15; shop_info['packageWidth'] = 10; shop_info['packageHeight'] = 2

    r4 = api(f'{_TK}/save_shop_collect_item_info', {'ossMd5': shop_oss, 'detailId': tk_did, 'shopId': shop_id, 'shopCollectItemInfo': shop_info})
    if r4.get('code') != 'success': return False, f'save_shop: {r4.get("message","")[:60]}'
    time.sleep(0.5)

    # ── 最后提交 --->
    r5 = api(f'{_TK}/save_move_collect_task', {'shopIds': [shop_id], 'detailIds': [tk_did]})
    if r5.get('code') != 'success': return False, f'publish: {r5.get("message","")[:60]}'
    return True, f'{COUNTRIES[site]["currency"]} {target_price:,.0f} 去中图+{tier}'

# ═══════════════════════════════════════════════
# 4. 主流程
# ═══════════════════════════════════════════════

def main():
    print("=" * 55)
    print("🍳 厨房24品 全量重上架")
    print("   规则: 混合定价(35%/20%) | 去中文图 | 5国语详情")
    print("   站点: TH→SmartKitchen / MY / VN / SG")
    print("=" * 55)

    # 起服务
    print("\n🔌 启动图片服务...")
    start_http(); base_url = start_tunnel()
    print(f"  ✅ ngrok → {base_url}")

    results = []
    for did, name, freight, seq in PRODUCTS:
        base_cny, has_stock, stock_cnt = get_price_stock(did)
        if not base_cny:
            results.append((did, name, '—', '❌', '无拿货价'))
            print(f'\n❌ {name} ({did}): 无拿货价'); continue
        if not has_stock:
            results.append((did, name, '—', '⏭️', '库存0'))
            print(f'\n⏭️ {name}: 库存0'); continue
        print(f'\n📍 #{seq:02d} {name} | ¥{base_cny}+¥{freight} | 库存{stock_cnt}')

        tk_did = get_tk_did(did)
        if not tk_did:
            results.append((did, name, '—', '❌', 'TK采集箱无'))
            print(f'  ❌ TK采集箱找不到'); continue

        for site in SITE_ORDER:
            shop_id = SITE_MAP[site]
            ok, msg = False, ''
            for attempt in range(1, MAX_RETRY + 2):
                if attempt > 1: time.sleep(2)
                claim(tk_did, shop_id); time.sleep(0.3)
                ok, msg = publish(did, name, tk_did, shop_id, site, base_cny, freight, seq, base_url)
                if ok: break
                time.sleep(0.5)
            emoji = '✅' if ok else '❌'
            print(f'    {emoji} {site}:{shop_id} {msg}')
            results.append((did, name, site, emoji, msg))
        time.sleep(1)

    # 汇总
    yes = sum(1 for r in results if r[3] == '✅')
    no = sum(1 for r in results if r[3] == '❌')
    print(f'\n{"="*55}')
    print(f'📊 厨房24品上架完成 ✅{yes} ❌{no}')
    print(f'{"="*55}')
    if no > 0:
        print('失败:')
        for r in results:
            if r[3] == '❌': print(f'  ❌ {r[1]} → {r[2]}: {r[4][:60]}')

if __name__ == '__main__':
    try:
        main()
    finally:
        cleanup()
