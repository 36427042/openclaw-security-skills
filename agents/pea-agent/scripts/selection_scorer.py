#!/usr/bin/env python3
"""
selection_scorer.py — 选品评分卡计算器 (v1.0)
从5维度输入计算选品成功率及建议

使用：
  python3 selection_scorer.py                    # 交互式输入
  python3 selection_scorer.py --batch batch.csv   # 批量评分

Hermes集成：
  from selection_scorer import SelectionScorer
  scorer = SelectionScorer()
  result = scorer.score(gpm=95.2, gpm_growth_pct=12.5, ...)
"""

import sys
import json
import argparse
from typing import Optional


class SelectionScorer:
    """
    选品成功率预测模型
    
    5维度加权评分：
    - 市场热度 (25%) — GPM绝对值+趋势
    - 竞争生态 (20%) — 同类数+集中度
    - 品类基础 (15%) — 历史出单率+退款率
    - 利润空间 (20%) — 毛利率+单件利润
    - 内容适配 (20%) — 视频效果+达人合作
    """

    # ==================== 默认权重（可外部加载） ====================
    WEIGHTS = {
        "market_heat": 0.25,
        "competition": 0.20,
        "category_base": 0.15,
        "profit_margin": 0.20,
        "content_fit": 0.20,
    }

    # ==================== 评分阈值 ====================
    THRESHOLDS = {
        "gpm_green": 120,
        "gpm_yellow": 80,
        "gpm_red": 50,
        "competitor_green": 50,
        "competitor_yellow": 200,
        "competitor_red": 500,
        "margin_green": 60,
        "margin_yellow": 45,
        "margin_red": 30,
        "refund_green": 3,
        "refund_yellow": 5,
        "refund_red": 10,
    }

    def __init__(self, weights: Optional[dict] = None):
        if weights:
            self.WEIGHTS.update(weights)

    # ==================== 各维度评分 ====================

    def score_market_heat(self, gpm: float, gpm_growth_pct: float) -> float:
        """市场热度 (25分)"""
        # GPM得分 (0-15分)
        if gpm >= self.THRESHOLDS["gpm_green"]:
            gpm_score = 15
        elif gpm >= self.THRESHOLDS["gpm_yellow"]:
            gpm_score = 12
        elif gpm >= self.THRESHOLDS["gpm_red"]:
            gpm_score = 8
        else:
            gpm_score = 4

        # GPM涨幅得分 (0-10分)
        if gpm_growth_pct > 20:
            growth_score = 10
        elif gpm_growth_pct > 10:
            growth_score = 8
        elif gpm_growth_pct > 0:
            growth_score = 6
        elif gpm_growth_pct > -10:
            growth_score = 4
        else:
            growth_score = 2

        return gpm_score + growth_score

    def score_competition(
        self, competitor_count: int, top10_gmv_share: float
    ) -> float:
        """竞争生态 (20分)"""
        # 同类竞争 (0-12分)
        if competitor_count < self.THRESHOLDS["competitor_green"]:
            comp_score = 12
        elif competitor_count < self.THRESHOLDS["competitor_yellow"]:
            comp_score = 9
        elif competitor_count < self.THRESHOLDS["competitor_red"]:
            comp_score = 6
        else:
            comp_score = 3

        # TOP10垄断度 (0-8分)
        if top10_gmv_share < 30:
            mono_score = 8
        elif top10_gmv_share < 50:
            mono_score = 6
        elif top10_gmv_share < 70:
            mono_score = 4
        else:
            mono_score = 2

        return comp_score + mono_score

    def score_category_base(
        self, historical_success_rate: float = 0.5,
        refund_rate: float = 4.0
    ) -> float:
        """品类基础 (15分)"""
        # 历史出单率 (0-9分)
        if historical_success_rate >= 0.7:
            hist_score = 9
        elif historical_success_rate >= 0.4:
            hist_score = 7
        elif historical_success_rate >= 0.2:
            hist_score = 5
        else:
            hist_score = 3

        # 退款率 (0-6分)
        if refund_rate < self.THRESHOLDS["refund_green"]:
            refund_score = 6
        elif refund_rate < self.THRESHOLDS["refund_yellow"]:
            refund_score = 5
        elif refund_rate < self.THRESHOLDS["refund_red"]:
            refund_score = 3
        else:
            refund_score = 1

        return hist_score + refund_score

    def score_profit_margin(
        self, gross_margin_pct: float, unit_profit_usd: float
    ) -> float:
        """利润空间 (20分)"""
        # 毛利率 (0-12分)
        if gross_margin_pct >= self.THRESHOLDS["margin_green"]:
            margin_score = 12
        elif gross_margin_pct >= self.THRESHOLDS["margin_yellow"]:
            margin_score = 9
        elif gross_margin_pct >= self.THRESHOLDS["margin_red"]:
            margin_score = 6
        else:
            margin_score = 3

        # 单件利润 (0-8分)
        if unit_profit_usd >= 8:
            profit_score = 8
        elif unit_profit_usd >= 5:
            profit_score = 6
        elif unit_profit_usd >= 3:
            profit_score = 4
        else:
            profit_score = 2

        return margin_score + profit_score

    def score_content_fit(
        self, video_effectiveness: str = "中等",
        has_viral_precedent: bool = False,
        creator_willingness: str = "中"
    ) -> float:
        """内容适配度 (20分)"""
        # 视频效果 (0-10分)
        effect_map = {"高": 10, "中等": 7, "低": 4}
        effect_score = effect_map.get(video_effectiveness, 5)

        # 爆款先例 (0-5分)
        precedent_score = 5 if has_viral_precedent else 2

        # 达人合作意愿 (0-5分)
        will_map = {"高": 5, "中": 3, "低": 1}
        willing_score = will_map.get(creator_willingness, 2)

        return effect_score + precedent_score + willing_score

    # ==================== 总分计算 ====================

    def predict_7d_orders(
        self, total_score: float, sku_count: int = 10,
        ad_intensity: str = "普通"
    ) -> int:
        """预测7天出单量"""
        intensity_map = {"不投": 0.5, "普通": 1.0, "重点": 1.5, "大推": 2.0}
        coef = intensity_map.get(ad_intensity, 1.0)
        return int(total_score * sku_count * 0.12 * coef)

    def get_grade(self, total_score: float) -> tuple:
        """返回 (等级, 等级名, 建议)"""
        if total_score >= 85:
            return ("🟢", "高概率成功", "直接上架，批量+广告推")
        elif total_score >= 70:
            return ("🟢", "较大概率", "正常上架，7天观察后决策")
        elif total_score >= 55:
            return ("🟡", "中等概率", "小规模测试，3天快速验证")
        elif total_score >= 40:
            return ("🟡", "低概率", "仅作补品/平替，注意止损")
        else:
            return ("🔴", "极小概率", "跳过，换选其他")

    def score(self, **kwargs) -> dict:
        """
        完整评分入口
        
        参数：
            gpm: float — GPM值
            gpm_growth_pct: float — GPM 7日涨幅(%)
            competitor_count: int — 同类产品数
            top10_gmv_share: float — TOP10占GMV比(%)
            historical_success_rate: float — 历史出单率(0-1)
            refund_rate: float — 品类退款率(%)
            gross_margin_pct: float — 毛利率(%)
            unit_profit_usd: float — 单件利润($)
            video_effectiveness: str — 视频效果(高/中等/低)
            has_viral_precedent: bool — 是否有爆款先例
            creator_willingness: str — 达人合作意愿(高/中/低)
            sku_count: int — 上架SKU数(默认10)
            ad_intensity: str — 投放强度(不投/普通/重点/大推)
            product_name: str — 产品名(可选)
            category: str — 品类(可选)
            target_countries: list — 目标国家(可选)
        
        返回：
            dict — 完整评分结果
        """
        gpm = kwargs.get("gpm", 80)
        gpm_growth = kwargs.get("gpm_growth_pct", 0)
        competitor_count = kwargs.get("competitor_count", 200)
        top10_share = kwargs.get("top10_gmv_share", 50)
        hist_rate = kwargs.get("historical_success_rate", 0.5)
        refund = kwargs.get("refund_rate", 4.0)
        margin = kwargs.get("gross_margin_pct", 50)
        profit = kwargs.get("unit_profit_usd", 5)
        video_eff = kwargs.get("video_effectiveness", "中等")
        viral = kwargs.get("has_viral_precedent", False)
        creator = kwargs.get("creator_willingness", "中")
        sku_count = kwargs.get("sku_count", 10)
        ad_intensity = kwargs.get("ad_intensity", "普通")

        # 各维度分
        raw_scores = {
            "market_heat": self.score_market_heat(gpm, gpm_growth),
            "competition": self.score_competition(competitor_count, top10_share),
            "category_base": self.score_category_base(hist_rate, refund),
            "profit_margin": self.score_profit_margin(margin, profit),
            "content_fit": self.score_content_fit(video_eff, viral, creator),
        }

        # 各维度满分
        dim_maxes = {
            "market_heat": 25,
            "competition": 20,
            "category_base": 15,
            "profit_margin": 20,
            "content_fit": 20,
        }
        # 归一化到0-100再加权
        total_score = sum(
            (raw_scores[d] / dim_maxes[d] * 100) * self.WEIGHTS[d]
            for d in self.WEIGHTS
        )
        total_score = round(total_score, 1)

        # 等级
        grade_icon, grade_name, suggestion = self.get_grade(total_score)

        # 预测出单
        predicted_orders = self.predict_7d_orders(
            total_score, sku_count, ad_intensity
        )

        result = {
            "total_score": total_score,
            "grade": {
                "icon": grade_icon,
                "name": grade_name,
                "suggestion": suggestion,
            },
            "raw_scores": {
                "market_heat": f"{raw_scores['market_heat']:.0f}/25 ({raw_scores['market_heat']/25*100:.0f}分归一)",
                "competition": f"{raw_scores['competition']:.0f}/20 ({raw_scores['competition']/20*100:.0f}分归一)",
                "category_base": f"{raw_scores['category_base']:.0f}/15 ({raw_scores['category_base']/15*100:.0f}分归一)",
                "profit_margin": f"{raw_scores['profit_margin']:.0f}/20 ({raw_scores['profit_margin']/20*100:.0f}分归一)",
                "content_fit": f"{raw_scores['content_fit']:.0f}/20 ({raw_scores['content_fit']/20*100:.0f}分归一)",
            },
            "predicted_7d_orders": predicted_orders,
            "input_summary": {
                "gpm": gpm,
                "gpm_growth_pct": gpm_growth,
                "competitor_count": competitor_count,
                "gross_margin_pct": margin,
                "ad_intensity": ad_intensity,
            },
            "product_name": kwargs.get("product_name", ""),
            "category": kwargs.get("category", ""),
            "target_countries": kwargs.get("target_countries", []),
        }

        return result

    def pretty_print(self, result: dict):
        """美观打印评分结果"""
        p = result["product_name"] or "未命名选品"
        cat = result["category"] or "未分类"
        grade = result["grade"]
        countries = ", ".join(result["target_countries"]) or "未指定"

        print(f"\n{'='*50}")
        print(f"  🍅 选品评分卡 · {p}")
        print(f"  品类: {cat} | 国家: {countries}")
        print(f"{'='*50}")
        print(f"  {grade['icon']} 总分: {result['total_score']}/100")
        print(f"  等级: {grade['name']}")
        print(f"  建议: {grade['suggestion']}")
        print(f"  预计7天出单: {result['predicted_7d_orders']} 单")
        print()
        print(f"  📊 各维度:")
        for dim, score_str in result["raw_scores"].items():
            dim_label = {
                "market_heat": "市场热度",
                "competition": "竞争生态",
                "category_base": "品类基础",
                "profit_margin": "利润空间",
                "content_fit": "内容适配",
            }.get(dim, dim)
            weight = self.WEIGHTS.get(dim, 0) * 100
            print(f"    {dim_label} ({weight:.0f}%): {score_str}")
        print(f"{'='*50}\n")


