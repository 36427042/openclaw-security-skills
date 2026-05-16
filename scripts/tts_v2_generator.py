#!/usr/bin/env python3
"""
🥕 萝卜 v2 配音生成器
SSML增强 + 情感语调控制 + 多引擎TTS
生成5国×2条话术音频到 ~/Desktop/配音输出/v2/
"""

import asyncio
import os
import subprocess
import shutil

OUTPUT_DIR = os.path.expanduser("~/Desktop/配音输出/v2")
V1_DIR = os.path.expanduser("~/Desktop/配音输出/v1")

# ==================== 配置 ====================
VOICES = {
    "th": {"voice": "th-TH-PremwadeeNeural", "lang": "th-TH", "name": "泰语"},
    "my": {"voice": "ms-MY-YasminNeural", "lang": "ms-MY", "name": "马来语"},
    "vn": {"voice": "vi-VN-HoaiMyNeural", "lang": "vi-VN", "name": "越南语"},
    "ph": {"voice": "fil-PH-BlessicaNeural", "lang": "fil-PH", "name": "菲律宾语"},
    "id": {"voice": "id-ID-GadisNeural", "lang": "id-ID", "name": "印尼语"},
}

# SSML风格可用的style值（所有语音通用，实际效果因语言而异）
EMOTION_STYLES = ["cheerful", "friendly", "excited", "newscast", "empathetic", "default"]

# ==================== 话术模板 ====================
SCRIPTS = {
    "th": [
        {  # 开场话术
            "name": "开场-美容仪",
            "emotion": "cheerful",
            "text": (
                '<mstts:express-as style="cheerful">'
                'สวัสดีค่าา~ ทุกคนนน <break time="300ms"/> วันนี้เรามีเครื่องนวดหน้าสุดปัง '
                '<emphasis level="moderate">ลดริ้วรอย</emphasis> ช่วยยกกระชับ '
                'มาแนะนำค่าา'
                '</mstts:express-as>'
            ),
            "rate": "-3%",
            "pitch": "+6Hz",
            "params": {}
        },
        {  # 产品展示话术
            "name": "产品展示-护肤",
            "emotion": "friendly",
            "text": (
                '<mstts:express-as style="friendly">'
                '<prosody rate="-5%">ตัวนี้เป็นเซรั่มคุณภาพดี </prosody>'
                '<break time="200ms"/> '
                'มีส่วนผสมของ <emphasis level="moderate">วิตามินซี</emphasis> '
                'และไฮยาลูรอน <break time="300ms"/> '
                'ใช้แล้วผิว <prosody rate="-10%">กระจ่างใส ดูอ่อนเยาว์</prosody>'
                '</mstts:express-as>'
            ),
            "rate": "-5%",
            "pitch": "+4Hz",
            "params": {}
        },
    ],
    "my": [
        {
            "name": "开场-美容仪",
            "emotion": "cheerful",
            "text": (
                '<mstts:express-as style="cheerful">'
                'Hai semua! <break time="300ms"/> '
                'Hari ni kami nak推介 <emphasis level="moderate">produk kecantikan terbaru</emphasis> '
                'yang tengah viral! <break time="200ms"/> '
                'Jom kita tengok sama-sama~'
                '</mstts:express-as>'
            ),
            "rate": "-3%",
            "pitch": "+5Hz",
            "params": {}
        },
        {
            "name": "产品展示-护肤",
            "emotion": "friendly",
            "text": (
                '<mstts:express-as style="friendly">'
                '<prosody rate="-5%">Produk ni <emphasis level="moderate">100% original</emphasis> '
                'dan berkualiti tinggi.</prosody> '
                '<break time="200ms"/> '
                'teksturnya ringan dan cepat meresap. '
                '<break time="300ms"/> '
                '<prosody rate="-8%">Cuba sekali, mesti nak lagi!</prosody>'
                '</mstts:express-as>'
            ),
            "rate": "-5%",
            "pitch": "+4Hz",
            "params": {}
        },
    ],
    "vn": [
        {
            "name": "开场-美容仪",
            "emotion": "cheerful",
            "text": (
                '<mstts:express-as style="cheerful">'
                'Xin chào các bạn! <break time="300ms"/> '
                'Hôm nay mình giới thiệu sản phẩm '
                '<emphasis level="moderate">máy rửa mặt</emphasis> '
                'siêu hot <break time="200ms"/> '
                'cực kỳ êm ái và sạch sâu nha!'
                '</mstts:express-as>'
            ),
            "rate": "-3%",
            "pitch": "+5Hz",
            "params": {}
        },
        {
            "name": "产品展示-护肤",
            "emotion": "friendly",
            "text": (
                '<mstts:express-as style="friendly">'
                '<prosody rate="-5%">Kem dưỡng này có chứa </prosody>'
                '<emphasis level="moderate">Vitamin C và HA</emphasis> '
                '<break time="200ms"/> '
                'giúp da <prosody rate="-8%">sáng mịn và đều màu</prosody> '
                '<break time="300ms"/> '
                'Dùng đều đặn mỗi ngày nha các bạn!'
                '</mstts:express-as>'
            ),
            "rate": "-5%",
            "pitch": "+4Hz",
            "params": {}
        },
    ],
    "ph": [
        {
            "name": "开场-美容仪",
            "emotion": "cheerful",
            "text": (
                '<mstts:express-as style="cheerful">'
                'Hello everyone! <break time="300ms"/> '
                'Guess what? <break time="200ms"/> '
                'Meron tayong <emphasis level="moderate">bago at super worth it</emphasis> '
                'na product ngayon! <break time="200ms"/> '
                'Sige, watch ’til the end for the price~'
                '</mstts:express-as>'
            ),
            "rate": "-3%",
            "pitch": "+5Hz",
            "params": {}
        },
        {
            "name": "产品展示-护肤",
            "emotion": "friendly",
            "text": (
                '<mstts:express-as style="friendly">'
                '<prosody rate="-5%">Ang serum na ito ay </prosody>'
                '<emphasis level="moderate">mild and gentle</emphasis> '
                'sa skin. <break time="200ms"/> '
                'May <prosody rate="-8%">Vitamin C at Niacinamide</prosody> '
                'para sa glowing skin mo~ <break time="300ms"/> '
                'Super worth it, promise!'
                '</mstts:express-as>'
            ),
            "rate": "-5%",
            "pitch": "+4Hz",
            "params": {}
        },
    ],
    "id": [
        {
            "name": "开场-美容仪",
            "emotion": "cheerful",
            "text": (
                '<mstts:express-as style="cheerful">'
                'Halo semuanya! <break time="300ms"/> '
                'Ada produk <emphasis level="moderate">baru yang lagi viral</emphasis> '
                'nih! <break time="200ms"/> '
                'Wajib banget kalian coba~'
                '</mstts:express-as>'
            ),
            "rate": "-3%",
            "pitch": "+5Hz",
            "params": {}
        },
        {
            "name": "产品展示-护肤",
            "emotion": "friendly",
            "text": (
                '<mstts:express-as style="friendly">'
                '<prosody rate="-5%">Produk ini <emphasis level="moderate">kualitasnya bagus</emphasis> '
                'banget.</prosody> '
                '<break time="200ms"/> '
                'Teksturnya ringan dan cepat meresap. '
                '<break time="300ms"/> '
                '<prosody rate="-8%">Cocok banget buat kamu yang mau glowing~</prosody>'
                '</mstts:express-as>'
            ),
            "rate": "-5%",
            "pitch": "+4Hz",
            "params": {}
        },
    ],
}


