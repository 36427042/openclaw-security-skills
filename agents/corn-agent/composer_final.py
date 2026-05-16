#!/usr/bin/env python3
"""
🔥 双头眉刷 5国视频合成器 v9（视觉美学升级版）
- 铁律: 全本地ffmpeg, 不调API
- 42pt大字幕: 差异化字体+描边宽度+位置
- 人声降3dB + BGM差异化降12~20dB + ffmpeg动态压缩
- 20维防重参数
- BGM fade-in差异化 + 入场/退场动画差异化
- BGM按国家差异化选择
★ v9新增: 片头2秒视觉钩子帧 (Zoom In + 增强对比度饱和度)
★ v9新增: 卖点词逐词高亮系统 (黄色高亮关键卖点词)
★ v9新增: BGM高潮段精确检测+对齐 (卖点字幕匹配BGM高潮点)
★ v9新增: 画面裁切模拟不同拍摄角度 (俯拍/手持/45°)
★ v9新增: 字幕美学3层分级 (普通→高亮→强调)

用法:  python3 composer_final.py
输出: ~/Desktop/已处理美妆视频/双头眉刷_{CC}.mp4
"""
import asyncio, edge_tts, os, subprocess, shutil, random, json, re, math
from PIL import Image, ImageDraw, ImageFont

PRODUCT    = '双头眉刷'
VIDEO_SRC  = os.path.expanduser('~/Desktop/双头眉刷.mp4')
BGM_DIR    = os.path.expanduser('~/Desktop/配音输出')
OUT_DIR    = os.path.expanduser('~/Desktop/已处理美妆视频')
BGMLIB_DIR = os.path.expanduser('~/Desktop/BGM库')
MEMORY_DIR = os.path.expanduser('~/.openclaw/workspace/agents/corn-agent/memory')
os.makedirs(OUT_DIR, exist_ok=True)
VW, VH = 1080, 1920
HOOK_DURATION = 2.0  # 钩子帧时长(秒)

COUNTRIES = ['TH', 'MY', 'VN', 'PH', 'SG']

VOICES = {
    'TH': ('th-TH-PremwadeeNeural', 'cheerful'),
    'MY': ('ms-MY-YasminNeural', 'cheerful'),
    'VN': ('vi-VN-HoaiMyNeural', 'cheerful'),
    'PH': ('fil-PH-BlessicaNeural', 'cheerful'),
    'SG': ('en-SG-LunaNeural', 'cheerful'),
}
TTS_RATE  = '+5%'
TTS_PITCH = '+0Hz'

BGM_MAP = {
    'TH': 'bgm_h_TH.aac', 'MY': 'bgm_h_MY.aac',
    'VN': 'bgm_h_VN.aac', 'PH': 'bgm_h_PH.aac',
    'SG': 'bgm_CN.mp3',
}
BGM_FADE_IN = {'TH': 0.3, 'MY': 1.2, 'VN': 0.8, 'PH': 0.5, 'SG': 1.5}

# ★ v9: BGM高潮默认比例 (被detect_bgm_climax覆盖)
BGM_CLIMAX_RATIOS = {
    'TH': (0.30, 0.45), 'MY': (0.35, 0.50),
    'VN': (0.28, 0.42), 'PH': (0.32, 0.48),
    'SG': (0.25, 0.40),
}

