# 🫘 日报模板实战化 — JSON格式自动填充模板

> **创建时间**：2026-05-11 05:55 GMT+8
> **作者**：🫘豌豆
> **目的**：将第一轮「总经理驾驶舱」做成可被cron调用的JSON日报模板

---

## 一、JSON日报模板（核心）

### 标准日报数据格式

```json
{
  "meta": {
    "report_type": "daily_summary",
    "date": "2026-05-11",
    "generated_at": "2026-05-11T22:00:00+08:00",
    "version": "1.0.0",
    "generated_by": "pea_agent",
    "schema": "daily_report_v1"
  },
  "summary": {
    "total_gmv": 12850.50,
    "gmv_currency": "USD",
    "total_orders": 423,
    "total_refunds": 21,
    "net_gmv": 11230.00,
    "refund_rate": 4.96,
    "gmv_vs_yesterday_pct": 12.3,
    "gmv_vs_last_week_pct": -5.1,
    "total_active_shops": 25,
    "shops_with_orders_today": 18,
    "overall_health": "🟡"
  },
  "by_country": [
    {
      "country": "TH",
      "gmv": 4850.00,
      "orders": 162,
      "refunds": 8,
      "refund_rate": 4.94,
      "gpm": 95.2,
      "roas": 3.8,
      "ad_spend": 1276.32,
      "shops_in_country": 7,
      "shops_with_orders": 5,
      "health": "🟢",
      "alerts": []
    },
    {
      "country": "MY",
      "gmv": 3200.00,
      "orders": 108,
      "refunds": 5,
      "refund_rate": 4.63,
      "gpm": 88.5,
      "roas": 3.2,
      "ad_spend": 1000.00,
      "shops_in_country": 6,
      "shops_with_orders": 4,
      "health": "🟢",
      "alerts": []
    },
    {
      "country": "VN",
      "gmv": 2100.00,
      "orders": 71,
      "refunds": 4,
      "refund_rate": 5.63,
      "gpm": 72.3,
      "roas": 2.5,
      "ad_spend": 840.00,
      "shops_in_country": 5,
      "shops_with_orders": 3,
      "health": "🟡",
      "alerts": [
        "VN-GPM-低于阈值：72.3 < 80，建议检查广告投放效率",
        "VN-ROAS-低于阈值：2.5 < 3.0，建议优化广告策略"
      ]
    },
    {
      "country": "PH",
      "gmv": 1850.50,
      "orders": 60,
      "refunds": 3,
      "refund_rate": 5.00,
      "gpm": 68.7,
      "roas": 2.8,
      "ad_spend": 660.89,
      "shops_in_country": 4,
      "shops_with_orders": 3,
      "health": "🟡",
      "alerts": [
        "PH-GPM-低于阈值：68.7 < 70，监控回复"
      ]
    },
    {
      "country": "SG",
      "gmv": 850.00,
      "orders": 22,
      "refunds": 1,
      "refund_rate": 4.55,
      "gpm": 110.3,
      "roas": 4.1,
      "ad_spend": 207.32,
      "shops_in_country": 3,
      "shops_with_orders": 3,
      "health": "🟢",
      "alerts": []
    }
  ],
  "selection_today": [
    {
      "sku_id": "SKU-MT-001",
      "product_name": "3D美妆蛋12只装",
      "category": "美妆工具",
      "source": "EchoTik-TH-20260511",
      "predicted_success_score": 82,
      "predicted_level": "🟢高概率",
      "predicted_7d_orders": 93,
      "status": "已提交上架",
      "selected_by": "🍅番茄",
      "target_countries": ["TH", "MY"],
      "target_price": 4.80,
      "retail_price": 26.40,
      "gross_margin_pct": 65.2,
      "supplier_candidates": ["S001-XX化妆刷厂", "A003-YY工具行"],
      "video_required": true,
      "video_assigned_to": "🌽玉米",
      "notes": ""
    },
    {
      "sku_id": "SKU-MT-002",
      "product_name": "便携睫毛夹套装",
      "category": "美妆工具",
      "source": "EchoTik-VN-20260511",
      "predicted_success_score": 71,
      "predicted_level": "🟢较大概率",
      "predicted_7d_orders": 43,
      "status": "待文案",
      "selected_by": "🍅番茄",
      "target_countries": ["VN", "PH"],
      "target_price": 2.50,
      "retail_price": 13.75,
      "gross_margin_pct": 68.0,
      "supplier_candidates": ["A003-YY工具行"],
      "video_required": true,
      "video_assigned_to": "暂无",
      "notes": "待玉米确认视频方案"
    },
    {
      "sku_id": "SKU-HO-001",
      "product_name": "多功能收纳盒",
      "category": "家居用品",
      "source": "EchoTik-MY-20260511",
      "predicted_success_score": 55,
      "predicted_level": "🟡中等概率",
      "predicted_7d_orders": 16,
      "status": "待评估",
      "selected_by": "🍅番茄",
      "target_countries": ["MY"],
      "target_price": 6.00,
      "retail_price": 33.00,
      "gross_margin_pct": 60.0,
      "supplier_candidates": ["B007-ZZ百货"],
      "video_required": false,
      "video_assigned_to": "无",
      "notes": "预测分55偏低，建议小规模测试"
    }
  ],
  "video_today": [
    {
      "sku_id": "SKU-MT-001",
      "product_name": "3D美妆蛋12只装",
      "video_count_today": 2,
      "total_video_count": 5,
      "total_views": 12500,
      "views_growth_pct": 15.3,
      "total_engagement": 843,
      "conversion_rate": 2.3,
      "top_video_url": "https://xxx",
      "video_creator": "🌽玉米",
      "production_status": "🟢进行中",
      "notes": ""
    },
    {
      "sku_id": "SKU-MT-003",
      "product_name": "粉扑清洁盒",
      "video_count_today": 0,
      "total_video_count": 3,
      "total_views": 8900,
      "views_growth_pct": -2.1,
      "total_engagement": 567,
      "conversion_rate": 1.8,
      "top_video_url": "",
      "video_creator": "🌽玉米",
      "production_status": "🟡暂停中",
      "notes": "视频效果不佳，待优化脚本"
    }
  ],
  "listing_today": [
    {
      "sku_id": "SKU-MT-001",
      "product_name": "3D美妆蛋12只装",
      "listing_time": "2026-05-11T16:00:00+08:00",
      "shops_listed": ["TH-shop1", "TH-shop2", "MY-shop1"],
      "total_listings": 3,
      "listing_by": "妙手上架",
      "status": "✅已上架"
    },
    {
      "sku_id": "SKU-MT-002",
      "product_name": "便携睫毛夹套装",
      "status": "⏳等待文案",
      "blocked_by": "🥬生菜",
      "eta": "2026-05-12"
    }
  ],
  "gpm_trends": {
    "overall": {
      "today": 85.4,
      "yesterday": 83.1,
      "last_week": 90.2,
      "trend_7d": [82.1, 85.3, 80.5, 87.0, 83.1, 83.1, 85.4],
      "trend_label": "近7日GPM",
      "alert": null
    },
    "by_country": {
      "TH": {
        "today": 95.2,
        "trend_7d": [90.1, 93.5, 91.2, 97.8, 94.0, 94.0, 95.2],
        "alert": null
      },
      "MY": {
        "today": 88.5,
        "trend_7d": [85.3, 87.2, 84.1, 91.3, 86.7, 86.7, 88.5],
        "alert": null
      },
      "VN": {
        "today": 72.3,
        "trend_7d": [78.0, 76.5, 73.2, 75.8, 71.0, 72.0, 72.3],
        "alert": "🟡连续3日低于80阈值，持续下滑趋势"
      },
      "PH": {
        "today": 68.7,
        "trend_7d": [70.2, 69.8, 65.5, 71.0, 67.5, 67.5, 68.7],
        "alert": "🟡偶尔低于70阈值，波动大"
      },
      "SG": {
        "today": 110.3,
        "trend_7d": [105.0, 108.2, 112.5, 115.0, 109.8, 109.8, 110.3],
        "alert": null
      }
    },
    "by_category": {
      "美妆工具": {
        "gpm_7d_avg": 92.5,
        "gpm_today": 95.0,
        "trend": "↗上升",
        "alert": null
      },
      "家居用品": {
        "gpm_7d_avg": 72.0,
        "gpm_today": 68.3,
        "trend": "↘下降",
        "alert": "🟡连续5天下降，建议检查选品方向"
      },
      "个护洗护": {
        "gpm_7d_avg": 85.0,
        "gpm_today": 86.1,
        "trend": "→平稳",
        "alert": null
      }
    }
  },
  "anomalies": {
    "critical": [
      {
        "id": "ANOM-001",
        "severity": "🔴",
        "type": "refund_rate_spike",
        "country": "VN",
        "detail": "VN某店铺退款率突然升至15%（昨日为5%），疑似到货质量问题",
        "product": "SKU-MT-003·粉扑清洁盒",
        "timestamp": "2026-05-11T14:30:00+08:00",
        "status": "待处理",
        "assigned_to": "🥒苦瓜",
        "action_required": "立即联系供应商确认产品批次，暂停该SKU继续投放"
      }
    ],
    "warnings": [
      {
        "id": "ANOM-002",
        "severity": "🟡",
        "type": "gpm_decline",
        "country": "VN",
        "detail": "越南市场GPM连续3天低于80阈值",
        "timestamp": "2026-05-11T18:00:00+08:00",
        "status": "监控中",
        "action_required": "越南团队检查广告受众定向与出价策略"
      },
      {
        "id": "ANOM-003",
        "severity": "🟡",
        "type": "stock_warning",
        "country": "TH",
        "detail": "SKU-MT-001(美妆蛋)库存仅剩120单，日均消耗60，预计2天断货",
        "product": "SKU-MT-001",
        "timestamp": "2026-05-11T16:00:00+08:00",
        "status": "待处理",
        "assigned_to": "🥕萝卜",
        "action_required": "立即联系供应商S001补货，同时检查备选供应商A003有无现货"
      },
      {
        "id": "ANOM-004",
        "severity": "🟡",
        "type": "video_slowing",
        "detail": "🌽玉米本周视频产出较上周下降30%，需确认是否遇到创作瓶颈",
        "timestamp": "2026-05-11T18:00:00+08:00",
        "status": "待确认",
        "assigned_to": "🥔土豆",
        "action_required": "与玉米沟通视频排期情况"
      }
    ],
    "info": [
      {
        "id": "ANOM-005",
        "severity": "ℹ️",
        "type": "milestone",
        "detail": "马来西亚市场累计GMV突破$50,000！",
        "timestamp": "2026-05-11T20:00:00+08:00",
        "status": "已记录"
      }
    ]
  },
  "recommendations": [
    "🔴 【紧急】SKU-MT-003粉扑清洁盒在VN出现15%退款率，立即暂停该SKU投放",
    "🟡 【优先】越南GPM连续3日下行，建议今日内优化VN广告出价结构",
    "🟡 【优先】SKU-MT-001美妆蛋库存告急，今日内完成补货",
    "ℹ️ 3D美妆蛋预测82分，今日上架3店，7天后复盘出单数据以校准模型",
    "ℹ️ 马来西亚累计破$50K，建议安排马来团队复盘增长原因"
  ],
  "daily_handoff": [
    {"to": "🥔土豆", "message": "日报已生成，异常项已标记，建议review告警列表"},
    {"to": "🍅番茄", "message": "今日选品3款待评估，家居收纳盒预测55分建议慎入"},
    {"to": "🌽玉米", "message": "粉扑清洁盒视频效果待优化，睫毛夹套装视频待确认方案"},
    {"to": "🥬生菜", "message": "睫毛夹套装文案待产出"},
    {"to": "🥕萝卜", "message": "美妆蛋补货紧急处理"},
    {"to": "🥒苦瓜", "message": "越南退款异常+供应商纠纷率监控"}
  ]
}
```

