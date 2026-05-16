#!/usr/bin/env python3
"""
hermes_routing.py — 伙伴间自动路由
根据任务意图自动分派到正确的伙伴

用法:
    from hermes_routing import router

    # 自动路由
    result = router.route("给爆款美白仪做个泰国视频")
    # → {"intent": "video", "targets": ["corn", "lettuce"], ...}

    # 手动路由
    router.to("booster", "搜索泰国美白仪爆款")
"""

import json
import logging
import os
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

logger = logging.getLogger("hermes_routing")

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/data/routing")
os.makedirs(DATA_DIR, exist_ok=True)

# 伙伴能力描述（用于匹配）
PARTNER_CAPABILITIES = {
    "booster": {
        "name": "番茄",
        "keywords": ["选品", "爆款", "选什么", "卖什么", "1688", "货源", "供应商",
                     "搜索", "热卖", "销量", "趋势"],
        "tools": ["booster_matrix", "searches", "product_analysis"],
    },
    "corn": {
        "name": "玉米",
        "keywords": ["视频", "剪辑", "素材", "渲染", "动画", "capcut", "画面",
                     "拍视频", "做视频", "模板"],
        "tools": ["video_pipeline", "capcut_mate"],
    },
    "lettuce": {
        "name": "生菜",
        "keywords": ["文案", "话术", "标题", "描述", "标题", "标题优化",
                     "写文案", "写话术", "商品描述"],
        "tools": ["copy_engine"],
    },
    "bittergourd": {
        "name": "苦瓜",
        "keywords": ["风控", "审核", "违禁", "FDA", "合规", "安全", "风险",
                     "检查", "审查", "封号", "投诉", "违规"],
        "tools": ["risk_controller"],
    },
    "carrot": {
        "name": "萝卜",
        "keywords": ["配音", "音频", "语音", "直播", "录音", "播报",
                     "配音", "声音", "TTS"],
        "tools": ["tts_engine"],
    },
    "pea": {
        "name": "豌豆",
        "keywords": ["数据", "报表", "统计", "分析", "看板", "监控",
                     "销量", "GMV", "转化", "报告"],
        "tools": ["data_monitor"],
    },
}

# 多伙伴组合（高级意图）
COMPOSITE_INTENTS = {
    "上架": ["booster", "lettuce", "bittergourd"],
    "视频": ["corn", "lettuce"],
    "全链路": ["booster", "corn", "lettuce", "bittergourd", "carrot", "pea"],
    "泰国": ["booster", "corn"],
    "风控": ["lettuce", "bittergourd"],
    "复盘": ["booster", "pea"],
}

# 明确指令模式
_EXPLICIT_PATTERNS = [
    (r"给(玉米|corn).*", "corn"),
    (r"给(番茄|booster).*", "booster"),
    (r"给(生菜|lettuce).*", "lettuce"),
    (r"给(苦瓜|bittergourd).*", "bittergourd"),
    (r"给(萝卜|carrot).*", "carrot"),
    (r"给(豌豆|pea).*", "pea"),
    (r"(玉米|corn).*做.*视频", "corn"),
    (r"(番茄|booster).*选.*品", "booster"),
    (r"(生菜|lettuce).*写.*文案", "lettuce"),
    (r"苦瓜.*审核", "bittergourd"),
    (r"(豌豆|pea).*看.*数据", "pea"),
]


@dataclass
class RouteResult:
    """路由结果"""
    intent: str
    targets: List[str]
    confidence: float
    text: str
    matched_keywords: List[str] = field(default_factory=list)
    routed_at: str = ""
    
    def __post_init__(self):
        if not self.routed_at:
            self.routed_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "targets": self.targets,
            "confidence": self.confidence,
            "text": self.text[:100],
            "matched_keywords": self.matched_keywords,
            "routed_at": self.routed_at,
        }


