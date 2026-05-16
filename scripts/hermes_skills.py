#!/usr/bin/env python3
"""
hermes_skills.py — Skill 技能系统
从 Claude Code 的 skillify + 16 个预置技能系统借鉴

Skill = 可复用的工作流，含参数、步骤、输入输出

用法:
    from hermes_skills import skill_registry, Skill

    # 创建Skill
    skill_registry.create("泰国专场上架", steps=["booster", "corn", "lettuce", "bittergourd"])

    # 列出Skills
    skill_registry.list()

    # 运行Skill
    skill_registry.run("泰国专场上架")
"""

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger("hermes_skills")

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/data/skills")
os.makedirs(DATA_DIR, exist_ok=True)


# ===================================================================
#  Skill 定义
# ===================================================================

@dataclass
class Skill:
    name: str
    description: str = ""
    steps: List[str] = field(default_factory=list)    # 伙伴key列表
    params_schema: dict = field(default_factory=dict)  # 参数JSON Schema
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    run_count: int = 0
    last_run: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
            "params_schema": self.params_schema,
            "tags": self.tags,
            "created_at": self.created_at,
            "run_count": self.run_count,
            "last_run": self.last_run,
            "metadata": self.metadata,
        }

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def summary(self) -> str:
        steps_str = " → ".join(self.steps) if self.steps else "(empty)"
        return f"[{self.run_count}次] {self.name}: {steps_str}"


# ===================================================================
#  Skill 注册中心
# ===================================================================

