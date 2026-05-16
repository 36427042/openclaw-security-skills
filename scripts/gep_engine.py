#!/usr/bin/env python3
"""
🧬 GEP Engine — EvoMap General Evolution Protocol
自进化引擎：7伙伴共享，记录失败→学习模式→避免重复犯错

用法:
    from gep_engine import GEP

    # 执行前检查：类似问题之前遇到过吗？
    advice = GEP.pre_check(partner="番茄", task="生成定价报告", context={"country": "TH"})
    if advice:
        print(f"📖 历史经验: {advice['solution']}")
        GEP.apply(advice)

    # 执行后记录：无论成功失败都记录
    GEP.post_record(partner="番茄", task="生成定价报告",
                    context={"country": "TH"}, outcome="success",
                    note="定价报告生成正常")
"""

import json, os, time, hashlib, re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# ========== 路径 ==========
WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
EVOLUTION_DIR = os.path.join(WORKSPACE, "data", "evolution")
os.makedirs(EVOLUTION_DIR, exist_ok=True)

REGISTRY_FILE = os.path.join(EVOLUTION_DIR, "registry.jsonl")
PATTERNS_FILE = os.path.join(EVOLUTION_DIR, "patterns.json")
CHECKPOINT_FILE = os.path.join(EVOLUTION_DIR, "gep_checkpoint.json")

# 所有注册的伙伴
ALL_PARTNERS = ["土豆", "番茄", "生菜", "玉米", "萝卜", "苦瓜", "豌豆"]


# ====================================================================
# GEPNode — 单条进化记录（不可变）
# ====================================================================

class GEPNode:
    """一条进化节点：记录了问题→尝试方案→结果"""

    def __init__(self, partner: str, task: str, problem: str,
                 context: dict = None, solution: str = "",
                 outcome: str = "unknown", note: str = ""):
        if partner not in ALL_PARTNERS:
            # 自动映射英文名
            PARTNER_MAP = {"tomato": "土豆", "booster": "番茄", "copy": "生菜",
                           "video": "玉米", "tts": "萝卜", "risk": "苦瓜", "data": "豌豆",
                           "土豆": "土豆", "番茄": "番茄", "生菜": "生菜",
                           "玉米": "玉米", "萝卜": "萝卜", "苦瓜": "苦瓜", "豌豆": "豌豆",
                           "hermes": "土豆"}
            partner = PARTNER_MAP.get(partner.lower(), partner)

        self.node_id = hashlib.md5(
            f"{partner}:{task}:{time.time_ns()}".encode()
        ).hexdigest()[:12]

        self.partner = partner
        self.task = task
        self.problem = problem
        self.context = context or {}
        self.solution = solution
        self.outcome = outcome
        self.note = note
        self.timestamp = datetime.now().isoformat()

        # 相似性键：用于匹配同类问题
        self.similarity_key = self._compute_similarity_key()

    def _compute_similarity_key(self) -> str:
        """生成用于匹配相似问题的键"""
        key_parts = [self.partner, self.task]
        # 提取关键上下文
        for k in ["country", "api", "endpoint", "model", "file_type"]:
            if k in self.context:
                key_parts.append(f"{k}={self.context[k]}")
        return ":".join(key_parts)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "partner": self.partner,
            "task": self.task,
            "problem": self.problem,
            "context": self.context,
            "solution": self.solution,
            "outcome": self.outcome,
            "note": self.note,
            "timestamp": self.timestamp,
            "similarity_key": self.similarity_key,
        }

    @classmethod
    def from_dict(cls, data: dict):
        node = cls.__new__(cls)
        for k, v in data.items():
            setattr(node, k, v)
        return node


# ====================================================================
# GEPRegistry — 进化节点存储与查询
# ====================================================================

