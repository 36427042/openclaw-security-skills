#!/usr/bin/env python3
"""
hermes_compact.py — 记忆压缩系统
去重、合并、压缩伙伴MEMORY.md，保持清晰

用法:
    from hermes_compact import compactor

    # 分析伙伴记忆状态
    report = compactor.analyze("booster")

    # 压缩（dry-run默认，安全）
    result = compactor.compact("booster", dry_run=True)
"""

import json
import logging
import os
import re
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger("hermes_compact")

PARTNER_MEMORY_DIRS = {
    "booster": os.path.expanduser("~/.openclaw/workspace/agents/booster-agent"),
    "corn": os.path.expanduser("~/.openclaw/workspace/agents/corn-agent"),
    "lettuce": os.path.expanduser("~/.openclaw/workspace/agents/lettuce-agent"),
    "bittergourd": os.path.expanduser("~/.openclaw/workspace/agents/bittergourd-agent"),
    "carrot": os.path.expanduser("~/.openclaw/workspace/agents/carrot-agent"),
    "pea": os.path.expanduser("~/.openclaw/workspace/agents/pea-agent"),
    "tomato": os.path.expanduser("~/.openclaw/workspace/agents/tomato-agent"),
}

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/data/compaction")
os.makedirs(DATA_DIR, exist_ok=True)


# 相似度阈值（很简单的jaccard相似度，用于句子级别去重）
def _jaccard_similarity(a: str, b: str) -> float:
    a_set = set(a.lower().split())
    b_set = set(b.lower().split())
    if not a_set or not b_set:
        return 0
    intersection = a_set & b_set
    union = a_set | b_set
    return len(intersection) / len(union)


