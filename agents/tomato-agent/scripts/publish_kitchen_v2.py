#!/usr/bin/env python3
"""
🍳 厨房品发布 v2 — 去中文图 + 混合定价 + 5国语 + 自动翻页 + 跳过已发布检查
"""
import hashlib, hmac, json, requests, time, sys, os, subprocess, atexit, signal, threading, re

# ── 配置 ──
CLEAN_IMG_DIR = os.path.expanduser("~/Desktop/40SKU产品图_去中文/")
HTTP_PORT = 19765
tunnel_proc = http_proc = None
sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/agents/tomato-agent/scripts'))
from pricing_v4 import calc_price, get_profit_tier, COUNTRIES

CONFIG = {
    'key': 'ak_680398a828ce43de832d342c8dcc89ef',
    'secret': '325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493',
    'base': 'https://openapi-erp.91miaoshou.com'
}
_COM = '/open/v1/product/common_collect_box/common_collect_box'
_TK = '/open/v1/product/collect_box/tiktok/collect_box'

# ── 厨房产品 ──
SITE_MAP = {'TH': 15470949, 'MY': 15471582, 'VN': 15470863, 'SG': 15470918}
SITE_ORDER = ['TH', 'MY', 'VN', 'SG']

PRODUCTS = [
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

# 5国语
COPY_FILE = "/tmp/kitchen_5lang_copy.json"
LOCAL_COPY = {}
if os.path.exists(COPY_FILE):
    with open(COPY_FILE) as f: LOCAL_COPY = json.load(f)

# ── 服务 ──
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
    global tunnel_proc
    url_found = [None]
    def reader(stream):
        for line in iter(stream.readline, ''):
            ls = line.strip()[:100]
            print(f"    [{ls}]")
            m = re.search(r'https://[^\s]+serveousercontent\.com', line)
            if m and not url_found[0]: url_found[0] = m.group(0)+'/'
        stream.close()
    tunnel_proc = subprocess.Popen(
        ['ssh','-o','StrictHostKeyChecking=no','-R',f'80:localhost:{HTTP_PORT}','serveo.net'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    t = threading.Thread(target=reader, args=(tunnel_proc.stdout,), daemon=True); t.start()
    for _ in range(30):
        if url_found[0]:
            print(f'  🔗 tunnel → {url_found[0]}'); return url_found[0]
        if tunnel_proc.poll() is not None: break
        time.sleep(1)
    raise RuntimeError("❌ tunnel启动失败")

def cleanup():
    for p in [tunnel_proc, http_proc]:
        if p:
            try: p.terminate()
            except: pass
    subprocess.run("pkill -f 'serveo.net' 2>/dev/null", shell=True)
    subprocess.run("pkill -f 'http.server.*19765' 2>/dev/null", shell=True)
atexit.register(cleanup)

def get_clean_urls(url, seq):
    urls = []
    if not os.path.isdir(CLEAN_IMG_DIR): return urls
    for f in sorted(os.listdir(CLEAN_IMG_DIR)):
        if (f.startswith(f"{seq:02d}_") or f.startswith(f"{seq}_")) and f.endswith('.jpg'):
            urls.append(url + f)
    return urls

# ── API ──
def api(path, body):
    ts = str(int(time.time()))
    body_s = json.dumps(body, separators=(',',':'))
    raw = CONFIG['secret'] + path + ts + CONFIG['key'] + body_s + CONFIG['secret']
    sign = hmac.new(CONFIG['secret'].encode(), raw.encode(), hashlib.sha256).hexdigest()
    return requests.post(CONFIG['base'] + path,
        headers={'x-app-key':CONFIG['key'],'x-timestamp':ts,'x-sign':sign,'Content-Type':'application/json'},
        data=body_s, timeout=15).json()

def search_tk_all():
    """全量搜索TK采集箱，返回 {common_id: tk_id}"""
    result = {}
    for page in range(1, 101):  # 最多100页
        r = api(f'{_TK}/search_collect_box_detail_list', {'pageNo': page, 'pageSize': 50})
        items = r.get('data',{}).get('detailList',[]) or r.get('data',{}).get('list',[])
        if not items: break
        for item in items:
            result[str(item.get('commonCollectBoxDetailId',''))] = item.get('collectBoxDetailId')
    print(f"  📋 TK采集箱搜索完成: {len(result)}项 ({page-1}页)")
    return result

# ── 类目映射（固定规则） ──
def infer_cid(name):
    n = name.lower()
    if any(k in n for k in ['保鲜','饭盒','密封','盒','米桶','储物罐']): return '600029'
    if any(k in n for k in ['筷子','锅铲','厨具','勺']): return '600030'
    if any(k in n for k in ['榨汁','封口','打蒜','机']): return '600031'
    if any(k in n for k in ['水龙头','过滤']): return '600032'
    if any(k in n for k in ['收纳','置物','架','整理','挂','碗碟']): return '600001'
    if any(k in n for k in ['压缩','袋','真空']): return '600002'
    return None

# ── 发布单个产品到单个站点 ──
def publish_one(tk_did, shop_id, site, did, name, base_cny, freight, seq, base_url):
    target_price = calc_price(site, base_cny, freight)
    tier = get_profit_tier(site, base_cny, freight)
    print(f"  💰 ¥{base_cny}+¥{freight} → {COUNTRIES[site]['symbol']}{target_price:,.0f} ({tier})")

    # ❶ 认领到店铺
    api(f'{_TK}/claim_to_shop', {'shopIds':[shop_id],'detailIds':[tk_did]})
    time.sleep(0.3)

    # ❷ 获取站点信息 → 替换图片/标题/类目
    r = api(f'{_TK}/get_site_collect_item_info', {'detailId': tk_did, 'site': site})
    if r.get('code') != 'success': return False, f'get_site: {r.get("message")}'
    info = r['data']['siteCollectItemInfo']
    oss = r['data']['ossMd5']

    # 去中文图
    clean_urls = get_clean_urls(base_url, seq)
    if clean_urls:
        info['imgUrls'] = clean_urls[:15]
        print(f"    🖼️ 去中文图 {len(clean_urls)}张")
    else:
        imgs = info.get('imgUrls',[])
        if len(imgs) > 15: info['imgUrls'] = imgs[:15]

    # 5国语标题+描述（无copy时自动生成长标题）
    copy = LOCAL_COPY.get(str(did),{}).get('sites',{}).get(site,{})
    if copy.get('title'):
        info['title'] = copy['title']
        print(f"    📝 {site}标题: {copy['title'][:40]}")
    else:
        # 自动生成长标题：中文品名+品类关键词
        base_name = name.replace('批发','').strip()
        extras = {'TH':'คุณภาพดี ใช้งานสะดวก ของใช้ในครัว','MY':'Berkualiti Mudah Diguna Peralatan Dapur','VN':'Chất lượng Tiện dụng Dụng cụ nhà bếp','SG':'Quality Convenient Kitchen Supplies'}
        auto_title = f"{base_name} {extras.get(site,'')}"
        info['title'] = auto_title[:120]
        print(f"    📝 {site}自生成标题: {info['title'][:40]}")
    if copy.get('description'):
        info['notesText'] = info.get('notesText','') + '\n' + copy['description']
        info['detail'] = copy['description']

    # 截断notes: 最多保留5张图片（避免'产品描述图片超过30张'）
    notes = info.get('notes', '')
    if notes:
        import re
        img_tags = re.findall(r'<img[^>]+>', notes, re.I)
        if len(img_tags) > 5:
            count = [0]
            def replacer(m):
                count[0] += 1
                return m.group(0) if count[0] <= 5 else ''
            info['notes'] = re.sub(r'<img[^>]+>', replacer, notes, flags=re.I)
            print(f"    📝 notes图片截断: {len(img_tags)}→5张")

    # 类目（SmartKitchen统一用600060）
    if not info.get('cid'):
        info['cid'] = '600060'

    info.setdefault('weight', 0.05)
    # 包装尺寸：妙手要求≥1，0或None都设默认值
    if not info.get('packageLength') or info['packageLength'] < 1: info['packageLength'] = 15
    if not info.get('packageWidth') or info['packageWidth'] < 1: info['packageWidth'] = 10
    if not info.get('packageHeight') or info['packageHeight'] < 1: info['packageHeight'] = 2
    info['deliveryOptionSetType'] = 'default'
    info['sizeChartType'] = ''

    # ❸ 保存站点信息
    r2 = api(f'{_TK}/save_site_collect_item_info', {'ossMd5':oss,'site':site,'detailId':tk_did,'siteCollectItemInfo':info})
    if r2.get('code') != 'success': return False, f'save_site: {r2.get("message","")[:60]}'
    time.sleep(0.5)

    # ❹ 获取店铺信息 → 设价
    r3 = api(f'{_TK}/get_shop_collect_item_info', {'detailId':tk_did,'shopId':shop_id})
    if r3.get('code') != 'success': return False, f'get_shop: {r3.get("message")}'
    shop_info = r3['data']['shopCollectItemInfo']
    shop_oss = r3['data']['ossMd5']
    sku_map = shop_info.get('skuMap',{})
    if isinstance(sku_map, dict):
        filtered = {}
        for k, v in sku_map.items():
            v['priceIncludeVat'] = target_price
            v['price'] = round(target_price / 1.1, 2)
            stock = int(v.get('stock',0) or 0)
            if stock > 99999: v['stock'] = 99999
            filtered[k] = v
        sku_map.clear(); sku_map.update(filtered)
    shop_info['deliveryOptionSetType'] = 'default'
    shop_info['sizeChartType'] = ''
    # 包装尺寸（shop端也需要）
    if not shop_info.get('packageLength') or shop_info['packageLength'] < 1: shop_info['packageLength'] = 15
    if not shop_info.get('packageWidth') or shop_info['packageWidth'] < 1: shop_info['packageWidth'] = 10
    if not shop_info.get('packageHeight') or shop_info['packageHeight'] < 1: shop_info['packageHeight'] = 2
    shop_info.setdefault('weight', 0.05)

    r4 = api(f'{_TK}/save_shop_collect_item_info', {'ossMd5':shop_oss,'detailId':tk_did,'shopId':shop_id,'shopCollectItemInfo':shop_info})
    if r4.get('code') != 'success': return False, f'save_shop: {r4.get("message","")[:60]}'
    time.sleep(0.5)

    # ❺ 最后提交
    r5 = api(f'{_TK}/save_move_collect_task', {'shopIds':[shop_id],'detailIds':[tk_did]})
    if r5.get('code') != 'success': return False, f'publish: {r5.get("message","")[:60]}'
    return True, f'{COUNTRIES[site]["currency"]} {target_price:,.0f} {tier}'

# ── 主流程 ──
def main():
    print("=" * 55)
    print("🍳 厨房品发布 v2")
    print("   3大修复: 全量翻页搜索 + 跳过已发布检查 + 中文类目")
    print("=" * 55)

    # 起服务
    print("\n🔌 启动图片服务...")
    start_http()
    base_url = start_tunnel()
    print(f"  ✅ tunnel就绪")

    # 全量搜索TK采集箱
    print("\n🔍 搜索TK采集箱...")
    tk_index = search_tk_all()

    results = []
    for did, name, freight, seq in PRODUCTS:
        # 取拿货价
        r = api(f'{_COM}/get_common_collect_box_detail', {'commonCollectBoxDetailId': did})
        if r.get('code') != 'success':
            print(f'\n❌ {name}: 公共采集箱无此商品'); results.append((name,'—','❌','公共采集箱无')); continue
        detail = r['data'].get('editCommonCollectBoxDetail', r['data'].get('collectDetail', {}))
        base_cny = detail.get('price', 0)
        stock = sum(int(v.get('stock',0) or 0) for v in (detail.get('skuMap',{}) or {}).values()) if isinstance(detail.get('skuMap'), dict) else 0
        if not base_cny or base_cny < 0.1:
            print(f'\n⏭️ {name}: 无拿货价'); results.append((name,'—','⏭️','无价')); continue

        # 查TK采集箱，若不在则从公共采集箱认领到TK
        tk_did = tk_index.get(str(did))
        if not tk_did:
            print(f'\n🔁 {name}: TK采集箱无→尝试从公共采集箱认领...')
            rc = api(f'{_COM}/claimed', {'detailSerialNumberPlatformList': [{'detailId': did, 'platform': 'tiktok', 'serialNumber': 1}]})
            if rc.get('code') == 'success':
                tk_map = rc['data']['platformCollectBoxDetailIdMap']['tiktok']
                tk_did = tk_map.get(str(did))
                if tk_did:
                    print(f'  ✅ 认领成功, TK did: {tk_did}')
                    time.sleep(1)
                    # 刷新tk_index
                    tk_index = search_tk_all()
                else:
                    print(f'  ❌ 认领失败: 未返回TK did'); results.append((name,'—','❌','认领TK失败')); continue
            else:
                print(f'  ❌ 认领失败: {rc.get("message","")[:60]}'); results.append((name,'—','❌',f'认领失败: {rc.get("message","")[:40]}')); continue

        print(f'\n📍 #{seq:02d} {name} | ¥{base_cny}+¥{freight} | 库存{stock}')
        for site in SITE_ORDER:
            shop_id = SITE_MAP[site]
            ok, msg = publish_one(tk_did, shop_id, site, did, name, base_cny, freight, seq, base_url)
            emoji = '✅' if ok else '❌'
            print(f'    {emoji} {site}:{shop_id} {msg}')
            results.append((name, site, emoji, msg))
            time.sleep(1)  # 避免频率限制

    # 汇总
    yes = sum(1 for r in results if r[2] == '✅')
    no = sum(1 for r in results if r[2] == '❌')
    skip = sum(1 for r in results if r[2] == '⏭️')
    print(f'\n{"="*55}')
    print(f'📊 厨房发布完成 ✅{yes} ❌{no} ⏭️{skip}')
    if no > 0:
        print('失败:')
        for r in results:
            if r[2] == '❌': print(f'  ❌ {r[0]} → {r[1]}: {r[3][:60]}')

if __name__ == '__main__':
    try:
        main()
    finally:
        cleanup()
