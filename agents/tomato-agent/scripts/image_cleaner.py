#!/usr/bin/env python3
"""
图片去中文化全流程 v1.0
1. 从妙手API提取5品的1688源链接和图片URL
2. 下载图片到本地
3. 使用easyocr+opencv检测并擦除中文文字
4. 输出清洗后的图片，准备上传回妙手
"""
import hashlib, hmac, json, requests, time, os, sys
import io
from PIL import Image
import cv2
import numpy as np

# ── Config ──
CONFIG = {
    'key': 'ak_680398a828ce43de832d342c8dcc89ef',
    'secret': '325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493',
    'base': 'https://openapi-erp.91miaoshou.com'
}
_COM = '/open/v1/product/common_collect_box/common_collect_box'
_TK = '/open/v1/product/collect_box/tiktok/collect_box'

PRODUCTS = {
    3579185120: '假睫毛',
    3564378971: '化妆刷',
    3514563993: '眉刷',
    3572629730: '不锈钢罐',
    3572629651: '收纳盒',
}

OUTPUT_DIR = os.path.expanduser('~/Desktop/去中文图片')
IMG_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Referer': 'https://detail.1688.com/',
}

# 全局easyocr reader（懒加载）
_reader = None

def api(path, body):
    ts = str(int(time.time()))
    bs = json.dumps(body, separators=(',', ':'))
    raw = CONFIG['secret'] + path + ts + CONFIG['key'] + bs + CONFIG['secret']
    sign = hmac.new(CONFIG['secret'].encode(), raw.encode(), hashlib.sha256).hexdigest()
    h = {'x-app-key': CONFIG['key'], 'x-timestamp': ts, 'x-sign': sign, 'Content-Type': 'application/json'}
    return requests.post(CONFIG['base'] + path, headers=h, data=bs, timeout=15).json()

def get_reader():
    global _reader
    if _reader is None:
        import easyocr
        print("  🔄 加载easyocr中文模型(首次~30秒)...")
        _reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
        print("  ✅ 模型就绪")
    return _reader

def download_img(url, timeout=10):
    """下载图片返回 (pil_image, cv2_bgr)."""
    r = requests.get(url, headers=IMG_HEADERS, timeout=timeout)
    if r.status_code != 200:
        return None, None
    pil = Image.open(io.BytesIO(r.content))
    bgr = cv2.cvtColor(np.array(pil.convert('RGB')), cv2.COLOR_RGB2BGR)
    return pil, bgr

def detect_clean(img_bgr):
    """检测中文并擦除。返回 (cleaned_bgr, chinese_count)."""
    reader = get_reader()
    results = reader.readtext(img_bgr)
    
    chinese_boxes = []
    for bbox, text, conf in results:
        if any('\u4e00' <= c <= '\u9fff' for c in text):
            chinese_boxes.append((bbox, text, conf))
    
    if not chinese_boxes:
        return img_bgr, 0
    
    # 创建mask并擦除
    mask = np.zeros(img_bgr.shape[:2], dtype=np.uint8)
    for bbox, text, conf in chinese_boxes:
        pts = np.array([[int(p[0]), int(p[1])] for p in bbox], np.int32)
        cv2.fillPoly(mask, [pts], 255)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    cleaned = cv2.inpaint(img_bgr, mask, 3, cv2.INPAINT_TELEA)
    return cleaned, len(chinese_boxes)


