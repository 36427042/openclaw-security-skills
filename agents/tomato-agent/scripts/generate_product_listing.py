#!/usr/bin/env python3
"""
🥔 土豆 - 5国商品标题+详情页生成器
基于：生菜SEO标题模板结构 + 已采集1688商品数据
用途：TK店铺开通后直接上架

实际商品：新款便携5支化妆刷迷你带镜子美妆工具
1688采集价：¥6.48 | 颜色：5色 | 重量：0.08g
"""

import json, os

# ============================
# 商品数据
# ============================
product = {
    "name_cn": "新款便携5支化妆刷迷你带镜子美妆工具套装",
    "price_rmb": 6.48,
    "colors": ["柔肤色", "清新蓝", "优雅紫", "墨绿色", "豆沙色"],
    "specs": "3.0新款镜盒独立OPP包装",
    "weight_g": 0.08,
    "features": [
        "带镜子化妆盒", "5支套刷齐全", "便携迷你尺寸",
        "人造纤维刷毛", "多功能组合", "跨境出口品质"
    ],
    "source_url": "https://detail.1688.com/offer/853940751157.html"
}

# ============================
# 5国定价（基于MEMORY中的定价规则）
# ============================
pricing = {
    "TH": {"multiplier": 6.0, "currency": "฿", "currency_code": "THB", "name": "泰国"},
    "MY": {"multiplier": 6.5, "currency": "RM", "currency_code": "MYR", "name": "马来西亚"},
    "VN": {"multiplier": 6.3, "currency": "₫", "currency_code": "VND", "name": "越南"},
    "PH": {"multiplier": 5.8, "currency": "₱", "currency_code": "PHP", "name": "菲律宾"},
    "SG": {"multiplier": 6.0, "currency": "S$", "currency_code": "SGD", "name": "新加坡"},
}

for c in pricing.values():
    c["price"] = round(product["price_rmb"] * c["multiplier"], 2)

# ============================
# 🇹🇭 泰国 - 泰语
# ============================
TH_TITLES = {
    "variant_a": (
        "แปรงแต่งหน้า5ชิ้นพกพา กระจกในตัว แปรงขนนุ่ม ครบเซ็ทแต่งหน้า "
        "แปรงรองพื้น แปรงทาตา แปรงปัดแก้ม เคสเล็กพกใส่กระเป๋าสะดวก"
    ),
    "variant_b": (
        "เซ็ทแปรงแต่งหน้าขนาดพกพา 5ชิ้น มีกระจก บางเบา พกพาง่าย "
        "แปรงขนนุ่มไม่ทำร้ายผิว เนื้อเคสแข็งแรงทนทาน"
    ),
    "variant_c": (
        "แปรงแต่งหน้าชุดเล็ก 5แท่ง พร้อมกระจก เหมาะพกพา "
        "แปรงคุณภาพดี ขนนุ่ม ใช้งานครบทุกขั้นตอน สะดวกทุกที่"
    ),
}

TH_DETAIL = """📦 **เซ็ทแปรงแต่งหน้าพกพา 5 ชิ้น พร้อมกระจก**

✨ **คุณสมบัติเด่น:**
• แปรงแต่งหน้าครบเซ็ท 5 ชิ้นในเคสเดียว — รองพื้น, ทาตา, ปัดแก้ม, เขียนคิ้ว, ปัดปอย
• มีกระจกในตัว สะดวกในการแต่งหน้าทุกที่
• ขนแปรงนุ่ม ไม่ระคายเคืองผิว ทำจากเส้นใยสังเคราะห์คุณภาพสูง
• เคสขนาดกะทัดรัด พกพาง่าย ใส่กระเป๋าสะดวก
• น้ำหนักเบาเพียง 0.08 กรัม

🌈 **5 สีให้เลือก:**
{five_colors_th}

💡 **วิธีใช้:**
ใช้แปรงแต่ละอันตามขั้นตอนการแต่งหน้า — รองพื้น → ปัดแก้ม → ทาตา → เขียนคิ้ว → ปัดปอย

📐 **รายละเอียดสินค้า:**
• จำนวน: แปรง 5 ชิ้น + เคสมีกระจก
• วัสดุขนแปรง: ใยสังเคราะห์
• ขนาด: พกพา
• น้ำหนัก: {weight}g
• แหล่งผลิต: จีน

⚠️ **ข้อควรระวัง:**
• หลีกเลี่ยงการแช่น้ำนานๆ
• ทำความสะอาดแปรงเป็นประจำด้วยน้ำยาทำความสะอาดแปรง"""

