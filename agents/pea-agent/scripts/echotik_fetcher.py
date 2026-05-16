#!/usr/bin/env python3
"""
EchoTik 数据拉取脚本 v1.0
豌豆·数据Agent — TikTok东南亚美妆工具选品数据管线

拉取3品类(美妆工具/厨房用品/家居日用) × 5国(VN/TH/MY/PH/SG) × 10页
按30天销量降序排序，仅本土店在售商品

输出:
  - pea-agent/output/echotik_raw/beauty_VN.json 等原始数据
  - pea-agent/output/echotik_summary_2026-05-14.md 汇总报告

支持命令行参数: --category [beauty|kitchen|home] --region [VN|TH|MY|PH|SG]
"""

import os
import sys
import json
import base64
import time
import argparse
import logging
from datetime import datetime
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

# =====================================================================
# 配置
# =====================================================================

BASE_URL = "https://open.echotik.live/api/v3/echotik/product/list"
USERNAME = "260420352750946330"
PASSWORD = "33cab81ea7104a0a88f2fc4f6744362f"

# 认证头
AUTH_HEADER = "Basic " + base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()

# 请求头
HEADERS = {
    "Authorization": AUTH_HEADER,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# 品类定义
CATEGORIES = {
    "beauty": {
        "name": "美妆工具",
        "l1": 601450,
        "l3s": [
            (601537, "化妆工具"),
            (852752, "化妆镜"),
            (852880, "化妆刷"),
            (853008, "化妆蛋和海绵"),
            (853264, "粉扑"),
            (853392, "睫毛夹"),
            (824720, "假睫毛与胶水"),
        ],
    },
    "kitchen": {
        "name": "厨房用品",
        "l1": 600024,
        "l3s": [
            (867208, "削皮器"),
            (866824, "开瓶器"),
            (600060, "水果蔬菜工具"),
            (600029, "保鲜容器"),
            (866952, "油壶"),
            (600148, "炒勺锅铲"),
            (600063, "筷子"),
            (865288, "调味工具"),
            (866568, "饮水工具"),
        ],
    },
    "home": {
        "name": "家居日用",
        "l1": 600001,
        "l3s": [
            (600621, "收纳盒"),
            (600686, "收纳篮"),
            (852872, "收纳架"),
            (853128, "挂钩"),
            (852744, "收纳包"),
            (600416, "皂液容器"),
            (600447, "皂盒"),
            (600409, "清洁抹布"),
            (855048, "清洁海绵"),
        ],
    },
}

REGIONS = ["VN", "TH", "MY", "PH", "SG"]
REGION_NAMES = {"VN": "越南", "TH": "泰国", "MY": "马来西亚", "PH": "菲律宾", "SG": "新加坡"}

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output",
    "echotik_raw",
)
SUMMARY_DIR = os.path.dirname(OUTPUT_DIR)

MAX_RETRIES = 3
RETRY_DELAY = 2  # 初始延迟秒
REQUEST_INTERVAL = 0.5  # 请求间隔秒

# =====================================================================
# 日志设置
# =====================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# =====================================================================
# 核心函数
# =====================================================================

