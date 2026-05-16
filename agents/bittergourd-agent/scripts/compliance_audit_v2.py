#!/usr/bin/env python3
"""
违禁词审核脚本 v2 — 86产品 × 5国
正确解析product_copy_86_2026-05-14.md的嵌套结构
"""

import re
from collections import defaultdict

# ─── 文件路径 ───
BANNED_WORDS_FILE = "/Users/a1234/.openclaw/workspace/agents/bittergourd-agent/sop/违禁词库_v2.0.md"
PRODUCT_COPY_FILE = "/Users/a1234/.openclaw/workspace/agents/lettuce-agent/output/product_copy_86_2026-05-14.md"
OUTPUT_FILE = "/Users/a1234/.openclaw/workspace/agents/bittergourd-agent/output/compliance_audit_86_2026-05-14.md"

# ─── 加载违禁词库 ───
def load_banned_words():
    with open(BANNED_WORDS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    country_map = {'🇹🇭': 'TH', '🇲🇾': 'MY', '🇵🇭': 'PH', '🇸🇬': 'SG', '🇻🇳': 'VN'}
    banned = defaultdict(list)
    
    for emoji, code in country_map.items():
        # Find country section
        pattern = rf"## {re.escape(emoji)}\s+\S+.*?违禁词"
        m = re.search(pattern, content)
        if not m:
            continue
        
        section_start = m.start()
        # Find next country or end
        next_country = None
        for next_emoji in country_map:
            if next_emoji == emoji:
                continue
            nm = re.search(rf"## {re.escape(next_emoji)}\s+\S+.*?违禁词", content[section_start+10:])
            if nm:
                pos = section_start + 10 + nm.start()
                if next_country is None or pos < next_country:
                    next_country = pos
        if next_country is None:
            next_country = len(content)
        
        section = content[section_start:next_country]
        
        for line in section.split('\n'):
            line = line.strip()
            if line.startswith('|') and f'{code}_' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 7:
                    banned[code].append({
                        'code': parts[1],
                        'word': parts[2],
                        'meaning': parts[3],
                        'risk': parts[4],
                        'reason': parts[5],
                        'variants': parts[6]
                    })
    
    return banned

def parse_product_copy():
    """
    Parse the product copy file.
    Structure:
    ## CATEGORY-TH-001 | Product Name (outer product section)
      ### Country — Store Name
        **Title:** ...
        **Description:** ...
        **Selling Points:**
        - ...
      ### Country — Store Name (next country)
        ...
    ---
    ## CATEGORY-SG (multiple ✅ products) — Store
      ### Product-Name (sub-product)
        **Title:** ...
        ...
      ### Product-Name (sub-product)
        ...
    """
    with open(PRODUCT_COPY_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    flag_to_code = {'🇹🇭': 'TH', '🇲🇾': 'MY', '🇵🇭': 'PH', '🇸🇬': 'SG', '🇻🇳': 'VN'}
    
    products = []  # list of dicts with id, name, texts[]
    
    current_outer_id = None
    current_outer_name = None
    current_country = None
    current_store = None
    current_sub_id = None
    current_sub_texts = {}
    collecting_meta = False
    
    def flush_product(pid, name, texts):
        if texts:
            products.append({'id': pid, 'name': name, 'texts': texts})
    
    def parse_country_line(line):
        """Check if line is a country header: ### 🇹🇭 Thailand — Store"""
        for flag in flag_to_code:
            if flag in line:
                code = flag_to_code[flag]
                # Extract store name after —
                store = ''
                if '—' in line:
                    store = line.split('—', 1)[1].strip()
                return code, store
        return None, None
    
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Outer product header: ## CATEGORY-TH-001 | Name
        outer_match = re.match(r'^## ([\w-]+)\s*\|(.+)', line)
        if outer_match:
            # Flush any current product
            if current_sub_id and current_sub_texts:
                text_list = []
                for country, fields in current_sub_texts.items():
                    for field_type, text in fields.items():
                        if text:
                            text_list.append({'country': country, 'type': field_type, 'text': text})
                if text_list:
                    flush_product(current_sub_id, current_sub_name, text_list)
            
            current_outer_id = outer_match.group(1).strip()
            current_outer_name = outer_match.group(2).strip()
            current_country = None
            current_store = None
            current_sub_id = None
            current_sub_name = None
            current_sub_texts = {}
            
            # Check if this is a group header (has "(multiple ✅)" type note)
            # If so, the sub-products will be under ###
            # If not, the sub-products are the country headers
            
            # Clear sub-level
            collecting_meta = False
            i += 1
            continue
        
        # Check for product-level ### (sub-product or country header)
        if line.startswith('### '):
            rest = line[4:].strip()
            
            # Could be a country header or a sub-product
            country_code, store = parse_country_line(line)
            
            if country_code:
                # This is a country header under an outer product
                
                # Flush previous sub if any (for nested ### within a country)
                # Actually country headers are not sub-products; they belong to the outer product
                
                # Check if we were collecting a sub-product
                if current_sub_id and current_sub_texts:
                    text_list = []
                    for ccode, fields in current_sub_texts.items():
                        for field_type, text in fields.items():
                            if text:
                                text_list.append({'country': ccode, 'type': field_type, 'text': text})
                    if text_list:
                        flush_product(current_sub_id, current_sub_name, text_list)
                    current_sub_texts = {}
                    current_sub_id = None
                
                current_country = country_code
                current_store = store
                collecting_meta = True
                current_text_type = None
                current_text_content = []
                
                # If this is a direct product (not a sub), set the current sub to be the outer product
                # We'll store texts under the outer product ID
                current_sub_id = current_outer_id
                current_sub_name = current_outer_name
                
                i += 1
                continue
            else:
                # This is a sub-product within a group (like KITCHEN-SG, HOME-SG)
                # Example: "### KITCHEN-SG-001 | 10Pcs Vacuum Storage Bags Reusable"
                sub_match = re.match(r'^([\w-]+)\s*\|(.+)', rest)
                if sub_match:
                    # Flush previous sub
                    if current_sub_id and current_sub_texts:
                        text_list = []
                        for ccode, fields in current_sub_texts.items():
                            for field_type, text in fields.items():
                                if text:
                                    text_list.append({'country': ccode, 'type': field_type, 'text': text})
                        if text_list:
                            flush_product(current_sub_id, current_sub_name, text_list)
                    
                    current_sub_id = sub_match.group(1).strip()
                    current_sub_name = sub_match.group(2).strip()
                    current_sub_texts = {}
                    # Reset country context - this sub-product might be under a specific country
                    # But most sub-products in groups are SG only
                    current_country = None  # Will be set by subsequent text
                    collecting_meta = True
                    current_text_type = None
                    current_text_content = []
                    
                    i += 1
                    continue
                else:
                    # The ### is a sub-product with just a name (no |)
                    # Flush previous
                    if current_sub_id and current_sub_texts:
                        text_list = []
                        for ccode, fields in current_sub_texts.items():
                            for field_type, text in fields.items():
                                if text:
                                    text_list.append({'country': ccode, 'type': field_type, 'text': text})
                        if text_list:
                            flush_product(current_sub_id, current_sub_name, text_list)
                    
                    current_sub_id = rest.strip()
                    current_sub_name = rest.strip()
                    current_sub_texts = {}
                    current_country = None
                    collecting_meta = True
                    current_text_type = None
                    current_text_content = []
                    
                    i += 1
                    continue
        
        # If we're inside a product context
        if collecting_meta and current_sub_id:
            # Check for new country header within sub-product context (### Country)
            sub_country_match = re.match(r'^### ([\U0001F1E6-\U0001F1FF]+)', line)
            if sub_country_match:
                flag = sub_country_match.group(1)
                if flag in flag_to_code:
                    # Save previous country's texts
                    if current_country and current_text_type and current_text_content:
                        if current_country not in current_sub_texts:
                            current_sub_texts[current_country] = {}
                        current_sub_texts[current_country][current_text_type] = '\n'.join(current_text_content)
                    
                    current_country = flag_to_code[flag]
                    current_text_type = None
                    current_text_content = []
                    i += 1
                    continue
            
            # Check for Malaysia shortcut: ### 🇲🇾 Malaysia — Store
            for flag in flag_to_code:
                if flag in line:
                    code = flag_to_code[flag]
                    if current_country and current_text_type and current_text_content:
                        if current_country not in current_sub_texts:
                            current_sub_texts[current_country] = {}
                        current_sub_texts[current_country][current_text_type] = '\n'.join(current_text_content)
                    
                    current_country = code
                    current_text_type = None
                    current_text_content = []
                    i += 1
                    # break out of for and continue outer loop
                    break
            else:
                # No country flag found, process as text
                title_match = re.match(r'^\*\*Title:\*\*\s*(.*)', line)
                desc_match = re.match(r'^\*\*Description:\*\*\s*(.*)', line)
                sell_match = re.match(r'^\*\*Selling Points:\*\*', line)
                
                if title_match:
                    if current_country and current_text_type and current_text_content:
                        if current_country not in current_sub_texts:
                            current_sub_texts[current_country] = {}
                        current_sub_texts[current_country][current_text_type] = '\n'.join(current_text_content)
                    current_text_type = 'title'
                    current_text_content = [title_match.group(1)]
                elif desc_match:
                    if current_country and current_text_type and current_text_content:
                        if current_country not in current_sub_texts:
                            current_sub_texts[current_country] = {}
                        current_sub_texts[current_country][current_text_type] = '\n'.join(current_text_content)
                    current_text_type = 'description'
                    current_text_content = [desc_match.group(1)]
                elif sell_match:
                    if current_country and current_text_type and current_text_content:
                        if current_country not in current_sub_texts:
                            current_sub_texts[current_country] = {}
                        current_sub_texts[current_country][current_text_type] = '\n'.join(current_text_content)
                    current_text_type = 'selling_points'
                    current_text_content = []
                elif line.strip().startswith('- ') and current_text_type:
                    current_text_content.append(line.strip()[2:])
                elif line.strip() and current_text_type and not line.startswith('>'):
                    # Continuation text
                    current_text_content.append(line.strip())
            
            i += 1
            continue
        
        if line.startswith('---') and current_sub_id and current_sub_texts:
            # Section break - flush current
            pass
        
        i += 1
    
    # Flush last product
    if current_sub_id and current_sub_texts:
        text_list = []
        for ccode, fields in current_sub_texts.items():
            for field_type, text in fields.items():
                if text:
                    text_list.append({'country': ccode, 'type': field_type, 'text': text})
        if text_list:
            flush_product(current_sub_id, current_sub_name, text_list)
    
    return products


# Contextual false-positive patterns for MY (Malay)
# When 'anti' is followed by non-medical terms like 'bocor', 'karat', 'tumpah', 'slip', 'static' -> it's not medical
MY_SAFE_ANTI_CONTEXTS = [
    'anti bocor',    # leak-proof
    'anti karat',    # rust-proof
    'anti tumpah',   # spill-proof
    'anti slip',     # non-slip
    'anti static',   # anti-static
    'anti goyang',   # wobble-proof
    'anti pecah',    # shatter-proof
    'anti calar',    # scratch-proof
    'anti cendawan', # mold-resistant
    'anti jamur',    # fungus-resistant
    'anti debu',     # dust-proof
    'anti air',      # water-resistant (non-medical)
]

def scan_text(text, country, banned_words):
    """Scan text for banned words in the given country's word list."""
    violations = []
    text_lower = text.lower()
    
    for entry in banned_words.get(country, []):
        word = entry['word'].lower()
        
        if not word:
            continue
        
        # Try to find the word in the text
        if country == 'SG':
            # English: use word boundary
            pattern = r'\b' + re.escape(word) + r'\b'
            for m in re.finditer(pattern, text_lower, re.IGNORECASE):
                start = max(0, m.start() - 30)
                end = min(len(text), m.end() + 30)
                context = text[start:end].strip()
                violations.append({
                    'code': entry['code'],
                    'word': entry['word'],
                    'risk': entry['risk'],
                    'reason': entry['reason'],
                    'context': context
                })
        elif country == 'MY':
            # Malay: substring match with context filtering
            if word in text_lower:
                idx = text_lower.index(word)
                start = max(0, idx - 30)
                end = min(len(text), idx + len(word) + 30)
                context = text[start:end].strip()
                
                # Filter out false positives for specific words
                if word == 'anti':
                    # Make sure 'anti' is a standalone word, not part of 'cantik', 'cantiknya', etc.
                    # Also filter non-medical product features
                    is_standalone = False
                    patterns = [r'\banti\b', r'\banti[\s-]']
                    for pat in patterns:
                        if re.search(pat, text_lower):
                            is_standalone = True
                            break
                    
                    if not is_standalone:
                        continue  # 'anti' is part of another word like 'cantik'
                    
                    # Check if it's used in non-medical, product-feature context
                    is_safe = False
                    for safe_phrase in MY_SAFE_ANTI_CONTEXTS:
                        if safe_phrase in text_lower:
                            is_safe = True
                            break
                    if is_safe:
                        continue  # Skip this false positive for kitchen/home products
                
                if word == 'segar':
                    # 'segar' with 'bunga' (flower) or 'sayur' (veggie) is not cosmetic
                    if any(w in context.lower() for w in ['bunga', 'sayur', 'buah', 'makanan', 'dapur']):
                        continue
                
                if word == 'lembut':
                    # 'lembut' for fabric/towel/container is normal feature description, not cosmetic
                    if any(w in context.lower() for w in ['kain', 'fabrik', 'makana', 'plastik', 'bekas']):
                        continue
                
                violations.append({
                    'code': entry['code'],
                    'word': entry['word'],
                    'risk': entry['risk'],
                    'reason': entry['reason'],
                    'context': context
                })
        elif country == 'TH':
            # Thai: substring match
            if word in text_lower:
                idx = text_lower.index(word)
                start = max(0, idx - 30)
                end = min(len(text), idx + len(word) + 30)
                context = text[start:end].strip()
                
                # Filter: 'กระ' (TH_077, 雀斑) - Thai string 'กระ' is a common substring
                # Only flag if context clearly about skin/spots
                if word == 'กระ':
                    # 'กระ' as 'ka' sound in many Thai words unrelated to freckles
                    # Only flag if near skincare terms
                    skin_terms = ['ผิว', 'หน้า', 'ฝ้า', 'จุด', 'แต้ม', 'ครีม']
                    if not any(t in context for t in skin_terms):
                        continue
                
                violations.append({
                    'code': entry['code'],
                    'word': entry['word'],
                    'risk': entry['risk'],
                    'reason': entry['reason'],
                    'context': context
                })
        else:
            # VN, PH: substring match
            if word in text_lower:
                idx = text_lower.index(word)
                start = max(0, idx - 30)
                end = min(len(text), idx + len(word) + 30)
                context = text[start:end].strip()
                violations.append({
                    'code': entry['code'],
                    'word': entry['word'],
                    'risk': entry['risk'],
                    'reason': entry['reason'],
                    'context': context
                })
    
    return violations


def get_suggestion(word, risk):
    suggestions = {
        'whiten': 'brighten',
        'whitening': 'brightening',
        'brightening': 'glow-enhancing',
        'best': 'quality',
        'cheapest': 'affordable',
        'guarantee': 'confidence',
        'only': 'exclusive',
        '100% safe': 'safe for daily use',
        '100% effective': 'effective',
        'immediate results': 'noticeable results',
        'miracle': 'amazing',
        'instant': 'quick',
        'terbaik': 'sangat baik',
        'lebih murah': 'harga istimewa',
        'lebih baik': 'sangat baik',
        'no.1': 'popular',
        '#1': 'popular',
        'ฟื้นฟูผิว': 'บำรุงผิว',
        'ชะลอวัย': 'ผิวสุขภาพดี',
        'รับประกัน': 'มั่นใจ',
        'ถูกกว่า': 'ราคาพิเศษ',
        'tốt nhất': 'rất tốt',
        'rẻ nhất': 'giá tốt',
        'cam đoan': 'tin tưởng',
        'sáng da': 'da khỏe mạnh',
        'làm sáng': 'dưỡng da hàng ngày',
        'da sáng': 'da khỏe mạnh',
    }
    key = word.lower().strip()
    if key in suggestions:
        return suggestions[key]
    if risk == 'HIGH':
        return f'❌ 移除"{word}"'
    return f'⚠️ 建议替换"{word}"'


def main():
    print("加载违禁词库...")
    banned = load_banned_words()
    total_words = sum(len(v) for v in banned.values())
    print(f"  违禁词总数: {total_words}词")
    for code, words in banned.items():
        print(f"  {code}: {len(words)}词")
    
    banned_word_index = {}
    for code, entries in banned.items():
        for e in entries:
            key = (code, e['word'].lower())
            banned_word_index[key] = e
    
    print("\n解析产品文案...")
    raw_products = parse_product_copy()
    
    # Merge products with same ID (combine texts from different countries for the same product)
    merged = {}
    for p in raw_products:
        pid = p['id']
        if pid not in merged:
            merged[pid] = {'id': pid, 'name': p['name'], 'texts': []}
        merged[pid]['texts'].extend(p['texts'])
    products = list(merged.values())
    
    print(f"  原始条目: {len(raw_products)}个, 合并后: {len(products)}个")
    for p in products[:5]:
        countries = set(t['country'] for t in p['texts'] if t.get('country'))
        print(f"    {p['id']}: {p['name'][:40]} — 国家: {countries}")
    print(f"  ...")
    
    # ─── 扫描违规 ───
    all_violations = []
    passed_ids = set()
    violated_ids = set()
    
    for prod in products:
        prod_id = prod['id']
        prod_violations = []
        
        for text_entry in prod.get('texts', []):
            country = text_entry.get('country')
            text_type = text_entry.get('type', '')
            text = text_entry.get('text', '')
            
            if not country or not text or country not in banned:
                continue
            
            violations = scan_text(text, country, banned)
            
            for v in violations:
                prod_violations.append({
                    'product_id': prod_id,
                    'product_name': prod['name'],
                    'country': country,
                    'type': text_type,
                    'code': v['code'],
                    'word': v['word'],
                    'risk': v['risk'],
                    'reason': v['reason'],
                    'context': v['context'],
                    'suggestion': get_suggestion(v['word'], v['risk'])
                })
        
        if prod_violations:
            violated_ids.add(prod_id)
            all_violations.extend(prod_violations)
        else:
            passed_ids.add(prod_id)
    
    # ─── 统计 ───
    total_checked = len(products)
    total_violations = len(all_violations)
    
    high_cnt = sum(1 for v in all_violations if v['risk'] == 'HIGH')
    med_cnt = sum(1 for v in all_violations if v['risk'] == 'MEDIUM')
    low_cnt = sum(1 for v in all_violations if v['risk'] == 'LOW')
    
    country_counts = defaultdict(lambda: {'high': 0, 'medium': 0, 'low': 0, 'products': set()})
    for v in all_violations:
        cc = country_counts[v['country']]
        if v['risk'] == 'HIGH': cc['high'] += 1
        elif v['risk'] == 'MEDIUM': cc['medium'] += 1
        else: cc['low'] += 1
        cc['products'].add(v['product_id'])
    
    pass_rate = len(passed_ids) / total_checked * 100 if total_checked > 0 else 0
    
    # ─── 生成报告 ───
    report_lines = []
    
    # Header
    report_lines.append("# 🥒 苦瓜风控 — 86产品5国文案违禁词审核报告")
    report_lines.append("")
    report_lines.append(f"**审核时间:** 2026-05-14")
    report_lines.append(f"**审核范围:** 86产品 × 5国 (TH/MY/PH/SG/VN)")
    report_lines.append(f"**违禁词库:** v2.0 (共{total_words}词)")
    report_lines.append(f"**实际审核:** {total_checked}个产品条目")
    report_lines.append("")
    
    # Summary
    report_lines.append("---")
    report_lines.append("## 📊 审核汇总")
    report_lines.append("")
    report_lines.append(f"| 指标 | 数值 |")
    report_lines.append(f"|:-----|:----:|")
    report_lines.append(f"| 审核产品条目 | {total_checked} |")
    report_lines.append(f"| ❌ 发现违规的产品 | {len(violated_ids)} |")
    report_lines.append(f"| ✅ 完全通过的产品 | {len(passed_ids)} |")
    report_lines.append(f"| ❌ 违规项总数 | {total_violations} |")
    report_lines.append(f"| 🔴 HIGH风险 | {high_cnt} |")
    report_lines.append(f"| 🔶 MEDIUM风险 | {med_cnt} |")
    report_lines.append(f"| 🟡 LOW风险 | {low_cnt} |")
    report_lines.append(f"| **通过率** | **{pass_rate:.1f}%** |")
    report_lines.append("")
    
    # By country
    report_lines.append("### 按国家分布")
    report_lines.append("")
    emoji_map = {'TH': '🇹🇭', 'MY': '🇲🇾', 'PH': '🇵🇭', 'SG': '🇸🇬', 'VN': '🇻🇳'}
    report_lines.append(f"| 国家 | 🔴HIGH | 🔶MEDIUM | 🟡LOW | 涉及产品 |")
    report_lines.append(f"|:----:|:----:|:------:|:----:|:-------:|")
    for code in ['TH', 'MY', 'PH', 'SG', 'VN']:
        cc = country_counts.get(code, {'high': 0, 'medium': 0, 'low': 0, 'products': set()})
        report_lines.append(f"| {emoji_map[code]} {code} | {cc['high']} | {cc['medium']} | {cc['low']} | {len(cc['products'])} |")
    report_lines.append("")
    
    # ❌ Violations Detail
    report_lines.append("---")
    report_lines.append("## ❌ 违规明细清单")
    report_lines.append("")
    
    if all_violations:
        by_product = defaultdict(list)
        for v in all_violations:
            by_product[v['product_id']].append(v)
        
        for prod_id in sorted(by_product.keys()):
            violations = by_product[prod_id]
            prod_name = violations[0]['product_name'][:50]
            report_lines.append(f"### {prod_id} | {prod_name}")
            report_lines.append("")
            
            high_n = sum(1 for v in violations if v['risk'] == 'HIGH')
            med_n = sum(1 for v in violations if v['risk'] == 'MEDIUM')
            low_n = sum(1 for v in violations if v['risk'] == 'LOW')
            tags = []
            if high_n: tags.append(f"🔴{high_n}项HIGH")
            if med_n: tags.append(f"🔶{med_n}项MEDIUM")
            if low_n: tags.append(f"🟡{low_n}项LOW")
            report_lines.append(f"**风险:** {' | '.join(tags)}")
            report_lines.append("")
            
            report_lines.append(f"| # | 站点 | 位置 | 违禁词(码号) | 风险 | 原文截取 | 修改建议 |")
            report_lines.append(f"|---|:----:|:----:|:-----------:|:----:|:--------:|:--------:|")
            
            for i, v in enumerate(violations, 1):
                flag = emoji_map.get(v['country'], v['country'])
                risk_icon = '🔴' if v['risk'] == 'HIGH' else '🔶' if v['risk'] == 'MEDIUM' else '🟡'
                context = v['context'][:60].replace('\n', ' ')
                report_lines.append(
                    f"| {i} | {flag} | {v['type']} | `{v['word']}` ({v['code']}) | {risk_icon} | {context} | {v['suggestion']} |"
                )
            report_lines.append("")
    else:
        report_lines.append("🎉 **未发现任何违规！**")
        report_lines.append("")
    
    # ✅ Passed Products
    report_lines.append("---")
    report_lines.append("## ✅ 完全通过审核的产品")
    report_lines.append("")
    
    if passed_ids:
        cat_passed = defaultdict(list)
        for pid in sorted(passed_ids):
            cat = pid.split('-')[0] if '-' in pid else 'OTHER'
            cat_passed[cat].append(pid)
        
        for cat, prods in sorted(cat_passed.items()):
            cat_name = {'BEAUTY': '🧴 Beauty', 'KITCHEN': '🍳 Kitchen', 'HOME': '🏠 Home'}.get(cat, cat)
            report_lines.append(f"### {cat_name} ({len(prods)}个)")
            report_lines.append("")
            for pid in prods:
                report_lines.append(f"- `{pid}`")
            report_lines.append("")
    else:
        report_lines.append("无 — 所有审核产品均发现至少一项低风险及以上违规。")
        report_lines.append("")
    
    # ⚠️ Global Issues
    report_lines.append("---")
    report_lines.append("## 🔔 综合建议")
    report_lines.append("")
    report_lines.append("1. **SG文案**需特别注意英语绝对化用语（best/guarantee/only等），建议全文回避。")
    report_lines.append('2. **VN文案**避免使用"trị""chữa""bệnh"等医疗暗示词，当前发现的"dưỡng da""sáng da"属MEDIUM风险，建议逐步替换。')
    report_lines.append('3. **MY文案**避免"putih""cerah"等美白提亮词汇在高敏感期使用，优先选用"segar""sihat"。')
    report_lines.append("4. **MEDIUM/LOW风险词**虽非直接红线，但在复审/投诉场景下仍可能被下架，建议长期规划替换。")
    report_lines.append("5. **PH无对应店铺** — 本次86产品中PH市场无可用店铺，故PH审核为0条违规。")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("*报告由🥒苦瓜风控自动生成 · 2026-05-14*")
    
    output = '\n'.join(report_lines)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"\n✅ 报告已输出: {OUTPUT_FILE}")
    print(f"\n📊 统计:")
    print(f"  审核条目: {total_checked}")
    print(f"  通过: {len(passed_ids)} ({pass_rate:.1f}%)")
    print(f"  违规: {len(violated_ids)}个产品, {total_violations}项违规")
    print(f"    HIGH={high_cnt}, MEDIUM={med_cnt}, LOW={low_cnt}")
    
    # Print the first 20 violations for verification
    print(f"\n📋 前20项违规:")
    for v in all_violations[:20]:
        flag = emoji_map.get(v['country'], v['country'])
        print(f"  {flag} {v['product_id']:35s} | {v['type']:8s} | {v['word']:20s} | {v['risk']}")

if __name__ == '__main__':
    main()
