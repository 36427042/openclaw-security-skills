#!/usr/bin/env python3
"""
hermes_memory_extract.py — 记忆自动提取系统
从 Claude Code 的 extractMemories + remember skill 借鉴

自动从对话/记录中提取关键事实，写入伙伴MEMORY.md

用法:
    from hermes_memory_extract import extractor

    # 从对话中提取事实
    facts = extractor.extract("我发现泰国美白仪最近销量暴涨300%")
    # → [{"type": "market_insight", "content": "泰国美白仪销量暴涨300%", ...}]

    # 保存到伙伴记忆
    extractor.save_to_memory("booster", facts)
"""

import json
import logging
import os
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger("hermes_memory_extract")

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/data/extracted_memories")
os.makedirs(DATA_DIR, exist_ok=True)

PARTNER_MEMORY_DIRS = {
    "booster": os.path.expanduser("~/.openclaw/workspace/agents/booster-agent"),
    "corn": os.path.expanduser("~/.openclaw/workspace/agents/corn-agent"),
    "lettuce": os.path.expanduser("~/.openclaw/workspace/agents/lettuce-agent"),
    "bittergourd": os.path.expanduser("~/.openclaw/workspace/agents/bittergourd-agent"),
    "carrot": os.path.expanduser("~/.openclaw/workspace/agents/carrot-agent"),
    "pea": os.path.expanduser("~/.openclaw/workspace/agents/pea-agent"),
}


# ===================================================================
#  记忆事实类型
# ===================================================================

FACT_TYPES = {
    "market_insight":    "市场洞察 — 爆款/趋势/价格变动",
    "product_insight":   "产品洞察 — 供应商/质量/评价",
    "risk_alert":        "风险告警 — 被封/违禁/投诉",
    "workflow_learn":    "流程学习 — 更好的做法/踩坑",
    "partner_learn":     "伙伴学习 — 谁擅长什么",
    "customer_feedback": "客户反馈 — 好评/差评/退货原因",
    "data_pattern":      "数据模式 — 销量/转化/流量规律",
    "decision":          "决策记录 — 做过的决定/原因",
}


@dataclass
class MemoryFact:
    """提取的记忆事实"""
    type: str
    content: str
    partner: str = ""
    source: str = ""
    confidence: float = 0.8  # 0.0-1.0
    created_at: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "content": self.content,
            "partner": self.partner,
            "source": self.source,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "tags": self.tags,
        }

    @property
    def to_memory_line(self) -> str:
        """转为 MEMORY.md 格式的一行"""
        tag_str = f" [{', '.join(self.tags)}]" if self.tags else ""
        return f"- [{self.created_at[:10]}] {self.content}{tag_str}"


# ===================================================================
#  提取器（基于规则+关键词）
# ===================================================================

# 提取规则: (关键词列表, 事实类型, 模板)
_EXTRACT_RULES = [
    # 市场洞察
    (["爆款", "热卖", "销量", "暴涨", "趋势", "热门"], "market_insight",
     "市场洞察"),
    (["价格", "涨价", "降价", "定价", "利润", "成本", "佣金"], "market_insight",
     "市场价格"),
    # 风险告警
    (["封号", "冻结", "违禁", "投诉", "退货", "差评", "下架", "违规",
      "FDA", "审核"], "risk_alert", "风险告警"),
    # 产品洞察
    (["供应商", "1688", "货源", "质量", "材质", "包装", "样品"], "product_insight",
     "产品洞察"),
    # 流程学习
    (["学会了", "踩坑", "更好的做法", "经验", "教训", "应该", "建议"], "workflow_learn",
     "流程学习"),
    # 客户反馈
    (["买家说", "客户反映", "好评", "差评", "退款", "投诉说"], "customer_feedback",
     "客户反馈"),
    # 数据模式
    (["转化率", "点击率", "客单价", "GMV", "ROI", "复购"], "data_pattern",
     "数据模式"),
    # 决策
    (["决定", "确认", "同意了", "批准", "方案A", "方案B", "选"], "decision",
     "决策"),
]

# 排除的噪音词（不提取）
_NOISE_PATTERNS = [
    r"\d{2}:\d{2}",           # 时间戳
    r"\[.*?\]",                # [标签]
    r"✅|❌|⚠️|⏰|💥|❓|📊|📝|🎬|🎵|🎨",  # emoji
    r"^(好的|明白|OK|收到|好的|可以|行|对|嗯|了|好|是的|不|没)$",
]


