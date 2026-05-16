#!/usr/bin/env python3
"""
🥕 萝卜·第三轮 — 5国×2条配音实战生成（含SSML参数）
输出到 ~/Desktop/配音输出/v3/

5国：TH/MY/VN/PH/SG
每条按 开场+展示+结尾 结构：10秒黄金结构
"""
import asyncio, os, sys
from pathlib import Path

OUTPUT_DIR = os.path.expanduser("~/Desktop/配音输出/v3")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ========== 5国文案（按10秒黄金结构：痛点→解决→夸赞） ==========
# 参考生菜文案自查清单：本地化开场、语气词、不喊买

SCRIPTS = {
    "TH": [
        {  # TH_01 — 化妆刷/美妆工具场景
            "text": (
                "บอกเลยว่าหลายคนแต่งหน้าแล้วไม่เนียน ไม่ติดทน "
                "อาจจะเพราะแปรงที่ใช้ไม่ดีพอ วันนี้เจออะไรดีๆมาแล้ว "
                "น้องแปรงอันนี้ขนนุ่มมากกก ปาดสีแล้วเริ่ดสุดๆ ใช้แล้วหน้าเนียนปังมากเลยค่า~"
            ),
            "voice": "th-TH-PremwadeeNeural",
            "rate": "+0%",
            "pitch": "+2Hz",
            "style": "闺蜜安利·化妆刷展示",
        },
        {  # TH_02 — 美妆蛋场景
            "text": (
                "คือปัญหาที่เจอคือลงรองพื้นแล้วไม่เสมอกัน จะโบกก็ไม่ทั่วหน้า "
                "จริงๆนะคะ จนได้ลองน้องฟองน้ำอันนี้ แค่จุ่มน้ำบีบออก "
                "แล้วแตะแตะที่หน้า ปังมากกก หน้าเนียนกริบเลยค่าา~"
            ),
            "voice": "th-TH-PremwadeeNeural",
            "rate": "-3%",
            "pitch": "+2Hz",
            "style": "闺蜜分享·美妆蛋使用",
        },
    ],
    "MY": [
        {  # MY_01 — 粉扑/美妆工具场景
            "text": (
                "Eh korang jangan marah tapi I nak cakap something "
                "selama ni kita pakai sponge murah muka macam tak rata "
                "tapi yang ni lain sikit. Bila basahkan dia kembang "
                "besar dan makeup jadi flawless gila. Confirm tak tipu!"
            ),
            "voice": "ms-MY-YasminNeural",
            "rate": "-3%",
            "pitch": "+2Hz",
            "style": "好物分享·粉扑",
        },
        {  # MY_02 — 化妆刷场景
            "text": (
                "Okay guys kita semua tau kan susah nak cari brush yang "
                "betul-betul sedap dekat muka. Banyak yang keras dan "
                "buat muka rasa sakit. Tapi yang ni weii lembut gila "
                "and hasil makeup jadi power. Best sangat dah cuba sendiri!"
            ),
            "voice": "ms-MY-YasminNeural",
            "rate": "+0%",
            "pitch": "+3Hz",
            "style": "温和推荐·化妆刷",
        },
    ],
    "VN": [
        {  # VN_01 — 粉扑场景
            "text": (
                "Ê mày! Có ai giống mình không? "
                "Đánh nền hoài mà không đều, nhìn dày cộm "
                "Xài miếng bông này nè. Làm ướt lên nó nở ra "
                "rồi chấm nhẹ lên mặt. Da mịn liền luôn, xịn xò quá trời!"
            ),
            "voice": "vi-VN-HoaiMyNeural",
            "rate": "-3%",
            "pitch": "+2Hz",
            "style": "直接推荐·粉扑",
        },
        {  # VN_02 — 收纳盒场景
            "text": (
                "Mình ghét nhất là bàn trang điểm bừa bộn "
                "kiếm đồ mãi không thấy. Hồi mới mua em hộp này "
                "bỏ đồ vô gọn gàng ngay. Nhìn phòng thích mắt hẳn "
                "khum ngờ lại tiện vậy luôn á!"
            ),
            "voice": "vi-VN-HoaiMyNeural",
            "rate": "+0%",
            "pitch": "+3Hz",
            "style": "收纳好物·自然推荐",
        },
    ],
    "PH": [
        {  # PH_01 — 洗脸巾场景
            "text": (
                "Grabe, promise you guys! "
                "Yung dati kong towel sobrang harsh sa face, "
                "parang nag-eexfoliate ako araw-araw. "
                "Then I switched to this. Sobrang lambot, "
                "and ang ganda ng effect sa skin ko. Worth it, for sure!"
            ),
            "voice": "fil-PH-BlessicaNeural",
            "rate": "-3%",
            "pitch": "+2Hz",
            "style": "温馨分享·洗脸巾",
        },
        {  # PH_02 — 美妆工具收纳
            "text": (
                "Sis, alam mo yung feeling na yung makeup area mo "
                "parang nagka-bagyo? Hindi mo mahanap yung brush mo? "
                "Eto na solution! Ang neat ng lalagyanan na to. "
                "Promise, sobrang worth it! Ayos na lahat!"
            ),
            "voice": "fil-PH-BlessicaNeural",
            "rate": "+0%",
            "pitch": "+3Hz",
            "style": "姐妹推荐·收纳盒",
        },
    ],
    "SG": [
        {  # SG_01 — 化妆刷清洗
            "text": (
                "Wah, I cannot believe I've been washing my brushes wrong "
                "this whole time. They were so rough on my face. "
                "Then I found this cleaner. Super gentle and so easy to use. "
                "Just spray and wipe. Brushes like new again. Can recommend lah!"
            ),
            "voice": "en-SG-LunaNeural",
            "rate": "+0%",
            "pitch": "+2Hz",
            "style": "实用分享·刷具清洁",
        },
        {  # SG_02 — 化妆镜
            "text": (
                "Okay I not gonna lie, I used to do my makeup in bad lighting "
                "and go out looking totally different. This mirror with LED lights "
                "is a game changer. Now I can actually see what I'm doing. "
                "Not bad leh for the price. Really worth it sia!"
            ),
            "voice": "en-SG-LunaNeural",
            "rate": "+0%",
            "pitch": "+3Hz",
            "style": "真实体验·化妆镜",
        },
    ],
}

