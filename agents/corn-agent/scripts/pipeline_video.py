#!/usr/bin/env python3
"""
🌽 玉米·5国视频剪辑管线 v1.0 — 轻量可靠版
============================================
铁律: 全本地ffmpeg，不调API
BGM: 从BGM库按国家匹配
TTS: Edge TTS + 自然化处理(pitch+rate)
字幕: 大字清晰，位置正确
输出: ~/Desktop/已处理TK视频_v8/

用法:
  python3 pipeline_video.py --input ~/Desktop/源视频/收纳篮.mp4 --product 收纳篮 --category 家居
  python3 pipeline_video.py --input ~/Desktop/源视频/粉底刷.mp4 --product 粉底刷 --category 美妆
  python3 pipeline_video.py --input ~/Desktop/源视频/切丝器.mp4 --product 切丝器 --category 厨房

5国全部处理，输出到已处理TK视频_v8/
"""
import asyncio
import edge_tts
import json
import os
import random
import subprocess
import sys
import argparse
from pathlib import Path

# ====== 配置 ======
VW, VH = 1080, 1920  # 目标分辨率（9:16竖屏）
BGM_DB_PATH = os.path.expanduser('~/Desktop/BGM库/bgm_database.json')
BGM_DIR = os.path.expanduser('~/Desktop/BGM库')
OUT_DIR = os.path.expanduser('~/Desktop/已处理TK视频_v8')
os.makedirs(OUT_DIR, exist_ok=True)

COUNTRIES = ['TH', 'MY', 'VN', 'PH', 'SG', 'CN']

# 6国TTS配音 - 20岁左右本地女生自然语调
TTS_CONFIG = {
    'TH': {'voice': 'th-TH-PremwadeeNeural', 'rate': '+20%', 'pitch': '+15Hz'},
    'MY': {'voice': 'ms-MY-YasminNeural',    'rate': '+18%', 'pitch': '+12Hz'},
    'VN': {'voice': 'vi-VN-HoaiMyNeural',    'rate': '+20%', 'pitch': '+15Hz'},
    'PH': {'voice': 'fil-PH-BlessicaNeural',  'rate': '+15%', 'pitch': '+10Hz'},
    'SG': {'voice': 'en-SG-LunaNeural',       'rate': '+12%', 'pitch': '+10Hz'},
    'CN': {'voice': 'zh-CN-XiaoxiaoNeural',   'rate': '+15%', 'pitch': '+10Hz'},
}

# 默认5国文案模板（可被--script覆盖）
DEFAULT_SCRIPTS = {
    'TH': ['ดูสิคะ ผลิตภัณฑ์นี้ใช้งานง่ายมาก', 'ออกแบบมาให้พอดีมือ จับถนัด', 'คุณภาพดี คุ้มค่าทุกบาท', 'ใช้แล้วชีวิตง่ายขึ้นเยอะเลย', 'ลองใช้ดูนะคะ รับรองไม่ผิดหวัง'],
    'MY': ['Tengok ni, produk ni senang guna sangat', 'Reka bentuk ergonomik, selesa dipegang', 'Kualiti tinggi, berbaloi dengan harga', 'Memang memudahkan rutin harian anda', 'Cubalah, mesti puas hati'],
    'VN': ['Nhìn này, sản phẩm này rất dễ sử dụng', 'Thiết kế vừa tay, cầm rất thoải mái', 'Chất lượng cao, đáng giá từng đồng', 'Dùng xong cuộc sống dễ dàng hơn hẳn', 'Hãy thử ngay, bạn sẽ thích'],
    'PH': ['Tingnan mo, ang dali gamitin nito', 'Ergonomic design, komportable hawakan', 'De-kalidad, worth it sa presyo', 'Gagaan ang daily routine mo dito', 'Subukan mo, siguradong magugustuhan mo'],
    'SG': ['Check this out, super easy to use', 'Ergonomic grip, feels so natural', 'Premium quality, totally worth it', 'Makes your routine so much smoother', 'Try it, you won\'t be disappointed'],
    'CN': ['看这个，产品特别好用', '人体工学设计，握着超舒服', '品质高，超值不亏', '用了之后日常轻松好多', '试试看吧，一定不会失望'],
}

