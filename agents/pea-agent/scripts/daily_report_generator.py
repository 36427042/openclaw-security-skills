#!/usr/bin/env python3
"""
daily_report_generator.py — 自动日报生成器 (v1.1)
可被cron调用，生成JSON日报+Markdown摘要

## cron配置（北京时间晚22:00生成今日完整日报）
我的cron：
  0 14 * * * cd /SSD/OpenClaw/workspace/agents/pea-agent && \
    /usr/bin/python3 scripts/daily_report_generator.py --output_dir=output \
    2>> /tmp/daily_report_cron.log

我的测试（直接跑）：
  cd ~/.openclaw/workspace/agents/pea-agent
  python3 scripts/daily_report_generator.py              # 生成今日日报+md摘要
  python3 scripts/daily_report_generator.py --mode=summary  # 生成前日摘要

输出文件：
  output/daily_report_YYYY-MM-DD.json       — 完整JSON日报（机器人解析用）
  output/daily_report_YYYY-MM-DD.md         — Markdown摘要（飞书可直接粘贴）

Hermes集成：
  from hermes_engine import HermesEngine
  engine.run_workflow("daily_report", {...})
"""

import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class DailyReportGenerator:
    """
    自动日报生成器——从飞书多维表格抓取数据→处理→输出JSON
    当前使用模拟数据，后续接入飞书API后替换 fetch_from_bitable()
    """

    # 阈值配置
    THRESHOLDS = {
        "gpm_min": 80.0,
        "gpm_amber": 50.0,
        "roas_min": 3.0,
        "roas_amber": 1.5,
        "refund_rate_max": 5.0,
        "refund_rate_amber": 10.0,
        "aov_min": 8.0,
        "aov_amber": 5.0,
        "video_factor": 0.7,  # 视频产出下降70%以下算异常
    }

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.today = datetime.now()
        self.yesterday = self.today - timedelta(days=1)
        self.last_week = self.today - timedelta(days=7)
        os.makedirs(self.output_dir, exist_ok=True)

    def fetch_from_bitable(self, table_id: str = "") -> dict:
        """
        从飞书多维表格拉取今日数据（TODO: 接入飞书API）
        需要抓取的5张表：
        1. 经营概况 — GMV/订单/退款/成本数据
        2. 商品分析 — SKU级数据
        3. 达人合作 — 视频数据
        4. 5国对比 — 各国横向数据
        5. 风控监控 — 异常数据
        """
        # 当前返回模拟数据用于模板测试
        return self._mock_today_data()

    def fetch_yesterday_data(self) -> dict:
        """从缓存取昨日数据"""
        yesterday_file = os.path.join(
            self.output_dir,
            f"daily_report_{self.yesterday.strftime('%Y-%m-%d')}.json",
        )
        data = self._load_json(yesterday_file)
        if data:
            return self._mock_yesterday_data()
        return self._mock_yesterday_data()

    def _mock_today_data(self) -> dict:
        return {
            "total_gmv": 12850.50,
            "total_orders": 423,
            "total_refunds": 21,
            "countries_data": self._mock_today_countries(),
            "skus_data": self._mock_skus(),
            "videos_data": self._mock_videos(),
            "gpm_7d": [82.1, 85.3, 80.5, 87.0, 83.1, 83.1, 85.4],
        }

    def _mock_yesterday_data(self) -> dict:
        return {
            "total_gmv": 11440.00,
            "total_orders": 385,
            "total_refunds": 16,
            "countries_data": [
                {"country": "TH", "gmv": 4300, "orders": 148, "refunds": 5,
                 "refund_rate": 3.38, "gpm": 93.5, "roas": 4.0,
                 "ad_spend": 1075.00, "gpm_7d_trend": [88, 92, 90, 95, 93, 91, 93.5]},
                {"country": "MY", "gmv": 2900, "orders": 98, "refunds": 3,
                 "refund_rate": 3.06, "gpm": 85.0, "roas": 3.5,
                 "ad_spend": 828.57, "gpm_7d_trend": [82, 86, 83, 89, 84, 84, 85.0]},
                {"country": "VN", "gmv": 1800, "orders": 62, "refunds": 3,
                 "refund_rate": 4.84, "gpm": 76.5, "roas": 2.8,
                 "ad_spend": 642.86, "gpm_7d_trend": [80, 78, 76, 78, 74, 75, 76.5]},
                {"country": "PH", "gmv": 1600, "orders": 52, "refunds": 3,
                 "refund_rate": 5.77, "gpm": 69.8, "roas": 3.0,
                 "ad_spend": 533.33, "gpm_7d_trend": [72, 71, 68, 73, 70, 69, 69.8]},
                {"country": "SG", "gmv": 840, "orders": 25, "refunds": 2,
                 "refund_rate": 8.00, "gpm": 108.2, "roas": 4.2,
                 "ad_spend": 200.00, "gpm_7d_trend": [102, 105, 110, 112, 108, 107, 108.2]},
            ],
            "skus_data": [],
            "videos_data": [],
            "gpm_7d": [80.5, 83.0, 78.2, 85.1, 81.0, 80.0, 83.0],
        }

    def _mock_today_countries(self) -> list:
        return [
            {"country": "TH", "gmv": 4850.00, "orders": 162, "refunds": 8,
             "refund_rate": 4.94, "gpm": 95.2, "roas": 3.8,
             "ad_spend": 1276.32, "gpm_7d_trend": [90.1, 93.5, 91.2, 97.8, 94.0, 94.0, 95.2]},
            {"country": "MY", "gmv": 3200.00, "orders": 108, "refunds": 5,
             "refund_rate": 4.63, "gpm": 88.5, "roas": 3.2,
             "ad_spend": 1000.00, "gpm_7d_trend": [85.3, 87.2, 84.1, 91.3, 86.7, 86.7, 88.5]},
            {"country": "VN", "gmv": 2100.00, "orders": 71, "refunds": 4,
             "refund_rate": 5.63, "gpm": 72.3, "roas": 2.5,
             "ad_spend": 840.00, "gpm_7d_trend": [78.0, 76.5, 73.2, 75.8, 71.0, 72.0, 72.3]},
            {"country": "PH", "gmv": 1850.50, "orders": 60, "refunds": 3,
             "refund_rate": 5.00, "gpm": 68.7, "roas": 2.8,
             "ad_spend": 660.89, "gpm_7d_trend": [70.2, 69.8, 65.5, 71.0, 67.5, 67.5, 68.7]},
            {"country": "SG", "gmv": 850.00, "orders": 22, "refunds": 1,
             "refund_rate": 4.55, "gpm": 110.3, "roas": 4.1,
             "ad_spend": 207.32, "gpm_7d_trend": [105.0, 108.2, 112.5, 115.0, 109.8, 109.8, 110.3]},
        ]

    def _mock_skus(self) -> list:
        return [
            {"sku_id": "SKU-MT-001", "product_name": "3D美妆蛋12只装",
             "daily_avg_sales": 60, "current_stock": 120,
             "predicted_score": 82, "gross_margin": 65.2},
            {"sku_id": "SKU-MT-002", "product_name": "便携睫毛夹套装",
             "daily_avg_sales": 15, "current_stock": 500,
             "predicted_score": 71, "gross_margin": 68.0},
            {"sku_id": "SKU-MT-003", "product_name": "粉扑清洁盒",
             "daily_avg_sales": 30, "current_stock": 200,
             "predicted_score": 65, "gross_margin": 60.0},
            {"sku_id": "SKU-HO-001", "product_name": "多功能收纳盒",
             "daily_avg_sales": 10, "current_stock": 400,
             "predicted_score": 55, "gross_margin": 55.0},
        ]

    def _mock_videos(self) -> list:
        return [
            {"sku_id": "SKU-MT-001", "video_count_today": 2,
             "total_views": 12500, "conversion_rate": 2.3},
            {"sku_id": "SKU-MT-003", "video_count_today": 0,
             "total_views": 8900, "conversion_rate": 1.8},
        ]

    def analyze_health(self, data: dict) -> str:
        """分析整体健康度"""
        warnings = 0
        red_flags = 0
        for country in data.get("countries_data", []):
            gpm = country.get("gpm", 100)
            roas = country.get("roas", 3.0)
            refund = country.get("refund_rate", 0)
            if gpm < self.THRESHOLDS["gpm_min"]:
                warnings += 1
            if gpm < self.THRESHOLDS["gpm_amber"]:
                red_flags += 1
            if roas < self.THRESHOLDS["roas_min"]:
                warnings += 1
            if roas < self.THRESHOLDS["roas_amber"]:
                red_flags += 1
            if refund > self.THRESHOLDS["refund_rate_max"]:
                warnings += 1
            if refund > self.THRESHOLDS["refund_rate_amber"]:
                red_flags += 1
        if red_flags >= 1 or warnings >= 4:
            return "🔴"
        elif warnings >= 1:
            return "🟡"
        return "🟢"

    def detect_anomalies(self, today: dict, yesterday: dict) -> dict:
        """异常检测引擎"""
        anomalies = {"critical": [], "warnings": [], "info": []}
        now_str = self.today.strftime("%Y-%m-%dT%H:%M:%S+08:00")

        # 1. 退款率突增检测
        for c in today.get("countries_data", []):
            yc = next((x for x in yesterday.get("countries_data", [])
                       if x["country"] == c["country"]), None)
            if yc:
                delta = c["refund_rate"] - yc["refund_rate"]
                if delta > 10:
                    anomalies["critical"].append({
                        "severity": "🔴", "type": "refund_rate_spike",
                        "country": c["country"],
                        "detail": f"退款率突增{delta:.1f}% ({yc['refund_rate']:.1f}→{c['refund_rate']:.1f}%)",
                        "timestamp": now_str, "status": "待处理"
                    })
                elif delta > 5:
                    anomalies["warnings"].append({
                        "severity": "🟡", "type": "refund_rate_rise",
                        "country": c["country"],
                        "detail": f"退款率上升{delta:.1f}%",
                        "timestamp": now_str, "status": "监控中"
                    })

        # 2. GPM持续下滑检测
        for c in today.get("countries_data", []):
            trend = c.get("gpm_7d_trend", [])
            if len(trend) >= 3 and trend[-3] > trend[-2] > trend[-1]:
                anomalies["warnings"].append({
                    "severity": "🟡", "type": "gpm_continuous_decline",
                    "country": c["country"],
                    "detail": f"GPM连续3日下降({trend[-3]:.1f}→{trend[-2]:.1f}→{trend[-1]:.1f})",
                    "timestamp": now_str, "status": "监控中"
                })

        # 3. 库存预警
        for sku in today.get("skus_data", []):
            daily = sku.get("daily_avg_sales", 0)
            stock = sku.get("current_stock", 0)
            if daily > 0 and stock / daily < 3:
                days_left = stock / daily
                anomalies["warnings"].append({
                    "severity": "🟡", "type": "stock_warning",
                    "sku_id": sku["sku_id"],
                    "detail": f"{sku['product_name']}库存{stock}，仅够{days_left:.1f}天",
                    "timestamp": now_str, "status": "待处理"
                })

        # 4. 视频产出下降
        if yesterday.get("videos_data"):
            t_views = sum(v.get("video_count_today", 0)
                          for v in today.get("videos_data", []))
            y_views = sum(v.get("video_count_today", 0)
                          for v in yesterday.get("videos_data", []))
            if y_views > 0 and t_views < y_views * self.THRESHOLDS["video_factor"]:
                anomalies["warnings"].append({
                    "severity": "🟡", "type": "video_production_drop",
                    "detail": f"视频产出较昨日下降{(1-t_views/y_views)*100:.0f}%",
                    "timestamp": now_str, "status": "待确认"
                })

        # 5. 里程碑记录
        milestones = []
        country_data = today.get("countries_data", [])
        for c in country_data:
            if c["gmv"] > 50000:
                milestones.append(f"{c['country']}累计GMV突破${c['gmv']:,.0f}！")
            elif c["orders"] > 200:
                milestones.append(f"{c['country']}单日订单突破{c['orders']}单！")
        for m in milestones:
            anomalies["info"].append({
                "severity": "ℹ️", "type": "milestone",
                "detail": m, "timestamp": now_str, "status": "已记录"
            })

        return anomalies

    def generate_report(self, app_id: str = "", table_id: str = "") -> str:
        """生成完整日报JSON"""
        today_data = self.fetch_from_bitable(table_id)
        yesterday_data = self.fetch_yesterday_data()

        report = {
            "meta": {
                "report_type": "daily_summary",
                "date": self.today.strftime("%Y-%m-%d"),
                "generated_at": self.today.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
                "version": "1.0.0",
                "generated_by": "pea_agent_daily_report_generator",
                "schema": "daily_report_v1"
            },
            "summary": {
                "total_gmv": today_data["total_gmv"],
                "gmv_currency": "USD",
                "total_orders": today_data["total_orders"],
                "total_refunds": today_data["total_refunds"],
                "net_gmv": today_data["total_gmv"] - today_data["total_refunds"] * 20,
                "refund_rate": round(
                    today_data["total_refunds"] / today_data["total_orders"] * 100, 2
                ) if today_data["total_orders"] > 0 else 0,
                "gmv_vs_yesterday_pct": round(
                    (today_data["total_gmv"] - yesterday_data.get("total_gmv", today_data["total_gmv"]))
                    / yesterday_data.get("total_gmv", 1) * 100, 1
                ),
                "overall_health": self.analyze_health(today_data),
            },
            "by_country": [],
            "gpm_trends": self._build_gpm_section(today_data),
            "anomalies": self.detect_anomalies(today_data, yesterday_data),
            "recommendations": [],
            "daily_handoff": [],
        }

        # 填充国家数据
        for c in today_data.get("countries_data", []):
            record = {
                "country": c["country"],
                "gmv": c["gmv"],
                "orders": c["orders"],
                "refunds": c["refunds"],
                "refund_rate": c["refund_rate"],
                "gpm": c["gpm"],
                "roas": c["roas"],
                "ad_spend": c["ad_spend"],
                "health": "🟢",
                "alerts": [],
            }
            country_anomalies = [
                a for a in report["anomalies"]["critical"]
                + report["anomalies"]["warnings"]
                if a.get("country") == c["country"]
            ]
            if country_anomalies:
                record["health"] = "🔴" if any(
                    a["severity"] == "🔴" for a in country_anomalies
                ) else "🟡"
                record["alerts"] = [a["detail"] for a in country_anomalies]
            report["by_country"].append(record)

        # 生成推荐行动
        report["recommendations"] = self._build_recommendations(
            report["anomalies"], today_data
        )

        # 生成交接清单
        report["daily_handoff"] = self._build_handoff(
            report["anomalies"], today_data
        )

        # 写文件
        output_file = os.path.join(
            self.output_dir,
            f"daily_report_{self.today.strftime('%Y-%m-%d')}.json",
        )
        self._save_json(output_file, report)
        return output_file

    def _build_gpm_section(self, data: dict) -> dict:
        gpm_7d = data.get("gpm_7d", [85] * 7)
        alerts = []
        if gpm_7d[-1] < self.THRESHOLDS["gpm_min"]:
            alerts.append(f"🟡低于{self.THRESHOLDS['gpm_min']}阈值")
        return {
            "overall": {
                "today": gpm_7d[-1],
                "trend_7d": gpm_7d,
                "alert": None if not alerts else alerts[0],
            },
            "by_country": {},
            "by_category": {},
        }

    def _build_recommendations(self, anomalies: dict, data: dict) -> list:
        recs = []
        for a in anomalies.get("critical", []):
            recs.append(f"🔴 【紧急】{a['detail']}")
        for a in anomalies.get("warnings", []):
            recs.append(f"🟡 【优先】{a['detail']}")
        for sku in data.get("skus_data", []):
            if sku.get("predicted_score", 0) >= 80:
                recs.append(
                    f"ℹ️ {sku['product_name']}预测分{sku['predicted_score']}，"
                    "建议上架后7天复盘校准模型"
                )
        return recs

    def _build_handoff(self, anomalies: dict, data: dict) -> list:
        handoff = []
        crit_tasks = [a["detail"] for a in anomalies.get("critical", [])]
        warn_tasks = [a["detail"] for a in anomalies.get("warnings", [])]
        skus = data.get("skus_data", [])

        if crit_tasks:
            handoff.append({"to": "🥔土豆", "message": f"⚠️ 紧急异常: {'; '.join(crit_tasks)}"})
            handoff.append({"to": "🥒苦瓜", "message": f"紧急: {crit_tasks[0]}"})
        if warn_tasks:
            handoff.append({"to": "🌽玉米", "message": "视频产出下降，请确认排期"})
        stock_warn = [w for w in anomalies.get("warnings", [])
                      if w["type"] == "stock_warning"]
        if stock_warn:
            handoff.append({"to": "🥕萝卜", "message": f"库存预警: {stock_warn[0]['detail']}"})
        if skus:
            low_score = [s for s in skus if s.get("predicted_score", 100) < 60]
            if low_score:
                handoff.append({
                    "to": "🍅番茄",
                    "message": f"低分选品: {low_score[0]['product_name']}({low_score[0].get('predicted_score', '?')}分)"
                })
        if not handoff:
            handoff.append({"to": "🥔土豆", "message": "今日无异常，一切正常"})
        return handoff

    def _load_json(self, path: str) -> Optional[dict]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def _save_json(self, path: str, data: dict):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 日报JSON: {path}")

    def generate_markdown_summary(self, report: dict) -> str:
        """从完整日报生成Markdown摘要，可直接贴飞书"""
        lines = []
        date_str = report["meta"]["date"]
        summary = report["summary"]
        health = summary["overall_health"]

        lines.append(f"# 📊 经营日报 · {date_str}")
        lines.append("")
        lines.append(f"## 📈 今日总览 {health}")
        lines.append(f"- **总GMV**: ${summary['total_gmv']:,.2f}  (vs昨日 {summary['gmv_vs_yesterday_pct']:+.1f}%)")
        lines.append(f"- **订单**: {summary['total_orders']} 单")
        lines.append(f"- **退款率**: {summary['refund_rate']:.2f}%")
        lines.append(f"- **净GMV**: ${summary['net_gmv']:,.2f}")
        lines.append("")

        # 5国横向
        lines.append("## 🌍 5国对比")
        lines.append("| 国家 | GMV | 订单 | 退款率 | GPM | ROAS | 健康 |")
        lines.append("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
        for c in report.get("by_country", []):
            lines.append(
                f"| {c['country']} | ${c['gmv']:,.0f} | {c['orders']} | "
                f"{c['refund_rate']:.1f}% | {c['gpm']:.1f} | {c['roas']:.1f} | {c['health']} |"
            )
        lines.append("")

        # 异常摘要
        anomalies = report.get("anomalies", {})
        crit = anomalies.get("critical", [])
        warns = anomalies.get("warnings", [])

        if crit:
            lines.append("## 🔴 紧急告警")
            for a in crit:
                lines.append(f"- {a['detail']}  (状态: {a.get('status','待处理')})")
            lines.append("")

        if warns:
            lines.append("## 🟡 待关注")
            for a in warns:
                lines.append(f"- {a['detail']}")
            lines.append("")

        # 推荐行动
        recs = report.get("recommendations", [])
        if recs:
            lines.append("## 📋 行动建议")
            for r in recs:
                lines.append(f"- {r}")
            lines.append("")

        # 交接清单
        handoff = report.get("daily_handoff", [])
        if handoff:
            lines.append("## 👥 交接清单")
            for h in handoff:
                lines.append(f"- **{h['to']}**: {h['message']}")
            lines.append("")

        lines.append("---")
        lines.append(f"*自动生成: {report['meta']['generated_at']} | v{report['meta']['version']}*")
        lines.append("")

        return "\n".join(lines)

    def generate_report_and_summary(self, app_id: str = "", table_id: str = "") -> tuple:
        """生成JSON日报+Markdown摘要，返回(JSON路径, MD路径)"""
        json_path = self.generate_report(app_id, table_id)

        with open(json_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        md_content = self.generate_markdown_summary(report)
        date_str = report["meta"]["date"]
        md_path = os.path.join(self.output_dir, f"daily_report_{date_str}.md")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"✅ 日报摘要: {md_path}")
        print()
        print("=" * 50)
        print("📋 飞书可直接粘贴的摘要:")
        print("=" * 50)
        print()
        print(md_content)

        return json_path, md_path


def parse_args():
    parser = argparse.ArgumentParser(description="自动日报生成器")
    parser.add_argument(
        "--mode", choices=["full", "summary"], default="full",
        help="生成模式: full完整日报, summary摘要"
    )
    parser.add_argument(
        "--output_dir", default="output",
        help="输出目录"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    generator = DailyReportGenerator(output_dir=args.output_dir)

    if args.mode == "summary":
        # 前日摘要模式 — 用昨天的日期生成前日报告
        yesterday = generator.today - timedelta(days=1)
        # 尝试加载已有JSON日报，如果没有就重新生成
        cached_json = os.path.join(
            generator.output_dir,
            f"daily_report_{yesterday.strftime('%Y-%m-%d')}.json"
        )
        if os.path.exists(cached_json):
            print(f"📂 使用已缓存的日报: {cached_json}")
            with open(cached_json, "r", encoding="utf-8") as f:
                report = json.load(f)
            md_content = generator.generate_markdown_summary(report)
            md_path = os.path.join(
                generator.output_dir,
                f"daily_report_{yesterday.strftime('%Y-%m-%d')}.md"
            )
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            print(f"✅ 摘要已写入: {md_path}")
            print()
            print(md_content)
        else:
            print("📦 缓存不存在，重新生成前日日报...")
            generator.generate_report_and_summary(
                app_id="",
                table_id="Mm7tbKj6na4EGws0QOAcgftnnQh"
            )
    else:
        # 完整日报模式
        json_path, md_path = generator.generate_report_and_summary(
            app_id="",
            table_id="Mm7tbKj6na4EGws0QOAcgftnnQh"
        )
        # 终端输出概要
        print(f"📊 日报生成完成")
        with open(json_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        print(f"  总GMV: ${report['summary']['total_gmv']:,.2f}")
        print(f"  健康状态: {report['summary']['overall_health']}")
        print(f"  异常数: 🔴{len(report['anomalies']['critical'])} 🟡{len(report['anomalies']['warnings'])}")
        print(f"  JSON: {json_path}")
        print(f"  MD:   {md_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