---

## 二、JSON模板各字段说明

### 顶层字段说明

| 字段 | 类型 | 必填 | 说明 |
|:-----|:----:|:----:|:-----|
| meta | object | ✅ | 报告元信息 |
| summary | object | ✅ | 全局汇总 |
| by_country | array | ✅ | 5国数据 |
| selection_today | array | ✅ | 今日选品动态 |
| video_today | array | ✅ | 今日视频产出 |
| listing_today | array | ✅ | 今日上架动态 |
| gpm_trends | object | ✅ | GPM趋势数据 |
| anomalies | object | ✅ | 异常/预警汇总 |
| recommendations | array | ✅ | 今日行动建议 |
| daily_handoff | array | ✅ | 各角色任务交接 |

### 异常等级制度 anomalies.severity

| 等级 | 颜色 | 含义 | 行动时限 |
|:----:|:----:|:-----|:--------:|
| critical | 🔴 | 需立即处理 | 立即(1h内) |
| warning | 🟡 | 需关注和跟踪 | 24h内review |
| info | ℹ️ | 记录性信息 | 无 |

### 健康标记 health

| 值 | 含义 | 判定条件 |
|:--:|:-----|:---------|
| 🟢 | 正常 | 所有指标在安全区 |
| 🟡 | 提醒 | 1-2个指标进黄区 |
| 🔴 | 告警 | ≥3个指标黄区/1个进红区 |