def ensure_mp3_extension(filename):
    """Ensure filename has .mp3 extension"""
    if not filename.endswith('.mp3'):
        return filename + '.mp3'
    return filename


async def generate_tts(text, voice, rate, pitch, filename):
    """Generate TTS audio using edge-tts with SSML"""
    from edge_tts import Communicate
    
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    try:
        communicate = Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume="+0%"
        )
        await communicate.save(filepath)
        
        size_kb = os.path.getsize(filepath) / 1024
        return {"status": "ok", "size_kb": size_kb, "filepath": filepath}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def generate_v1_comparison():
    """Compare v1 vs v2 if v1 files exist"""
    if not os.path.exists(V1_DIR):
        print("ℹ️ No v1 directory found for comparison")
        return
    
    v1_files = [f for f in os.listdir(V1_DIR) if f.endswith('.mp3')]
    if not v1_files:
        print("ℹ️ No v1 files found for comparison")
        return
    
    print(f"\n📊 v1 vs v2 文件大小对比:")
    print(f"{'文件':<40} {'v1(KB)':<15} {'v2(KB)':<15} {'变化':<15}")
    print("-" * 85)
    
    for v2_f in sorted(os.listdir(OUTPUT_DIR)):
        if not v2_f.endswith('.mp3'):
            continue
        v2_size = os.path.getsize(os.path.join(OUTPUT_DIR, v2_f)) / 1024
        
        # Find matching v1 file
        v1_found = False
        for v1_f in v1_files:
            # Match by country code (first part of filename)
            if v2_f[:6] == v1_f[:6] or v2_f.split('_')[0] == v1_f.split('_')[0]:
                v1_size = os.path.getsize(os.path.join(V1_DIR, v1_f)) / 1024
                change = ((v2_size - v1_size) / v1_size) * 100
                print(f"{v2_f:<40} {v1_size:<15.1f} {v2_size:<15.1f} {change:+.1f}%")
                v1_found = True
                break
        
        if not v1_found:
            print(f"{v2_f:<40} {'-':<15} {v2_size:<15.1f} {'N/A':<15}")


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("=" * 60)
    print("🥕 萝卜 v2 配音生成器 - SSML增强版")
    print(f"⏰ 开始时间: {__import__('datetime').datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    total = 0
    success = 0
    errors = []
    
    for lang_code, lang_info in VOICES.items():
        lang_name = lang_info["name"]
        scripts = SCRIPTS.get(lang_code, [])
        
        print(f"\n🌍 [{lang_code}] {lang_name} - {len(scripts)}段话术")
        
        for i, script in enumerate(scripts):
            filename = f"{lang_code}_{script['name']}_{script['emotion']}_v2.mp3"
            total += 1
            
            print(f"  📝 {i+1}/{len(scripts)} {filename}")
            
            result = await generate_tts(
                text=script["text"],
                voice=lang_info["voice"],
                rate=script["rate"],
                pitch=script["pitch"],
                filename=filename
            )
            
            if result["status"] == "ok":
                success += 1
                print(f"    ✅ {result['size_kb']:.1f} KB")
            else:
                errors.append(f"{lang_code}/{filename}: {result['error']}")
                print(f"    ❌ ERROR: {result['error']}")
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"📊 生成完成!")
    print(f"   ✅ 成功: {success}/{total}")
    if errors:
        print(f"   ❌ 失败: {len(errors)}")
        for e in errors:
            print(f"      - {e}")
    
    # Compare with v1
    await generate_v1_comparison()
    
    # List all v2 files
    print(f"\n📁 输出目录: {OUTPUT_DIR}")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        size = os.path.getsize(os.path.join(OUTPUT_DIR, f)) / 1024
        if f.endswith('.mp3'):
            print(f"   {f:<50} {size:.1f} KB")


if __name__ == "__main__":
    asyncio.run(main())