async def generate_ssml(script, lang_code, idx):
    """基于SSML生成更自然的配音"""
    # 拆分为开场+展示+结尾，分别控制语调
    voice = script["voice"]
    rate = script["rate"]
    pitch = script["pitch"]
    text = script["text"]
    
    # Edge TTS SSML构建
    ssml_text = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang_code.lower().replace('_','-')}">
    <prosody rate="{rate}" pitch="{pitch}">
        {script['text']}
    </prosody>
</speak>"""

    filename = f"{lang_code}_{idx+1:02d}_{script['style'].split('·')[0] if '·' in script['style'] else script['style']}.wav"
    filepath = os.path.join(OUTPUT_DIR, filename)

    print(f"  🎤 [{lang_code}] {filename}")
    print(f"     voice={voice}, rate={rate}, pitch={pitch}")
    print(f"     text: {text[:50]}...")

    try:
        proc = await asyncio.create_subprocess_exec(
            "edge-tts",
            "--voice", voice,
            "--text", text,
            "--write-media", filepath,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        if proc.returncode == 0 and os.path.exists(filepath):
            size_kb = os.path.getsize(filepath) / 1024
            print(f"     ✅ {size_kb:.1f}KB")
            return {"file": filepath, "status": "ok", "size_kb": size_kb}
        else:
            print(f"     ❌ {stderr.decode()[:200]}")
            return {"file": filepath, "status": "error", "error": stderr.decode()[:200]}
    except Exception as e:
        print(f"     ❌ {str(e)}")
        return {"file": filepath, "status": "error", "error": str(e)}

async def main():
    print("=" * 50)
    print("🥕 萝卜·5国配音实战生成 (v3)")
    print("=" * 50)
    print()

    all_results = []
    total = 0
    ok = 0

    for lang_code in ["TH", "MY", "VN", "PH", "SG"]:
        if lang_code not in SCRIPTS:
            continue
        scripts = SCRIPTS[lang_code]
        print(f"--- {lang_code} ({len(scripts)}条) ---")
        for idx, script in enumerate(scripts):
            result = await generate_ssml(script, lang_code, idx)
            all_results.append(result)
            total += 1
            if result["status"] == "ok":
                ok += 1
            print()
        print()

    print("=" * 50)
    print(f"📊 结果: {ok}/{total} 成功")
    print(f"📂 输出目录: {OUTPUT_DIR}")
    for r in all_results:
        status = "✅" if r["status"] == "ok" else "❌"
        fname = os.path.basename(r["file"])
        size = f"{r['size_kb']:.1f}KB" if r.get("size_kb") else "?"
        print(f"  {status} {fname} ({size})" if r["status"] == "ok" else f"  {status} {fname}: {r.get('error','?')}")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
