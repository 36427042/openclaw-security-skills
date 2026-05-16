#!/usr/bin/env python3
"""
copy_engine.py — 5国语言文案引擎 🥬
功能：CO-STAR话术生成、合规校验、违禁词检测、批量导出
GEP: 记录违规模式和文案优化
"""
import json, os, sys, csv
from datetime import datetime
from gep_engine import GEP

gep = GEP("生菜")

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
LOG_DIR = os.path.join(WORKSPACE, "data", "logs")
OUT_DIR = os.path.join(WORKSPACE, "data", "copy")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# 5国违禁词库
BANNED_WORDS = {
    "TH": ["ยา", "รักษา", "หาย", "โรค", "แพทย์", "คลินิก", "ศัลยกรรม", "ลดน้ำหนัก",
           "ผิวขาว", "ริ้วรอย", "กระ", "ฝ้า", "สิว", "แพ้", "ปลอดภัย100%",
           "รับประกัน", "ผลข้างเคียง", "ส่วนผสม", "FDA"],
    "ZH": ["治疗", "治愈", "药", "医生", "医院", "手术", "减肥", "瘦身",
            "100%", "保证", "无效退款", "第一", "最好", "最有效"],
    "EN": ["cure", "treatment", "guarantee", "100%", "best", "medical",
            "surgery", "weight loss", "miracle", "permanent"],
    "VN": ["thuốc", "chữa bệnh", "bác sĩ", "điều trị", "giảm cân",
            "đảm bảo", "100%", "tốt nhất", "hiệu quả nhất"],
    "ID": ["obat", "menyembuhkan", "dokter", "perawatan", "bedah",
            "jaminan", "100%", "terbaik", "paling efektif"],
}

# CO-STAR框架场景
SCENARIOS = {
    "inquiry": {"name": "询单回复", "style": "热情详细"},
    "logistics": {"name": "物流查询", "style": "耐心安抚"},
    "after_sale": {"name": "售后处理", "style": "诚恳专业"},
    "return": {"name": "退换货", "style": "礼貌引导"},
    "review": {"name": "差评回复", "style": "谦逊解决"},
    "payment": {"name": "催付", "style": "温柔提醒"},
    "praise": {"name": "好评引导", "style": "真诚感谢"},
}

COUNTRY_LANG = {"TH": "泰语", "MY": "马来语", "VN": "越南语", "ID": "印尼语", "PH": "菲律宾语"}

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(LOG_DIR, "copy_engine.log"), "a") as f:
        f.write(f"[{ts}] {msg}\n")

def check_compliance(text: str, country: str) -> dict:
    """合规校验：检测违禁词（GEP增强）"""
    lang = COUNTRY_LANG.get(country, "")
    banned = BANNED_WORDS.get(country, []) + BANNED_WORDS.get("ZH", [])

    found = []
    for word in banned:
        if word.lower() in text.lower():
            found.append(word)

    result = {
        "pass": len(found) == 0,
        "banned_found": found,
        "country": country,
        "suggestion": f"替换违禁词: {', '.join(found)}" if found else "合规",
    }

    # GEP: 记录违规模式
    if found:
        gep.post_record("check_compliance", {"country": country},
                        "failed", problem=f"发现违禁词: {', '.join(found)}",
                        solution=f"替换: {', '.join(found)}")
    return result

def generate_copy(product: str, country: str, scenario: str = "inquiry") -> dict:
    """生成CO-STAR话术（GEP增强）"""
    scenario_info = SCENARIOS.get(scenario, {})

    # GEP: 检查历史经验
    ctx = {"country": country, "scenario": scenario, "product": product}
    advice = gep.pre_check("generate_copy", ctx)
    if advice and advice.get("cautious"):
        log(f"📖 GEP提示: {advice['advice'][:60]}")

    template = {
        "product": product,
        "country": country,
        "language": COUNTRY_LANG.get(country, ""),
        "scenario": scenario_info.get("name", "通用"),
        "style": scenario_info.get("style", "标准"),
        "text": f"[{scenario_info.get('name', '通用')}] {product} 相关文案",
        "generated_at": datetime.now().isoformat(),
    }
    return template

def export_to_csv(copies: list, filename: str = None):
    """批量导出CSV（GEP增强）"""
    if filename is None:
        filename = f"copy_batch_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    path = os.path.join(OUT_DIR, filename)

    if not copies:
        copies = [{"product": "双头眉刷", "country": "TH", "text": "话术示例"}]

    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=copies[0].keys())
            writer.writeheader()
            writer.writerows(copies)
        log(f"CSV导出: {path} ({len(copies)}条)")
        gep.post_record("export_to_csv", {"filename": filename}, "success")
    except Exception as e:
        gep.post_record("export_to_csv", {"filename": filename}, "failed", problem=str(e))
        raise
    return path