def interactive_mode():
    """交互式评分"""
    scorer = SelectionScorer()
    print("🍅 选品评分卡 · 交互模式")
    print("直接回车使用默认值，持续到输入q退出\n")

    while True:
        print("\n--- 新选品 ---")
        name = input("产品名: ").strip()
        if name.lower() == "q":
            break

        try:
            gpm = float(input("GPM值 [80]: ") or "80")
            growth = float(input("GPM 7日涨幅(%) [0]: ") or "0")
            comp_count = int(input("同类产品数 [200]: ") or "200")
            top10 = float(input("TOP10占GMV比(%) [50]: ") or "50")
            margin = float(input("毛利率(%) [50]: ") or "50")
            profit = float(input("单件利润($) [5]: ") or "5")
            refund = float(input("退款率(%) [4]: ") or "4")
            video = input("视频效果(高/中等/低) [中等]: ") or "中等"
            viral = input("有爆款先例?(y/N): ").lower() == "y"
            creator = input("达人合作意愿(高/中/低) [中]: ") or "中"
            skus = int(input("上架SKU数 [10]: ") or "10")
            ad = input("投放强度(不投/普通/重点/大推) [普通]: ") or "普通"
            cat = input("品类: ") or ""
            countries = input("目标国家(逗号分隔): ") or ""

            result = scorer.score(
                product_name=name,
                category=cat,
                gpm=gpm,
                gpm_growth_pct=growth,
                competitor_count=comp_count,
                top10_gmv_share=top10,
                gross_margin_pct=margin,
                unit_profit_usd=profit,
                refund_rate=refund,
                video_effectiveness=video,
                has_viral_precedent=viral,
                creator_willingness=creator,
                sku_count=skus,
                ad_intensity=ad,
                target_countries=[c.strip() for c in countries.split(",") if c.strip()],
            )
            scorer.pretty_print(result)
        except ValueError as e:
            print(f"❌ 输入错误: {e}")