class GEPRegistry:
    """进化节点注册表：存储、查询、模式发现"""

    def __init__(self):
        self._cache: List[GEPNode] = []
        self._load()

    def _load(self):
        """从 JSONL 文件加载历史节点"""
        if os.path.exists(REGISTRY_FILE):
            with open(REGISTRY_FILE) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            self._cache.append(GEPNode.from_dict(data))
                        except json.JSONDecodeError:
                            pass

    def save(self, node: GEPNode) -> str:
        """保存一条进化节点"""
        with open(REGISTRY_FILE, "a") as f:
            f.write(json.dumps(node.to_dict(), ensure_ascii=False) + "\n")
        self._cache.append(node)
        return node.node_id

    def find_similar(self, task: str = "", partner: str = "",
                     context: dict = None, max_results: int = 3) -> List[GEPNode]:
        """查找相似问题的历史节点"""
        context = context or {}
        scored = []

        for node in self._cache:
            score = 0
            # 同伙伴 +5
            if partner and node.partner == partner:
                score += 5
            # 同任务 +10
            if task and task.lower() in node.task.lower():
                score += 10
            # 同上下文 +3/项
            for k, v in context.items():
                cv = node.context.get(k)
                if cv and str(cv).lower() == str(v).lower():
                    score += 3
            # 失败记录权重高
            if node.outcome in ("failed", "error", "timeout"):
                score += 8
            # 成功记录有参考价值
            if node.outcome == "success" and node.solution:
                score += 4

            if score > 0:
                scored.append((score, node))

        scored.sort(key=lambda x: -x[0])
        return [n for _, n in scored[:max_results]]

    def get_stats(self) -> dict:
        """进化统计"""
        if not self._cache:
            return {"total": 0, "by_partner": {}, "by_outcome": {}}

        by_partner = {}
        by_outcome = {}
        for node in self._cache:
            by_partner[node.partner] = by_partner.get(node.partner, 0) + 1
            by_outcome[node.outcome] = by_outcome.get(node.outcome, 0) + 1

        return {
            "total": len(self._cache),
            "by_partner": by_partner,
            "by_outcome": by_outcome,
            "last_update": self._cache[-1].timestamp if self._cache else "",
        }

    def analyze_patterns(self) -> dict:
        """分析重复失败模式"""
        if len(self._cache) < 3:
            return {"patterns": [], "summary": "数据不足，继续积累中"}

        # 找出由同一伙伴、同一任务、同一问题的重复失败
        failure_groups = {}
        for node in self._cache:
            if node.outcome in ("failed", "error", "timeout"):
                key = f"{node.partner}:{node.task}:{node.problem[:40]}"
                if key not in failure_groups:
                    failure_groups[key] = []
                failure_groups[key].append(node)

        patterns = []
        for key, nodes in failure_groups.items():
            if len(nodes) >= 2:  # 同一个问题出现2次以上
                partner, task, *_ = key.split(":")
                patterns.append({
                    "partner": partner,
                    "task": task,
                    "problem": nodes[0].problem[:80],
                    "occurrences": len(nodes),
                    "first_seen": nodes[0].timestamp,
                    "last_seen": nodes[-1].timestamp,
                    "recommendation": f"该问题已出现{len(nodes)}次，建议修改{partner}的{task}逻辑"
                })

        patterns.sort(key=lambda p: -p["occurrences"])

        return {
            "patterns": patterns,
            "total_failures": sum(1 for n in self._cache
                                  if n.outcome in ("failed", "error", "timeout")),
            "repeated_issue_count": len(patterns),
            "summary": f"发现{len(patterns)}个重复问题模式"
        }


# ====================================================================
# GEPEngine — 自进化协议执行引擎
# ====================================================================

