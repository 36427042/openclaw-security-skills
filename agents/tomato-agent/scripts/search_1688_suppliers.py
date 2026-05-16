#!/usr/bin/env python3
"""
🔗 1688供应商搜索脚本
通过1688公开搜索页面查找供应商链接
使用web_fetch/wget模拟浏览器搜索
"""
import json, os, re, subprocess

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.expanduser("~/Desktop")

def search_1688(keyword):
    """使用curl模拟浏览器搜索1688"""
    url = f"https://s.1688.com/selloffer/offer_search.htm?keywords={keyword}&n=y&beginPage=1&pageSize=5"
    cmd = [
        "curl", "-sL", url,
        "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8",
        "--connect-timeout", "10",
        "--max-time", "15"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        html = result.stdout
        
        # 找到所有offer_id和标题
        offers = []
        # 匹配offer链接
        offer_ids = re.findall(r'//detail\.1688\.com/offer/(\d+)\.html', html)
        titles = re.findall(r'title="([^"]{8,100})"', html)
        
        seen = set()
        for i, oid in enumerate(offer_ids):
            if oid not in seen:
                seen.add(oid)
                title = titles[i] if i < len(titles) else keyword
                offers.append({
                    "id": oid,
                    "title": title.strip(),
                    "url": f"https://detail.1688.com/offer/{oid}.html"
                })
        
        # 如果没找到offer，试试价格匹配
        if not offers:
            # 尝试不同的模式
            price_matches = re.findall(r'[¥￥]([\d.]+)\s*成交(\d+)笔', html)
            for pm in price_matches[:5]:
                offers.append({
                    "id": "?",
                    "title": f"{keyword} - ¥{pm[0]} (成交{pm[1]}笔)",
                    "url": url,
                    "price": pm[0],
                    "sales": pm[1]
                })
        
        return offers if offers else []
    except Exception as e:
        return []

def main():
    # 读取选品报告
    report_path = os.path.join(OUTPUT_DIR, "番茄选品报告_含供应商.md")
    with open(report_path) as f:
        content = f.read()
    
    # 提取前15个产品名称
    product_names = re.findall(r'^### (.+)$', content, re.MULTILINE)[:15]
    
    print(f"📋 搜索 {len(product_names)} 个产品的1688供应商...\n")
    
    supplier_data = {}
    for i, name in enumerate(product_names):
        # 提取中文关键词
        cn_words = re.findall(r'[\u4e00-\u9fff]+', name)
        if not cn_words:
            print(f"  [{i+1}/15] {name[:25]}... 无中文关键词")
            continue
        
        keyword = " ".join(cn_words[:3])
        print(f"  [{i+1}/15] 搜索: {keyword}...", end=" ", flush=True)
        
        offers = search_1688(keyword)
        if offers:
            supplier_data[name] = offers
            print(f"✅ {len(offers)}个结果")
            for o in offers[:2]:
                print(f"     → {o['title'][:40]}")
                print(f"       {o['url']}")
        else:
            print("❌ 未找到")
        
        if (i + 1) % 3 == 0:
            import time
            time.sleep(1)  # 防封
    
    # 导出结果
    output_path = os.path.join(OUTPUT_DIR, "1688_suppliers_found.json")
    with open(output_path, "w") as f:
        json.dump(supplier_data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 供应商数据已保存: {output_path}")
    return supplier_data

if __name__ == "__main__":
    main()