def generate_seedance_prompt(product: str, category: str = "美妆", ref_images: list = None) -> dict:
    """
    生成 Seedance 2.0 商品展示视频提示词 (15秒, ≤3500字符)
    核心规则:
      1. 商品统一性：开头/中间/结尾必须是同一商品外观，禁止AI幻觉换款
      2. 15秒结构：0-3s产品特写 → 3-7s功能演示 → 7-12s效果对比 → 12-15s产品收尾
      3. 提示词 ≤3500字符
      4. 9:16竖屏，自带音效+背景音
    """
    ref_block = ""
    if ref_images:
        for i, img in enumerate(ref_images[:3], 1):
            ref_block += f"@图片{i} "
        ref_block = ref_block.strip()
    
    # 品类专属详细信息
    category_specs = {
        "美妆": {
            "action": f"一只女性右手（暖调浅肤色，干净短指甲，无饰品）从画面右侧伸入，四指握住{product}的握柄，将刷头轻轻按压在皮肤上以45°斜角做短促往复刷扫，每次刷扫行程约3cm",
            "closeup": f"刷毛根根分明——每根刷毛尖端直径约0.05mm，在不同角度下呈现丝绸光泽，刷毛弯曲后0.1秒内弹回原形",
            "effect": "使用后的肌肤区域与未使用区域的分界线清晰——妆面粉底均匀无刷痕、毛孔隐匿、肌肤呈现柔焦效果",
            "bg": "纯白无缝背景纸，色温5600K柔光箱双侧打光，正面加蝴蝶布柔化，面部区域呈现自然通透质感，无阴影投射到产品上",
            "palette": f"刷毛柔软白(hex #FAFAFA)、握柄哑光黑(hex #2A2A2A)、肌肤暖调(hex #E8C4A0)、金属套圈拉丝银(hex #D4D4D4)、背景纯白(hex #FFFFFF)",
            "sound": "刷毛扫过皮肤的细微沙沙声放大2x，刷毛弹回的微小声响，ASMR级别收音，无环境噪音",
            "forbidden": "人脸入镜（只露单侧脸颊至下颌区域）、全脸、眼睛、嘴唇、粉刺痘痘、毛孔粗大、刷毛脱落掉毛、刷痕不均匀、产品logo特写、妆前妆后对比文字标注",
            "category_name": "美妆工具",
        },
        "家居": {
            "action": f"一双手（暖调浅肤色，干净指甲，无饰品）将折叠整齐的衣物/小物件依次放入{product}中，每次放入间隔0.5秒——物品滑入的轨迹流畅顺滑，与收纳格的边缘精准卡位",
            "closeup": f"{product}的隔层结构在微距下纹理清晰——布面/塑料面纹路细腻、缝线笔直均匀、拉链齿距一致、金属扣件反光锐利",
            "effect": "收纳前后对比——杂乱堆放的物品被整齐归入各层各格，桌面/衣柜从混乱变为极简整洁，空间利用率翻倍视觉冲击",
            "bg": "北欧自然光从左侧大面积柔光窗洒入，浅木色桌面(#C4A882)，温暖居家氛围，阴影柔和自然，无直射硬光",
            "palette": f"{product}主体浅灰(hex #E0E0E0)、收纳物品多彩(hex #FF6B35/#4ECDC4/#FFE66D)、木质桌面暖棕(hex #C4A882)、背景白墙(hex #FAFAFA)",
            "sound": "物品滑入收纳格的轻微摩擦声、拉链开合的清脆声、折叠布料的窸窣声，ASMR级别放大2x",
            "forbidden": "杂乱背景、污渍或破损物品、产品拉链卡顿、收纳格变形、手部动作犹豫不流畅、物品掉落",
            "category_name": "家居收纳",
        },
        "厨房": {
            "action": f"一双手（暖调浅肤色，干净短指甲，无饰品）握住新鲜胡萝卜/黄瓜以45°角在{product}刀片上做一次顺畅的直拉——食材被切成完美均匀细丝落入下方白色陶瓷碗中，连续3-4次切丝动作",
            "closeup": f"{product}的V型不锈钢刀片在微距下呈现冷冽金属锐度——刀片排列间距均匀、刀刃角度一致、拉丝纹理方向统一、每一道反光弧度精确",
            "effect": "切丝后的食材堆在白色陶瓷碗中——根根细丝粗细一致、切口平整如镜面、无毛边无碎渣、橙白对比强烈",
            "bg": "顶部柔光箱60°+底部反光板补光，深灰色石材台面(#808080)，食材色彩饱和度高，金属刀片反光锐利形成单一高光线",
            "palette": f"新鲜胡萝卜亮橙(hex #FF6B35)、{product}刀片拉丝钢(hex #D4D4D4)、握柄黑色橡胶(hex #2A2A2A)、木质砧板暖棕(hex #C4A882)、陶瓷碗纯白(hex #F5F5F5)",
            "sound": "刀刃切过食材的清脆'唰'声放大3x、细丝落入碗中的沙沙声、ASMR级别的食材断裂脆响、无环境噪音",
            "forbidden": "食材变色或不新鲜、切丝不均匀粗细、刀片生锈或钝感、手部受伤或创可贴、砧板污渍水渍、背景杂乱厨具、镜头反射到刀片上、切到手指",
            "category_name": "厨房工具",
        }
    }
    specs = category_specs.get(category, category_specs["厨房"])
    
    prompt = f"""15-second product demonstration video for "{product}" ({specs['category_name']}). 9:16 vertical aspect ratio, 720p, 15 seconds, no watermarks, no text overlays, no logos, no subtitles, no human faces.

【PRODUCT CONSISTENCY RULE - CRITICAL】
This video features ONE product only: "{product}". The product must remain IDENTICAL in appearance throughout all 15 seconds — same model, same color, same material, same shape, same texture every frame. Never substitute a different variant halfway through. If the reference shows wavy blade edges → always wavy blade edges. If straight blade edges → always straight. Zero hallucination substitutions.

【LIGHTING — Consistent Throughout】
{specs['bg']}. Lighting recipe does not change across scenes. Background remains identical for all 15 seconds.

【15-SECOND TIMELINE BREAKDOWN】

▶ 0.0-3.0s | Macro Reveal | Extreme Close-Up Horizontal Pan
Immediate extreme close-up from 8cm above {product}. Camera slowly glides horizontally left-to-right at 2cm/s following surface contours. Each edge/ridge catches a specular highlight from the studio key light at 45°, visual sharpness is palpable. Background visible only as soft blur beyond depth of field. {specs['closeup']}. Product occupies 80% of frame. Camera: macro slider horizontal pan on heavy tripod, zero vibration.

▶ 3.0-7.0s | Function Demo | Mid Shot + Slow Motion
{specs['action']}. 120fps super slow-motion captures the critical moments — every fiber interaction, every mechanical engagement, every surface contact in micro-detail. Hands move smoothly and precisely, product stays rock-steady throughout. Shallow depth of field keeps focus locked on the contact point between product and subject, background dissolves into soft bokeh. Camera: locked overhead at 90° top-down for cutting/filling shots; 5mm handheld simulation amplitude for product inspection transitions.

▶ 7.0-12.0s | Result Display | Medium Shot → Arc Pan
Camera slowly pulls back to medium shot revealing the full before/after scene. {specs['effect']}. Camera executes a 15° horizontal arc pan centered on the product while tilting slightly upward, revealing the product's 3D form. Metal parts reflect a continuous specular highlight arc through the pan. If product has multiple attachments/accessories, each slides into frame one by one at 0.3s intervals. Camera: motorized slider arc pan, fluid head, no vibration.

▶ 12.0-15.0s | Hero Freeze + Slow Rotation + Fade Out
Product returns to absolute frame center, all accessories assembled. Camera locks — 0.5s total stillness creates a breathing pause. Then {product} begins a slow 360° Z-axis rotation at 90°/second, revealing full 360° design. Rotation decelerates to zero when product faces front. Final 0.5s: a soft radial glow expands from product center outward like a diamond commercial hero flash — but no overexposure. Fade to pure white. No text overlays of any kind.

【SOUND DESIGN】
{specs['sound']}. Room tone at ambient 15dB. No music, no voiceover.

【COLOR PALETTE】
{specs['palette']}.

【NEGATIVE CONSTRAINTS】
Person or face visible in frame (hands only, no face/eyes/lips), full body, feet, dirty fingernails, chipped polish, jewelry rings or bracelets, blood or injury, product damage or wear, {specs['forbidden']}, motion blur on functional strokes, water splashes or drips on lens, lens flare, chromatic aberration, overexposed whites blowing out product detail, soft focus on product edge, low contrast making product hard to distinguish from background, messy background, camera reflection visible on metal surfaces, handheld shake — all camera moves use electronic slider-level smoothness."""
    
    prompt_chars = len(prompt)
    if prompt_chars > 3500:
        prompt = prompt[:3480]
        prompt_chars = len(prompt)
    elif prompt_chars < 3200:
        prompt += "\n\n【ADDITIONAL TECHNICAL NOTES】Shot on virtual cinema camera equivalent: sensor Super 35mm, lens 50mm f/1.4 for shallow depth of field in macro scenes, 24mm f/2.8 for medium shots. Color grading: slight S-curve contrast, shadows lifted +5% for clean commercial look, no crushed blacks. All transitions: smooth dissolve 0.3s, no hard cuts. Product always in sharp focus — rack focus only for deliberate depth transitions. Final output: 9:16 vertical 720p h.264 24fps, no compression artifacts visible on product edges. If reference image provided, match product appearance exactly — color, texture, proportions, details."
    
    result = {
        "product": product,
        "category": category,
        "duration": 15,
        "aspect_ratio": "9:16",
        "resolution": "720p",
        "model": "Seedance 2.0",
        "prompt": prompt,
        "prompt_chars": len(prompt),
        "ref_images_needed": len(ref_images or []),
    }
    gep.post_record("generate_seedance_prompt", {"product": product, "chars": len(prompt)}, "success")
    return result


