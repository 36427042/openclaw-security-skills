#!/usr/bin/env python3
"""
🔥 超细纤维抹布 6国视频合成器 v1
- 第一个源视频：source_video_01.mp4 (540×960, 10s)
- 20维防重参数 + 6国版本
- 适配540×960分辨率 (非1080×1920)
- 字幕居中下方
- 从源视频提取音频保留

用法:  python3 composer_microfiber_v1.py
输出:  output/v1_microfiber_cloth_{CC}.mp4
"""
import asyncio, edge_tts, os, subprocess, shutil, random, json, re, math
from PIL import Image, ImageDraw, ImageFont

PRODUCT    = 'microfiber_cloth'
VIDEO_SRC  = os.path.abspath(os.path.join(os.path.dirname(__file__), 'source_video_01.mp4'))
BGM_DIR    = os.path.expanduser('~/Desktop/配音输出')
OUT_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), 'output'))
BGMLIB_DIR = os.path.expanduser('~/Desktop/BGM库')
MEMORY_DIR = os.path.expanduser('~/.openclaw/workspace/agents/corn-agent/memory')
os.makedirs(OUT_DIR, exist_ok=True)

# 源视频实际尺寸 (540×960 竖屏)
VW, VH = 540, 960
HOOK_DURATION = 2.0  # 钩子帧时长(秒)

COUNTRIES = ['CN', 'TH', 'MY', 'VN', 'PH', 'SG']

VOICES = {
    'CN': ('zh-CN-XiaoxiaoNeural', 'cheerful'),
    'TH': ('th-TH-PremwadeeNeural', 'cheerful'),
    'MY': ('ms-MY-YasminNeural', 'cheerful'),
    'VN': ('vi-VN-HoaiMyNeural', 'cheerful'),
    'PH': ('fil-PH-BlessicaNeural', 'cheerful'),
    'SG': ('en-SG-LunaNeural', 'cheerful'),
}
TTS_RATE  = '+5%'
TTS_PITCH = '+0Hz'

BGM_MAP = {
    'CN': 'bgm_CN.mp3',
    'TH': 'bgm_h_TH.aac',
    'MY': 'bgm_h_MY.aac',
    'VN': 'bgm_h_VN.aac',
    'PH': 'bgm_h_PH.aac',
    'SG': 'bgm_CN.mp3',
}
BGM_FADE_IN = {'CN': 0.5, 'TH': 0.3, 'MY': 1.2, 'VN': 0.8, 'PH': 0.5, 'SG': 1.5}

BGM_CLIMAX_RATIOS = {
    'CN': (0.25, 0.40), 'TH': (0.30, 0.45),
    'MY': (0.35, 0.50), 'VN': (0.28, 0.42),
    'PH': (0.32, 0.48), 'SG': (0.25, 0.40),
}

