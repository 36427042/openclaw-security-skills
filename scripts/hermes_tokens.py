#!/usr/bin/env python3
"""
hermes_tokens.py — Token消耗追踪 + 成本看板
从 Claude Code cost-tracker.ts + /cost 命令借鉴

追踪每次API调用的token消耗，汇总到成本看板

用法:
    from hermes_tokens import tracker

    # 记录一次API调用
    tracker.record(model="deepseek-v4-flash", prompt_tokens=150, completion_tokens=50)

    # 查看统计
    stats = tracker.stats()
    print(f"今日消耗: {stats['today_cost']}")
"""

import json
import logging
import os
import threading
from datetime import datetime, date, timezone
from typing import Dict, List, Optional

logger = logging.getLogger("hermes_tokens")

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/data/tokens")
os.makedirs(DATA_DIR, exist_ok=True)

JSONL_PATH = os.path.join(DATA_DIR, "usage.jsonl")

# 模型价格（每千token, 人民币）
# 来源: DeepSeek 官方定价 / 通义千问 Coding Plan 套餐价
MODEL_PRICES = {
    # DeepSeek (按量计费)
    "deepseek-v4-flash":  {"input": 0.001,  "output": 0.002},
    "deepseek-v4-pro":    {"input": 0.004,  "output": 0.008},
    "deepseek-v3":        {"input": 0.002,  "output": 0.008},
    "deepseek-r1":        {"input": 0.006,  "output": 0.018},
    # 通义千问 Coding Plan (套餐内不计费, 记录参考)
    "qwen3.5-plus":       {"input": 0,      "output": 0},  # 套餐内
    "kimi-k2.5":          {"input": 0,      "output": 0},  # 套餐内
    "glm-5":              {"input": 0,      "output": 0},  # 套餐内
    "qwen3-coder-plus":   {"input": 0,      "output": 0},  # 套餐内
    # 简创AIGC (按次计费, 约0.3元/次)
    "jc-api-video":       {"input": 0.3,    "output": 0},  # 每次0.3元
    # 火山引擎 Coding Plan (套餐内)
    "doubao-seed-2.0":    {"input": 0,      "output": 0},
    # 未知模型
    "unknown":            {"input": 0.005,  "output": 0.01},
}

# 每月预算预警
MONTHLY_BUDGET_WARN = 200.0  # 超过200元预警
MONTHLY_BUDGET_HARD = 500.0  # 超过500元严格预警