class GEPEngine:
    """
    GEP 自进化协议执行引擎

    核心流程：
    pre_check → 执行 → post_record → analyze → evolve
    """

    def __init__(self, partner: str):
        self.partner = partner
        self.registry = GEPRegistry()
        self._checkpoint = self._load_checkpoint()

    def _load_checkpoint(self) -> dict:
        """加载上次进化检查点"""
        cp = {"last_analyze": "", "nodes_since_analyze": 0}
        if os.path.exists(CHECKPOINT_FILE):
            try:
                with open(CHECKPOINT_FILE) as f:
                    cp.update(json.load(f))
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return cp

    def _save_checkpoint(self):
        """保存进化检查点"""
        with open(CHECKPOINT_FILE, "w") as f:
            json.dump(self._checkpoint, f, ensure_ascii=False)

    # ----------------------------------------------------------------
    # 核心 API
    # ----------------------------------------------------------------

    def pre_check(self, task: str, context: dict = None,
                  force: bool = False) -> Optional[dict]:
        """
        任务执行前检查：是否有类似问题的历史经验

        Args:
            task: 要执行的任务名
            context: 上下文信息
            force: 是否强制检查（即使历史记录为空）

        Returns:
            如果有相关经验，返回建议；否则返回 None
        """
        context = context or {}

        # 查找相似历史
        similar = self.registry.find_similar(
            task=task, partner=self.partner, context=context
        )

        if not similar:
            return None

        # 聚合建议
        warnings = []
        solutions = []
        for node in similar[:2]:
            if node.outcome in ("failed", "error", "timeout"):
                warnings.append(f"⚠️ 同名任务历史失败: {node.problem[:60]}")
            if node.solution:
                solutions.append(node.solution)

        if warnings or (force and similar):
            return {
                "has_warnings": len(warnings) > 0,
                "warnings": warnings,
                "solutions": solutions,
                "similar_count": len(similar),
                "advice": solutions[0] if solutions else "无历史解决方案",
                "cautious": len(warnings) > 0,
            }
        return None

    def post_record(self, task: str, context: dict = None,
                    outcome: str = "unknown", problem: str = "",
                    solution: str = "", note: str = ""):
        """
        任务执行后记录进化节点

        Args:
            task: 执行的任务名
            context: 上下文
            outcome: success / failed / error / timeout / partial
            problem: 如果失败，描述问题
            solution: 如果解决，记录方案
            note: 备注
        """
        context = context or {}

        node = GEPNode(
            partner=self.partner,
            task=task,
            problem=problem or f"任务执行{outcome}",
            context=context,
            solution=solution,
            outcome=outcome,
            note=note,
        )

        node_id = self.registry.save(node)

        # 更新检查点
        self._checkpoint["nodes_since_analyze"] = \
            self._checkpoint.get("nodes_since_analyze", 0) + 1

        # 每10个新节点自动分析模式
        if self._checkpoint["nodes_since_analyze"] >= 10:
            self.analyze()
            self._checkpoint["nodes_since_analyze"] = 0

        self._save_checkpoint()
        return node_id

    def analyze(self) -> dict:
        """分析进化模式，输出优化建议"""
        patterns = self.registry.analyze_patterns()

        # 保存分析结果
        patterns["analyzed_at"] = datetime.now().isoformat()
        patterns["by"] = self.partner
        with open(PATTERNS_FILE, "w") as f:
            json.dump(patterns, f, ensure_ascii=False, indent=2)

        self._checkpoint["last_analyze"] = patterns["analyzed_at"]
        self._save_checkpoint()
        return patterns

    def get_advice(self, task: str, context: dict = None) -> str:
        """
        获取执行建议（简化版 pre_check 供 CLI 使用）

        Returns:
            人性化的建议文本
        """
        advice = self.pre_check(task, context)
        if not advice:
            return "🟢 无相关历史经验，可以正常执行"

        parts = []
        if advice["warnings"]:
            parts.append("🔴 历史警报：")
            parts.extend(f"  {w}" for w in advice["warnings"])
        if advice["solutions"]:
            parts.append("💡 已知解决方案：")
            parts.append(f"  {advice['solutions'][0]}")
        if not advice["cautious"]:
            parts.append("✅ 历史经验表明无严重问题")

        return "\n".join(parts) if parts else "🟢 无相关历史经验"

    def get_stats(self) -> dict:
        """获取进化统计"""
        return self.registry.get_stats()


# ====================================================================
# 简化API（无需创建实例）
# ====================================================================

_registries: Dict[str, GEPEngine] = {}


def GEP(partner: str) -> GEPEngine:
    """
    获取伙伴的 GEP 进化引擎实例

    用法:
        gep = GEP("番茄")
        advice = gep.pre_check("生成定价报告", {"country": "TH"})
        gep.post_record("生成定价报告", {"country": "TH"}, "success")
    """
    if partner not in _registries:
        _registries[partner] = GEPEngine(partner)
    return _registries[partner]