# ----- 20维防重参数 (6国差异化) -----
ANTI_DUP_CONFIG = {
    'CN': {
        'speed': 1.00, 'brightness': 0,
        'gamma_r': 1.00, 'gamma_g': 1.00, 'gamma_b': 1.00,
        'noise': 0, 'crf': 26, 'bgm_db': -14,
        'sub_offset_y': 0,
        'sub_color_r': 255, 'sub_color_g': 255, 'sub_color_b': 255,
        'contrast': 1.00, 'saturation': 1.00, 'color_temp': 5000,
        'sharpness': 0.3, 'crop_offset_x': 0, 'crop_offset_y': 0,
        'bgm_fade_in': 0.5, 'sub_animation': 'fade',
        'outline_width': 3, 'font_size': 48,
    },
    'TH': {
        'speed': 1.01, 'brightness': -2,
        'gamma_r': 0.95, 'gamma_g': 0.98, 'gamma_b': 1.02,
        'noise': 1.5, 'crf': 24, 'bgm_db': -16,
        'sub_offset_y': -10,
        'sub_color_r': 255, 'sub_color_g': 255, 'sub_color_b': 250,
        'contrast': 1.02, 'saturation': 1.05, 'color_temp': 5500,
        'sharpness': 0.3, 'crop_offset_x': 0, 'crop_offset_y': 0,
        'bgm_fade_in': 0.3, 'sub_animation': 'fade',
        'outline_width': 3, 'font_size': 44,
    },
    'MY': {
        'speed': 0.99, 'brightness': 1,
        'gamma_r': 1.02, 'gamma_g': 1.00, 'gamma_b': 0.97,
        'noise': 1.8, 'crf': 26, 'bgm_db': -16,
        'sub_offset_y': 5,
        'sub_color_r': 255, 'sub_color_g': 252, 'sub_color_b': 245,
        'contrast': 0.98, 'saturation': 0.95, 'color_temp': 4800,
        'sharpness': 0.5, 'crop_offset_x': 0, 'crop_offset_y': 2,
        'bgm_fade_in': 1.2, 'sub_animation': 'scroll',
        'outline_width': 4, 'font_size': 46,
    },
    'VN': {
        'speed': 1.02, 'brightness': -1,
        'gamma_r': 0.98, 'gamma_g': 1.02, 'gamma_b': 1.00,
        'noise': 2.0, 'crf': 22, 'bgm_db': -16,
        'sub_offset_y': -5,
        'sub_color_r': 255, 'sub_color_g': 250, 'sub_color_b': 255,
        'contrast': 1.01, 'saturation': 1.02, 'color_temp': 5200,
        'sharpness': 0.4, 'crop_offset_x': 0, 'crop_offset_y': -2,
        'bgm_fade_in': 0.8, 'sub_animation': 'slide',
        'outline_width': 2, 'font_size': 42,
    },
    'PH': {
        'speed': 0.98, 'brightness': 2,
        'gamma_r': 1.00, 'gamma_g': 0.97, 'gamma_b': 0.95,
        'noise': 1.2, 'crf': 28, 'bgm_db': -18,
        'sub_offset_y': 10,
        'sub_color_r': 255, 'sub_color_g': 248, 'sub_color_b': 240,
        'contrast': 0.97, 'saturation': 0.92, 'color_temp': 4600,
        'sharpness': 0.6, 'crop_offset_x': 0, 'crop_offset_y': 0,
        'bgm_fade_in': 0.5, 'sub_animation': 'fade',
        'outline_width': 5, 'font_size': 48,
    },
    'SG': {
        'speed': 1.00, 'brightness': 0,
        'gamma_r': 0.97, 'gamma_g': 1.00, 'gamma_b': 1.02,
        'noise': 1.0, 'crf': 20, 'bgm_db': -14,
        'sub_offset_y': 0,
        'sub_color_r': 255, 'sub_color_g': 255, 'sub_color_b': 255,
        'contrast': 1.00, 'saturation': 1.00, 'color_temp': 5000,
        'sharpness': 0.2, 'crop_offset_x': 2, 'crop_offset_y': 0,
        'bgm_fade_in': 1.5, 'sub_animation': 'scroll',
        'outline_width': 3, 'font_size': 48,
    },
}

# ----- 字幕配色 -----
SUB_COLOR_SCHEME = {
    'normal':    {'text': (255, 255, 255), 'outline': (0, 0, 0)},
    'highlight': {'text': (255, 215, 0),   'outline': (0, 0, 0)},
    'emphasis':  {'text': (255, 107, 157), 'outline': (30, 30, 30)},
}

SUB_STYLE = {
    'CN': {'bg_alpha': 160, 'bg_color': (0, 0, 0),     'show_bg': True},
    'TH': {'bg_alpha': 160, 'bg_color': (0, 0, 0),     'show_bg': True},
    'MY': {'bg_alpha': 140, 'bg_color': (20, 20, 30),  'show_bg': True},
    'VN': {'bg_alpha': 180, 'bg_color': (0, 0, 0),     'show_bg': True},
    'PH': {'bg_alpha': 130, 'bg_color': (10, 10, 20),  'show_bg': True},
    'SG': {'bg_alpha': 170, 'bg_color': (0, 0, 0),     'show_bg': True},
}

FONTS = {
    'CN': '/Library/Fonts/Arial Unicode.ttf',
    'TH': '/System/Library/Fonts/Supplemental/Thonburi.ttc',
    'MY': '/Library/Fonts/Arial Unicode.ttf',
    'VN': '/Library/Fonts/Arial Unicode.ttf',
    'PH': '/Library/Fonts/Arial Unicode.ttf',
    'SG': '/Library/Fonts/Arial Unicode.ttf',
}