def make_request(params: dict, retries: int = MAX_RETRIES) -> Optional[dict]:
    """带重试的API请求"""
    query_string = urlencode(params)
    url = f"{BASE_URL}?{query_string}"

    for attempt in range(1, retries + 1):
        try:
            req = Request(url, headers=HEADERS, method="GET")
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data
        except HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            logger.warning(f"HTTP {e.code} (attempt {attempt}/{retries}): {body[:200]}")
            if attempt < retries:
                wait = RETRY_DELAY * (2 ** (attempt - 1))
                time.sleep(wait)
        except (URLError, ConnectionError, TimeoutError) as e:
            logger.warning(f"网络错误 (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                wait = RETRY_DELAY * (2 ** (attempt - 1))
                time.sleep(wait)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析错误 (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                wait = RETRY_DELAY * (2 ** (attempt - 1))
                time.sleep(wait)

    logger.error(f"请求失败（重试{retries}次后）: {url[:200]}")
    return None


def fetch_category_l3(
    category_key: str,
    region: str,
    page_num: int = 1,
    page_size: int = 10,
) -> Optional[dict]:
    """拉取单个品类单个国家的商品列表"""
    cat = CATEGORIES[category_key]
    params = {
        "region": region,
        "page_size": page_size,
        "page_num": page_num,
        "product_sort_field": 5,   # 30天销量排序
        "sort_type": 1,            # 降序
        "off_mark": 0,             # 仅上架
        "from_flag": 1,            # 仅本土店
    }

    # 注意: EchoTik API 用 category_l3_id 过滤
    # 但L3品类的每一层都是独立的L3分类
    # 我们先遍历所有L3子分类，组合每页的调用

    results = []
    l3_list = cat["l3s"]

    for l3_id, l3_name in l3_list:
        params_l3 = dict(params)
        params_l3["category_l3_id"] = l3_id

        for pn in range(1, page_num + 1):
            params_l3["page_num"] = pn
            logger.info(
                f"📡 [{category_key}] [{region}] [{l3_name}({l3_id})] "
                f"第{pn}/{page_num}页..."
            )

            data = make_request(params_l3)
            if data and data.get("code") == 0:
                items = data.get("data", [])
                if items:
                    for item in items:
                        item["_l3_name"] = l3_name
                        item["_l3_id"] = l3_id
                    results.extend(items)
                    logger.info(f"  ✅ 获取 {len(items)} 个商品")
                else:
                    logger.info(f"  ℹ️ 无商品")
            else:
                err_msg = data.get("msg", "未知错误") if data else "无响应"
                logger.warning(f"  ⚠️ {err_msg}")

            time.sleep(REQUEST_INTERVAL)

    return results


def fetch_all(
    categories: list = None,
    regions: list = None,
    pages: int = 10,
) -> dict:
    """拉取全部品类全部国家的数据"""
    if categories is None:
        categories = list(CATEGORIES.keys())
    if regions is None:
        regions = REGIONS

    all_data = {}

    total_requests = len(categories) * len(regions) * sum(
        len(CATEGORIES[c]["l3s"]) for c in categories
    ) * pages

    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 EchoTik 数据拉取启动")
    logger.info(f"品类: {', '.join(CATEGORIES[c]['name'] for c in categories)}")
    logger.info(f"国家: {', '.join(regions)}")
    logger.info(f"预计请求数: ~{total_requests} 次")
    logger.info(f"预计费用: ~¥{total_requests * 0.01:.2f}")
    logger.info(f"{'='*60}\n")

    for cat_key in categories:
        cat = CATEGORIES[cat_key]
        cat_data = {r: [] for r in regions}

        for region in regions:
            logger.info(f"\n{'─'*40}")
            logger.info(f"📦 [{cat['name']}] [{REGION_NAMES.get(region, region)}] 开始")
            logger.info(f"{'─'*40}")

            l3_ids = [l3[0] for l3 in cat["l3s"]]

            for l3_id, l3_name in cat["l3s"]:
                params = {
                    "region": region,
                    "category_l3_id": l3_id,
                    "page_size": 10,
                    "product_sort_field": 5,
                    "sort_type": 1,
                    "off_mark": 0,
                    "from_flag": 1,
                }

                for pn in range(1, pages + 1):
                    params["page_num"] = pn
                    logger.info(
                        f"📡 [{cat['name']}] [{region}] [{l3_name}] 第{pn}/{pages}页..."
                    )

                    data = make_request(params)
                    if data and data.get("code") == 0:
                        items = data.get("data", [])
                        if items:
                            for item in items:
                                item["_l3_name"] = l3_name
                                item["_l3_id"] = l3_id
                            cat_data[region].extend(items)
                            logger.info(f"  ✅ {len(items)} 个商品")
                        else:
                            logger.info(f"  ℹ️ 无商品")
                    else:
                        err_msg = data.get("msg", "无响应") if data else "无响应"
                        logger.warning(f"  ⚠️ 请求失败: {err_msg}")

                    time.sleep(REQUEST_INTERVAL)

            region_count = len(cat_data[region])
            logger.info(
                f"📊 [{cat['name']}] [{REGION_NAMES.get(region, region)}] "
                f"完成 — 共 {region_count} 个商品"
            )

        all_data[cat_key] = cat_data

    return all_data


def save_raw_data(all_data: dict):
    """保存原始JSON数据到文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    saved_files = []
    for cat_key, cat_data in all_data.items():
        for region, items in cat_data.items():
            filename = f"{cat_key}_{region}.json"
            filepath = os.path.join(OUTPUT_DIR, filename)
            # 保存为{ items: [...] }格式，保留完整字段
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({"items": items, "total": len(items), "category": cat_key, "region": region}, f, ensure_ascii=False, indent=2)
            saved_files.append((filepath, len(items)))
            logger.info(f"💾 已保存: {filename} ({len(items)} 个商品)")

    return saved_files


def generate_summary(all_data: dict, saved_files: list) -> str:
    """生成汇总报告"""
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    total_all = 0

    for cat_key, cat_data in all_data.items():
        for region, items in cat_data.items():
            total_all += len(items)

    # 建立文件映射
    file_map = {}
    for fpath, cnt in saved_files:
        fname = os.path.basename(fpath)
        key = fname.replace(".json", "")
        file_map[key] = fname

    # 生成报告
    lines = []
    lines.append(f"# EchoTik 数据拉取报告（{today}）\n")
    lines.append(f"> 生成时间: {timestamp}\n")
    lines.append(f"---\n")
    lines.append(f"## 📊 总览\n")
    lines.append(f"| 品类 | 国家 | 商品数 | 原始文件 |")
    lines.append(f"|:---|:---:|:---:|:---|")

    for cat_key, cat_data in all_data.items():
        cat_name = CATEGORIES[cat_key]["name"]
        for region, items in cat_data.items():
            region_name = REGION_NAMES.get(region, region)
            count = len(items)
            fname = file_map.get(f"{cat_key}_{region}", "—")
            lines.append(f"| {cat_name} | {region_name} | {count} | `{fname}` |")

    lines.append(f"| **合计** | **15组** | **{total_all}** | |\n")

    lines.append(f"---\n")
    lines.append(f"## 🛒 按单品统计（精选字段）\n")
    lines.append(f"> 字段: 商品名, 品类, 国家, 价格区间, 30天销量, 30天GMV, 评分, 佣金率\n")
    lines.append(f"| # | 商品名 | L3品类 | 国家 | 价格(起) | 30天销量 | 30天GMV($) | 评分 | 佣金率 | 店铺 |")
    lines.append(f"|---:|:---|:---|:---:|---:|---:|---:|---:|---:|:---|")

    seq = 0
    for cat_key, cat_data in all_data.items():
        cat = CATEGORIES[cat_key]
        for region, items in cat_data.items():
            region_name = REGION_NAMES.get(region, region)
            # 按30天销量降序排列
            sorted_items = sorted(items, key=lambda x: x.get("total_sale_30d_cnt", 0) or 0, reverse=True)
            for item in sorted_items:
                seq += 1
                name = item.get("product_name", "—")
                if len(name) > 40:
                    name = name[:37] + "..."
                l3_name = item.get("_l3_name", "—")
                min_price = item.get("min_price", "—")
                max_price = item.get("max_price", "—")
                price = f"{min_price}" if min_price == max_price else f"{min_price}~{max_price}"
                sale_30d = item.get("total_sale_30d_cnt", 0) or 0
                gmv_30d = item.get("total_sale_gmv_30d_amt", 0) or 0
                rating = item.get("product_rating", "—")
                commission = item.get("product_commission_rate", "—")
                if commission != "—":
                    commission = f"{commission}%"
                shop = item.get("shop_name", "—")
                lines.append(f"| {seq} | {name} | {l3_name} | {region_name} | {price} | {sale_30d:,} | {gmv_30d:,.2f} | {rating} | {commission} | {shop} |")
                if seq >= 200:
                    break
            if seq >= 200:
                break
        if seq >= 200:
            break

    if seq > 200:
        lines.append(f"| ... | *更多商品请查看原始JSON文件* | | | | | | | |")

    lines.append(f"\n---\n")
    lines.append(f"## 📐 调用统计\n")
    lines.append(f"- 总商品数: **{total_all}**\n")
    lines.append(f"- 覆盖品类: {len(all_data)} 个\n")
    lines.append(f"- 覆盖国家: {len(REGIONS)} 个\n")
    lines.append(f"- 筛选条件: 30天销量降序 · 仅本土店 · 仅在售\n")

    lines.append(f"\n---\n")
    lines.append(f"*由 豌豆·数据Agent 于 {timestamp} 自动生成*\n")

    report = "\n".join(lines)
    report_path = os.path.join(SUMMARY_DIR, f"echotik_summary_{today}.md")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    logger.info(f"📄 汇总报告已保存: {os.path.basename(report_path)}")
    return report_path, total_all


def run_single(category: str, region: str, pages: int = 10):
    """运行单品类单国家拉取"""
    logger.info(f"🔍 单次拉取: {category}/{region}, {pages}页")

    cat = CATEGORIES.get(category)
    if not cat:
        logger.error(f"未知品类: {category}, 可选: {list(CATEGORIES.keys())}")
        return

    if region not in REGIONS:
        logger.error(f"未知国家: {region}, 可选: {REGIONS}")
        return

    cat_data = {region: []}
    for l3_id, l3_name in cat["l3s"]:
        params = {
            "region": region,
            "category_l3_id": l3_id,
            "page_size": 10,
            "product_sort_field": 5,
            "sort_type": 1,
            "off_mark": 0,
            "from_flag": 1,
        }
        for pn in range(1, pages + 1):
            params["page_num"] = pn
            logger.info(f"📡 [{cat['name']}] [{region}] [{l3_name}] 第{pn}/{pages}页...")
            data = make_request(params)
            if data and data.get("code") == 0:
                items = data.get("data", [])
                if items:
                    for item in items:
                        item["_l3_name"] = l3_name
                        item["_l3_id"] = l3_id
                    cat_data[region].extend(items)
                    logger.info(f"  ✅ {len(items)} 个商品")
                else:
                    logger.info(f"  ℹ️ 无商品")
            time.sleep(REQUEST_INTERVAL)

    all_data = {category: cat_data}
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    saved = save_raw_data(all_data)
    report_path, total = generate_summary(all_data, saved)
    return all_data, report_path


# =====================================================================
# 入口
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="EchoTik 数据拉取脚本 - TikTok东南亚选品数据管线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 echotik_fetcher.py                       # 全量拉取(3品类×5国×10页)
  python3 echotik_fetcher.py --category beauty      # 仅美妆工具
  python3 echotik_fetcher.py --region VN            # 仅越南
  python3 echotik_fetcher.py --category beauty --region VN  # 美妆×越南
        """,
    )
    parser.add_argument("--category", type=str, choices=list(CATEGORIES.keys()), help="品类: beauty/kitchen/home")
    parser.add_argument("--region", type=str, choices=REGIONS, help="国家: VN/TH/MY/PH/SG")
    parser.add_argument("--pages", type=int, default=10, help="每L3拉取页数（默认10）")
    parser.add_argument("--no-save", action="store_true", help="仅打印，不保存文件")
    args = parser.parse_args()

    start_time = time.time()

    if args.category and args.region:
        run_single(args.category, args.region, args.pages)
    elif args.category:
        all_data = fetch_all(categories=[args.category], regions=REGIONS, pages=args.pages)
    elif args.region:
        all_data = fetch_all(categories=list(CATEGORIES.keys()), regions=[args.region], pages=args.pages)
    else:
        all_data = fetch_all(pages=args.pages)

    if not args.no_save and not (args.category and args.region):
        # 创建输出目录
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        saved_files = save_raw_data(all_data)
        report_path, total = generate_summary(all_data, saved_files)

        elapsed = time.time() - start_time
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ EchoTik 数据拉取完成！")
        logger.info(f"⏱ 耗时: {elapsed:.1f}秒")
        logger.info(f"📦 总商品数: {total}")
        logger.info(f"💾 原始数据: {OUTPUT_DIR}/")
        logger.info(f"📄 汇总报告: {report_path}")
        logger.info(f"{'='*60}")
    elif args.no_save:
        logger.info("ℹ️ --no-save 模式，跳过文件保存")


if __name__ == "__main__":
    main()
