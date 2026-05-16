#!/usr/bin/env python3
"""
🥕 萝卜·配音引擎 - 直播间/短视频 TTS 配音
功能：Edge TTS 多语言配音生成
GEP: 记录TTS失败和备选方案
用法：python3 qwen_tts_engine.py [text] [lang]
"""
import asyncio, json, os, subprocess, sys, time
from pathlib import Path
from gep_engine import GEP

gep = GEP("萝卜")

OUTPUT_DIR = os.path.expanduser("~/Desktop/配音输出")
LANGUAGES = {
    "TH": {"voice": "th-TH-PremangadeeNeural", "name": "🇹🇭 泰语"},
    "MY": {"voice": "ms-MY-YasminNeural", "name": "🇲🇾 马来语"},
    "VN": {"voice": "vi-VN-HoaiMyNeural", "name": "🇻🇳 越南语"},
    "ID": {"voice": "id-ID-GadisNeural", "name": "🇮🇩 印尼语"},
    "PH": {"voice": "fil-PH-BlessicaNeural", "name": "🇵🇭 菲律宾语"},
    "ZH": {"voice": "zh-CN-XiaoxiaoNeural", "name": "🇨🇳 中文"},
}

def generate_tts(text: str, lang: str = "ZH", filename: str = None) -> dict:
    """用 Edge TTS 生成配音（GEP增强）"""
    if lang not in LANGUAGES:
        lang = "ZH"
    voice = LANGUAGES[lang]["voice"]

    # GEP: 检查该语言TTS历史成功率
    ctx = {"lang": lang, "voice": voice}
    advice = gep.pre_check("generate_tts", ctx)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not filename:
        safe = "".join(c if c.isalnum() else "_" for c in text[:20]).strip("_")
        filename = f"tts_{lang}_{safe or 'voice'}.mp3"
    output_path = os.path.join(OUTPUT_DIR, filename)

    try:
        start = time.time()
        result = subprocess.run(
            ["edge-tts", "--voice", voice, "--text", text, "--write-media", output_path],
            capture_output=True, text=True, timeout=30
        )
        duration = round(time.time() - start, 2)

        if result.returncode == 0 and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            gep.post_record("generate_tts", ctx, "success")
            return {
                "status": "ok", "lang": lang, "voice": voice,
                "file": output_path, "size": file_size, "duration": duration,
                "name": LANGUAGES[lang]["name"],
            }
        else:
            error_msg = result.stderr[:200] if result.stderr else f"returncode={result.returncode}"
            gep.post_record("generate_tts", ctx, "failed", problem=error_msg,
                            solution=f"检查edge-tts或换{lang}其他音色")
            return {"status": "error", "lang": lang, "voice": voice,
                    "error": error_msg, "duration": duration}
    except subprocess.TimeoutExpired:
        gep.post_record("generate_tts", ctx, "timeout", problem="TTS超时",
                        solution="缩短文本或加大超时")
        return {"status": "timeout", "lang": lang, "voice": voice}
    except FileNotFoundError:
        gep.post_record("generate_tts", ctx, "missing_tool",
                        problem="edge-tts未安装",
                        solution="pip install edge-tts")
        return {"status": "error", "error": "edge-tts not installed (pip install edge-tts)"}

def generate_5_countries(text: str) -> list:
    """生成5国配音"""
    results = []
    for lang_code in ["TH", "MY", "VN", "ID", "PH"]:
        result = generate_tts(text, lang_code)
        results.append(result)
        status_icon = "✅" if result["status"] == "ok" else "❌"
        name = LANGUAGES[lang_code]["name"]
        if result["status"] == "ok":
            print(f"  {status_icon} {name}: {result['file']}")
        else:
            print(f"  {status_icon} {name}: {result.get('error', result['status'])}")
    return results

def main(text: str = None, lang: str = None, output_dir: str = None):
    """TTS配音引擎主入口
    接收参数，生成多国配音，输出JSON到stdout供框架捕获
    """
    if output_dir:
        global OUTPUT_DIR
        OUTPUT_DIR = output_dir

    if text is None:
        text = "欢迎来到我们的直播间，今天给大家带来超值好物！"

    if lang and lang != "ALL":
        # 单语言模式
        result = generate_tts(text, lang)
        print(json.dumps(result, ensure_ascii=False))
    else:
        # 5国模式
        print(f"🎤 萝卜·配音引擎 (GEP进化引擎已加载)")
        print(f"   文本: {text[:60]}...")
        print(f"   生成5国配音...")
        results = generate_5_countries(text)
        ok = sum(1 for r in results if r["status"] == "ok")
        print(f"  {'─'*30}")
        print(f"  📊 {ok}/{len(results)} 生成成功")

        # JSON stdout — 框架捕获
        stats = gep.get_stats()
        output = {
            "status": "completed",
            "text": text[:60],
            "results": results,
            "success_count": ok,
            "total": len(results),
            "gep_stats": stats,
        }
        print(json.dumps(output, ensure_ascii=False))

    return 0

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="🥕 萝卜·配音引擎 - TTS多语言配音")
    parser.add_argument("--text", default=None, help="配音文本")
    parser.add_argument("--lang", default="ALL", choices=["TH","MY","VN","ID","PH","ZH","ALL"], help="语言代码(默认ALL=5国)")
    parser.add_argument("--output-dir", default=None, help="输出目录")
    args = parser.parse_args()
    sys.exit(main(args.text, args.lang, args.output_dir))