class MemoryCompactor:
    """记忆压缩器"""

    def __init__(self):
        self._lock = threading.Lock()

    def analyze(self, partner: str) -> dict:
        """分析伙伴记忆状态"""
        memory_dir = PARTNER_MEMORY_DIRS.get(partner)
        if not memory_dir:
            return {"error": f"伙伴 '{partner}' 目录未配置"}

        mem_path = os.path.join(memory_dir, "MEMORY.md")
        if not os.path.exists(mem_path):
            return {"error": f"MEMORY.md 不存在: {mem_path}"}

        daily_dir = os.path.join(memory_dir, "memory")
        
        # 读取主MEMORY.md
        with open(mem_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        lines = content.strip().split("\n")
        sections = [s.strip() for s in content.split("## ") if s.strip()]
        
        # 分析daily记忆
        daily_files = []
        if os.path.isdir(daily_dir):
            daily_files = sorted([f for f in os.listdir(daily_dir) if f.endswith(".md")])
        
        daily_total_chars = 0
        daily_total_lines = 0
        for fname in daily_files:
            fpath = os.path.join(daily_dir, fname)
            if os.path.isfile(fpath):
                with open(fpath, "r", encoding="utf-8") as f:
                    fc = f.read()
                    daily_total_chars += len(fc)
                    daily_total_lines += len(fc.split("\n"))
        
        # 去重分析
        dupes = self._find_duplicates(content)
        
        return {
            "partner": partner,
            "mem_file": {
                "path": mem_path,
                "size_chars": len(content),
                "size_lines": len(lines),
                "sections": len(sections),
            },
            "daily_memory": {
                "files": len(daily_files),
                "total_chars": daily_total_chars,
                "total_lines": daily_total_lines,
            },
            "duplicates_found": len(dupes),
            "duplicate_pairs": dupes[:10],
            "total_size": len(content) + daily_total_chars,
        }

    def analyze_all(self) -> Dict[str, dict]:
        """分析所有伙伴"""
        results = {}
        for partner in PARTNER_MEMORY_DIRS:
            results[partner] = self.analyze(partner)
        return results

    def compact(self, partner: str, dry_run: bool = True,
                min_similarity: float = 0.7) -> dict:
        """压缩指定伙伴的记忆

        执行的操作:
        1. 去重（相似度超过阈值的合并）
        2. 删除空 section
        3. 统计总结
        
        默认 dry_run=True 只报告不修改
        """
        memory_dir = PARTNER_MEMORY_DIRS.get(partner)
        if not memory_dir:
            return {"error": f"伙伴 '{partner}' 目录未配置"}

        mem_path = os.path.join(memory_dir, "MEMORY.md")
        if not os.path.exists(mem_path):
            return {"error": f"MEMORY.md 不存在: {mem_path}"}

        with open(mem_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_lines = content.split("\n")
        original_len = len(content)

        # 1. 行级别去重
        seen: List[str] = []
        dedup_count = 0
        dedup_lines = []
        for line in original_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("- ["):
                dedup_lines.append(line)
                continue
            # 检查是否与已有行高度相似
            is_dup = False
            for existing in seen:
                if _jaccard_similarity(stripped, existing) >= min_similarity:
                    is_dup = True
                    break
            if is_dup:
                dedup_count += 1
            else:
                seen.append(stripped)
                dedup_lines.append(line)

        new_content = "\n".join(dedup_lines)

        # 2. 去除空section
        sections = new_content.split("## ")
        cleaned_sections = []
        empty_count = 0
        for sec in sections:
            lines = sec.strip().split("\n")
            # 排除只有标题和空行的section
            non_empty = [l for l in lines if l.strip() and not l.strip().startswith("#")]
            if non_empty:
                cleaned_sections.append(sec)
            else:
                empty_count += 1
        new_content = "## ".join(cleaned_sections).strip() or content

        # 3. 统计
        stats = {
            "partner": partner,
            "dry_run": dry_run,
            "original_chars": original_len,
            "original_lines": len(original_lines),
            "new_chars": len(new_content),
            "new_lines": len(new_content.split("\n")),
            "removed_chars": original_len - len(new_content),
            "removed_lines": len(original_lines) - len(new_content.split("\n")),
            "duplicates_collapsed": dedup_count,
            "empty_sections_removed": empty_count,
        }

        if not dry_run:
            # 备份原文件
            backup_path = mem_path + ".bak"
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(content)
            # 写入压缩后版本
            with open(mem_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            logger.info("✅ 已压缩 %s: %d→%d chars (备份: %s)",
                        partner, original_len, len(new_content), backup_path)
            # 记录
            self._log_compaction(partner, stats)
        else:
            logger.info("📋 (dry-run) %s: 可压缩 %d chars, %d 重复行",
                        partner, stats["removed_chars"], dedup_count)

        return stats

    def _find_duplicates(self, content: str) -> List[dict]:
        """找出相似度高的重复行"""
        lines = [l.strip() for l in content.split("\n") if l.strip() 
                 and not l.startswith("#") and not l.startswith("- [")]
        dupes = []
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                sim = _jaccard_similarity(lines[i], lines[j])
                if sim >= 0.7:
                    dupes.append({
                        "idx_a": i, "idx_b": j,
                        "similarity": round(sim, 2),
                        "a": lines[i][:60],
                        "b": lines[j][:60],
                    })
                    if len(dupes) >= 10:
                        return dupes
        return dupes

    def _log_compaction(self, partner: str, stats: dict):
        """记录压缩操作"""
        try:
            path = os.path.join(DATA_DIR, "history.jsonl")
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "partner": partner,
                    **stats,
                }, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error("记录压缩历史失败: %s", e)

    def stats(self) -> dict:
        """查看所有伙伴记忆概况"""
        results = {}
        total_chars = 0
        for partner in PARTNER_MEMORY_DIRS:
            r = self.analyze(partner)
            results[partner] = {
                "mem_size": r.get("mem_file", {}).get("size_chars", 0),
                "daily_files": r.get("daily_memory", {}).get("files", 0),
                "duplicates": r.get("duplicates_found", 0),
            }
            total_chars += results[partner]["mem_size"]
        
        return {
            "partners": results,
            "total_chars": total_chars,
            "avg_chars": total_chars // max(len(PARTNER_MEMORY_DIRS), 1),
        }


compactor = MemoryCompactor()


def _test():
    print("=== 记忆压缩系统测试 ===")
    s = compactor.stats()
    total = s["total_chars"]
    print(f"✅ 7个伙伴总记忆: {total:,} chars")
    for p, d in s["partners"].items():
        mem = d.get("mem_size", 0) or 0
        dup = d.get("duplicates", 0)
        color = "🟢" if dup == 0 else "🟡" if dup < 3 else "🔴"
        print(f"  {color} {p:15s} {mem:>6,} chars, {d['daily_files']} daily, {dup} dupes")

    # 对第一个有记忆的分析
    for p in PARTNER_MEMORY_DIRS:
        report = compactor.analyze(p)
        if "error" not in report:
            r = compactor.compact(p, dry_run=True)
            print(f"\n{report['partner']}: 可压缩 {r['removed_chars']} chars, {r['duplicates_collapsed']} 重复行")
            break
    print("\n✅ 分析完成")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _test()