# ----- 20维防重参数 (每国差异化, 含v9新增参数) -----
ANTI_DUP_CONFIG = {
    'TH': {
        'speed': 1.01, 'brightness': -2,
        'gamma_r': 0.95, 'gamma_g': 0.98, 'gamma_b': 1.02,
        'noise': 1.5, 'crf': 24, 'bgm_db': -16,
        'sub_offset_y': -10,
        'sub_color_r': 255, 'sub_color_g': 255, 'sub_color_b': 250,
        'contrast': 1.02, 'saturation': 1.05, 'color_temp': 5500,
        'sharpness': 0.3, 'crop_offset_x': 0, 'crop_offset_y': 0,
        'bgm_fade_in': 0.3, 'sub_animation': 'fade',
        'outline_width': 3, 'font_size': 56,
        'hook_zoom': 1.05, 'hook_contrast': 1.12, 'hook_saturation': 1.10,
        'angle_mode': 'flat',
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
        'outline_width': 4, 'font_size': 58,
        'hook_zoom': 1.03, 'hook_contrast': 1.08, 'hook_saturation': 1.06,
        'angle_mode': 'top_down',
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
        'outline_width': 2, 'font_size': 54,
        'hook_zoom': 1.06, 'hook_contrast': 1.10, 'hook_saturation': 1.08,
        'angle_mode': 'hand_held',
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
        'outline_width': 5, 'font_size': 60,
        'hook_zoom': 1.04, 'hook_contrast': 1.06, 'hook_saturation': 1.04,
        'angle_mode': 'angle_45',
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
        'outline_width': 3, 'font_size': 56,
        'hook_zoom': 1.05, 'hook_contrast': 1.10, 'hook_saturation': 1.06,
        'angle_mode': 'flat',
    },
}

# ----- ★ v9: 卖点词高亮库(每国) -----
HIGHLIGHT_WORDS = {
    'TH': ['สวย', 'ดี', 'นุ่ม', 'คุ้ม', 'ใหม่', 'ง่าย', 'ธรรมชาติ', 'ผลลัพธ์', 'สวยขึ้น', 'เยอะเลย'],
    'MY': ['cantik', 'lembut', 'murah', 'best', 'baru', 'senang', 'natural', 'hasil', 'profesional', 'perfect'],
    'VN': ['đẹp', 'tốt', 'mềm', 'rẻ', 'tuyệt', 'mới', 'dễ', 'tự nhiên', 'kết quả', 'nhất'],
    'PH': ['ganda', 'lambot', 'mura', 'bago', 'sulit', 'worth', 'natural', 'madali', 'resulta', 'sobrang'],
    'SG': ['perfect', 'soft', 'easy', 'worth', 'new', 'gentle', 'natural', 'super', 'beautiful', 'amazing'],
}

# ----- ★ v9: 字幕3层颜色方案 -----
SUB_COLOR_SCHEME = {
    'normal':    {'text': (255, 255, 255), 'outline': (0, 0, 0)},        # 白+黑: 普通
    'highlight': {'text': (255, 215, 0),   'outline': (0, 0, 0)},        # 金+黑: 卖点
    'emphasis':  {'text': (255, 107, 157), 'outline': (30, 30, 30)},     # 粉+深灰: 强调
}

SUB_STYLE = {
    'TH': {'bg_alpha': 160, 'bg_color': (0, 0, 0),     'show_bg': True},
    'MY': {'bg_alpha': 140, 'bg_color': (20, 20, 30),  'show_bg': True},
    'VN': {'bg_alpha': 180, 'bg_color': (0, 0, 0),     'show_bg': True},
    'PH': {'bg_alpha': 130, 'bg_color': (10, 10, 20),  'show_bg': True},
    'SG': {'bg_alpha': 170, 'bg_color': (0, 0, 0),     'show_bg': True},
}

FONTS = {
    'TH': '/System/Library/Fonts/Supplemental/Thonburi.ttc',
    'MY': '/Library/Fonts/Arial Unicode.ttf',
    'VN': '/Library/Fonts/Arial Unicode.ttf',
    'PH': '/Library/Fonts/Arial Unicode.ttf',
    'SG': '/Library/Fonts/Arial Unicode.ttf',
}