def process_product(common_id, name):
    """处理单个产品的所有图片."""
    print(f'\n{"="*60}')
    print(f'📍 {name} (ID:{common_id})')
    
    # 1. 获取产品信息
    r = api(f'{_COM}/get_common_collect_box_detail', {'commonCollectBoxDetailId': common_id})
    if r.get('code') != 'success':
        print(f'  ❌ API失败: {r.get("message")}')
        return None
    
    detail = r['data'].get('editCommonCollectBoxDetail', r['data'].get('collectDetail', {}))
    source_list = detail.get('sourceList', [])
    source_url = source_list[0].get('sourceItemUrl', '') if source_list else ''
    source_id = source_list[0].get('sourceItemId', '') if source_list else ''
    
    print(f'  1688: {source_url}')
    print(f'  1688 ID: {source_id}')
    
    # 2. 收集所有图片URL
    all_imgs = []
    img_urls = detail.get('imgUrls', [])
    for u in img_urls:
        all_imgs.append(('主图', u))
    
    # SKU变体图
    color_map = detail.get('colorMap', {})
    for sku_name, sku_data in color_map.items():
        sku_img = sku_data.get('imgUrl') or sku_data.get('imgUrls', [None])[0]
        if sku_img:
            all_imgs.append(('变体图', sku_img))
    
    # 视频
    video_url = detail.get('mainImgVideoUrl') or detail.get('mainImgAppVideoId')
    if video_url:
        all_imgs.append(('视频', video_url))
    
    print(f'  共{len(all_imgs)}个资源 ({len(img_urls)}主图 + {len(color_map)}变体 + {1 if video_url else 0}视频)')
    
    # 3. 下载并清洗
    out_dir = os.path.join(OUTPUT_DIR, name)
    os.makedirs(out_dir, exist_ok=True)
    
    results = {'source_url': source_url, 'source_id': source_id, 'images': []}
    clean_count = 0
    dirty_count = 0
    
    for idx, (img_type, url) in enumerate(all_imgs):
        print(f'  [{idx+1}/{len(all_imgs)}] {img_type}', end=' ')
        
        if img_type == '视频':
            results['images'].append({'type': img_type, 'url': url, 'chinese': 'SKIP_VIDEO'})
            print('⏭️ 视频跳过(需ffmpeg逐帧处理)')
            continue
        
        try:
            pil, bgr = download_img(url)
            if bgr is None:
                results['images'].append({'type': img_type, 'url': url, 'chinese': 'DOWNLOAD_FAIL'})
                print('❌ 下载失败')
                continue
            
            cleaned_bgr, cn_count = detect_clean(bgr)
            
            # 保存
            fname = f'{img_type}_{idx:03d}'
            if cn_count > 0:
                # 保存原图+清洗后
                orig_path = os.path.join(out_dir, f'{fname}_orig.jpg')
                clean_path = os.path.join(out_dir, f'{fname}_clean.jpg')
                cv2.imwrite(orig_path, bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
                cv2.imwrite(clean_path, cleaned_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
                dirty_count += 1
                print(f'⚠️ {cn_count}处中文 → {fname}_clean.jpg')
            else:
                clean_path = os.path.join(out_dir, f'{fname}.jpg')
                cv2.imwrite(clean_path, bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
                clean_count += 1
                print(f'✅ 无中文 → {fname}.jpg')
            
            results['images'].append({
                'type': img_type, 'url': url,
                'chinese_count': cn_count,
                'cleaned_path': clean_path
            })
            time.sleep(0.3)
        except Exception as e:
            results['images'].append({'type': img_type, 'url': url, 'chinese': f'ERROR:{e}'})
            print(f'❌ {e}')
    
    print(f'  📊 {name}: {clean_count}张无需处理 | {dirty_count}张已清洗')
    return results


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_results = {}
    
    for did, name in PRODUCTS.items():
        try:
            result = process_product(did, name)
            if result:
                all_results[name] = result
        except Exception as e:
            print(f'  ❌ {name} 处理失败: {e}')
    
    # 汇总
    print(f'\n{"="*60}')
    print(f'📊 全量汇总')
    total_clean, total_dirty = 0, 0
    for name, r in all_results.items():
        c = sum(1 for img in r['images'] if img.get('chinese_count', 0) == 0)
        d = sum(1 for img in r['images'] if img.get('chinese_count', 0) > 0)
        total_clean += c
        total_dirty += d
        print(f'  {name}: {c}干净 + {d}有中文')
    print(f'\n  总计: {total_clean}干净 + {total_dirty}需清洗')
    print(f'  输出: {OUTPUT_DIR}')
    
    # 保存json报告
    import json as j
    with open(os.path.join(OUTPUT_DIR, 'report.json'), 'w') as f:
        j.dump(all_results, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