COLORS_TH = {c: t for c, t in 
    [("柔肤色", "สีผิวธรรมชาติ"), ("清新蓝", "สีฟ้าสด"), 
     ("优雅紫", "สีม่วง"), ("墨绿色", "สีเขียวเข้ม"), ("豆沙色", "สีน้ำตาลแดง")]
}

# ============================
# 🇲🇾 马来西亚 - 马来语
# ============================
MY_TITLES = {
    "variant_a": (
        "Set Berus Solek 5pc Mini Mudah Alih Dengan Cermin "
        "Berus Lembut Lengkap Foundation Eyeshadow Blush"
    ),
    "variant_b": (
        "Berus Solek Portable 5pc Set Ada Cermin Kecil "
        "Bulu Berus Lembut Tak Cecah Kulit Kotak Kuat Tahan Lama"
    ),
    "variant_c": (
        "Set Berus Makeup 5in1 Mini Travel Size Dengan Cermin "
        "Berus Sintetik Lembut Sesuai Jalan-jalan"
    ),
}

MY_DETAIL = """📦 **Set Berus Solek 5pc Mudah Alih + Cermin**

✨ **Ciri-ciri Utama:**
• Set berus solek lengkap 5pcs dalam satu kotak — foundation, eyeshadow, blush, eyebrow, blending
• Dilengkapi cermin kecil untuk solek di mana-mana sahaja
• Bulu berus lembut, tidak merengsakan kulit (gentian sintetik berkualiti tinggi)
• Saiz padat, senang dibawa dalam beg tangan
• Berat hanya {weight}g

🌈 **5 Warna Pilihan:**
{five_colors_ms}

💡 **Cara Guna:**
Gunakan setiap berus mengikut langkah solek: foundation → blush → eyeshadow → eyebrow → setting

📐 **Spesifikasi:**
• Kandungan: 5 berus + kotak dengan cermin
• Bahan bulu: Gentian sintetik
• Saiz: Mini portable
• Berat: {weight}g
• Asal: China

⚠️ **Penjagaan:**
• Bersihkan berus secara berkala dengan pencuci berus khas
• Jangan rendam dalam air terlalu lama
• Simpan di tempat kering"""

COLORS_MS = {c: t for c, t in
    [("柔肤色", "Warna Kulit"), ("清新蓝", "Biru Segar"),
     ("优雅紫", "Ungu Elegan"), ("墨绿色", "Hijau Tua"), ("豆沙色", "Merah Koko")]
}

# ============================
# 🇻🇳 越南 - 越南语
# ============================
VN_TITLES = {
    "variant_a": (
        "Bộ Cọ Trang Điểm 5 Cây Mini Du Lịch Có Gương Soi "
        "Lông Mềm Đầy Đủ Cọ Nền Cọ Mắt Cọ Má"
    ),
    "variant_b": (
        "Cọ Trang Điểm Bỏ Túi 5 Cây Kèm Gương Siêu Nhỏ Gọn "
        "Lông Mịn Không Xước Da Hộp Chắc Chắn"
    ),
    "variant_c": (
        "Set Cọ Makeup 5 Món Mini Travel Kèm Gương "
        "Cọ Sợi Tổng Hợp Mềm Dễ Thương Mang Theo"
    ),
}

