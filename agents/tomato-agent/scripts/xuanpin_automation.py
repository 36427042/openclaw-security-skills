#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EchoTik 选品自动化脚本
========================
拉取 TikTok 东南亚5国(TH/MY/VN/PH/SG)美妆类目热销商品，评分筛选，生成选品报告。

TikTok 东南亚5国美妆电商选品自动化
Author: 土豆 (Tudou 🤖)
"""

import json
import os
import sys
import time
import base64
import urllib.request
import urllib.error
from datetime import datetime, date
from typing import Optional


# ============================================================
# 1. 配置模块
# ============================================================

class Config:
    """全局配置：读取凭证、定义国家参数、美妆类目映射"""

    # 美妆工具相关三级类目ID（泰国已验证）
    # 一级: 601450 美妆(ความงามและของใช้ส่วนตัว)
    # 二级: 848648 彩妆(เครื่องสำอางและน้ำหอม)
    MAKEUP_TOOLS_L3_IDS = {
        "601537": "化妆工具(อุปกรณ์แต่งหน้า)",
        "601529": "化妆套装(เซ็ทแต่งหน้า)",
        "601585": "睫毛膏(มาสคาร่า)",
        "601586": "眉笔/眉胶(ดินสอและเจลเขียนคิ้ว)",
        "601587": "眼线笔(อายไลเนอร์และลิปไลเนอร์)",
        "601588": "眼影(อายแชโดว์)",
        "852752": "化妆镜(กระจกแต่งหน้า)",
        "852880": "美妆蛋(ปุ๋ยแต่งหน้า)",
        "853392": "睫毛夹(เครื่องบีบขูบขนตา)",
        "853520": "睫毛增长/打底(ตัวยกระดับและปริเมอร์ขนตา)",
    }

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config", "echotik.json"
            )
        with open(config_path, "r", encoding="utf-8") as f:
            creds = json.load(f)

        self.base_url = creds["base_url"].rstrip("/")
        self.username = creds["username"]
        self.password = creds["password"]

        # 国家配置
        self.regions = {
            "TH": {"lang": "th-TH", "currency": "THB", "name": "泰国", "rate2usd": 0.028},
            "MY": {"lang": "ms-MY", "currency": "MYR", "name": "马来西亚", "rate2usd": 0.22},
            "VN": {"lang": "vi-VN", "currency": "VND", "name": "越南", "rate2usd": 0.000041},
            "PH": {"lang": "en-US", "currency": "PHP", "name": "菲律宾", "rate2usd": 0.018},
            "SG": {"lang": "en-US", "currency": "SGD", "name": "新加坡", "rate2usd": 0.74},
        }

    def get_auth_header(self) -> dict:
        """Basic Auth 请求头"""
        auth_str = f"{self.username}:{self.password}"
        encoded = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
        return {"Authorization": f"Basic {encoded}", "Content-Type": "application/json"}


# ============================================================
# 2. API 客户端
# ============================================================

class EchoTikClient:
    """EchoTik Open API 客户端"""

    def __init__(self, config: Config):
        self.config = config
        self.headers = config.get_auth_header()
        self.base_url = config.base_url

    def _request(self, method: str, path: str, body: dict = None,
                 max_retries: int = 3) -> Optional[dict]:
        """通用请求封装，含指数退避重试"""
        url = f"{self.base_url}/{path.lstrip('/')}"
        data_bytes = None
        if body:
            data_bytes = json.dumps(body).encode("utf-8")

        for attempt in range(1, max_retries + 1):
            try:
                req = urllib.request.Request(url, data=data_bytes,
                                             headers=self.headers, method=method)
                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    code = result.get("code")
                    if code not in (None, 0, 200):
                        print(f"  ⚠ API警告 [{path}]: code={code} msg={result.get('message','')}")
                    return result

            except urllib.error.HTTPError as e:
                code = e.code
                print(f"  ⚠ HTTP {code} [{path}]", end="")
                if code >= 500 and attempt < max_retries:
                    wait = 2 ** attempt
                    print(f" → 等待{wait}s重试({attempt}/{max_retries})")
                    time.sleep(wait)
                else:
                    print(f" → 放弃")
                    try:
                        print(f"    响应: {e.read().decode('utf-8')[:200]}")
                    except Exception:
                        pass
                    return None

            except urllib.error.URLError as e:
                print(f"  ⚠ 网络错误[{path}]: {e.reason}", end="")
                if attempt < max_retries:
                    wait = 2 ** attempt
                    print(f" → 等待{wait}s")
                    time.sleep(wait)
                else:
                    print(" → 放弃")
                    return None

            except (json.JSONDecodeError, Exception) as e:
                print(f"  ⚠ 解析错误[{path}]: {e}")
                return None

        return None

    def get(self, path: str) -> Optional[dict]:
        return self._request("GET", path)

    def post(self, path: str, body: dict) -> Optional[dict]:
        return self._request("POST", path, body)

    def search_products(self, region: str, category_l3_id: str = None,
                        page_num: int = 1, page_size: int = 10,
                        sort_field: int = 1, sort_type: int = 1,
                        min_price: float = None, max_price: float = None,
                        min_sale_30d: int = None,
                        from_flag: int = None) -> list:
        """
        搜索商品列表（核心接口）。

        参数:
            region: TH/MY/VN/PH/SG
            category_l3_id: 三级类目ID
            sort_field: 1=总销量 2=总GMV 5=近30天销量 7=近30天GMV
            sort_type: 0=升序 1=降序
            min_price/max_price: SKU均价范围
            min_sale_30d: 近30天销量下限
            from_flag: 1=本土 2=跨境
        """
        params = [
            f"region={region}",
            f"page_num={page_num}",
            f"page_size={page_size}",
            f"product_sort_field={sort_field}",
            f"sort_type={sort_type}",
        ]
        if category_l3_id:
            params.append(f"category_l3_id={category_l3_id}")
        if min_price is not None:
            params.append(f"min_spu_avg_price={min_price}")
        if max_price is not None:
            params.append(f"max_spu_avg_price={max_price}")
        if min_sale_30d is not None:
            params.append(f"min_total_sale_30d_cnt={min_sale_30d}")
        if from_flag is not None:
            params.append(f"from_flag={from_flag}")

        path = f"product/list?{'&'.join(params)}"
        data = self.get(path)
        if data and isinstance(data, dict):
            return data.get("data", [])
        return []

    def get_product_detail(self, product_ids: list) -> list:
        """批量获取商品详情（最多10个/次）"""
        ids_str = ",".join(product_ids[:10])
        path = f"product/detail?product_ids={ids_str}"
        data = self.get(path)
        if data and isinstance(data, dict):
            return data.get("data", [])
        return []

    def get_top_selling_products(self, region: str, category_l3_id: str,
                                 page_size: int = 10) -> list:
        """获取某三级类目热销商品（默认按总销量降序）"""
        return self.search_products(
            region=region,
            category_l3_id=category_l3_id,
            page_size=min(page_size, 10),  # max page_size is 10
            sort_field=1,  # 总销量
            sort_type=1,   # 降序
        )


# ============================================================
# 3. 选品分析器
# ============================================================

class ProductAnalyzer:
    """
    选品分析器
    - 遍历美妆工具三级类目，拉取热销商品
    - 计算评分，价格筛选 $1-$20
    """

    # 评分权重
    WEIGHTS = {
        "sale_cnt": 0.30,     # 总销量
        "gmv": 0.25,          # GMV
        "ifl_cnt": 0.20,      # 带货达人数
        "video_cnt": 0.15,    # 关联视频数
        "rating": 0.10,       # 评分
    }

    PRICE_MIN_USD = 0.05
    PRICE_MAX_USD = 20.0

    def __init__(self, client: EchoTikClient, config: Config):
        self.client = client
        self.config = config

    def _currency_to_usd(self, amount: float, currency: str) -> float:
        """粗略汇率换算"""
        rates = {
            "THB": 0.028, "MYR": 0.22, "VND": 0.000041,
            "PHP": 0.018, "SGD": 0.74,
        }
        return amount * rates.get(currency, 1.0)

    def _get_price_usd(self, product: dict, currency: str,
                       rate2usd: float) -> float:
        """获取商品均价并转美元
        
        API返回的min_price/max_price是单品/散件的价格（不是套装价），
        美妆工具很多单品就几THB（如化妆蛋、睫毛夹散件）。
        用spu_avg_price（SPU均价）更能反映实际售价。
        """
        # 优先使用spu_avg_price，其次min_price
        spu_avg_price = float(product.get("spu_avg_price", 0) or 0)
        if spu_avg_price > 0:
            return spu_avg_price * rate2usd
        min_price = float(product.get("min_price", 0) or 0)
        return min_price * rate2usd

    def _score_product(self, product: dict) -> float:
        """选品评分 (0-100)"""
        w = self.WEIGHTS
        sale_cnt = float(product.get("total_sale_cnt", 0) or 0)
        gmv = float(product.get("total_sale_gmv_amt", 0) or 0)
        ifl_cnt = float(product.get("total_ifl_cnt", 0) or 0)
        video_cnt = float(product.get("total_video_cnt", 0) or 0)
        rating = float(product.get("product_rating", 0) or 0)

        # 对数缩放标准化
        norm_sale = min(100, (sale_cnt ** 0.3) * 8) if sale_cnt > 0 else 0
        norm_gmv = min(100, (gmv ** 0.25) * 5) if gmv > 0 else 0
        norm_ifl = min(100, ifl_cnt * 2) if ifl_cnt > 0 else 0
        norm_video = min(100, video_cnt * 1.5) if video_cnt > 0 else 0
        norm_rating = (rating / 5.0) * 100 if rating > 0 else 0

        score = (
            w["sale_cnt"] * norm_sale +
            w["gmv"] * norm_gmv +
            w["ifl_cnt"] * norm_ifl +
            w["video_cnt"] * norm_video +
            w["rating"] * norm_rating
        )
        return round(score, 2)

    def _get_l3_category_name(self, region: str, category_l3_id: str) -> str:
        """获取三级类目名称（已知映射或用ID）"""
        # 直接用已知的美妆工具类目
        known = Config.MAKEUP_TOOLS_L3_IDS
        if category_l3_id in known:
            return known[category_l3_id]
        return f"类目{category_l3_id}"

    def analyze_region(self, region: str, top_per_category: int = 10,
                       max_products: int = 300) -> dict:
        """
        对指定国家执行选品分析。

        流程:
        1. 遍历各美妆工具三级类目
        2. 拉取热销商品
        3. 评分筛选 ($1-$20, 有销量)
        4. 分类统计
        """
        region_cfg = self.config.regions[region]
        region_name = region_cfg["name"]
        currency = region_cfg["currency"]
        rate2usd = region_cfg["rate2usd"]

        print(f"\n{'='*60}")
        print(f"📍 {region_name} ({region}) | 货币: {currency}")
        print(f"{'='*60}")

        # 使用已知类目遍历
        all_products = []
        seen_pids = set()
        category_stats = {}

        l3_ids = list(Config.MAKEUP_TOOLS_L3_IDS.keys())

        for cat_idx, l3_id in enumerate(l3_ids):
            cat_name = self._get_l3_category_name(region, l3_id)
            print(f"\n  [{cat_idx+1}/{len(l3_ids)}] 📦 {cat_name}...", end="")

            # 拉取热销商品（每类目前TOP，page_size最多10）
            products = self.client.get_top_selling_products(
                region=region,
                category_l3_id=l3_id,
                page_size=top_per_category,
            )

            if not products:
                print(" → 0件")
                category_stats[l3_id] = {"name": cat_name, "count": 0}
                time.sleep(0.3)
                continue

            # 去重
            new_count = 0
            for p in products:
                pid = p.get("product_id", "")
                if pid and pid not in seen_pids:
                    seen_pids.add(pid)
                    p["_region"] = region
                    p["_category_name"] = cat_name
                    p["_category_l3_id"] = l3_id
                    all_products.append(p)
                    new_count += 1

            category_stats[l3_id] = {"name": cat_name, "count": len(products)}
            print(f" → {len(products)}件 (新增{new_count})")
            time.sleep(0.3)

        print(f"\n  📊 共采集 {len(all_products)} 件商品 (去重后)")

        # 评分筛选
        scored = []
        for p in all_products:
            price_usd = self._get_price_usd(p, currency, rate2usd)
            sale_cnt = int(p.get("total_sale_cnt", 0) or 0)
            off_mark = p.get("off_mark", 0)

            if price_usd < self.PRICE_MIN_USD or price_usd > self.PRICE_MAX_USD:
                continue
            if sale_cnt <= 0:
                continue
            if off_mark != 0:
                continue

            score = self._score_product(p)
            p["_score"] = score
            p["_price_usd"] = round(price_usd, 2)
            scored.append(p)

        scored.sort(key=lambda x: x["_score"], reverse=True)

        # 分本土/跨境
        local_products = [p for p in scored
                          if str(p.get("from_flag", "")) == "1"]
        cross_products = [p for p in scored
                          if str(p.get("from_flag", "")) == "2"]

        # 价格带分析
        price_analysis = self._analyze_price_band(scored)

        print(f"\n  ✅ 筛选后: {len(scored)} 件合格")
        print(f"    本土: {len(local_products)} | 跨境: {len(cross_products)}")

        return {
            "region": region,
            "region_name": region_name,
            "currency": currency,
            "all_count": len(all_products),
            "scored": scored,
            "local_products": local_products,
            "cross_products": cross_products,
            "category_stats": category_stats,
            "price_analysis": price_analysis,
        }

    def _analyze_price_band(self, products: list) -> dict:
        """价格带分布分析"""
        bands = {
            "$1-$3": {"min": 1, "max": 3, "count": 0, "total_sales": 0},
            "$3-$5": {"min": 3, "max": 5, "count": 0, "total_sales": 0},
            "$5-$10": {"min": 5, "max": 10, "count": 0, "total_sales": 0},
            "$10-$15": {"min": 10, "max": 15, "count": 0, "total_sales": 0},
            "$15-$20": {"min": 15, "max": 20, "count": 0, "total_sales": 0},
        }

        for p in products:
            pu = p.get("_price_usd", 0)
            if not pu:
                continue
            for name, band in bands.items():
                if band["min"] <= pu < band["max"]:
                    band["count"] += 1
                    band["total_sales"] += int(p.get("total_sale_cnt", 0) or 0)
                    break

        best = max(bands.items(), key=lambda kv: kv[1]["total_sales"]) if bands else ("N/A", {})
        return {"bands": bands, "best_selling_band": best[0]}


# ============================================================
# 4. 报告生成器
# ============================================================

class ReportGenerator:
    """Markdown 选品报告生成"""

    def __init__(self, output_dir: str = None):
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "reports"
            )
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _truncate(self, s: str, max_chars: int = 25) -> str:
        if not s:
            return "N/A"
        result = []
        width = 0
        for ch in s:
            w = 2 if ord(ch) > 127 else 1
            if width + w > max_chars - 2:
                result.append("…")
                break
            result.append(ch)
            width += w
        return "".join(result)

    def _fmt_gmv_local(self, gmv: float, currency: str) -> str:
        symbols = {"THB": "฿", "MYR": "RM", "VND": "₫", "PHP": "₱", "SGD": "S$"}
        sym = symbols.get(currency, currency)
        if gmv >= 1_000_000:
            return f"{sym}{gmv/1_000_000:.1f}M"
        elif gmv >= 1_000:
            return f"{sym}{gmv/1_000:.1f}K"
        return f"{sym}{gmv:.0f}"

    def generate_report(self, results: dict) -> str:
        """生成完整五国选品报告"""
        today = date.today()
        report_date = today.strftime("%Y-%m-%d")
        week_day = today.strftime("%A")

        lines = []
        lines.append(f"# TikTok 东南亚5国美妆工具选品报告\n")
        lines.append(f"**生成日期**: {report_date} ({week_day})\n")
        lines.append(f"**覆盖市场**: 🇹🇭泰国(TH) · 🇲🇾马来西亚(MY) · 🇻🇳越南(VN) · 🇵🇭菲律宾(PH) · 🇸🇬新加坡(SG)\n")
        lines.append(f"**价格范围**: $1 - $20 USD\n")
        lines.append(f"**三级类目**: {len(Config.MAKEUP_TOOLS_L3_IDS)} 个美妆工具子类目\n")
        lines.append(f"**评分权重**: 销量(30%) · GMV(25%) · 达人关联(20%) · 视频关联(15%) · 评分(10%)\n")
        lines.append("\n---\n")

        # 全局汇总
        lines.append("## 📊 全局汇总\n")
        lines.append("| 市场 | 采集数 | 合格数 | 本土 | 跨境 | 最佳价格带 |\n")
        lines.append("|------|-------|-------|-----|------|----------|\n")

        total_all = 0
        total_scored = 0
        for code, r in results.items():
            if "error" in r:
                lines.append(f"| {r.get('region_name',code)} | ❌ {r['error']} | - | - | - | - |\n")
            else:
                scored = r["scored"]
                total_all += r["all_count"]
                total_scored += len(scored)
                local = len(r["local_products"])
                cross = len(r["cross_products"])
                best = r["price_analysis"].get("best_selling_band", "-")
                lines.append(f"| {r['region_name']} {code} | {r['all_count']} | {len(scored)} | {local} | {cross} | {best} |\n")

        lines.append(f"\n**合计**: 采集 {total_all} 件 → 合格 {total_scored} 件\n")
        lines.append("\n---\n")

        for region_code, result in results.items():
            if "error" in result:
                lines.append(f"## ❌ {result.get('region_name', region_code)} ({region_code})\n")
                lines.append(f"> 数据采集失败: {result['error']}\n")
                lines.append("\n---\n")
                continue

            self._append_region_report(lines, region_code, result)
            lines.append("\n---\n")

        return "\n".join(lines)

    def _append_region_report(self, lines: list, region_code: str, r: dict):
        """添加单个国家报告"""
        rn = r["region_name"]
        currency = r["currency"]
        scored = r["scored"]
        if not scored:
            lines.append(f"## {rn} ({region_code}) ⚠️\n")
            lines.append(f"> 未筛选出符合价格条件($1-$20)的商品\n")
            return

        local = r["local_products"]
        cross = r["cross_products"]
        pa = r["price_analysis"]
        cs = r["category_stats"]

        lines.append(f"## {rn} ({region_code})\n")

        # 统计概览
        lines.append("### 📊 统计概览\n")
        lines.append(f"| 指标 | 数值 |\n")
        lines.append(f"|------|------|\n")
        lines.append(f"| 采集商品数 | {r['all_count']} |\n")
        lines.append(f"| 合格商品数(筛选后) | {len(scored)} |\n")
        lines.append(f"| 本土商品 | {len(local)} |\n")
        lines.append(f"| 跨境商品 | {len(cross)} |\n")
        lines.append(f"| 覆盖类目 | {sum(1 for v in cs.values() if v['count']>0)}/{len(cs)} |\n")
        lines.append("")

        # TOP10 选品推荐
        top10 = scored[:10]
        lines.append("### 🏆 TOP10 选品推荐\n")
        header = "| # | 商品名 | 价格(USD)"
        sep = "|---|--------|-----------"
        header += " | 总销量 | 月GMV"
        sep += " |------|-------"
        header += " | 视频 | 达人 | 评分 | 来源"
        sep += " |------|------|------|------"
        header += " | 趋势 | 评分 |"
        sep += " |------|------|"
        lines.append(header)
        lines.append(sep)

        symbols = {"THB": "฿", "MYR": "RM", "VND": "₫", "PHP": "₱", "SGD": "S$"}
        sym = symbols.get(currency, currency)

        for i, p in enumerate(top10, 1):
            name = self._truncate(p.get("product_name", ""), 22) or "N/A"
            price = p.get("_price_usd", 0)
            sale_cnt = int(p.get("total_sale_cnt", 0) or 0)
            gmv_local = float(p.get("total_sale_gmv_amt", 0) or 0)
            gmv_str = self._fmt_gmv_local(gmv_local, currency)
            video = int(p.get("total_video_cnt", 0) or 0)
            ifl = int(p.get("total_ifl_cnt", 0) or 0)
            rating = p.get("product_rating", 0) or 0
            from_flag = p.get("from_flag", 0)
            source = "🇹🇭本土" if str(from_flag) == "1" else "🌏跨境"

            trend = p.get("sales_trend_flag", 0)
            trend_s = {0: "平稳📊", 1: "上升📈", 2: "下降📉"}.get(trend, "N/A")

            score = p.get("_score", 0)
            lines.append(f"| {i} | {name} | ${price} | {sale_cnt:,} | {gmv_str} | {video} | {ifl} | {rating} | {source} | {trend_s} | **{score}** |")

        lines.append("")

        # 价格带分析
        lines.append("### 💰 价格带分析\n")
        lines.append("| 价格带(USD) | 商品数 | 总销量 | 占比 |\n")
        lines.append("|-------------|--------|--------|------|\n")

        bands = pa.get("bands", {})
        total_sales_all = sum(b["total_sales"] for b in bands.values())
        for name in ["$1-$3", "$3-$5", "$5-$10", "$10-$15", "$15-$20"]:
            b = bands.get(name)
            if b and b["count"] > 0:
                pct = (b["total_sales"] / total_sales_all * 100) if total_sales_all > 0 else 0
                lines.append(f"| {name} | {b['count']} | {b['total_sales']:,} | {pct:.1f}% |\n")

        best = pa.get("best_selling_band", "N/A")
        lines.append(f"\n**🏅 最佳销量价格带**: {best}\n")
        lines.append("")

        # 达人合作机会
        products_with_ifl = [p for p in scored
                             if int(p.get("total_ifl_cnt", 0) or 0) > 0]
        if products_with_ifl:
            lines.append(f"### 🤝 达人带货机会\n")
            lines.append(f"已有 **{len(products_with_ifl)}** 件商品有达人带货:\n")
            lines.append("| 商品名 | 价格(USD) | 达人数 | 总销量 | 来源 |\n")
            lines.append("|--------|-----------|-------|--------|------|\n")

            for p in products_with_ifl[:8]:
                name = self._truncate(p.get("product_name", ""), 18) or "N/A"
                price = p.get("_price_usd", 0)
                ifl_cnt = p.get("total_ifl_cnt", 0) or 0
                sale_cnt = p.get("total_sale_cnt", 0) or 0
                fsrc = "本土" if str(p.get("from_flag", "")) == "1" else "跨境"
                lines.append(f"| {name} | ${price} | {ifl_cnt} | {sale_cnt:,} | {fsrc} |\n")
            lines.append("")
        else:
            lines.append("### 🤝 达人带货机会\n")
            lines.append("> 该市场暂未发现达人带货商品，存在蓝海机会\n\n")


# ============================================================
# 5. 主流程
# ============================================================

def main():
    """选品自动化主入口"""
    print("=" * 60)
    print("🥔 EchoTik 选品自动化")
    print(f"   启动: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 初始化
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(os.path.dirname(script_dir), "config", "echotik.json")
    config = Config(config_path)
    client = EchoTikClient(config)
    analyzer = ProductAnalyzer(client, config)
    report_gen = ReportGenerator(output_dir=os.path.join(script_dir, "reports"))

    # 2. 逐国分析
    regions_to_run = ["TH", "MY", "VN", "PH", "SG"]
    all_results = {}

    for region in regions_to_run:
        try:
            result = analyzer.analyze_region(region)
            all_results[region] = result
            time.sleep(1)
        except Exception as e:
            print(f"\n❌ {region} 分析异常: {e}")
            import traceback
            traceback.print_exc()
            cfg = config.regions[region]
            all_results[region] = {
                "region": region,
                "region_name": cfg["name"],
                "error": str(e),
            }

    # 3. 生成报告
    print(f"\n{'='*60}")
    print("📝 生成选品报告...")
    report = report_gen.generate_report(all_results)

    # 4. 保存
    today = date.today()
    report_filename = f"{today}_XuanpinReport.md"
    report_path = os.path.join(report_gen.output_dir, report_filename)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"✅ 报告已保存: {report_path}")
    print(f"   共分析 {len(all_results)} 个国家")

    # 5. 汇总
    print(f"\n{'='*60}")
    print("📊 汇总:")
    for region_code, result in all_results.items():
        if "error" in result:
            print(f"  ❌ {result['region_name']} ({region_code}): {result['error']}")
        else:
            scored = result.get("scored", [])
            top = scored[:3] if scored else []
            top_names = [p.get("product_name", "?")[:20] for p in top]
            print(f"  ✅ {result['region_name']} ({region_code}): {len(scored)} 件合格")
            if top_names:
                print(f"     TOP3: {top_names}")
    print(f"{'='*60}")
    print(f"🥔 运行完成 @ {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()