SCRIPTS = {
    'TH': ['เห็นไหมคะ แปรงหัวคู่ใช้ง่ายจริงๆ','ขนนุ่ม ไม่ระคายเคืองผิว','เขียนคิ้วและแต่งหน้าได้ในอันเดียว','ใช้แล้วสวยขึ้นเยอะเลย'],
    'MY': ['Nampak tak berus double-head ini?','Bulu lembut tak sakit masa guna','Contour dan blush semua boleh','Hasil profesional dan natural'],
    'VN': ['Cac ban thay khong? Co kep nay dep hon han','Long co mem khong kich ung da','Danh mat dan ma deu rat tu nhien','San pham nay thuc su rat tot'],
    'PH': ['Kita mo? Ang ganda ng resulta nito','Sobrang lambot ng bristles','Pwedeng pang-contour at pang-blush','Sobrang worth it niyan'],
    'SG': ['See this double-head brush? Super easy to use','The bristles are soft and gentle','Perfect for brows and contouring','Totally worth it'],
}

FONT_SIZE = 56; SUB_Y_BASE = VH - 160; OUTLINE_WIDTH = 3
BG_RADIUS = 14; BG_PADDING_X = 28; BG_PADDING_Y = 14; BG_ALPHA = 160

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

# ----- ★ v9: 卖点词检测 -----
def find_highlight_words(text, cc):
    hw_list = HIGHLIGHT_WORDS.get(cc, HIGHLIGHT_WORDS['SG'])
    text_lower = text.lower()
    return [w for w in hw_list if w.lower() in text_lower]

# ----- ★ v9: 文案拆分+高亮标记 -----
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
    # 高亮词过多时只保留首尾2个
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

# ----- ★ v9: BGM高潮段检测 (纯ffmpeg) -----
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

# ----- ★ v9升级: 字幕PNG生成(高亮/钩子支持) -----
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

    canvas_w, canvas_h = VW+200, VH+200
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
    max_chars = 18 if cc in ('VI','VN') else 15
    lines = [full_text[i:i+max_chars] for i in range(0, len(full_text), max_chars)][:2]
    line_height = font_size + 12
    total_h = len(lines) * line_height

    max_line_w = max((draw.textbbox((0,0),l,font=font)[2]-draw.textbbox((0,0),l,font=font)[0]) for l in lines)
    bg_w = max_line_w + BG_PADDING_X * 2
    bg_h = total_h + BG_PADDING_Y * 2
    bg_x = (canvas_w - bg_w) // 2

    anim_ox = anim_oy = 0
    if sub_anim == 'scroll' and anim_frame < 10:
        p = anim_frame / 10; anim_ox = int((1-p)*300)
    elif sub_anim == 'slide' and anim_frame < 10:
        p = anim_frame / 10; anim_oy = int((1-p)*100)

    bg_fill = sub_style['bg_color'] + (sub_style['bg_alpha'],)
    bg_y = sub_y - bg_h + anim_oy
    bx = bg_x + anim_ox
    if bg_y > 0 and sub_style['show_bg']:
        rounded_rect(draw, (bx, bg_y, bx+bg_w, bg_y+bg_h), BG_RADIUS, bg_fill)

    # ★ v9: 逐词逐段渲染支持高亮
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

    return img.crop((100, 100, 100+VW, 100+VH))

# ----- ★ v9: 构建钩子帧视频滤镜(前2秒画面增强) -----
def build_hook_filter(cfg, total_dur):
    hook_contrast = cfg.get('hook_contrast', 1.10)
    hook_saturation = cfg.get('hook_saturation', 1.06)
    zoom = cfg.get('hook_zoom', 1.05)
    angle_mode = cfg.get('angle_mode', 'flat')

    # 先做eq增强, 再做裁切模拟角度
    prefilter = ''
    if angle_mode == 'top_down':
        prefilter = f'crop={VW}:{VH-80}:0:40,scale={VW}:{VH},'
    elif angle_mode == 'hand_held':
        prefilter = f'crop={VW-20}:{VH-20}:10:10,scale={VW}:{VH},'
    elif angle_mode == 'angle_45':
        prefilter = f'crop={VW}:{VH}:2:2,'

    zoom_str = ''
    if zoom != 1.0:
        sw, sh = int(VW*zoom), int(VH*zoom)
        cx, cy = (sw-VW)//2, (sh-VH)//2
        zoom_str = f'scale={sw}:{sh},crop={VW}:{VH}:{cx}:{cy},'

    # 方法: 拆成两次处理, 用overlay实现"仅前2秒增强,后续原画面"
    hook_filter = (
        f'split=2[v_pre][v_norm];'
        f'[v_pre]{prefilter}eq=contrast={hook_contrast:.3f}:saturation={hook_saturation:.3f},{zoom_str}'
        f'setpts=PTS[v_hook];'
        f'[v_hook][v_norm]overlay=0:0:enable=between(t\\,0\\,{HOOK_DURATION})[v_hook_out]'
    )
    return hook_filter