VN_DETAIL = """📦 **Bộ Cọ Trang Điểm 5 Cây Mini Du Lịch + Gương Soi**

✨ **Tính Năng Nổi Bật:**
• Bộ cọ đầy đủ 5 cây trong một hộp — cọ nền, cọ mắt, cọ má, cọ mày, cọ tán
• Có gương soi tiện lợi, trang điểm mọi lúc mọi nơi
• Lông cọ mềm mại, không gây kích ứng da (sợi tổng hợp cao cấp)
• Kích thước nhỏ gọn, dễ dàng mang theo trong túi xách
• Trọng lượng siêu nhẹ {weight}g

🌈 **5 Màu Sắc:**
{five_colors_vi}

💡 **Hướng Dẫn Sử Dụng:**
Dùng từng cây theo các bước trang điểm: nền → má → mắt → mày → tán đều

📐 **Thông Tin Sản Phẩm:**
• Số lượng: 5 cọ + hộp có gương
• Chất liệu lông: Sợi tổng hợp
• Kích thước: Mini, xách tay
• Cân nặng: {weight}g
• Xuất xứ: Trung Quốc

⚠️ **Lưu Ý:**
• Vệ sinh cọ thường xuyên bằng dung dịch chuyên dụng
• Tránh ngâm nước lâu
• Bảo quản nơi khô ráo"""

COLORS_VI = {c: t for c, t in 
    [("柔肤色", "Màu Da"), ("清新蓝", "Xanh Nhạt"),
     ("优雅紫", "Tím Thanh Lịch"), ("墨绿色", "Xanh Lá Đậm"), ("豆沙色", "Nâu Đỏ")]
}

# ============================
# 🇵🇭 菲律宾 - 英语+他加禄语
# ============================
PH_TITLES = {
    "variant_a": (
        "5pc Travel Makeup Brush Set with Mirror Mini Portable "
        "Soft Bristles Complete Foundation Eyeshadow Blush Kit"
    ),
    "variant_b": (
        "Portable Makeup Brush Set 5in1 with Mirror Travel Size "
        "Gentle Synthetic Bristles Perfect for On-the-Go Touch Up"
    ),
    "variant_c": (
        "Mini Makeup Brushes 5pcs Set w/ Mirror Travel Friendly "
        "Soft Bristle Brush Kit Complete Face Eye Powder Blush"
    ),
}

PH_DETAIL = """📦 **5pc Makeup Brush Set with Mirror — Travel Size!**

✨ **Why You'll Love It:**
• Complete 5-piece brush set in one compact case — foundation, eyeshadow, blush, eyebrow, blending
• Built-in mirror for touch-ups anywhere, anytime
• Ultra-soft synthetic bristles — gentle on skin, no irritation
• Compact and lightweight — perfect for bag, office, or travel
• Weighs only {weight}g — you won't even notice it's there

🌈 **5 Colors to Choose From:**
{five_colors_ph}

💡 **How to Use:**
Follow your makeup routine step by step with the right brush for each look

📐 **Product Details:**
• Contents: 5 brushes + mirrored case
• Bristle material: High-quality synthetic fiber
• Case size: Mini travel size
• Weight: {weight}g
• Origin: China

⚠️ **Care Instructions:**
• Clean brushes regularly with brush cleaner
• Don't soak in water for too long
• Store in a dry place
• For external use only"""

COLORS_PH = {c: t for c, t in
    [("柔肤色", "Nude"), ("清新蓝", "Sky Blue"),
     ("优雅紫", "Elegant Purple"), ("墨绿色", "Forest Green"), ("豆沙色", "Rosewood")]
}

# ============================
# 🇸🇬 新加坡 - 简洁高级风英语
# ============================
SG_TITLES = {
    "variant_a": (
        "5-Piece Mini Makeup Brush Set with Mirror Portable Travel "
        "Synthetic Bristles Foundation Blush Eyeshadow Brushes Kit"
    ),
    "variant_b": (
        "Travel Makeup Brush Kit 5pcs w Compact Mirror On-the-Go "
        "Soft Bristle Brush Set Daily Essential Touch Up"
    ),
    "variant_c": (
        "Mini Brush Set 5pc for Makeup with Mirror Lightweight "
        "Synthetic Hair Brushes Foundation Eye Blush Eyebrow"
    ),
}