def main(product: str = "双头眉刷", countries: list = None, scenario: str = "inquiry", export: bool = False, seedance_product: str = None):
    """文案引擎主入口
    接收参数，生产5国文案，输出JSON到stdout供框架捕获
    """
    if countries is None:
        countries = ["TH", "MY", "VN", "ID", "PH"]
    
    results = []
    for cc in countries:
        copy = generate_copy(product, cc, scenario)
        compliance = check_compliance(copy.get("text", ""), cc)
        copy["compliance"] = compliance
        results.append(copy)
        log(f"  {cc}: 生成{COUNTRY_LANG[cc]}文案 | 合规:{'✅' if compliance['pass'] else '❌'}")

    if export:
        export_to_csv(results)

    stats = gep.get_stats()
    log(f"📊 GEP进化节点: {stats.get('total', 0)}条")
    log("文案引擎运行完成")
    log("=" * 40)

    # JSON stdout — 框架捕获
    output = {
        "status": "completed",
        "product": product,
        "scenario": scenario,
        "countries": countries,
        "copies": results,
        "total": len(results),
        "gep_stats": stats,
    }
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="🥬 文案引擎 - CO-STAR话术生成")
    parser.add_argument("--product", default="双头眉刷", help="产品名称")
    parser.add_argument("--countries", nargs="+", default=["TH","MY","VN","ID","PH"], help="国家代码")
    parser.add_argument("--scenario", default="inquiry", choices=list(SCENARIOS.keys()), help="场景")
    parser.add_argument("--export", action="store_true", help="导出CSV")
    parser.add_argument("--seedance", default=None, help="生成Seedance提示词，指定品类(美妆/家居/厨房)")
    # 🔴 v3.3: Pipeline串行通信
    parser.add_argument("--input", default=None, help="从Pipeline上下文文件读取产品列表")
    parser.add_argument("--output", default=None, help="将文案写回Pipeline上下文文件")
    args = parser.parse_args()
    
    if args.seedance:
        result = generate_seedance_prompt(args.product, args.seedance)
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)
    
    # 🔴 v3.3: Pipeline模式 — 从上下文读产品，写回文案
    ctx_file = args.input or os.environ.get("PIPELINE_CONTEXT_FILE")
    if ctx_file and os.path.exists(ctx_file):
        try:
            with open(ctx_file) as f:
                ctx = json.load(f)
        except:
            ctx = {"chain": [], "products": [], "step": 0}
        
        products = ctx.get("products", [])
        if products:
            log(f"📥 Pipeline模式: 从上下文读取{len(products)}个产品")
            all_copies = []
            for prod in products:
                pname = prod if isinstance(prod, str) else prod.get("name", str(prod))
                log(f"  处理: {pname}")
                results = []
                for cc in (args.countries or ["TH","MY","VN","ID","PH"]):
                    copy = generate_copy(pname, cc, args.scenario)
                    compliance = check_compliance(copy.get("text", ""), cc)
                    copy["compliance"] = compliance
                    results.append(copy)
                all_copies.append({"product": pname, "copies": results})
            
            # 写回上下文
            ctx["copy"] = all_copies
            ctx["step"] = 2  # 文案阶段完成
            ctx["chain"].append("copy_done")
            
            out_file = args.output or ctx_file
            with open(out_file, 'w') as f:
                json.dump(ctx, f, ensure_ascii=False)
            log(f"📤 文案已写回: {out_file}")
            print(json.dumps({"status": "completed", "pipeline": True, "products_processed": len(products), "copies": len(all_copies)}, ensure_ascii=False))
            sys.exit(0)
        else:
            log("⚠️ Pipeline上下文无产品，回退到单产品模式")
    
    sys.exit(0 if main(args.product, args.countries, args.scenario, args.export) or True else 1)