def batch_mode(csv_path: str):
    """批量评分CSV"""
    import csv
    scorer = SelectionScorer()

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        results = []
        for row in reader:
            try:
                result = scorer.score(
                    product_name=row.get("product_name", ""),
                    category=row.get("category", ""),
                    gpm=float(row.get("gpm", 80)),
                    gpm_growth_pct=float(row.get("gpm_growth_pct", 0)),
                    competitor_count=int(row.get("competitor_count", 200)),
                    top10_gmv_share=float(row.get("top10_gmv_share", 50)),
                    gross_margin_pct=float(row.get("gross_margin_pct", 50)),
                    unit_profit_usd=float(row.get("unit_profit_usd", 5)),
                    refund_rate=float(row.get("refund_rate", 4)),
                    video_effectiveness=row.get("video_effectiveness", "中等"),
                    has_viral_precedent=row.get("has_viral_precedent", "False").lower() == "true",
                    creator_willingness=row.get("creator_willingness", "中"),
                    sku_count=int(row.get("sku_count", 10)),
                    ad_intensity=row.get("ad_intensity", "普通"),
                    target_countries=row.get("target_countries", "").split(",") if row.get("target_countries") else [],
                )
                results.append(result)
                scorer.pretty_print(result)
            except (ValueError, KeyError) as e:
                print(f"❌ 行错误: {row.get('product_name','?')} → {e}")

        # 输出JSON摘要
        summary_path = csv_path.replace(".csv", "_scored.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"✅ 批量评分完成，结果保存至: {summary_path}")


def main():
    parser = argparse.ArgumentParser(description="选品评分卡计算器")
    parser.add_argument("--batch", type=str, help="批量评分CSV文件路径")
    parser.add_argument("--json", type=str, help="从JSON文件读输入")
    parser.add_argument("--output", type=str, default="", help="输出JSON路径（可选）")
    args = parser.parse_args()

    if args.batch:
        batch_mode(args.batch)
    elif args.json:
        with open(args.json, "r", encoding="utf-8") as f:
            input_data = json.load(f)
        scorer = SelectionScorer()
        result = scorer.score(**input_data)
        scorer.pretty_print(result)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"✅ 结果已保存至: {args.output}")
    else:
        interactive_mode()

    return 0


if __name__ == "__main__":
    sys.exit(main())