# ----- 6国文案（超细纤维抹布，每国4句）-----
SCRIPTS = {
    'CN': [
        '湿抹布擦不干？又湿又臭？别担心！',
        '超细纤维抹布40×40，一次就干透',
        '擦桌子、擦镜子、擦厨房，都好用',
        '10条一包，洗了再用，用了再洗，超耐用！',
    ],
    'TH': [
        'เบื่อไหมเวลาเช็ดโต๊ะแล้วผ้าเปียกแฉะ เหม็นอับ?',
        'ผ้าไมโครไฟเบอร์ 40×40 10 ผืน—เช็ดครั้งเดียวแห้งสนิท',
        'เช็ดกระจก เช็ดครัว เช็ดทุกอย่าง แห้งไวใน 5 นาที',
        'ซักแล้วใช้ซ้ำได้ ลองแล้วจะติดใจ!',
    ],
    'MY': [
        'Dah penat basuh pinggan? Handuk dapur kotor, lembab, berbau?',
        'Kain microfiber ni—40×40, sepuluh helai—sekali lap terus kering',
        'Lap meja, lap cermin, lap segala. Kering dalam 5 minit.',
        'Guna, basuh, guna lagi. Dah cuba? Confirm puas hati!',
    ],
    'VN': [
        'Mệt mỏi vì lau mãi không khô? Khăn ẩm mốc, có mùi hôi?',
        'Khăn microfiber 40×40, 10 cái—lau một lần là khô ngay',
        'Lau bàn, lau gương, lau bếp—cái gì cũng sạch bong',
        'Giặt, phơi khô, dùng lại. Thử một lần là nghiền!',
    ],
    'PH': [
        'Sawsaw nang sawsaw sa basang basahan? Nakakainis?',
        'Itong microfiber cloth, 10 piraso, 40×40—isa lang punas, tuyo na',
        'Pwede sa kusina, pwede sa salamin. Walang himulmol.',
        'Labahan, patuyuin, gamitin ulit. Isang subok, panindigan mo!',
    ],
    'SG': [
        'Tired of wet countertops that never dry properly?',
        'This microfiber cloth 40×40, 10 pieces—one wipe, instantly dry',
        'Use it on tables, mirrors, kitchen—everything streak-free',
        'Wash, dry, reuse. Try it once, you\'ll never go back!',
    ],
}

FONT_SIZE = 48
SUB_Y_BASE = VH - 120
OUTLINE_WIDTH = 3
BG_RADIUS = 12
BG_PADDING_X = 20
BG_PADDING_Y = 10
BG_ALPHA = 160

# ==================== 工具函数 ====================

def run_cmd(cmd, timeout=120):
    try: return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired: return type('R',(),{'returncode':-1,'stdout':'','stderr':''})()

def get_dur(path):
    if not os.path.exists(path) or os.path.getsize(path) < 200: return 2.0
    r = run_cmd(['ffprobe','-v','quiet','-show_entries','format=duration','-of','csv=p=0',path],5)
    try: return float(r.stdout.strip())
    except: return 2.0

def rounded_rect(draw, xy, radius, fill):
    x1,y1,x2,y2 = xy
    draw.rectangle([x1+radius,y1,x2-radius,y2], fill=fill)
    draw.rectangle([x1,y1+radius,x2,y2-radius], fill=fill)
    draw.pieslice([x1,y1,x1+2*radius,y1+2*radius],180,270,fill=fill)
    draw.pieslice([x2-2*radius,y1,x2,y1+2*radius],270,360,fill=fill)
    draw.pieslice([x1,y2-2*radius,x1+2*radius,y2],90,180,fill=fill)
    draw.pieslice([x2-2*radius,y2-2*radius,x2,y2],0,90,fill=fill)

# ----- 卖点词高亮库 -----
HIGHLIGHT_WORDS = {
    'CN': ['干透', '超细纤维', '好用', '耐用', '干净', '10条', '一次', '就'],
    'TH': ['แห้ง', 'ใหม่', 'ดี', 'คุ้ม', 'สะอาด', 'ง่าย', '10 ผืน', 'สนิท'],
    'MY': ['kering', 'baru', 'bagus', 'puas', 'bersih', 'mudah', 'sepuluh', 'cepat'],
    'VN': ['khô', 'mới', 'tốt', 'sạch', 'dễ', '10 cái', 'ngay', 'nghiền'],
    'PH': ['tuyo', 'bago', 'ganda', 'sulit', 'bisa', '10 piraso', 'punas', 'panindigan'],
    'SG': ['dry', 'new', 'good', 'worth', 'clean', 'easy', '10 pieces', 'streak-free'],
}

def find_highlight_words(text, cc):
    hw_list = HIGHLIGHT_WORDS.get(cc, HIGHLIGHT_WORDS['SG'])
    text_lower = text.lower()
    return [w for w in hw_list if w.lower() in text_lower]

def split_text_with_highlight(text, cc):
    hw_list = HIGHLIGHT_WORDS.get(cc, HIGHLIGHT_WORDS['SG'])
    text_lower = text.lower()
    matches = []
    for w in hw_list:
        idx = text_lower.find(w.lower())
        if idx >= 0:
            matches.append((idx, idx+len(w), w))
            text_lower = text_lower[:idx] + '\x00'*len(w) + text_lower[idx+len(w):]
    if not matches:
        return [(text, 'normal')]
    matches.sort(key=lambda x: x[0])
    segments = []; last_end = 0
    for start,end,w in matches:
        if start > last_end: segments.append((text[last_end:start], 'normal'))
        segments.append((text[start:end], 'highlight'))
        last_end = end
    if last_end < len(text): segments.append((text[last_end:], 'normal'))
    hc = sum(1 for _,s in segments if s == 'highlight')
    if hc > 2:
        kept = 0; new_segs = []
        for seg_text, seg_type in segments:
            if seg_type == 'highlight':
                new_segs.append((seg_text, 'highlight' if kept in (0, hc-1) else 'normal'))
                kept += 1
            else:
                new_segs.append((seg_text, seg_type))
        segments = new_segs
    return segments

