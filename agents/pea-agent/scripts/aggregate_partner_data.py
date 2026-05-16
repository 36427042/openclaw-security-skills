#!/usr/bin/env python3
"""
aggregate_partner_data.py — 全伙伴数据聚合脚本 (v1.0)
扫描各伙伴输出→按sku_id关联→检测全链路断点→输出聚合数据

使用：
  python3 aggregate_partner_data.py                     # 聚合今日数据
  python3 aggregate_partner_data.py --date=2026-05-10   # 指定日期
  python3 aggregate_partner_data.py --output-only        # 仅输出聚合结果

Hermes集成：
  from hermes_hub import hub; hub.run("aggregate")
"""

import json
import os
import sys
import glob
import argparse
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict


class PartnerDataAggregator:
    """
    全伙伴数据聚合器
    从各伙伴数据文件拉取数据→按sku_id关联→全链路检测→输出
    """

    # 各伙伴文件名前缀
    PARTNER_PREFIXES = {
        "tomato": "tomato_data",
        "corn": "corn_data",
        "lettuce": "lettuce_data",
        "radish": "radish_data",
        "bitter": "bitter_data",
    }

    def __init__(self, data_dir: str = ""):
        self.data_dir = data_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "partner_data"
        )
        # 回退到 pea-agent 内部
        if not os.path.exists(self.data_dir):
            alt = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "output"
            )
            if os.path.exists(alt):
                self.data_dir = alt
        os.makedirs(self.data_dir, exist_ok=True)
        self.today = datetime.now().strftime("%Y-%m-%d")

    def _find_files(self, date_str: str) -> dict:
        """按日期查找所有伙伴数据文件"""
        files = {}
        for partner, prefix in self.PARTNER_PREFIXES.items():
            pattern = os.path.join(self.data_dir, f"{prefix}_{date_str}.json")
            matches = glob.glob(pattern)
            if matches:
                files[partner] = matches[0]
        return files

    def _load_json(self, path: str) -> Optional[dict]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  加载失败 {path}: {e}")
        return None

    def aggregate(self, date_str: str = "") -> dict:
        """聚合指定日期所有伙伴数据"""
        date_str = date_str or self.today
        files = self._find_files(date_str)

        print(f"\n📦 聚合日期: {date_str}")
        print(f"{'='*45}")

        if not files:
            print("⚠️  当天无伙伴数据文件，返回空聚合")
            return self._empty_result(date_str)

        # 加载所有伙伴数据
        partner_data = {}
        for partner, path in files.items():
            data = self._load_json(path)
            if data:
                partner_data[partner] = data
                print(f"  ✅ {self.PARTNER_PREFIXES[partner]} → 已加载")

        print(f"\n📊 已加载 {len(partner_data)}/{len(files)} 个伙伴数据")

        # 按 sku_id 建立索引
        return self._build_aggregation(partner_data, date_str, files)

    def _empty_result(self, date_str: str) -> dict:
        return {
            "meta": {
                "date": date_str,
                "aggregated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
                "source_files": [],
                "partner_coverage": {},
                "note": "⚠️ 无伙伴数据文件",
            },
            "sku_aggregation": [],
            "cross_partner_gaps": [],
            "summary": {
                "total_skus": 0,
                "skus_with_full_coverage": 0,
                "total_gaps": 0,
            },
        }

    def _build_aggregation(self, partner_data: dict, date_str: str, files: dict) -> dict:
        """构建sku_id聚合数据"""
        # 从番茄选品数据提取SKU主列表
        sku_index = {}  # sku_id → {source_data}

        # 1. 🍅番茄选品
        tomato = partner_data.get("tomato", {})
        for sel in tomato.get("selections", []):
            sku_id = sel.get("sku_id", "")
            if sku_id:
                if sku_id not in sku_index:
                    sku_index[sku_id] = {
                        "sku_id": sku_id,
                        "product_name": sel.get("product_name", ""),
                        "category": sel.get("category", ""),
                        "selections": [],
                        "videos": [],
                        "copywritings": [],
                        "replenishments": [],
                        "voiceovers": [],
                        "risk_alerts": [],
                        "suppliers": [],
                    }
                sku_index[sku_id]["selections"].append(sel)

        # 如果番茄没有数据，也从玉米/其他人数据提取
        corn = partner_data.get("corn", {})
        for vid in corn.get("videos", []):
            sku_id = vid.get("sku_id", "")
            if sku_id and sku_id not in sku_index:
                sku_index[sku_id] = self._empty_sku(sku_id, vid.get("product_name", ""))
            if sku_id:
                sku_index[sku_id]["videos"].append(vid)

        # 生菜文案
        lettuce = partner_data.get("lettuce", {})
        for cp in lettuce.get("copywritings", []):
            sku_id = cp.get("sku_id", "")
            if sku_id and sku_id not in sku_index:
                sku_index[sku_id] = self._empty_sku(sku_id, cp.get("product_name", ""))
            if sku_id:
                sku_index[sku_id]["copywritings"].append(cp)

        # 萝卜补货+配音
        radish = partner_data.get("radish", {})
        for rp in radish.get("replenishments", []):
            sku_id = rp.get("sku_id", "")
            if sku_id and sku_id not in sku_index:
                sku_index[sku_id] = self._empty_sku(sku_id, rp.get("product_name", ""))
            if sku_id:
                sku_index[sku_id]["replenishments"].append(rp)

        for vo in radish.get("voiceovers", []):
            sku_id = vo.get("sku_id", "")
            if sku_id and sku_id not in sku_index:
                sku_index[sku_id] = self._empty_sku(sku_id, vo.get("product_name", ""))
            if sku_id:
                sku_index[sku_id]["voiceovers"].append(vo)

        for sp in radish.get("suppliers", []):
            sp_id = sp.get("supplier_id", "")
            if sp_id:
                # 供应商信息关联到所有使用该供应商的SKU
                for skuid, sku_data in sku_index.items():
                    for sel in sku_data.get("selections", []):
                        if sel.get("supplier_id") == sp_id:
                            if sp not in sku_data["suppliers"]:
                                sku_data["suppliers"].append(sp)

        # 苦瓜风控
        bitter = partner_data.get("bitter", {})
        for alert in bitter.get("alerts", []):
            sku_id = alert.get("sku_id", "")
            if sku_id and sku_id not in sku_index:
                sku_index[sku_id] = self._empty_sku(sku_id, alert.get("product_name", ""))
            if sku_id:
                sku_index[sku_id]["risk_alerts"].append(alert)

        # 2. 检测全链路断点
        gaps = self._detect_gaps(sku_index)

        # 3. 统计
        total = len(sku_index)
        full_coverage = sum(
            1 for s in sku_index.values()
            if s["selections"] and s["videos"] and s["copywritings"]
        )

        sku_list = list(sku_index.values())

        result = {
            "meta": {
                "date": date_str,
                "aggregated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
                "source_files": list(files.values()),
                "partner_coverage": {
                    p: os.path.basename(files[p]) for p in files
                },
            },
            "sku_aggregation": sku_list,
            "cross_partner_gaps": gaps,
            "summary": {
                "total_skus": total,
                "skus_with_full_coverage": full_coverage,
                "skus_with_selections": sum(1 for s in sku_index.values() if s["selections"]),
                "skus_with_videos": sum(1 for s in sku_index.values() if s["videos"]),
                "skus_with_copywritings": sum(1 for s in sku_index.values() if s["copywritings"]),
                "skus_with_replenishments": sum(1 for s in sku_index.values() if s["replenishments"]),
                "total_gaps": len(gaps),
            },
        }

        return result

    def _empty_sku(self, sku_id: str, name: str = "") -> dict:
        return {
            "sku_id": sku_id,
            "product_name": name,
            "category": "",
            "selections": [],
            "videos": [],
            "copywritings": [],
            "replenishments": [],
            "voiceovers": [],
            "risk_alerts": [],
            "suppliers": [],
        }

    def _detect_gaps(self, sku_index: dict) -> list:
        """检测全链路断点"""
        gaps = []

        for sku_id, sku_data in sku_index.items():
            name = sku_data.get("product_name", sku_id)
            missing = []

            if sku_data["selections"]:
                # 已选品 → 需要后续环节
                if not sku_data["videos"]:
                    missing.append("videos")
                if not sku_data["copywritings"]:
                    missing.append("copywritings")
                if not sku_data["replenishments"]:
                    # 选品已出但没有补货记录，可能是新选品
                    pass

            if missing:
                gap = {
                    "sku_id": sku_id,
                    "product_name": name,
                    "missing": missing,
                    "has_selection": bool(sku_data["selections"]),
                    "has_video": bool(sku_data["videos"]),
                    "has_copywriting": bool(sku_data["copywritings"]),
                    "has_replenishment": bool(sku_data["replenishments"]),
                    "risk_alerts_count": len(sku_data["risk_alerts"]),
                }

                # 给断点加阻塞方信息
                if "videos" in missing and sku_data["selections"]:
                    gap["blocked_by"] = "🌽玉米（视频未产出）"
                elif "copywritings" in missing and sku_data["videos"]:
                    gap["blocked_by"] = "🥬生菜（文案未产出）"
                elif "copywritings" in missing and not sku_data["videos"]:
                    gap["blocked_by"] = "🌽玉米→🥬生菜（待视频完成）"
                else:
                    gap["blocked_by"] = "未知"

                gaps.append(gap)

        return gaps

    def pretty_print(self, result: dict):
        """美观打印聚合结果"""
        meta = result["meta"]
        summary = result["summary"]
        gaps = result["cross_partner_gaps"]

        print(f"\n{'='*50}")
        print(f"  🔗 全伙伴数据聚合 · {meta['date']}")
        print(f"{'='*50}")
        print(f"  来源文件: {len(meta['source_files'])}")
        for f in meta.get("source_files", []):
            print(f"    📄 {os.path.basename(f)}")
        print()

        print(f"  📊 聚合统计:")
        print(f"   总SKU数: {summary['total_skus']}")
        print(f"   有选品: {summary['skus_with_selections']}")
        print(f"   有视频: {summary['skus_with_videos']}")
        print(f"   有文案: {summary['skus_with_copywritings']}")
        print(f"   全链路覆盖: {summary['skus_with_full_coverage']}")
        print(f"   全链路断点: {summary['total_gaps']}")

        if gaps:
            print(f"\n  🔗 全链路断点检测:")
            for g in gaps:
                missing_str = ", ".join(g["missing"])
                print(f"    ⚠️  {g['sku_id']} ({g['product_name']})")
                print(f"       缺: {missing_str}")
                print(f"       阻塞: {g.get('blocked_by', '未知')}")

        print(f"\n{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(description="全伙伴数据聚合")
    parser.add_argument("--date", type=str, default="",
                        help="聚合日期 YYYY-MM-DD（默认今日）")
    parser.add_argument("--output", type=str, default="",
                        help="输出文件路径（默认输出到data_dir）")
    parser.add_argument("--output-only", action="store_true",
                        help="仅输出聚合结果，不打印摘要")
    parser.add_argument("--data-dir", type=str, default="",
                        help="伙伴数据目录")
    args = parser.parse_args()

    agg = PartnerDataAggregator(data_dir=args.data_dir)
    date_str = args.date or agg.today
    result = agg.aggregate(date_str)

    if not args.output_only:
        agg.pretty_print(result)

    # 写文件
    out_dir = args.data_dir or agg.data_dir
    if not args.output:
        output_file = os.path.join(out_dir, f"agg_daily_report_{date_str}.json")
    else:
        output_file = args.output

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ 聚合数据已写入: {output_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