SG_DETAIL = """📦 **5-Piece Compact Makeup Brush Set with Mirror**

✨ **Key Features:**
• Complete 5-brush set in a sleek mirrored case — foundation, eyeshadow, blush, brow, blend
• Integrated mirror for convenient touch-ups anytime, anywhere
• Premium synthetic bristles — soft, cruelty-free, gentle on skin
• Ultra-portable design — slips easily into any bag or pocket
• Featherlight at only {weight}g

🌈 **5 Colour Options:**
{five_colors_sg}

💡 **Usage:**
Each brush serves a specific step — apply, blend, contour, highlight, set

📐 **Specifications:**
• Set includes: 5 brushes + mirror case
• Bristle type: Synthetic fibre
• Size: Mini travel
• Weight: {weight}g
• Origin: China

⚠️ **Care:**
• Clean periodically with brush shampoo
• Air dry after washing
• Store in a cool, dry place"""

COLORS_SG = {c: t for c, t in
    [("柔肤色", "Nude Beige"), ("清新蓝", "Pastel Blue"),
     ("优雅紫", "Lavender"), ("墨绿色", "Deep Teal"), ("豆沙色", "Mauve")]
}


def fmt_colors(color_map):
    """Format 5 colors into bullet list"""
    lines = []
    for orig, translated in color_map.items():
        lines.append(f"  • {translated}")
    return "\n".join(lines)


def generate_listing():
    """Generate all 5-country listings to a single markdown file"""
    output = []
    output.append("# 🛍️ 5国商品标题+详情页 — 便携5支化妆刷带镜子套装")
    output.append("")
    output.append(f"**1688链接**: {product['source_url']}")
    output.append(f"**采集价**: ¥{product['price_rmb']}")
    output.append(f"**颜色**: {', '.join(product['colors'])}")
    output.append(f"**规格**: {product['specs']}")
    output.append(f"**重量**: {product['weight_g']}g")
    output.append("")
    
    # Language code -> country code mapping for color variables
    LANG_MAP = {"TH": "TH", "MY": "MS", "VN": "VI", "PH": "PH", "SG": "SG"}
    
    for (country_code, info) in [
        ("TH", "🇹🇭 泰国"),
        ("MY", "🇲🇾 马来西亚"),
        ("VN", "🇻🇳 越南"),
        ("PH", "🇵🇭 菲律宾"),
        ("SG", "🇸🇬 新加坡"),
    ]:
        p = pricing[country_code]
        output.append(f"---")
        output.append(f"## {info}")
        output.append(f"**定价**: {p['currency']}{p['price']} ({p['currency_code']})")
        output.append("")
        
        # Titles
        titles = globals()[f"{country_code}_TITLES"]
        output.append(f"### 📌 标题")
        for var, title in titles.items():
            vname = var.replace("variant_", "变体").upper()
            output.append(f"- **{vname}**: {title}")
        output.append("")
        
        # Detail page
        lang_code = LANG_MAP[country_code]
        colors_map = globals()[f"COLORS_{lang_code}"]
        five_colors = fmt_colors(colors_map)
        
        detail = globals()[f"{country_code}_DETAIL"].format(
            weight=product["weight_g"],
            five_colors_th=five_colors,
            five_colors_ms=five_colors,
            five_colors_vi=five_colors,
            five_colors_ph=five_colors,
            five_colors_sg=five_colors,
        )
        output.append(f"### 📄 详情页")
        output.append(detail)
        output.append("")
        output.append("")
    
    # Write output
    out_path = os.path.expanduser("~/Desktop/化妆刷_5国商品标题详情页.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output))
    print(f"✅ 已生成：{out_path}")
    print(f"   文件大小：{len('\n'.join(output))} 字符")

    # Also output to console for immediate feedback
    print("\n" + "=" * 60)
    print("预览 - 泰国标题变体A:")
    print(TH_TITLES["variant_a"])
    print("\n预览 - 新加坡标题变体A:")
    print(SG_TITLES["variant_a"])

if __name__ == "__main__":
    generate_listing()