def export_report(output_dir: str = None) -> str:
    """导出进化报告（Markdown）"""
    if output_dir is None:
        output_dir = EVOLUTION_DIR

    registry = GEPRegistry()
    stats = registry.get_stats()
    patterns = registry.analyze_patterns()

    report = [
        "# 🧬 GEP 自进化报告",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 📊 统计概览",
        f"- **总进化节点数**：{stats['total']}",
        f"- **按伙伴分布**：",
    ]
    for p, c in sorted(stats.get("by_partner", {}).items(),
                        key=lambda x: -x[1]):
        report.append(f"  - {p}：{c} 条")
    report.extend([
        f"- **按结果分布**：",
    ])
    for o, c in sorted(stats.get("by_outcome", {}).items()):
        report.append(f"  - {o}：{c} 条")
    report.extend([
        "",
        "## 🔍 重复失败模式",
    ])
    for p in patterns.get("patterns", []):
        report.append(
            f"- **{p['partner']} / {p['task']}** "
            f"（{p['occurrences']}次）"
        )
        report.append(f"  - 问题：{p['problem']}")
        report.append(f"  - 建议：{p['recommendation']}")

    if not patterns.get("patterns"):
        report.append("  - 暂无重复失败模式 ✅")

    report.extend([
        "",
        "## 📋 建议行动",
        "1. 高频失败的任务优先优化",
        "2. 按伙伴分配进化节点，确保学习覆盖面",
        "3. 每50个新节点做一次深度模式分析",
    ])

    content = "\n".join(report)
    path = os.path.join(output_dir, f"gep_report_{datetime.now().strftime('%Y%m%d')}.md")
    with open(path, "w") as f:
        f.write(content)
    return path


# ====================================================================
# CLI 入口
# ====================================================================
def main():
    import sys

    if len(sys.argv) < 2:
        print("🧬 GEP 自进化引擎")
        print("用法：")
        print("  python3 gep_engine.py status             # 查看进化统计")
        print("  python3 gep_engine.py analyze            # 分析模式")
        print("  python3 gep_engine.py report             # 导出报告")
        print("  python3 gep_engine.py advice <伙伴> <任务> [上下文]")
        print("  python3 gep_engine.py record <伙伴> <任务> <结果> [问题]")
        return

    cmd = sys.argv[1]
    registry = GEPRegistry()

    if cmd == "status":
        stats = registry.get_stats()
        print(f"📊 GEP 进化统计")
        print(f"  总节点：{stats['total']}")
        print(f"  按伙伴：")
        for p, c in sorted(stats.get("by_partner", {}).items(),
                            key=lambda x: -x[1]):
            print(f"    {p}: {c}")
        print(f"  按结果：")
        for o, c in sorted(stats.get("by_outcome", {}).items()):
            print(f"    {o}: {c}")

    elif cmd == "analyze":
        patterns = registry.analyze_patterns()
        print(f"🔍 模式分析")
        print(f"  总失败：{patterns['total_failures']}")
        print(f"  重复问题：{patterns['repeated_issue_count']}")
        for p in patterns.get("patterns", []):
            print(f"  ⚠️  {p['partner']}/{p['task']} ×{p['occurrences']}")
            print(f"      建议: {p['recommendation']}")

    elif cmd == "report":
        path = export_report()
        print(f"📋 报告已导出：{path}")

    elif cmd == "advice" and len(sys.argv) >= 4:
        partner = sys.argv[2]
        task = sys.argv[3]
        context = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
        engine = GEP(partner)
        advice = engine.pre_check(task, context)
        if advice:
            print(engine.get_advice(task, context))
        else:
            print("🟢 无相关历史经验")

    elif cmd == "record" and len(sys.argv) >= 5:
        partner = sys.argv[2]
        task = sys.argv[3]
        outcome = sys.argv[4]
        problem = sys.argv[5] if len(sys.argv) > 5 else ""
        engine = GEP(partner)
        nid = engine.post_record(task=task, outcome=outcome, problem=problem)
        print(f"✅ 进化节点已记录: {nid}")

    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