class TokenTracker:
    """Token消耗追踪器"""

    def __init__(self):
        self._lock = threading.Lock()
        self._records: List[dict] = []
        self._load()

    def record(self, model: str = "", prompt_tokens: int = 0,
               completion_tokens: int = 0, total_tokens: int = 0,
               partner: str = "", source: str = "", cost: float = None) -> dict:
        """记录一次API调用消耗

        参数:
            model: 模型名称
            prompt_tokens: 输入token数
            completion_tokens: 输出token数
            partner: 执行伙伴
            source: 来源描述
            cost: 手动指定成本（元），自动计算为None
        """
        if total_tokens == 0:
            total_tokens = prompt_tokens + completion_tokens

        # 计算成本
        if cost is None:
            price = MODEL_PRICES.get(model, MODEL_PRICES["unknown"])
            cost = (prompt_tokens / 1000 * price["input"] +
                    completion_tokens / 1000 * price["output"])
            cost = round(cost, 4)

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": model or "unknown",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost": cost,
            "partner": partner,
            "source": source,
        }

        with self._lock:
            self._records.append(record)

        # 异步持久化（通过记录号前缀文件名）
        self._save(record)
        return record

    def record_api(self, response: dict, partner: str = "", source: str = "") -> dict:
        """从API响应中提取token消耗并记录"""
        usage = response.get("usage", {}) if isinstance(response, dict) else {}
        if not usage:
            usage = response.get("response", {}).get("usage", {}) if isinstance(response, dict) else {}
        model = ""
        if isinstance(response, dict):
            model = response.get("model", "")

        return self.record(
            model=model or "unknown",
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            partner=partner,
            source=source,
        )

    # ── 统计 ──

    def stats(self, days: int = 30) -> dict:
        """统计消耗（最近N天）"""
        import time as _time
        cutoff = _time.time() - days * 86400
        recent = [r for r in self._records if self._ts_to_time(r["timestamp"]) >= cutoff]

        total_cost = sum(r["cost"] for r in recent)
        total_tokens = sum(r["total_tokens"] for r in recent)

        # 按模型汇总
        by_model: Dict[str, dict] = {}
        for r in recent:
            m = r["model"]
            if m not in by_model:
                by_model[m] = {"calls": 0, "tokens": 0, "cost": 0.0}
            by_model[m]["calls"] += 1
            by_model[m]["tokens"] += r["total_tokens"]
            by_model[m]["cost"] += r["cost"]

        # 按伙伴汇总
        by_partner: Dict[str, dict] = {}
        for r in recent:
            p = r.get("partner", "") or "unknown"
            if p not in by_partner:
                by_partner[p] = {"calls": 0, "tokens": 0, "cost": 0.0}
            by_partner[p]["calls"] += 1
            by_partner[p]["tokens"] += r["total_tokens"]
            by_partner[p]["cost"] += r["cost"]

        # 今日统计
        today_start = datetime.now().strftime("%Y-%m-%d")
        today = [r for r in recent if r["timestamp"].startswith(today_start)]
        today_cost = sum(r["cost"] for r in today)
        today_tokens = sum(r["total_tokens"] for r in today)

        return {
            "total_calls": len(recent),
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 2),
            "today_calls": len(today),
            "today_tokens": today_tokens,
            "today_cost": round(today_cost, 2),
            "by_model": by_model,
            "by_partner": by_partner,
            "budget_warn": MONTHLY_BUDGET_WARN,
            "budget_hard": MONTHLY_BUDGET_HARD,
            "above_warn": total_cost > MONTHLY_BUDGET_WARN,
            "above_hard": total_cost > MONTHLY_BUDGET_HARD,
        }

    def list(self, limit: int = 20, partner: str = None) -> List[dict]:
        """列出最近的记录"""
        records = list(self._records)
        if partner:
            records = [r for r in records if r.get("partner") == partner]
        records.reverse()
        return records[:limit]

    # ── 持久化 ──

    def _save(self, record: dict):
        """追加到JSONL"""
        try:
            with open(JSONL_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error("保存token记录失败: %s", e)

    def _load(self):
        """加载历史记录"""
        if not os.path.exists(JSONL_PATH):
            return
        try:
            with open(JSONL_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            record = json.loads(line)
                            with self._lock:
                                self._records.append(record)
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            logger.warning("加载token记录失败: %s", e)
        logger.info("📊 已加载 %d 条token记录", len(self._records))

    @staticmethod
    def _ts_to_time(ts: str) -> float:
        try:
            dt = datetime.fromisoformat(ts)
            return dt.timestamp()
        except (ValueError, TypeError):
            return 0


# ── 全局实例（自动加载历史） ──
tracker = TokenTracker()


def _test():
    # 模拟记录
    tracker.record(model="deepseek-v4-flash", prompt_tokens=150, completion_tokens=50,
                   partner="booster", source="选品分析")
    tracker.record(model="deepseek-v4-pro", prompt_tokens=500, completion_tokens=150,
                   partner="lettuce", source="文案生成")
    tracker.record(model="jc-api-video", prompt_tokens=0, completion_tokens=0,
                   partner="corn", source="视频生成", cost=0.3)

    print("✅ 已记录3条token消耗")

    s = tracker.stats()
    print(f"\n📊 Token统计:")
    print(f"  总调用: {s['total_calls']}次")
    print(f"  总token: {s['total_tokens']}")
    print(f"  总成本: ¥{s['total_cost']}")
    print(f"  今日: {s['today_calls']}次 / ¥{s['today_cost']}")
    print(f"  预算警戒: {'⚠️ 超警戒线!' if s['above_warn'] else '✅ 正常'}")
    print(f"  按模型:")
    for m, d in s["by_model"].items():
        print(f"    {m}: {d['calls']}次, {d['tokens']}tokens, ¥{d['cost']:.2f}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _test()