# ----- BGM高潮段检测 -----
def detect_bgm_climax(bgm_path, num_samples=20):
    if not bgm_path or not os.path.exists(bgm_path) or os.path.getsize(bgm_path) < 5000:
        return (0.30, 0.45)
    bgm_dur = get_dur(bgm_path)
    if bgm_dur < 3 or bgm_dur > 600:
        return (0.30, 0.45)
    sample_interval = bgm_dur / num_samples
    rms_values = []
    for i in range(num_samples):
        t = i * sample_interval + sample_interval / 2
        if t >= bgm_dur: break
        r = run_cmd([
            'ffmpeg','-y','-ss',str(t),'-t',str(sample_interval*0.8),
            '-i',bgm_path,
            '-af','astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level',
            '-f','null','-'
        ],10)
        got = False
        if r.stderr:
            for line in r.stderr.split('\n'):
                if 'RMS_level' in line:
                    try:
                        val = float(line.split('=')[-1].strip())
                        rms_values.append(val); got = True; break
                    except: pass
        if not got: rms_values.append(-30.0)
    if not rms_values: return (0.30, 0.45)
    window_size = max(3, len(rms_values)//4)
    max_avg, best_start = -100, 0
    for i in range(len(rms_values)-window_size+1):
        avg = sum(rms_values[i:i+window_size])/window_size
        if avg > max_avg: max_avg, best_start = avg, i
    si, ei = best_start, best_start+window_size-1
    thresh = max_avg - 3
    while si > 0 and rms_values[si-1] > thresh: si -= 1
    while ei < len(rms_values)-1 and rms_values[ei+1] > thresh: ei += 1
    s_ratio = max(0.1, min(0.6, (si*sample_interval)/bgm_dur))
    e_ratio = max(s_ratio+0.1, min(0.8, ((ei+1)*sample_interval)/bgm_dur))
    print(f'    📊 BGM高潮段检测: {s_ratio:.0%}~{e_ratio:.0%} (峰值: {max_avg:.1f}dB)', flush=True)
    return (s_ratio, e_ratio)

def get_climax_times(bgm_path, bgm_dur, cc):
    if bgm_path and os.path.exists(bgm_path) and os.path.getsize(bgm_path) > 5000:
        s_r, e_r = detect_bgm_climax(bgm_path)
    else:
        s_r, e_r = BGM_CLIMAX_RATIOS.get(cc, (0.30, 0.45))
    return bgm_dur*s_r, bgm_dur*e_r, (s_r+e_r)/2

# ----- 字幕PNG生成 -----
def make_subtitle_png(segments_or_text, cc, anim_frame=0, is_hook_frame=False):
    if is_hook_frame:
        return Image.new('RGBA', (VW, VH), (0,0,0,0))

    cfg = ANTI_DUP_CONFIG.get(cc, ANTI_DUP_CONFIG['SG'])
    sub_style = SUB_STYLE.get(cc, SUB_STYLE['SG'])
    sub_y_offset = cfg['sub_offset_y']
    outline_width = cfg['outline_width']
    font_size = cfg['font_size']
    sub_anim = cfg.get('sub_animation', 'fade')
    sub_y = SUB_Y_BASE + sub_y_offset

    canvas_w, canvas_h = VW+100, VH+100
    img = Image.new('RGBA', (canvas_w, canvas_h), (0,0,0,0))
    draw = ImageDraw.Draw(img)

    font = None
    fp = FONTS.get(cc)
    try:
        if fp and os.path.exists(fp): font = ImageFont.truetype(fp, font_size)
    except: pass
    if not font:
        for fb in ['/Library/Fonts/Arial Unicode.ttf',
                    '/System/Library/Fonts/Supplemental/Arial.ttf',
                    '/System/Library/Fonts/Helvetica.ttc']:
            if os.path.exists(fb):
                try: font = ImageFont.truetype(fb, font_size); break
                except: continue
    if not font: font = ImageFont.load_default()

    if isinstance(segments_or_text, str):
        segments = split_text_with_highlight(segments_or_text, cc)
    else:
        segments = segments_or_text

    full_text = ''.join(s[0] for s in segments)
    # 每国字幕每行字数不同（泰文/中文更紧凑）
    if cc == 'CN':
        max_chars = 18
    elif cc == 'TH':
        max_chars = 22
    elif cc == 'VN':
        max_chars = 25
    elif cc == 'PH':
        max_chars = 30
    elif cc == 'SG':
        max_chars = 32
    else:
        max_chars = 28
    lines = [full_text[i:i+max_chars] for i in range(0, len(full_text), max_chars)][:2]
    line_height = font_size + 10
    total_h = len(lines) * line_height

    max_line_w = max((draw.textbbox((0,0),l,font=font)[2]-draw.textbbox((0,0),l,font=font)[0]) for l in lines)
    bg_w = max_line_w + BG_PADDING_X * 2
    bg_h = total_h + BG_PADDING_Y * 2
    bg_x = (canvas_w - bg_w) // 2

    anim_ox = anim_oy = 0
    if sub_anim == 'scroll' and anim_frame < 10:
        p = anim_frame / 10; anim_ox = int((1-p)*150)
    elif sub_anim == 'slide' and anim_frame < 10:
        p = anim_frame / 10; anim_oy = int((1-p)*60)

    bg_fill = sub_style['bg_color'] + (sub_style['bg_alpha'],)
    bg_y = sub_y - bg_h + anim_oy
    bx = bg_x + anim_ox
    if bg_y > 0 and sub_style['show_bg']:
        rounded_rect(draw, (bx, bg_y, bx+bg_w, bg_y+bg_h), BG_RADIUS, bg_fill)

    if len(segments) > 1:
        for i, line in enumerate(lines):
            tw = draw.textbbox((0,0),line,font=font)[2] - draw.textbbox((0,0),line,font=font)[0]
            y = bg_y + BG_PADDING_Y + i*line_height + anim_oy
            x = (canvas_w - tw)//2 + anim_ox
            lsc = i * max_chars; lec = min((i+1)*max_chars, len(full_text))
            ci = 0
            for seg_text, seg_type in segments:
                for ch in seg_text:
                    if ci < lsc: ci += 1; continue
                    if ci >= lec: break
                    c_info = SUB_COLOR_SCHEME.get(seg_type, SUB_COLOR_SCHEME['normal'])
                    tc = c_info['text'] + (255,); oc = c_info['outline'] + (255,)
                    for ox in range(-outline_width, outline_width+1):
                        for oy in range(-outline_width, outline_width+1):
                            if ox==0 and oy==0: continue
                            draw.text((x+ox, y+oy), ch, font=font, fill=oc)
                    draw.text((x,y), ch, font=font, fill=tc)
                    cb = draw.textbbox((0,0),ch,font=font); x += cb[2]-cb[0]; ci += 1
    else:
        for i, line in enumerate(lines):
            bb = draw.textbbox((0,0),line,font=font)
            tw, th = bb[2]-bb[0], bb[3]-bb[1]
            x = (canvas_w - tw)//2 + anim_ox
            y = bg_y + BG_PADDING_Y + i*line_height + anim_oy
            tc = (cfg['sub_color_r'], cfg['sub_color_g'], cfg['sub_color_b'], 255)
            oc = (0,0,0,255)
            for ox in range(-outline_width, outline_width+1):
                for oy in range(-outline_width, outline_width+1):
                    if ox==0 and oy==0: continue
                    draw.text((x+ox, y+oy), line, font=font, fill=oc)
            draw.text((x,y), line, font=font, fill=tc)

    return img.crop((50, 50, 50+VW, 50+VH))


async def gen_tts(text, voice, rate, pitch, outpath):
    # 使用edge-tts CLI (更稳定，避免Python API连接问题)
    cmd = ['edge-tts', '--text', text, '--voice', voice, '--write-media', outpath]
    # 非中文voice不带rate/pitch
    if voice.startswith('zh-'):
        cmd.extend(['--rate', rate, '--pitch', pitch])
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )
    try:
        await asyncio.wait_for(proc.wait(), timeout=30)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
    if not os.path.exists(outpath) or os.path.getsize(outpath) < 500:
        # 重试不带rate/pitch
        proc = await asyncio.create_subprocess_exec(
            'edge-tts', '--text', text, '--voice', voice, '--write-media', outpath,
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        try:
            await asyncio.wait_for(proc.wait(), timeout=30)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()

def find_bgm(cc):
    bgm_name = BGM_MAP.get(cc)
    if bgm_name:
        p = os.path.join(BGM_DIR, bgm_name)
        if os.path.exists(p) and os.path.getsize(p) > 5000: return p
    # fallback
    all_bgm = [os.path.join(BGMLIB_DIR, f) for f in os.listdir(BGMLIB_DIR)
               if f.endswith('.mp3') and not f.startswith('bgm_synth')
               and os.path.getsize(os.path.join(BGMLIB_DIR, f)) > 5000] if os.path.isdir(BGMLIB_DIR) else []
    if all_bgm: return random.choice(all_bgm)
    return None

async def process_country(cc):
    print(f'\n--- 🌍 Processing {cc} (超细纤维抹布) ---', flush=True)
    out_path = os.path.join(OUT_DIR, f'v1_microfiber_cloth_{cc}.mp4')
    td = f'/tmp/c_{cc}_{random.randint(1000,9999)}'
    os.makedirs(td, exist_ok=True)

    cfg = ANTI_DUP_CONFIG.get(cc, ANTI_DUP_CONFIG['SG'])
    bgm_fade_in = BGM_FADE_IN.get(cc, 0.5)
    voice, _ = VOICES[cc]
    segs = SCRIPTS[cc]

    # 1. TTS
    seg_paths = []
    for i, txt in enumerate(segs):
        p = os.path.join(td, f's{i}.mp3')
        # 重试机制
        for attempt in range(3):
            await gen_tts(txt, voice, TTS_RATE, TTS_PITCH, p)
            if os.path.exists(p) and os.path.getsize(p) > 500:
                break
            print(f'  ⚠️ 句{i} 重试 #{attempt+1}', flush=True)
            await asyncio.sleep(2)
        if os.path.exists(p) and os.path.getsize(p) > 500:
            seg_paths.append(p)
        else:
            print(f'  ⚠️ 句{i} TTS失败, 静音替代', flush=True)
            run_cmd(['ffmpeg','-y','-f','lavfi','-i','anullsrc=r=44100:cl=mono','-t','1.5',p],5)
            seg_paths.append(p)
    if len(seg_paths) < 2:
        print(f'  ❌ TTS严重失败', flush=True)
        shutil.rmtree(td, ignore_errors=True); return False

    seg_durs = [get_dur(p) for p in seg_paths]
    print(f'  TTS: {[f"{d:.1f}s" for d in seg_durs]}', flush=True)

    # 2. 合并TTS + 提取源音频并存档（保留原声参考）
    list_p = os.path.join(td, 'files.txt')
    with open(list_p, 'w') as f:
        for p in seg_paths: f.write(f"file '{p}'\n")
    tts_raw = os.path.join(td, 'tts.aac')
    run_cmd(['ffmpeg','-y','-f','concat','-safe','0','-i',list_p,'-c:a','aac','-b:a','192k',tts_raw],20)
    tts_f = os.path.join(td, 'tts_v.aac')
    run_cmd(['ffmpeg','-y','-i',tts_raw,'-af','volume=-2dB','-c:a','aac','-b:a','192k',tts_f],10)

    # 3. BGM
    bgm_path = find_bgm(cc)
    bgm_vol_db = cfg['bgm_db']

    mix_f = os.path.join(td, 'final.aac')
    if bgm_path and os.path.exists(bgm_path) and os.path.getsize(bgm_path) > 5000:
        print(f'  BGM: {os.path.basename(bgm_path)} 降{bgm_vol_db}dB + fade-in={bgm_fade_in}s', flush=True)
        r = run_cmd(['ffmpeg','-y','-i',tts_f,'-i',bgm_path,
            '-filter_complex',
            f'[1:a]volume={bgm_vol_db}dB,afade=t=in:d={bgm_fade_in}[bgm];'
            f'[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[out]',
            '-map','[out]','-c:a','aac','-b:a','192k',mix_f],30)
        if r.returncode == 0 and os.path.exists(mix_f) and os.path.getsize(mix_f) > 1000:
            print(f'  ✅ 音频混合成功', flush=True)
        else:
            mix_f = tts_f; print(f'  ⚠️ BGM失败, 仅TTS', flush=True)
    else:
        mix_f = tts_f; print(f'  ℹ️ 无BGM, 仅TTS', flush=True)

    # 4. 字幕时间
    total_dur = sum(seg_durs)
    if total_dur < 6:    seg_durs = [d*6/total_dur for d in seg_durs]
    if total_dur > 12:   seg_durs = [d*12/total_dur for d in seg_durs]
    total_dur = sum(seg_durs)

    seg_start = [sum(seg_durs[:i]) for i in range(len(seg_durs))]

    # 对齐BGM高潮
    bgm_dur = get_dur(bgm_path) if bgm_path and os.path.exists(bgm_path) else 10
    climax_start, climax_end, climax_mid = get_climax_times(bgm_path, bgm_dur, cc)
    print(f'  BGM高潮段: {climax_start:.1f}s~{climax_end:.1f}s', flush=True)

    timings = []
    for i, d in enumerate(seg_durs):
        if cc in ['TH', 'VN', 'CN']:      enter_offset = 0.3
        elif cc in ['MY', 'PH']:          enter_offset = 0.7
        else:                             enter_offset = 0.5
        st = max(0, seg_start[i] + enter_offset)
        et = min(seg_start[i] + d + 0.5, total_dur - 0.2)
        if et <= st: et = st + 0.8
        timings.append((st, et))

    print(f'  字幕时间: {[(f"{s:.1f}",f"{e:.1f}") for s,e in timings]}', flush=True)

    # 5. 生成字幕PNG
    sub_pngs_hl = []
    for i, txt in enumerate(segs):
        sp = os.path.join(td, f's{i}_hl.png')
        is_hook = (timings[i][0] < HOOK_DURATION)
        if not is_hook:
            segments = split_text_with_highlight(txt, cc)
            make_subtitle_png(segments, cc, anim_frame=i*10).save(sp)
        else:
            make_subtitle_png(txt, cc, anim_frame=i*10, is_hook_frame=True).save(sp)
        sub_pngs_hl.append(sp)

    # 6. 视频滤镜管道
    speed = cfg['speed']
    brightness = cfg['brightness']
    gamma_r, gamma_g, gamma_b = cfg['gamma_r'], cfg['gamma_g'], cfg['gamma_b']
    noise_amt = cfg['noise']
    crf = cfg['crf']
    contrast = cfg.get('contrast', 1.0)
    saturation = cfg.get('saturation', 1.0)
    color_temp = cfg.get('color_temp', 5000)
    sharpness = cfg.get('sharpness', 0.3)
    crop_off_x, crop_off_y = cfg.get('crop_offset_x', 0), cfg.get('crop_offset_y', 0)

    video_filters = []
    if speed != 1.0:
        video_filters.append(f'setpts={1/speed}*PTS')

    vf_eq_parts = []
    if brightness != 0: vf_eq_parts.append(f'brightness={brightness/100.0:.3f}')
    if contrast != 1.0: vf_eq_parts.append(f'contrast={contrast:.3f}')
    if saturation != 1.0: vf_eq_parts.append(f'saturation={saturation:.3f}')
    if any(g != 1.0 for g in [gamma_r, gamma_g, gamma_b]):
        vf_eq_parts.append(f'gamma_r={gamma_r:.3f}:gamma_g={gamma_g:.3f}:gamma_b={gamma_b:.3f}')
    if vf_eq_parts:
        video_filters.append('eq=' + ':'.join(vf_eq_parts))

    if color_temp > 5200:
        r_adj = (color_temp-5200)/2000*0.1
        b_adj = -(color_temp-5200)/2000*0.1
        video_filters.append(f'colorbalance=rs={r_adj:.3f}:gs=0:bs={b_adj:.3f}')
    elif color_temp < 4800:
        r_adj = (4800-color_temp)/2000*0.1
        b_adj = -(4800-color_temp)/2000*0.1
        video_filters.append(f'colorbalance=rs={-r_adj:.3f}:gs=0:bs={b_adj:.3f}')

    if sharpness > 0.01:
        # unsharp: lx/ly=锐化半径(3-23整数), la=强度(0-3浮点)
        radius = max(3, min(23, int(sharpness * 5 + 2)))
        strength = min(1.5, sharpness * 0.5)
        video_filters.append(f'unsharp=lx={radius}:ly={radius}:la={strength:.2f}')

    if noise_amt > 0:
        video_filters.append(f'noise=alls={noise_amt:.0f}:allf=t+u')

    if crop_off_x != 0 or crop_off_y != 0:
        video_filters.append(f'crop={VW}:{VH}:{crop_off_x}:{crop_off_y}')

    vf_chain = ','.join(video_filters) if video_filters else ''

    main_vf = ''
    if vf_chain:
        main_vf = f'[0:v]{vf_chain}[v_main]'

    current_src = 'v_main' if main_vf else '0:v'

    # 字幕叠加
    overlay_chain = ''
    if main_vf:
        overlay_chain = f'{main_vf};'

    for i, (st, et) in enumerate(timings):
        src_label = f'[{current_src}]' if i == 0 else f'[v{i}]'
        out_label = f'[v{i+1}]'
        if i == len(timings)-1: out_label = '[vout]'

        if overlay_chain:
            # 使用Pillow生成的字幕PNG作为覆盖层
            overlay_chain += f'{src_label}[{2+i}:v]overlay=0:0:enable=between(t\\,{st:.2f}\\,{et:.2f}){out_label};'
        else:
            overlay_chain += f'[0:v][{2+i}:v]overlay=0:0:enable=between(t\\,{st:.2f}\\,{et:.2f})[v{i+1}];'

    overlay_chain = overlay_chain.rstrip(';')

    # 7. ffmpeg合成
    cmd = ['ffmpeg', '-y', '-i', VIDEO_SRC, '-i', mix_f]
    # 字幕PNG作为额外输入
    for sp in sub_pngs_hl: cmd.extend(['-i', sp])
    cmd.extend(['-filter_complex', overlay_chain,
                '-map', '[vout]', '-map', '1:a',
                '-c:v', 'libx264', '-preset', 'fast', '-crf', str(crf),
                '-c:a', 'aac', '-b:a', '192k', '-shortest', out_path])

    r = run_cmd(cmd, 300)
    if r.returncode != 0:
        print(f'  ❌ ffmpeg错误: {r.stderr[-400:]}', flush=True)
        shutil.rmtree(td, ignore_errors=True)
        return False

    if not os.path.exists(out_path) or os.path.getsize(out_path) < 50000:
        print(f'  ❌ 输出文件太小', flush=True)
        shutil.rmtree(td, ignore_errors=True)
        return False

    sz_mb = os.path.getsize(out_path) / 1024 / 1024
    print(f'  ✅ {cc}: {sz_mb:.1f}MB', flush=True)

    # 8. 自检
    verify_p = os.path.join(td, 'verify.png')
    run_cmd(['ffmpeg','-y','-ss','3','-i',out_path,'-vframes','1','-q:v','2',verify_p],10)
    if os.path.exists(verify_p):
        try:
            vimg = Image.open(verify_p).convert('RGB')
            vpx = vimg.load()
            w, h = vimg.size
            wp_count = yp_count = 0
            for y in range(h-120, h):
                for x in range(w//2-200, w//2+200):
                    r, g, b = vpx[x, y]
                    if r > 200 and g > 200 and b > 200: wp_count += 1
                    if r > 200 and g > 180 and b < 100: yp_count += 1
            print(f'  自检白像素: {wp_count}  黄色高亮像素: {yp_count}', flush=True)
            if wp_count < 50: print(f'  ⚠️ 字幕可能未渲染', flush=True)
        except: pass

    shutil.rmtree(td, ignore_errors=True)
    return True


async def main():
    print(f'🔥 {PRODUCT} 6国视频合成器 v1', flush=True)
    print(f'源视频: {VIDEO_SRC}', flush=True)
    print(f'产品: 超细纤维抹布40×40cm×10条', flush=True)
    print(f'输出: {OUT_DIR}', flush=True)
    print(f'{"="*50}', flush=True)

    if not os.path.exists(VIDEO_SRC):
        print(f'❌ 源视频不存在: {VIDEO_SRC}', flush=True)
        return

    src_dur = get_dur(VIDEO_SRC)
    print(f'源视频: {src_dur:.1f}s ({VW}x{VH})', flush=True)

    # 先提取源视频信息
    print(f'输出目录: {OUT_DIR}', flush=True)

    results = {}
    for cc in COUNTRIES:
        results[cc] = await process_country(cc)

    print(f'\n{"="*50}', flush=True)
    print('📊 6国合成结果:', flush=True)
    print('='*50, flush=True)
    all_pass = True
    for cc in COUNTRIES:
        fp = os.path.join(OUT_DIR, f'v1_{PRODUCT}_{cc}.mp4')
        sz = os.path.getsize(fp)/1024/1024 if os.path.exists(fp) else 0
        md5 = run_cmd(['md5','-q',fp],5).stdout.strip()[:8] if os.path.exists(fp) else 'N/A'
        flag = '✅' if results.get(cc) else '❌'
        if not results.get(cc): all_pass = False
        print(f'  {flag} {cc}: {sz:.1f}MB  md5={md5}', flush=True)

    print(f'\n输出目录: {OUT_DIR}', flush=True)
    print(f'全通过: {"✅ 全部通过" if all_pass else "❌ 有失败"}', flush=True)

    # 记忆更新
    mem_path = os.path.join(MEMORY_DIR, '2026-05-11.md')
    try:
        os.makedirs(MEMORY_DIR, exist_ok=True)
        with open(mem_path, 'a') as f:
            f.write(f'\n### ⏰ 2026-05-11 22:48 — 超细纤维抹布 6国视频合成\n')
            f.write(f'产品: 超细纤维抹布40×40cm×10条 (source_video_01.mp4)\n')
            f.write(f'20维防重 + 6国版本 (CN/TH/MY/VN/PH/SG)\n')
            for cc in COUNTRIES:
                fp = os.path.join(OUT_DIR, f'v1_{PRODUCT}_{cc}.mp4')
                sz = os.path.getsize(fp)/1024/1024 if os.path.exists(fp) else 0
                f.write(f'- v1_{PRODUCT}_{cc}.mp4: {sz:.1f}MB {results.get(cc)}\n')
            f.write(f'全通过: {all_pass}\n')
    except Exception as e:
        print(f'  ⚠️ 记忆写入失败: {e}', flush=True)

    print(f'\n📝 记忆已记录', flush=True)


if __name__ == '__main__':
    asyncio.run(main())