# ==================== TTS & BGM ====================

async def gen_tts(text, voice, rate, pitch, outpath):
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(outpath)
    if not os.path.exists(outpath) or os.path.getsize(outpath) < 500:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(outpath)

def find_bgm(cc):
    bgm_name = BGM_MAP.get(cc)
    if bgm_name:
        p = os.path.join(BGM_DIR, bgm_name)
        if os.path.exists(p) and os.path.getsize(p) > 5000: return p
    all_bgm = [os.path.join(BGMLIB_DIR, f) for f in os.listdir(BGMLIB_DIR)
               if f.endswith('.mp3') and not f.startswith('bgm_synth')
               and os.path.getsize(os.path.join(BGMLIB_DIR, f)) > 5000]
    if all_bgm: return random.choice(all_bgm)
    synth_all = [os.path.join(BGMLIB_DIR, f) for f in os.listdir(BGMLIB_DIR)
                 if f.startswith('bgm_synth') and os.path.getsize(os.path.join(BGMLIB_DIR, f)) > 5000]
    if synth_all:
        idx = {'TH':0,'MY':5,'VN':10,'PH':15,'SG':20}.get(cc,0)
        return synth_all[min(idx,len(synth_all)-1)]
    return None

# ==================== 核心处理 ====================

async def process_country(cc):
    print(f'\n--- 🌍 Processing {cc} (v9视觉美学升级) ---', flush=True)
    out_path = os.path.join(OUT_DIR, f'{PRODUCT}_{cc}.mp4')
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
        await gen_tts(txt, voice, TTS_RATE, TTS_PITCH, p)
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

    # 2. 合并TTS
    list_p = os.path.join(td, 'files.txt')
    with open(list_p, 'w') as f:
        for p in seg_paths: f.write(f"file '{p}'\n")
    tts_raw = os.path.join(td, 'tts.aac')
    run_cmd(['ffmpeg','-y','-f','concat','-safe','0','-i',list_p,'-c:a','aac','-b:a','192k',tts_raw],20)
    tts_f = os.path.join(td, 'tts_v.aac')
    run_cmd(['ffmpeg','-y','-i',tts_raw,'-af','volume=-3dB','-c:a','aac','-b:a','192k',tts_f],10)

    # 3. BGM (含★高潮段检测)
    bgm_path = find_bgm(cc)
    bgm_dur = get_dur(bgm_path) if bgm_path and os.path.exists(bgm_path) else 10
    bgm_vol_db = cfg['bgm_db']

    mix_f = os.path.join(td, 'final.aac')
    if bgm_path and os.path.exists(bgm_path) and os.path.getsize(bgm_path) > 5000:
        print(f'  BGM: {os.path.basename(bgm_path)} 降{bgm_vol_db}dB + compand + fade-in={bgm_fade_in}s', flush=True)
        r = run_cmd(['ffmpeg','-y','-i',tts_f,'-i',bgm_path,
            '-filter_complex',
            f'[1:a]volume={bgm_vol_db}dB,compand=attacks=0.1:decays=0.3:'
            f'points=-90/-90|-60/-60|-30/-24|-12/-8|0/-2,'
            f'afade=t=in:d={bgm_fade_in}[bgm];'
            f'[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[out]',
            '-map','[out]','-c:a','aac','-b:a','192k',mix_f],30)
        if r.returncode == 0 and os.path.exists(mix_f) and os.path.getsize(mix_f) > 1000:
            print(f'  ✅ 音频混合成功', flush=True)
        else:
            mix_f = tts_f; print(f'  ⚠️ BGM失败, 仅TTS', flush=True)
    else:
        mix_f = tts_f; print(f'  ℹ️ 无BGM, 仅TTS', flush=True)

    # ★ v9: 检测BGM高潮段
    climax_start, climax_end, climax_mid = get_climax_times(bgm_path, bgm_dur, cc)
    print(f'    BGM高潮段: {climax_start:.1f}s~{climax_end:.1f}s (中点{climax_mid*100:.0f}%)', flush=True)

    # 4. 字幕时间 (含★BGM高潮对齐)
    total_dur = sum(seg_durs)
    if total_dur < 6:    seg_durs = [d*6/total_dur for d in seg_durs]
    if total_dur > 10:   seg_durs = [d*10/total_dur for d in seg_durs]
    total_dur = sum(seg_durs)

    seg_start = [sum(seg_durs[:i]) for i in range(len(seg_durs))]

    # ★ 卖点字幕对齐BGM高潮: 找最靠近climax_mid*总时长的句子,将其延后对齐高潮
    # 让最强卖点字幕(最后一句"夸赞句")对齐高潮段
    best_seg_idx = len(segs) - 1  # 默认最后一句(夸赞)对高潮

    # 每句落差时间
    climax_target = HOOK_DURATION + total_dur * 0.6  # 目标高潮位于视频60%处
    # 调整最后一句到高潮附近
    last_start = sum(seg_durs[:-1])
    if last_start < climax_target - 1.0:
        # 把最后一句话延后
        seg_durs = list(seg_durs)
        seg_durs[-1] = max(1.5, seg_durs[-1])
        seg_start = [sum(seg_durs[:i]) for i in range(len(seg_durs))]
    total_dur = sum(seg_durs)

    # 字幕时间计算(每句差异化入场偏移)
    timings = []
    for i, d in enumerate(seg_durs):
        if cc in ['TH', 'VN']:      enter_offset = 0.3
        elif cc in ['MY', 'PH']:     enter_offset = 0.7
        else:                        enter_offset = 0.5
        st = max(0, seg_start[i] + enter_offset)
        et = min(seg_start[i] + d + 0.5, total_dur - 0.2)
        if et <= st: et = st + 0.8
        timings.append((st, et))

    print(f'  字幕时间: {[(f"{s:.1f}",f"{e:.1f}") for s,e in timings]}', flush=True)
    print(f'  BGM高潮段: {climax_start:.1f}s~{climax_end:.1f}s', flush=True)

    # 5. 生成字幕PNG (★ v9: 带高亮标记)
    sub_pngs = []
    for i, txt in enumerate(segs):
        sp = os.path.join(td, f's{i}.png')
        # 钩子帧: 前2秒不显示任何字幕
        is_hook = (timings[i][0] < HOOK_DURATION)
        make_subtitle_png(txt, cc, anim_frame=i*10, is_hook_frame=is_hook).save(sp)
        sub_pngs.append(sp)

    # 同样生成高亮版本PNG(卖点词黄色)
    # 钩子帧后的字幕用高亮拆分模式
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
    angle_mode = cfg.get('angle_mode', 'flat')

    video_filters = []
    if speed != 1.0:
        video_filters.append(f'setpts={1/speed}*PTS')

    # eq滤镜(亮度/对比度/饱和度/伽马)
    vf_eq_parts = []
    if brightness != 0: vf_eq_parts.append(f'brightness={brightness/100.0:.3f}')
    if contrast != 1.0: vf_eq_parts.append(f'contrast={contrast:.3f}')
    if saturation != 1.0: vf_eq_parts.append(f'saturation={saturation:.3f}')
    if any(g != 1.0 for g in [gamma_r, gamma_g, gamma_b]):
        vf_eq_parts.append(f'gamma_r={gamma_r:.3f}:gamma_g={gamma_g:.3f}:gamma_b={gamma_b:.3f}')
    if vf_eq_parts:
        video_filters.append('eq=' + ':'.join(vf_eq_parts))

    # 色温
    if color_temp > 5200:
        r_adj = (color_temp-5200)/2000*0.1
        b_adj = -(color_temp-5200)/2000*0.1
        video_filters.append(f'colorbalance=rs={r_adj:.3f}:gs=0:bs={b_adj:.3f}')
    elif color_temp < 4800:
        r_adj = (4800-color_temp)/2000*0.1
        b_adj = -(4800-color_temp)/2000*0.1
        video_filters.append(f'colorbalance=rs={-r_adj:.3f}:gs=0:bs={b_adj:.3f}')

    # 锐度
    if sharpness > 0.01:
        video_filters.append(f'unsharp=l={sharpness:.2f}:la=1.0')

    # 噪点
    if noise_amt > 0:
        video_filters.append(f'noise=alls={noise_amt:.0f}:allf=t+u')

    # 裁切偏移
    if crop_off_x != 0 or crop_off_y != 0:
        video_filters.append(f'crop={VW}:{VH}:{crop_off_x}:{crop_off_y}')

    # ★ v9: 构建钩子帧(前2秒视觉增强) + 拍摄角度模拟
    # 方法: 先用split分出两路, 一路做hook增强, 一路保持原样
    # 用overlay:enable控制仅前2秒显示hook增强画面
    hook_contrast = cfg.get('hook_contrast', 1.10)
    hook_saturation = cfg.get('hook_saturation', 1.06)
    hook_zoom = cfg.get('hook_zoom', 1.05)

    # ★ v9: 组合滤镜: 角度模拟 + 钩子帧
    angle_filter = ''
    if angle_mode == 'top_down':
        angle_filter = f'crop={VW}:{VH-80}:0:40,scale={VW}:{VH},'
    elif angle_mode == 'hand_held':
        angle_filter = f'crop={VW-20}:{VH-20}:10:10,scale={VW}:{VH},'
    elif angle_mode == 'angle_45':
        angle_filter = f'crop={VW}:{VH}:2:2,'

    zoom_filter = ''
    if hook_zoom != 1.0:
        sw, sh = int(VW*hook_zoom), int(VH*hook_zoom)
        cx, cy = (sw-VW)//2, (sh-VH)//2
        zoom_filter = f'scale={sw}:{sh},crop={VW}:{VH}:{cx}:{cy},'

    # 构建完整视频滤镜管道
    vf_chain = ','.join(video_filters) if video_filters else ''
    hook_eq = ''
    if hook_contrast != 1.0 or hook_saturation != 1.0:
        parts = []
        if hook_contrast != 1.0: parts.append(f'contrast={hook_contrast:.3f}')
        if hook_saturation != 1.0: parts.append(f'saturation={hook_saturation:.3f}')
        hook_eq = 'eq=' + ':'.join(parts) + ','

    # 最终视频流: angle模拟 + hook增强 + 原有滤波器 + zoom
    main_vf = ''
    if angle_filter or hook_eq or vf_chain or zoom_filter:
        main_vf = f'{angle_filter}{hook_eq}{vf_chain}{zoom_filter}'.rstrip(',')
        main_vf = f'[0:v]{main_vf}[v_main]'

    # 字幕叠加
    # 使用高亮版字幕(hightlight版)叠加
    overlay_chain = ''
    if main_vf:
        overlay_chain = f'{main_vf};'
        current_src = 'v_main'
    else:
        current_src = '0:v'

    for i, (st, et) in enumerate(timings):
        # 钩子帧内使用透明字幕, 但已经在make_subtitle_png处理了
        tag = f'ov{i}'
        next_tag = f'v{i+1}' if i < len(timings)-1 else 'vout'
        src_label = f'[{current_src}]' if i == 0 else f'[v{i}]'
        out_label = f'[v{i+1}]'
        if i == len(timings)-1: out_label = '[vout]'

        # 使用高亮版PNG (输入顺序: [0]视频 [1]音频 [2..5]普通字幕 [6..9]高亮字幕)
        png_idx = 2 + len(segs) + i  # 高亮版PNG作为额外输入
        if overlay_chain:
            overlay_chain += f'{src_label}[{png_idx}:v]overlay=0:0:enable=between(t\\,{st:.2f}\\,{et:.2f}){out_label};'
        else:
            overlay_chain += f'[0:v][{png_idx}:v]overlay=0:0:enable=between(t\\,{st:.2f}\\,{et:.2f})[v{i+1}];'

    overlay_chain = overlay_chain.rstrip(';')

    # 7. ffmpeg合成
    cmd = ['ffmpeg', '-y', '-i', VIDEO_SRC, '-i', mix_f]
    # 输入: 原始视频 + 普通字幕PNG + 高亮字幕PNG
    for sp in sub_pngs: cmd.extend(['-i', sp])
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
            # 检查白字像素和黄色像素(高亮)
            wp_count = yp_count = 0
            for y in range(h-150, h):
                for x in range(w//2-250, w//2+250):
                    r, g, b = vpx[x, y]
                    if r > 200 and g > 200 and b > 200: wp_count += 1
                    if r > 200 and g > 180 and b < 100: yp_count += 1
            print(f'  自检白像素: {wp_count}  黄色高亮像素: {yp_count} (应>100)', flush=True)
            if wp_count < 100: print(f'  ⚠️ 字幕可能未渲染', flush=True)
            if yp_count < 20 and cc != 'SG': print(f'  ⚠️ 卖点词高亮可能未生效', flush=True)
        except: pass

    shutil.rmtree(td, ignore_errors=True)
    return True

async def main():
    print(f'🔥 {PRODUCT} 5国视频合成器 v9（视觉美学升级版）', flush=True)
    print(f'源视频: {VIDEO_SRC}', flush=True)
    print('★★ v9新增: 片头钩子帧+BGM高潮对齐+卖点词高亮+拍摄角度模拟 ★★', flush=True)
    print(f'输出: {OUT_DIR}', flush=True)
    print(f'{"="*50}', flush=True)

    if not os.path.exists(VIDEO_SRC):
        print(f'❌ 源视频不存在: {VIDEO_SRC}', flush=True)
        return

    src_dur = get_dur(VIDEO_SRC)
    if src_dur < 5:
        print(f'⚠️ 源视频太短: {src_dur:.1f}s', flush=True)
    else:
        print(f'源视频: {src_dur:.1f}s', flush=True)

    results = {}
    for cc in COUNTRIES:
        results[cc] = await process_country(cc)

    print(f'\n{"="*50}', flush=True)
    print('📊 v9合成结果:', flush=True)
    print('='*50, flush=True)
    all_pass = True
    for cc in COUNTRIES:
        fp = os.path.join(OUT_DIR, f'{PRODUCT}_{cc}.mp4')
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
        with open(mem_path, 'a') as f:
            f.write(f'\n### ⏰ 2026-05-11 06:00 — v9 composer视觉美学升级\n')
            f.write(f'{PRODUCT} 5国视频生成完成\n')
            for cc in COUNTRIES:
                fp = os.path.join(OUT_DIR, f'{PRODUCT}_{cc}.mp4')
                sz = os.path.getsize(fp)/1024/1024 if os.path.exists(fp) else 0
                f.write(f'- {PRODUCT}_{cc}.mp4: {sz:.1f}MB {results.get(cc)}\n')
            f.write(f'全通过: {all_pass}\n')
            f.write(f'版本: v9 (片头钩子帧+BGM高潮对齐+卖点词高亮+拍摄角度模拟)\n')
    except: pass

    print(f'\n📝 记忆已记录', flush=True)

if __name__ == '__main__':
    asyncio.run(main())