---

## 三、数据采集脚本（cron可调用）

### Python自动日报生成器

```python
#!/usr/bin/env python3
"""
daily_report_generator.py — 自动日报生成器
cron: 0 22 * * * /usr/bin/python3 /path/to/daily_report_generator.py

依赖：飞书多维表格API (python-feishu-bitable)
      本地数据缓存 (pickle/json)
输出：/output/daily_report_YYYY-MM-DD.json
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class DailyReportGenerator:
    """
    自动日报生成器——从飞书多维表格抓取数据→处理→输出JSON
    """
    
    # 阈值配置（可在config.yaml中外部化）
    THRESHOLDS = {
        "gpm_min": 80,          # GPM最低安全线
        "gpm_amber": 50,        # GPM黄区线
        "roas_min": 3.0,        # ROAS最低安全线
        "roas_amber": 1.5,      # ROAS黄区线
        "refund_rate_max": 5,   # 最高安全退款率(%)
        "refund_rate_amber": 10,# 退款率黄区线(%)
        "aov_min": 8,           # AOV最低线($)
        "aov_amber": 5,        # AOV黄区线($)
        "listing_rate_min": 30  # 出单率最低线(%)
    }
    
    def __init__(self, output_dir: str = "/output"):
        self.output_dir = output_dir
        self.today = datetime.now()
        self.yesterday = self.today - timedelta(days=1)
        self.last_week = self.today - timedelta(days=7)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def fetch_from_bitable(self, table_id: str):
        """
        从飞书多维表格拉取今日数据
        
        接入点示例（飞书API）：
        bitable.apps.feishu.cn/open-apis/bitable/v1/apps/{app}/tables/{table}/records
        
        需要抓取的5张表：
        1. 经营概况 — GMV/订单/退款/成本数据
        2. 商品分析 — SKU级数据
        3. 达人合作 — 视频数据
        4. 5国对比 — 各国横向数据
        5. 风控监控 — 异常数据
        """
        # TODO: 接入飞书API后实现
        # 当前返回模拟数据用于模板测试
        return self._mock_data()
    
    def _mock_data(self) -> dict:
        """生成模拟数据用于测试JSON结构"""
        # 实际生产环境中移除
        return {
            "total_gmv": 12850.50,
            "total_orders": 423,
            "total_refunds": 21,
            "countries_data": self._mock_country_data(),
            "skus_data": self._mock_sku_data(),
            "gpm_7d": self._mock_gpm_7d()
        }
    
    def analyze_health(self, data: dict) -> str:
        """分析整体健康度"""
        warnings = 0
        red_flags = 0
        
        for country in data.get("countries_data", []):
            if country["gpm"] < self.THRESHOLDS["gpm_min"]:
                warnings += 1
            if country["gpm"] < self.THRESHOLDS["gpm_amber"]:
                red_flags += 1
            if country["roas"] < self.THRESHOLDS["roas_min"]:
                warnings += 1
            if country["refund_rate"] > self.THRESHOLDS["refund_rate_max"]:
                warnings += 1
        
        if red_flags >= 1 or warnings >= 3:
            return "🔴"
        elif warnings >= 1:
            return "🟡"
        return "🟢"
    
    def detect_anomalies(self, today_data: dict, yesterday_data: dict) -> dict:
        """异常检测引擎"""
        anomalies = {
            "critical": [],
            "warnings": [],
            "info": []
        }
        
        # 1. 退款率突增检测
        for country in today_data["countries_data"]:
            y_country = next(
                (c for c in yesterday_data["countries_data"] 
                 if c["country"] == country["country"]), 
                None
            )
            if y_country:
                delta = country["refund_rate"] - y_country["refund_rate"]
                if delta > 10:  # 退款率突增超过10%
                    anomalies["critical"].append({
                        "type": "refund_rate_spike",
                        "country": country["country"],
                        "detail": f"退款率突增{delta:.1f}% ({y_country['refund_rate']:.1f}→{country['refund_rate']:.1f}%)",
                        "urgency": "🔴"
                    })
                elif delta > 5:
                    anomalies["warnings"].append({
                        "type": "refund_rate_rise",
                        "country": country["country"],
                        "detail": f"退款率上升{delta:.1f}%",
                        "urgency": "🟡"
                    })
        
        # 2. GPM持续下滑检测
        for country in today_data["countries_data"]:
            if country.get("gpm_7d_trend"):
                # 检查近3天是否持续下降
                trend = country["gpm_7d_trend"][-3:]
                if len(trend) >= 3 and trend[0] > trend[1] > trend[2]:
                    anomalies["warnings"].append({
                        "type": "gpm_continuous_decline",
                        "country": country["country"],
                        "detail": f"GPM连续3日下降({trend[0]:.1f}→{trend[1]:.1f}→{trend[2]:.1f})",
                        "urgency": "🟡"
                    })
        
        # 3. 库存预警
        for sku in today_data.get("skus_data", []):
            daily_sales = sku.get("daily_avg_sales", 0)
            current_stock = sku.get("current_stock", 0)
            if daily_sales > 0 and current_stock / daily_sales < 3:
                anomalies["warnings"].append({
                    "type": "stock_warning",
                    "sku_id": sku["sku_id"],
                    "detail": f"{sku['product_name']}库存{current_stock}仅够{current_stock/daily_sales:.1f}天",
                    "urgency": "🟡"
                })
        
        # 4. 视频产出下降
        today_videos = sum(v.get("video_count_today", 0) for v in today_data.get("videos_data", []))
        yesterday_videos = sum(v.get("video_count_today", 0) for v in yesterday_data.get("videos_data", []))
        if yesterday_videos > 0 and today_videos < yesterday_videos * 0.7:
            anomalies["warnings"].append({
                "type": "video_production_drop",
                "detail": f"视频产出较昨日下降{(1-today_videos/yesterday_videos)*100:.0f}%",
                "urgency": "🟡"
            })
        
        return anomalies
    
    def generate_daily_report(self, app_id: str = "", table_id: str = "") -> str:
        """生成完整日报JSON"""
        
        today_data = self.fetch_from_bitable(table_id)
        
        # 从缓存取昨日数据
        yesterday_file = os.path.join(
            self.output_dir, 
            f"daily_report_{self.yesterday.strftime('%Y-%m-%d')}.json"
        )
        yesterday_data = self._load_json(yesterday_file) or today_data
        
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
                "refund_rate": round(today_data["total_refunds"] / today_data["total_orders"] * 100, 2) if today_data["total_orders"] > 0 else 0,
                "gmv_vs_yesterday_pct": self._calc_pct_change(
                    today_data["total_gmv"], 
                    yesterday_data.get("total_gmv", today_data["total_gmv"])
                ),
                "overall_health": self.analyze_health(today_data)
            },
            "by_country": self._build_country_section(today_data),
            "selection_today": [],
            "video_today": [],
            "listing_today": [],
            "gpm_trends": self._build_gpm_section(today_data),
            "anomalies": self.detect_anomalies(today_data, yesterday_data),
            "recommendations": [],
            "daily_handoff": []
        }
        
        # 写入文件
        output_file = os.path.join(
            self.output_dir, 
            f"daily_report_{self.today.strftime('%Y-%m-%d')}.json"
        )
        self._save_json(output_file, report)
        
        return output_file
    
    def _build_country_section(self, data: dict) -> List[dict]:
        """按国家拆分数据"""
        # TODO: 调用飞书API获取真实数据
        return [
            {"country": "TH", "gmv": 4850, "orders": 162, "refunds": 8, "refund_rate": 4.94},
            {"country": "MY", "gmv": 3200, "orders": 108, "refunds": 5, "refund_rate": 4.63},
            {"country": "VN", "gmv": 2100, "orders": 71, "refunds": 4, "refund_rate": 5.63},
            {"country": "PH", "gmv": 1850, "orders": 60, "refunds": 3, "refund_rate": 5.00},
            {"country": "SG", "gmv": 850, "orders": 22, "refunds": 1, "refund_rate": 4.55}
        ]
    
    def _build_gpm_section(self, data: dict) -> dict:
        """构建GPM趋势"""
        gpm_7d = data.get("gpm_7d", [82.1, 85.3, 80.5, 87.0, 83.1, 83.1, 85.4])
        return {
            "overall": {
                "today": gpm_7d[-1],
                "trend_7d": gpm_7d,
                "alert": None
            },
            "by_country": {
                "TH": {"today": 95.2, "trend_7d": [90.1, 93.5, 91.2, 97.8, 94.0, 94.0, 95.2], "alert": None},
                "VN": {"today": 72.3, "trend_7d": [78.0, 76.5, 73.2, 75.8, 71.0, 72.0, 72.3], "alert": "🟡连续3日低于80阈值"}
            },
            "by_category": {
                "美妆工具": {"gpm_7d_avg": 92.5, "gpm_today": 95.0, "trend": "↗上升", "alert": None},
                "家居用品": {"gpm_7d_avg": 72.0, "gpm_today": 68.3, "trend": "↘下降", "alert": "🟡连续5天下降"}
            }
        }
    
    def _calc_pct_change(self, current: float, previous: float) -> float:
        """计算变化百分比"""
        if previous == 0:
            return 0
        return round((current - previous) / previous * 100, 1)
    
    def _load_json(self, path: str) -> Optional[dict]:
        """加载JSON文件"""
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def _save_json(self, path: str, data: dict):
        """保存JSON至文件"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 日报已写入: {path}")


# ========== cron入口 ==========
if __name__ == "__main__":
    generator = DailyReportGenerator(
        output_dir="/Users/a1234/.openclaw/workspace/agents/pea-agent/output"
    )
    output_path = generator.generate_daily_report(
        app_id="",
        table_id="Mm7tbKj6na4EGws0QOAcgftnnQh"
    )
    print(f"📊 日报生成完成: {output_path}")
```