# 字幕位置（从底部算起）
SUB_Y_OFFSET = 80   # 底部往上80px（避免遮挡人物下巴）
SUB_FONT_SIZE = 58
SUB_LINE_MAX_CHARS = 14  # 每行最大字符数，超了就折行

# ====== 工具函数 ======

def run_cmd(cmd, timeout=120):
    """安全执行shell命令"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r
    except subprocess.TimeoutExpired:
        print(f'  ⚠️ 命令超时: {" ".join(cmd[:3])}')
        return type('R', (), {'returncode': -1, 'stdout': '', 'stderr': ''})()


def get_duration(path):
    """获取音视频时长"""
    if not path or not os.path.exists(path) or os.path.getsize(path) < 200:
        return 2.0
    r = run_cmd(['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                 '-of', 'csv=p=0', path], 5)
    try:
        return float(r.stdout.strip())
    except:
        return 2.0


def load_bgm_db():
    """加载BGM库，按国家分组"""
    if not os.path.exists(BGM_DB_PATH):
        print('  ⚠️ BGM数据库不存在')
        return {}
    try:
        with open(BGM_DB_PATH) as f:
            data = json.load(f)
    except:
        return {}
    
    bgms = data.get('bgm', [])
    by_country = {}
    for b in bgms:
        c = b.get('country', '?')
        if c not in by_country:
            by_country[c] = []
        by_country[c].append(b)
    return by_country


def pick_matching_mp3(country):
    """
    从BGM库中按国家选一首BGM。
    先尝试从数据库按国家匹配，再从实际mp3文件里找。
    """
    all_mp3 = [f for f in os.listdir(BGM_DIR) 
               if f.endswith('.mp3') and os.path.getsize(os.path.join(BGM_DIR, f)) > 5000]
    if not all_mp3:
        return None
    
    # 检查BGM数据库有没有这个国家的歌
    bm = load_bgm_db()
    country_bgms = bm.get(country, [])
    
    if country_bgms:
        # 选一首这个国家的歌（每次随机，保证差异化）
        chosen = random.choice(country_bgms)
        title = chosen.get('title', '')
        # 尝试匹配文件名（可能有误差）
        match_score = {}
        for mp3 in all_mp3:
            name_lower = mp3.lower().replace('.mp3', '').replace('-', ' ').replace('_', ' ')
            # 简中匹配：包含关键词
            score = 0
            for word in title.lower().split()[:3]:
                if word in name_lower:
                    score += 1
            match_score[mp3] = score
        # 找最匹配的
        best = max(match_score, key=match_score.get) if match_score else None
        if best and match_score[best] > 0:
            print(f'  🎵 BGM匹配: {title} → {best}')
            return os.path.join(BGM_DIR, best)
    
    # 没匹配上，随机选一首
    selected = random.choice(all_mp3)
    print(f'  🎵 BGM随机: {selected}')
    return os.path.join(BGM_DIR, selected)


async def generate_tts(text, country, out_path):
    """生成TTS配音，使用本地20岁女生声音参数"""
    cfg = TTS_CONFIG.get(country)
    if not cfg:
        print(f'  ⚠️ 未找到{country}的TTS配置')
        return False
    
    try:
        communicate = edge_tts.Communicate(
            text, 
            cfg['voice'],
            rate=cfg['rate'],
            pitch=cfg['pitch']
        )
        await communicate.save(out_path)
        
        if os.path.exists(out_path) and os.path.getsize(out_path) > 500:
            return True
        else:
            # 降级：不加rate/pitch再试一次
            communicate = edge_tts.Communicate(text, cfg['voice'])
            await communicate.save(out_path)
            return os.path.exists(out_path) and os.path.getsize(out_path) > 500
    except Exception as e:
        print(f'  ⚠️ TTS生成失败: {e}')
        return False


def make_subtitle_png(text, country, out_path, is_last=False):
    """
    生成字幕PNG
    - 大字: 58pt
    - 位置: 底部往上200px
    - 描边: 黑色描边保证可读
    - 多行: 超过14字符自动折行
    """
    from PIL import Image, ImageDraw, ImageFont
    
    img = Image.new('RGBA', (VW, VH), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 选字体
    font_path = None
    font_candidates = {
        'TH': '/System/Library/Fonts/Supplemental/Thonburi.ttc',
        'MY': '/Library/Fonts/Arial Unicode.ttf',
        'VN': '/Library/Fonts/Arial Unicode.ttf',
    }
    if country in font_candidates and os.path.exists(font_candidates[country]):
        font_path = font_candidates[country]
    if not font_path:
        for fb in ['/Library/Fonts/Arial Unicode.ttf',
                    '/System/Library/Fonts/Supplemental/Arial.ttf',
                    '/System/Library/Fonts/Helvetica.ttc']:
            if os.path.exists(fb):
                font_path = fb
                break
    
    font_size = SUB_FONT_SIZE
    font = None
    if font_path:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            pass
    if not font:
        font = ImageFont.load_default()
    
    # 文字折行
    max_chars = SUB_LINE_MAX_CHARS
    lines = []
    for i in range(0, len(text), max_chars):
        lines.append(text[i:i+max_chars])
    lines = lines[:2]  # 最多2行
    
    # 计算每行尺寸
    line_height = font_size + 10
    total_h = len(lines) * line_height
    
    # 计算最宽行
    max_w = 0
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        w = bb[2] - bb[0]
        if w > max_w:
            max_w = w
    
    # 位置：底部往上
    bg_h = total_h + 30
    bg_y = VH - SUB_Y_OFFSET - bg_h
    bg_x = (VW - max_w - 40) // 2
    
    # 半透明黑底
    draw.rounded_rectangle(
        [bg_x - 10, bg_y - 5, bg_x + max_w + 50, bg_y + bg_h + 5],
        radius=12,
        fill=(0, 0, 0, 160)
    )
    
    # 渲染文字（白色+黑色描边）
    for i, line in enumerate(lines):
        bb = draw.textbbox((0, 0), line, font=font)
        tw = bb[2] - bb[0]
        x = (VW - tw) // 2
        y = bg_y + 15 + i * line_height
        
        outline_w = 3
        # 描边
        for ox in range(-outline_w, outline_w + 1):
            for oy in range(-outline_w, outline_w + 1):
                if ox == 0 and oy == 0:
                    continue
                draw.text((x + ox, y + oy), line, font=font, fill=(0, 0, 0, 255))
        # 白字主体
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
    
    img.save(out_path)
    return True


# ====== 核心处理 ======

async def process_country(country, input_video, product_name, scripts=None):
    """处理单个国家的视频"""
    print(f'\n{"="*50}')
    print(f'🌍 处理 {country} — {product_name}')
    print(f'{"="*50}')
    
    out_path = os.path.join(OUT_DIR, f'{product_name}_{country}.mp4')
    tmp_dir = f'/tmp/vpipe_{product_name}_{country}_{random.randint(1000,9999)}'
    os.makedirs(tmp_dir, exist_ok=True)
    
    # 1. 获取源视频信息 & 横→竖转换
    src_dur = get_duration(input_video)
    
    # 1a. 检测源视频方向：横屏(16:9) → 裁剪成竖屏(9:16)
    r = run_cmd(['ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
                 '-show_entries', 'stream=width,height', '-of', 'csv=p=0',
                 input_video], 5)
    src_w, src_h = 0, 0
    if r.stdout.strip():
        parts = r.stdout.strip().split(',')
        src_w, src_h = int(parts[0]), int(parts[1])
    
    vert_video = input_video
    if src_w > src_h:
        # 横屏→竖屏：scale高度到1920再crop宽度到1080（取中）
        vert_video = os.path.join(tmp_dir, 'vert.mp4')
        print(f'  📐 横屏({src_w}x{src_h}) → 竖屏({VW}x{VH})')
        r2 = run_cmd([
            'ffmpeg', '-y', '-i', input_video,
            '-vf', f'scale=-2:{VH},crop={VW}:{VH}:(iw-{VW})/2:0',
            '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
            '-an', vert_video
        ], 120)
        if r2.returncode != 0 or not os.path.exists(vert_video):
            print(f'  ⚠️ 竖屏转换失败，按原尺寸继续')
            vert_video = input_video
        src_w, src_h = VW, VH
    elif src_w < VW or src_h < VH:
        # 竖屏但分辨率不足(如Seedance 720×1280) → 上采样到1080×1920
        vert_video = os.path.join(tmp_dir, 'vert.mp4')
        print(f'  📐 上采样({src_w}x{src_h}) → ({VW}x{VH})')
        r2 = run_cmd([
            'ffmpeg', '-y', '-i', input_video,
            '-vf', f'scale={VW}:{VH}:flags=lanczos',
            '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
            '-an', vert_video
        ], 180)
        if r2.returncode != 0 or not os.path.exists(vert_video):
            print(f'  ⚠️ 上采样失败，按原尺寸继续')
            vert_video = input_video
        else:
            src_w, src_h = VW, VH
    else:
        # 竖屏或1:1，scale到标准尺寸
        if src_w != VW or src_h != VH:
            vert_video = os.path.join(tmp_dir, 'vert.mp4')
            run_cmd([
                'ffmpeg', '-y', '-i', input_video,
                '-vf', f'scale={VW}:{VH}',
                '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
                '-an', vert_video
            ], 60)
            if not os.path.exists(vert_video):
                vert_video = input_video
    
    print(f'  源视频: {os.path.basename(input_video)} ({src_dur:.1f}s) → {src_w}x{src_h}')
    
    # 2. 文案（优先用传入的，没有用默认）
    texts = scripts.get(country, DEFAULT_SCRIPTS.get(country, ['']))
    
    # 3. 生成TTS - 分段
    tts_paths = []
    for i, txt in enumerate(texts):
        p = os.path.join(tmp_dir, f'tts_{i}.mp3')
        ok = await generate_tts(txt, country, p)
        if ok:
            tts_paths.append(p)
        else:
            # 失败的话用静音占位
            p = os.path.join(tmp_dir, f'silence_{i}.mp3')
            run_cmd(['ffmpeg', '-y', '-f', 'lavfi', '-i', 
                     'anullsrc=r=44100:cl=mono', '-t', '2.0', p], 5)
            tts_paths.append(p)
    
    if not tts_paths:
        print(f'  ❌ TTS全部失败')
        run_cmd(['rm', '-rf', tmp_dir])
        return False
    
    tts_durs = [get_duration(p) for p in tts_paths]
    total_tts_dur = sum(tts_durs)
    print(f'  🎤 TTS: {[f"{d:.1f}s" for d in tts_durs]} 合计{total_tts_dur:.1f}s')
    
    # 4. 合并TTS
    list_file = os.path.join(tmp_dir, 'tts_list.txt')
    with open(list_file, 'w') as f:
        for p in tts_paths:
            f.write(f"file '{p}'\n")
    tts_merged = os.path.join(tmp_dir, 'tts_merged.aac')
    run_cmd(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', list_file,
             '-c:a', 'aac', '-ar', '44100', '-b:a', '192k', tts_merged], 10)
    
    # 5. 找BGM并混合
    bgm_path = pick_matching_mp3(country)
    audio_final = os.path.join(tmp_dir, 'audio_final.aac')
    
    if bgm_path and os.path.exists(bgm_path):
        bgm_dur = get_duration(bgm_path)
        print(f'  🎵 BGM: {os.path.basename(bgm_path)} ({bgm_dur:.1f}s)')
        
        # BGM音量 -24dB（轻微背景，不压人声）
        # 人声 -3dB轻微压缩
        # amix混合
        r = run_cmd([
            'ffmpeg', '-y',
            '-i', tts_merged,
            '-i', bgm_path,
            '-filter_complex',
            '[0:a]compand=attacks=0.1:decays=0.5:'
            'points=-90/-90|-60/-60|-30/-20|-10/-6|0/-2[voice];'
            '[1:a]volume=-14dB,afade=t=in:d=1.0[bgm];'
            '[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[out]',
            '-map', '[out]',
            '-c:a', 'aac', '-ar', '44100', '-b:a', '192k',
            audio_final
        ], 30)
        
        if r.returncode == 0 and os.path.exists(audio_final) and os.path.getsize(audio_final) > 1000:
            print(f'  ✅ BGM混合成功')
        else:
            print(f'  ⚠️ BGM混合失败，仅TTS')
            audio_final = tts_merged
    else:
        print(f'  ℹ️ 无BGM可用，仅TTS')
        audio_final = tts_merged
    
    # 6. 生成字幕PNG（每句配时间轴）
    # 均匀分布：每句在对应时间段显示
    sub_pngs = []
    sub_times = []
    
    for i, (txt, dur) in enumerate(zip(texts, tts_durs)):
        p = os.path.join(tmp_dir, f'sub_{i}.png')
        make_subtitle_png(txt, country, p, is_last=(i == len(texts)-1))
        sub_pngs.append(p)
        sub_times.append((sum(tts_durs[:i]), sum(tts_durs[:i+1])))
    
    print(f'  📺 字幕: {len(sub_pngs)}条')
    
    # 7. 视频滤镜：速度微调（5国差异化）
    # 差异化参数（20维防重简化版）
    anti_dup = {
        'TH': {'speed': 1.01, 'brightness': 0.02, 'contrast': 1.02, 'crf': 24},
        'MY': {'speed': 0.99, 'brightness': -0.02, 'contrast': 0.98, 'crf': 26},
        'VN': {'speed': 1.02, 'brightness': 0.01, 'contrast': 1.01, 'crf': 22},
        'PH': {'speed': 0.98, 'brightness': 0.03, 'contrast': 0.97, 'crf': 28},
        'SG': {'speed': 1.00, 'brightness': 0.00, 'contrast': 1.00, 'crf': 20},
    }
    cfg = anti_dup.get(country, anti_dup['SG'])
    
    video_filters = []
    
    # 速度
    speed = cfg['speed']
    if speed != 1.0:
        video_filters.append(f'setpts={1/speed}*PTS')
        audio_speed = speed
    else:
        audio_speed = 1.0
    
    # 亮度/对比度
    eq_parts = []
    if cfg['brightness'] != 0:
        eq_parts.append(f'brightness={cfg["brightness"]:.3f}')
    if cfg['contrast'] != 1.0:
        eq_parts.append(f'contrast={cfg["contrast"]:.3f}')
    if eq_parts:
        video_filters.append('eq=' + ':'.join(eq_parts))
    
    # 字幕叠加 - 使用stream overlay方法
    # 构建filter_complex
    filter_parts = []
    
    # 视频流
    if video_filters:
        vf = ','.join(video_filters)
        filter_parts.append(f'[0:v]{vf}[v0]')
        current = 'v0'
    else:
        current = '0:v'
    
    # 叠加字幕
    for i, (st, et) in enumerate(sub_times):
        next_label = f'v{i+1}'
        if i < len(sub_times) - 1:
            filter_parts.append(
                f'[{current}][{i+2}:v]overlay=0:0:enable=between(t\\,{st:.1f}\\,{et:.1f})[{next_label}]'
            )
        else:
            filter_parts.append(
                f'[{current}][{i+2}:v]overlay=0:0:enable=between(t\\,{st:.1f}\\,{et:.1f})[vout]'
            )
        current = next_label
    
    # 音频：如果需要速度调整
    if audio_speed != 1.0 and audio_speed > 0:
        filter_parts.append(f'[1:a]atempo={audio_speed:.2f}[aout]')
        audio_map = '[aout]'
    else:
        audio_map = '1:a'
    
    if not filter_parts:
        # 无滤镜，简单合成
        cmd = ['ffmpeg', '-y',
               '-i', vert_video,
               '-i', audio_final]
        for sp in sub_pngs:
            cmd.extend(['-i', sp])
        cmd.extend([
            '-map', '0:v', '-map', '1:a',
            '-c:v', 'libx264', '-preset', 'fast',
            '-c:a', 'aac', '-ar', '44100', '-b:a', '192k',
            '-shortest',
            out_path
        ])
    else:
        cmd = ['ffmpeg', '-y',
               '-i', vert_video,
               '-i', audio_final]
        for sp in sub_pngs:
            cmd.extend(['-i', sp])
        cmd.extend([
            '-filter_complex', ';'.join(filter_parts),
            '-map', '[vout]',
            '-map', audio_map,
            '-c:v', 'libx264', '-preset', 'fast', '-crf', str(cfg['crf']),
            '-c:a', 'aac', '-ar', '44100', '-b:a', '192k',
            '-shortest',
            out_path
        ])
    
    r = run_cmd(cmd, 300)
    
    if r.returncode != 0:
        print(f'  ❌ ffmpeg错误: {r.stderr[-300:]}')
        run_cmd(['rm', '-rf', tmp_dir])
        return False
    
    if not os.path.exists(out_path) or os.path.getsize(out_path) < 50000:
        print(f'  ❌ 输出文件异常')
        run_cmd(['rm', '-rf', tmp_dir])
        return False
    
    size_mb = os.path.getsize(out_path) / 1024 / 1024
    print(f'  ✅ {product_name}_{country}.mp4 — {size_mb:.1f}MB')
    
    # 清理
    run_cmd(['rm', '-rf', tmp_dir])
    return True


async def main():
    parser = argparse.ArgumentParser(description='🌽 玉米·5国视频剪辑管线')
    parser.add_argument('--input', default=None, help='源视频路径（留空自动扫描~/Desktop/源视频/）')
    parser.add_argument('--product', default=None, help='产品名称（如 双头眉刷）')
    parser.add_argument('--category', default='通用', help='品类（美妆/家居/厨房）')
    parser.add_argument('--countries', default=','.join(COUNTRIES), help='国家列表，逗号分隔')
    parser.add_argument('--scripts', help='文案JSON文件路径（可选）')
    parser.add_argument('--skip-tts', action='store_true', help='跳过TTS生成（仅测试视频管线）')
    
    args = parser.parse_args()
    
    # 自动扫描：无 --input 时扫描 ~/Desktop/源视频/
    if not args.input:
        source_dir = os.path.expanduser('~/Desktop/源视频')
        if not os.path.isdir(source_dir):
            print(f'❌ 源视频目录不存在: {source_dir}')
            sys.exit(1)
        videos = sorted([f for f in os.listdir(source_dir) if f.endswith('.mp4')])
        if not videos:
            print(f'ℹ️ 源视频目录为空，无需处理')
            sys.exit(0)
        print(f'🔍 自动扫描: {len(videos)}个源视频 → {", ".join(videos)}')
        products = [(os.path.splitext(v)[0], os.path.join(source_dir, v)) for v in videos]
    else:
        if not os.path.exists(args.input):
            print(f'❌ 源视频不存在: {args.input}')
            sys.exit(1)
        pname = args.product or os.path.splitext(os.path.basename(args.input))[0]
        products = [(pname, os.path.abspath(args.input))]
    
    countries = [c.strip() for c in args.countries.split(',')]
    
    # 加载文案（可选）
    scripts = {}
    if args.scripts and os.path.exists(args.scripts):
        with open(args.scripts) as f:
            scripts = json.load(f)
    
    all_products_pass = True
    for product_name, input_video in products:
        if len(products) > 1:
            print(f'\n{"#"*50}')
            print(f'📦 {product_name}')
            print(f'{"#"*50}')
        
        print(f'{"="*50}')
        print(f'🌽 玉米视频剪辑管线')
        print(f'产品: {product_name} ({args.category})')
        print(f'源视频: {input_video}')
        print(f'国家: {len(countries)}国 ({", ".join(countries)})')
        print(f'输出: {OUT_DIR}')
        print(f'{"="*50}')
        
        results = {}
        for cc in countries:
            results[cc] = await process_country(cc, input_video, product_name, scripts)
        
        print(f'\n{"="*50}')
        print('📊 处理结果:')
        print(f'{"="*50}')
        all_pass = True
        for cc in countries:
            fp = os.path.join(OUT_DIR, f'{product_name}_{cc}.mp4')
            sz = os.path.getsize(fp) / 1024 / 1024 if os.path.exists(fp) else 0
            flag = '✅' if results.get(cc) else '❌'
            if not results.get(cc):
                all_pass = False
            print(f'  {flag} {cc}: {sz:.1f}MB')
        
        print(f'\n全通过: {"✅" if all_pass else "❌ 有失败"}')
        if not all_pass:
            all_products_pass = False
        
        # 记录GEP
        if all_pass:
            run_cmd(['python3', 
                     '/Users/a1234/.openclaw/workspace/scripts/gep_adapter.py',
                     'post_record', 'corn',
                     f'{product_name} 5国视频剪辑', 'success'], 5)
    
    sys.exit(0 if all_products_pass else 1)


if __name__ == '__main__':
    asyncio.run(main())