class MemoryExtractor:
    """记忆提取器"""

    def __init__(self):
        self._lock = threading.Lock()
        self._friendly_partner_names = {
            "booster": "番茄", "corn": "玉米", "lettuce": "生菜",
            "bittergourd": "苦瓜", "carrot": "萝卜", "pea": "豌豆",
        }

    def extract(self, text: str, partner: str = "",
                source: str = "") -> List[MemoryFact]:
        """从文本中提取记忆事实"""
        facts = []
        text_lower = text.lower()

        # 规则匹配
        for keywords, fact_type, label in _EXTRACT_RULES:
            if any(kw.lower() in text_lower for kw in keywords):
                # 取包含关键词的那句
                sentences = re.split(r'[。！？\n]', text)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if any(kw.lower() in sentence.lower() for kw in keywords):
                        # 去噪
                        cleaned = self._clean(sentence)
                        if cleaned and len(cleaned) > 3:
                            fact = MemoryFact(
                                type=fact_type,
                                content=cleaned[:200],
                                partner=partner,
                                source=source,
                                tags=[label, self._friendly_partner_names.get(partner, partner)],
                            )
                            facts.append(fact)
                            break  # 每种类型只取一句

        # 大写/感叹号的重要信息
        important_matches = re.findall(r'[^。！？]*重要[^。！？]*[。！？]', text)
        for match in important_matches:
            cleaned = self._clean(match)
            if cleaned and not any(f.content == cleaned for f in facts):
                fact = MemoryFact(
                    type="workflow_learn",
                    content=cleaned[:200],
                    partner=partner,
                    source=source,
                    confidence=0.7,
                    tags=["重要", self._friendly_partner_names.get(partner, partner)],
                )
                facts.append(fact)

        # 数字类洞察（包含百分比/金额的句子）
        number_matches = re.findall(r'[^。！？]*[%％元\$][^。！？]*[。！？]', text)
        for match in number_matches[:3]:
            cleaned = self._clean(match)
            if cleaned and len(cleaned) > 5:
                fact = MemoryFact(
                    type="data_pattern",
                    content=cleaned[:200],
                    partner=partner,
                    source=source,
                    confidence=0.6,
                    tags=[self._friendly_partner_names.get(partner, partner)],
                )
                if not any(f.content == cleaned for f in facts):
                    facts.append(fact)

        # 去重
        seen = set()
        unique = []
        for f in facts:
            key = f"{f.type}:{f.content[:60]}"
            if key not in seen:
                seen.add(key)
                unique.append(f)

        logger.info("📝 从 %d 字文本中提取 %d 条记忆", len(text), len(unique))
        return unique

    def extract_and_save(self, text: str, partner: str,
                         source: str = "") -> List[dict]:
        """提取 + 保存到伙伴记忆"""
        facts = self.extract(text, partner, source)
        if facts:
            self.save_to_memory(partner, facts)
            self._archive(partner, facts)
        return [f.to_dict() for f in facts]

    def save_to_memory(self, partner: str, facts: List[MemoryFact],
                       filename: str = "MEMORY.md") -> int:
        """将提取的事实追加到伙伴的MEMORY.md"""
        memory_dir = PARTNER_MEMORY_DIRS.get(partner)
        if not memory_dir or not os.path.isdir(memory_dir):
            logger.warning("伙伴 '%s' 目录不存在: %s", partner, memory_dir)
            return 0

        memory_path = os.path.join(memory_dir, filename)
        if not os.path.exists(memory_path):
            logger.warning("伙伴 '%s' MEMORY.md 不存在", partner)
            return 0

        lines_to_add = []
        for f in facts:
            lines_to_add.append(f.to_memory_line)

        if not lines_to_add:
            return 0

        try:
            with open(memory_path, "a", encoding="utf-8") as f:
                f.write(f"\n## 自动提取记忆 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n")
                for line in lines_to_add:
                    f.write(line + "\n")

            logger.info("💾 已向 %s MEMORY.md 写入 %d 条记忆", partner, len(lines_to_add))
            return len(lines_to_add)
        except Exception as e:
            logger.error("写入记忆失败: %s", e)
            return 0

    def _clean(self, text: str) -> str:
        """清洗文本"""
        text = text.strip()
        # 移除噪音模式
        for pattern in _NOISE_PATTERNS:
            text = re.sub(pattern, "", text).strip()
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text)
        return text[:200] if len(text) > 2 else ""

    def _archive(self, partner: str, facts: List[MemoryFact]):
        """归档到集中存储"""
        try:
            path = os.path.join(DATA_DIR, f"{partner}.jsonl")
            with open(path, "a", encoding="utf-8") as f:
                for fact in facts:
                    f.write(json.dumps(fact.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error("归档记忆失败: %s", e)

    def stats(self) -> dict:
        """统计"""
        total = 0
        by_partner = {}
        by_type = {}
        for partner in PARTNER_MEMORY_DIRS:
            path = os.path.join(DATA_DIR, f"{partner}.jsonl")
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        count = 0
                        for line in f:
                            if line.strip():
                                count += 1
                                try:
                                    data = json.loads(line)
                                    t = data.get("type", "unknown")
                                    by_type[t] = by_type.get(t, 0) + 1
                                except json.JSONDecodeError:
                                    pass
                        by_partner[partner] = count
                        total += count
                except Exception:
                    pass

        return {
            "total": total,
            "by_partner": by_partner,
            "by_type": by_type,
            "fact_types": list(FACT_TYPES.keys()),
        }


# ── 全局实例 ──
extractor = MemoryExtractor()


# ── 便捷函数 ──
def extract_from_text(text: str, partner: str = "", source: str = "") -> List[str]:
    """从文本提取记忆并返回摘要"""
    facts = extractor.extract(text, partner, source)
    return [f.to_memory_line for f in facts]


def auto_extract(text: str, partner: str, source: str = "") -> int:
    """提取并保存到伙伴记忆（一键调用）"""
    saved = extractor.extract_and_save(text, partner, source)
    return len(saved)


def _test():
    text = """
今天发现泰国美白仪最近销量暴涨300%，客单价从$8涨到$12，利润空间大了。
但有个问题，供应商1688那家说FDA审核可能出问题，有些成分在泰国属违禁。
之前的经验是吃过大亏，建议先等苦瓜审核结果再大批量推。
转化率原来只有1.2%，加了对比视频后到3.8%，这数据模式值得记录。
决定：先上50件试水，看看市场反应再决定要不要加量。
    """

    facts = extractor.extract(text, partner="booster", source="选品分析")
    print(f"✅ 从测试文本提取 {len(facts)} 条事实:")
    for f in facts:
        print(f"  [{f.type:20s}] {f.confidence:.1f} {f.content[:80]}")

    saved = extractor.save_to_memory("booster", facts)
    print(f"\n✅ 已写入 {saved} 条到 booster MEMORY.md")

    stats = extractor.stats()
    print(f"\n📊 记忆统计: {stats['total']}条")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _test()