### cron 配置
```bash
# 每天22:00(北京时间)自动生成日报
0 14 * * * cd /Users/a1234/.openclaw/workspace && /usr/bin/python3 output/daily_report_generator.py 2>> /var/log/daily_report_cron.log

# 每天08:00生成前日日报摘要（方便早会）
0 0 * * * cd /Users/a1234/.openclaw/workspace && /usr/bin/python3 output/daily_report_generator.py --mode=summary 2>> /var/log/daily_report_summary_cron.log
```

### Hermes 集成调用
```python
# 通过Hermes调用（遵循融合工作流）
from hermes_engine import HermesEngine

engine = HermesEngine()
engine.run_workflow("daily_report", {
    "output_dir": "/output",
    "table_id": "Mm7tbKj6na4EGws0QOAcgftnnQh"
})
```

---

## 四、飞书卡片视图（自动渲染用）

日报JSON产出后，可渲染为飞书消息卡片：

### 机器人推送卡片模板

```json
{
  "config": {"wide_screen_mode": true},
  "header": {
    "title": {"tag": "plain_text", "content": "📊 总经理日报 | 2026-05-11"},
    "template": "blue"
  },
  "elements": [
    {
      "tag": "div",
      "fields": [
        {"is_short": true, "text": {"tag": "lark_md", "content": "**总GMV**\n$12,850.50"}},
        {"is_short": true, "text": {"tag": "lark_md", "content": "**📈 vs昨日**\n+12.3%"}}
      ]
    },
    {
      "tag": "div",
      "fields": [
        {"is_short": true, "text": {"tag": "lark_md", "content": "**订单**\n423单"}},
        {"is_short": true, "text": {"tag": "lark_md", "content": "**退款率**\n4.96% 🟢"}}
      ]
    },
    {"tag": "hr"},
    {
      "tag": "div",
      "text": {"tag": "lark_md", "content": "**🌍 5国对比**"}
    },
    {
      "tag": "table", 
      "rows": [
        [{"tag": "text", "text": "TH"}, {"tag": "text", "text": "$4,850"}, {"tag": "text", "text": "3.8"}, {"tag": "text", "text": "🟢"}],
        [{"tag": "text", "text": "MY"}, {"tag": "text", "text": "$3,200"}, {"tag": "text", "text": "3.2"}, {"tag": "text", "text": "🟢"}],
        [{"tag": "text", "text": "VN"}, {"tag": "text", "text": "$2,100"}, {"tag": "text", "text": "2.5"}, {"tag": "text", "text": "🟡"}],
        [{"tag": "text", "text": "PH"}, {"tag": "text", "text": "$1,850"}, {"tag": "text", "text": "2.8"}, {"tag": "text", "text": "🟡"}],
        [{"tag": "text", "text": "SG"}, {"tag": "text", "text": "$850"}, {"tag": "text", "text": "4.1"}, {"tag": "text", "text": "🟢"}]
      ],
      "header": ["国家", "GMV", "ROAS", "健康"]
    },
    {"tag": "hr"},
    {
      "tag": "div",
      "text": {"tag": "lark_md", "content": "**🔴 紧急告警**\n1️⃣ SKU-MT-003 越南退款率15%，立即暂停投放\n2️⃣ SKU-MT-001 美妆蛋库存仅够2天，紧急补货"}
    },
    {
      "tag": "div",
      "text": {"tag": "lark_md", "content": "**🟡 待关注**\n• 越南GPM连续3天<80\n• 玉米视频产出下降30%\n• 家居收纳盒预测分55"}
    }
  ]
}