class Router:
    """任务路由"""

    def __init__(self):
        self._lock = threading.Lock()
        self._history: List[RouteResult] = []
        self._custom_routes: Dict[str, List[str]] = {}
        self._load()

    # ── 核心路由 ──

    def route(self, text: str) -> RouteResult:
        """自动路由：输入文本 → 目标伙伴"""
        text_lower = text.lower()

        result = None

        # 1. 检查明确指令（"给玉米做视频"）
        if not result:
            for pattern, partner in _EXPLICIT_PATTERNS:
                if re.match(pattern, text_lower):
                    result = RouteResult(
                        intent="直接指定", targets=[partner],
                        confidence=1.0, text=text, matched_keywords=[pattern],
                    )
                    break

        # 2. 检查复合意图（"上架"→选品+文案+风控）
        if not result:
            for intent, partners in COMPOSITE_INTENTS.items():
                if intent in text:
                    result = RouteResult(
                        intent=intent, targets=partners,
                        confidence=0.9, text=text, matched_keywords=[intent],
                    )
                    break

        # 3. 检查自定义路由
        if not result:
            with self._lock:
                for pattern, partners in self._custom_routes.items():
                    if pattern.lower() in text_lower:
                        result = RouteResult(
                            intent="自定义路由", targets=partners,
                            confidence=0.85, text=text, matched_keywords=[pattern],
                        )
                        break

        # 4. 关键词匹配（按得分排名）
        if not result:
            scores: Dict[str, float] = {}
            matched: Dict[str, List[str]] = {}
            for partner, info in PARTNER_CAPABILITIES.items():
                sc = 0
                mks = []
                for kw in info["keywords"]:
                    if kw in text_lower:
                        sc += 1
                        mks.append(kw)
                if sc > 0:
                    scores[partner] = sc
                    matched[partner] = mks
            if scores:
                best = max(scores, key=scores.get)
                result = RouteResult(
                    intent="关键词匹配", targets=[best],
                    confidence=round(min(0.5 + scores[best] * 0.1, 0.95), 2),
                    text=text, matched_keywords=matched.get(best, []),
                )

        # 5. 无匹配 → 默认给土豆
        if not result:
            result = RouteResult(
                intent="未匹配", targets=["tudou"],
                confidence=0.3, text=text, matched_keywords=[],
            )

        self._record(result)
        return result

    def to(self, partner: str, task: str, force: bool = False) -> dict:
        """手动指向特定伙伴（返回 RouteResult）"""
        if partner not in PARTNER_CAPABILITIES and partner != "tudou":
            if not force:
                return {"error": f"伙伴不存在: {partner}", "partners": list(PARTNER_CAPABILITIES.keys())}
        result = RouteResult(
            intent="手动指定",
            targets=[partner],
            confidence=1.0,
            text=task,
        )
        self._record(result)
        return result.to_dict()

    def add_composite(self, intent: str, partners: List[str]):
        """注册复合意图"""
        with self._lock:
            COMPOSITE_INTENTS[intent] = partners
            self._save()

    def add_route(self, keyword: str, partners: List[str]):
        """注册自定义路由规则"""
        with self._lock:
            self._custom_routes[keyword] = partners
            self._save()

    # ── 反馈 ──

    def _record(self, result: RouteResult):
        with self._lock:
            self._history.append(result)
            if len(self._history) > 500:
                self._history = self._history[-100:]

    def history(self, limit: int = 20) -> List[dict]:
        with self._lock:
            h = [r.to_dict() for r in self._history]
        return h[-limit:]

    # ── 持久化 ──

    def _save(self):
        try:
            path = os.path.join(DATA_DIR, "config.json")
            data = {"custom_routes": self._custom_routes,
                    "custom_composites": list(COMPOSITE_INTENTS.items())}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("保存路由配置失败: %s", e)

    def _load(self):
        try:
            path = os.path.join(DATA_DIR, "config.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                with self._lock:
                    self._custom_routes = data.get("custom_routes", {})
                    for intent, partners in data.get("custom_composites", []):
                        COMPOSITE_INTENTS[intent] = partners
        except Exception as e:
            logger.warning("加载路由配置失败: %s", e)

    def stats(self) -> dict:
        with self._lock:
            return {
                "total_routes": len(self._history),
                "custom_routes": len(self._custom_routes),
                "composite_intents": len(COMPOSITE_INTENTS),
                "partners": list(PARTNER_CAPABILITIES.keys()),
            }


router = Router()


def _test():
    print("=== 自动路由测试 ===")
    
    tests = [
        "给玉米做泰国美白仪的视频",
        "全链路上架这个产品",
        "选品搜索泰国美白仪",
        "风控审核这个文案",
        "看下本周的数据报表",
        "随便说一句",
        "泰国专场搞一下",
    ]
    
    for t in tests:
        r = router.route(t)
        color = "🟢" if r.confidence >= 0.8 else "🟡" if r.confidence >= 0.5 else "🔴"
        print(f"  {color} [{r.confidence:.1f}] {t[:40]:40s} → {', '.join(r.targets)} ({r.intent})")
    
    print(f"\n✅ 共路由 {len(router.history())} 次")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _test()