class SkillRegistry:
    """Skill 注册 + 持久化"""

    def __init__(self):
        self._lock = threading.Lock()
        self._skills: Dict[str, Skill] = {}
        self._auto_save_enabled = True
        self._load()

    # ── CRUD ──

    def create(self, name: str, description: str = "",
               steps: List[str] = None, tags: List[str] = None,
               params_schema: dict = None, metadata: dict = None) -> Skill:
        """创建Skill"""
        if name in self._skills:
            logger.warning("Skill '%s' 已存在, 将覆盖", name)
        skill = Skill(
            name=name,
            description=description,
            steps=steps or [],
            tags=tags or [],
            params_schema=params_schema or {},
            metadata=metadata or {},
        )
        with self._lock:
            self._skills[name] = skill
        self._save(skill)
        logger.info("📋 Skill创建: %s (%d步)", name, len(skill.steps))
        return skill

    def get(self, name: str) -> Optional[Skill]:
        with self._lock:
            return self._skills.get(name)

    def list(self, tag: str = None, limit: int = 50) -> List[dict]:
        """列出Skills"""
        with self._lock:
            skills = list(self._skills.values())
        if tag:
            skills = [s for s in skills if tag in s.tags]
        skills.sort(key=lambda s: s.run_count, reverse=True)
        return [s.to_dict() for s in skills[:limit]]

    def delete(self, name: str) -> bool:
        """删除Skill"""
        with self._lock:
            if name not in self._skills:
                return False
            del self._skills[name]
        self._delete_file(name)
        logger.info("🗑️ Skill删除: %s", name)
        return True

    def rename(self, old_name: str, new_name: str) -> bool:
        """重命名Skill"""
        skill = self.get(old_name)
        if not skill:
            return False
        with self._lock:
            skill.name = new_name
            del self._skills[old_name]
            self._skills[new_name] = skill
        self._delete_file(old_name)
        self._save(skill)
        return True

    # ── 执行 ──

    def run(self, name: str, params: dict = None, executor: Callable = None) -> dict:
        """执行Skill (需外部提供executor, 或走预设)"""
        skill = self.get(name)
        if not skill:
            return {"status": "error", "error": f"Skill '{name}' 未找到"}

        start = time.time()
        try:
            if executor:
                result = executor(skill, params or {})
            else:
                # 默认executor: 只返回步骤列表
                result = {"steps": skill.steps, "status": "ready"}

            # 更新运行统计
            skill.run_count += 1
            skill.last_run = datetime.now(timezone.utc).isoformat()
            self._save(skill)
            result["duration_s"] = round(time.time() - start, 2)
            result["skill"] = name
            logger.info("🏃 Skill运行: %s (%.1fs)", name, result["duration_s"])
            return result
        except Exception as e:
            logger.error("Skill '%s' 执行失败: %s", name, e)
            return {"status": "error", "error": str(e), "skill": name}

    # ── 从工作流创建Skill (skillify) ──

    def skillify(self, name: str, description: str, workflow_steps: List[str],
                 tags: List[str] = None) -> Skill:
        """从工作流步骤创建Skill (类比Claude Code的/skillify)"""
        return self.create(
            name=name,
            description=description,
            steps=workflow_steps,
            tags=tags or ["auto-skill"],
            metadata={"source": "skillify"},
        )

    def suggest_name(self, steps: List[str]) -> str:
        """根据步骤自动建议Skill名称"""
        name_map = {
            ("booster",): "选品",
            ("corn", "lettuce"): "视频文案",
            ("booster", "corn"): "选品视频",
            ("booster", "corn", "lettuce", "bittergourd", "carrot", "pea"): "全链路",
        }
        key = tuple(steps)
        if key in name_map:
            return name_map[key]
        if len(steps) <= 3:
            return "+".join(steps[:3])
        return f"{steps[0]}+{steps[1]}+...+{steps[-1]}"

    # ── 持久化 ──

    def _save(self, skill: Skill):
        """保存到文件"""
        if not self._auto_save_enabled:
            return
        try:
            path = os.path.join(DATA_DIR, f"{skill.name}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(skill.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("保存Skill失败 '%s': %s", skill.name, e)

    def _load(self):
        """加载Skills"""
        if not os.path.isdir(DATA_DIR):
            return
        for fn in os.listdir(DATA_DIR):
            if not fn.endswith(".json"):
                continue
            try:
                path = os.path.join(DATA_DIR, fn)
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                skill = Skill(
                    name=data["name"],
                    description=data.get("description", ""),
                    steps=data.get("steps", []),
                    tags=data.get("tags", []),
                    params_schema=data.get("params_schema", {}),
                    created_at=data.get("created_at", ""),
                    run_count=data.get("run_count", 0),
                    last_run=data.get("last_run", ""),
                    metadata=data.get("metadata", {}),
                )
                with self._lock:
                    self._skills[skill.name] = skill
            except Exception as e:
                logger.warning("加载Skill失败 %s: %s", fn, e)
        logger.info("📋 已加载 %d 个Skills", len(self._skills))

    def _delete_file(self, name: str):
        path = os.path.join(DATA_DIR, f"{name}.json")
        if os.path.exists(path):
            os.remove(path)

    def stats(self) -> dict:
        with self._lock:
            return {
                "total": len(self._skills),
                "total_runs": sum(s.run_count for s in self._skills.values()),
                "skills": [s.summary for s in self._skills.values()],
            }

    def __len__(self):
        with self._lock:
            return len(self._skills)


# ===================================================================
#  预置 Skills
# ===================================================================

_PRESET_SKILLS = {
    "全链路上架": {
        "description": "选品→视频→文案→风控→配音→数据 全链路",
        "steps": ["booster", "corn", "lettuce", "bittergourd", "carrot", "pea"],
        "tags": ["全链路", "自动化"],
    },
    "市场检查": {
        "description": "快速检查选品+风控+数据",
        "steps": ["booster", "bittergourd", "pea"],
        "tags": ["巡检", "快速"],
    },
    "内容生产": {
        "description": "文案→配音→视频 一条龙",
        "steps": ["lettuce", "carrot", "corn"],
        "tags": ["内容", "视频"],
    },
    "风控审核": {
        "description": "风控全面检查: 文案+视频+数据",
        "steps": ["lettuce", "bittergourd", "corn", "pea"],
        "tags": ["风控", "安全"],
    },
    "数据复盘": {
        "description": "经营数据+选品数据+风控数据汇总分析",
        "steps": ["booster", "bittergourd", "pea"],
        "tags": ["数据", "复盘"],
    },
}


# ===================================================================
#  全局实例
# ===================================================================

skill_registry = SkillRegistry()

# 注册预置Skills
for name, cfg in _PRESET_SKILLS.items():
    if not skill_registry.get(name):
        skill_registry.create(
            name=name,
            description=cfg["description"],
            steps=cfg["steps"],
            tags=cfg["tags"],
            metadata={"preset": True},
        )


# ===================================================================
#  测试
# ===================================================================

def _test():
    # 1. 预置Skills
    all_skills = skill_registry.list()
    print(f"✅ 预置Skills: {len(all_skills)}个")

    # 2. 创建自定义Skill
    s = skill_registry.create(
        "泰国专场",
        description="泰国站选品+视频+文案",
        steps=["booster", "corn", "lettuce"],
        tags=["泰国", "专场"],
    )
    print(f"✅ 自定义Skill: {s.name} ({len(s.steps)}步)")

    # 3. skillify
    s2 = skill_registry.skillify("越南专场", "越南站快速上架",
                                  ["booster", "lettuce", "bittergourd"])
    print(f"✅ skillify: {s2.name}")

    # 4. 列出带标签
    specific = skill_registry.list(tag="泰国")
    print(f"✅ 标签过滤: {len(specific)}个")

    # 5. 运行
    r = skill_registry.run("泰国专场")
    print(f"✅ 运行Skill: {r}")

    # 6. 统计
    stats = skill_registry.stats()
    print(f"\n📊 统计: {stats['total']}个, {stats['total_runs']}次运行")

    # 7. 删除
    skill_registry.delete("越南专场")
    print(f"✅ 删除后: {len(skill_registry)}个")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _test()
