#!/usr/bin/env python3
"""
hermes_flags.py — Feature Flag 系统
允许动态开关系统特性，无需重启 Gateway

用法:
    from hermes_flags import flags

    # 检查特性是否启用
    if flags.is_on("video_pipeline"):
        run_video()

    # 开关特性
    flags.on("video_pipeline")
    flags.off("video_pipeline")

    # 带启用条件
    flags.when("risk_auto_confirm", condition=lambda: user_role == "苦瓜")
    # → condition返回False时自动返回off
"""

import json
import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Set

logger = logging.getLogger("hermes_flags")

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/data/flags")
os.makedirs(DATA_DIR, exist_ok=True)
FLAGS_PATH = os.path.join(DATA_DIR, "flags.json")


@dataclass
class FeatureFlag:
    """特性开关"""
    name: str
    enabled: bool = False
    category: str = "general"
    description: str = ""
    created_at: str = ""
    updated_at: str = ""
    updated_by: str = ""
    # 条件函数（仅在 flag 为 on 时额外检查）
    condition: Optional[Callable[[], bool]] = None
    # 依赖的 flag（需全部启用才有效）
    depends_on: List[str] = field(default_factory=list)

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def is_effective(self) -> bool:
        """检查 flag 是否有效（启用 + 条件满足 + 依赖链正常）"""
        if not self.enabled:
            return False
        if self.condition and not self.condition():
            return False
        return True

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "enabled": self.enabled,
            "category": self.category,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "updated_by": self.updated_by,
            "depends_on": self.depends_on,
        }
        # condition 不序列化（函数不可序列化）
        return d


class FlagManager:
    """Feature Flag 管理器"""

    DEFAULT_FLAGS: List[dict] = [
        # 核心特性
        {"name": "retry", "enabled": True, "category": "core",
         "description": "指数退避重试"},
        {"name": "tools_standard", "enabled": True, "category": "core",
         "description": "统一工具接口"},
        {"name": "tasks", "enabled": True, "category": "core",
         "description": "任务生命周期管理"},
        {"name": "messages", "enabled": True, "category": "core",
         "description": "伙伴间通信"},
        {"name": "skills", "enabled": True, "category": "core",
         "description": "Skill技能系统"},
        {"name": "perms", "enabled": True, "category": "core",
         "description": "权限分级系统"},
        {"name": "tokens", "enabled": True, "category": "core",
         "description": "Token消耗追踪"},
        {"name": "memory_extract", "enabled": True, "category": "core",
         "description": "记忆自动提取"},
        # 工作流特性
        {"name": "video_pipeline", "enabled": True, "category": "workflow",
         "description": "视频管线"},
        {"name": "market_check", "enabled": True, "category": "workflow",
         "description": "市场检查工作流"},
        {"name": "content_pipeline", "enabled": True, "category": "workflow",
         "description": "内容生产流水线"},
        {"name": "deerflow", "enabled": True, "category": "workflow",
         "description": "DeerFlow全链路"},
        # 实验性特性（默认关）
        {"name": "auto_routing", "enabled": False, "category": "experimental",
         "description": "伙伴间自动路由"},
        {"name": "memory_compaction", "enabled": False, "category": "experimental",
         "description": "记忆压缩"},
        {"name": "hermes_watch", "enabled": False, "category": "experimental",
         "description": "Hermes实时监控"},
    ]

    def __init__(self):
        self._lock = threading.Lock()
        self._flags: Dict[str, FeatureFlag] = {}
        self._callbacks: Dict[str, List[Callable[[bool], None]]] = {}
        self._load()

    # ── 开关操作 ──

    def on(self, name: str, by: str = "") -> bool:
        """启用 feature"""
        return self._set(name, True, by)

    def off(self, name: str, by: str = "") -> bool:
        """禁用 feature"""
        return self._set(name, False, by)

    def toggle(self, name: str) -> bool:
        """切换开关"""
        f = self._get(name)
        if not f:
            return False
        return self._set(name, not f.enabled, "toggle")

    def is_on(self, name: str) -> bool:
        """检查是否有效（开启 + 条件 + 依赖链）"""
        f = self._get(name)
        if not f:
            return "default_" + name not in self._flags
        return f.is_effective()

    def is_off(self, name: str) -> bool:
        """检查是否无效"""
        return not self.is_on(name)

    # ── 条件注册 ──

    def when(self, name: str, condition: Callable[[], bool],
             depends_on: List[str] = None):
        """注册启用条件（仅在 flag 为 on 时额外生效）"""
        f = self._get(name)
        if f:
            f.condition = condition
            if depends_on:
                f.depends_on = depends_on
            self._save()

    # ── 观察者 ──

    def on_change(self, name: str, callback: Callable[[bool], None]):
        """注册状态变化回调"""
        with self._lock:
            if name not in self._callbacks:
                self._callbacks[name] = []
            self._callbacks[name].append(callback)

    def _notify(self, name: str, new_state: bool):
        """通知回调"""
        with self._lock:
            cbs = list(self._callbacks.get(name, []))
        for cb in cbs:
            try:
                cb(new_state)
            except Exception as e:
                logger.warning("Flag回调异常 [%s]: %s", name, e)

    # ── 查询 ──

    def get(self, name: str) -> Optional[dict]:
        f = self._get(name)
        return f.to_dict() if f else None

    def list(self, category: str = "") -> List[dict]:
        flags = list(self._flags.values())
        if category:
            flags = [f for f in flags if f.category == category]
        return [f.to_dict() for f in sorted(flags, key=lambda x: x.name)]

    def stats(self) -> dict:
        flags = list(self._flags.values())
        enabled = [f for f in flags if f.enabled]
        return {
            "total": len(flags),
            "enabled": len(enabled),
            "disabled": len(flags) - len(enabled),
            "categories": {f.category for f in flags},
            "effective": sum(1 for f in flags if f.is_effective()),
        }

    # ── 内部 ──

    def _get(self, name: str) -> Optional[FeatureFlag]:
        with self._lock:
            return self._flags.get(name)

    def _set(self, name: str, value: bool, by: str) -> bool:
        f = self._get(name)
        if not f:
            logger.warning("Flag不存在: %s", name)
            return False
        old = f.enabled
        f.enabled = value
        f.updated_at = datetime.now(timezone.utc).isoformat()
        f.updated_by = by
        self._save()
        if old != value:
            self._notify(name, value)
            logger.info("🚩 %s → %s (by %s)", name, "ON" if value else "OFF", by or "?")
        return True

    def _save(self):
        try:
            with self._lock:
                data = [f.to_dict() for f in self._flags.values()]
            with open(FLAGS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("保存flags失败: %s", e)

    def _load(self):
        flags = {}
        # 尝试加载持久化数据
        if os.path.exists(FLAGS_PATH):
            try:
                with open(FLAGS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    f = FeatureFlag(**{k: v for k, v in item.items()
                                       if k in FeatureFlag.__dataclass_fields__})
                    flags[f.name] = f
            except Exception as e:
                logger.warning("加载flags失败: %s", e)

        # 补全缺失的默认flag
        for default in self.DEFAULT_FLAGS:
            name = default["name"]
            if name not in flags:
                flags[name] = FeatureFlag(**default)

        with self._lock:
            self._flags = flags
        logger.info("🚩 %d flags loaded (%d enabled)",
                    len(flags), sum(1 for f in flags.values() if f.enabled))


# ── 全局实例 ──
flags = FlagManager()


def _test():
    print("=== Feature Flag 系统测试 ===")

    s = flags.stats()
    print(f"✅ {s['total']} flags, {s['enabled']} ON, {s['disabled']} OFF")

    print(f"  retry:           {flags.is_on('retry')}")
    print(f"  video_pipeline:  {flags.is_on('video_pipeline')}")
    print(f"  auto_routing:    {flags.is_on('auto_routing')}")

    flags.off("video_pipeline")
    print(f"  ⛔ 关闭后: video_pipeline = {flags.is_on('video_pipeline')}")
    flags.on("video_pipeline")
    print(f"  ✅ 恢复后: video_pipeline = {flags.is_on('video_pipeline')}")

    print(f"  toggle: auto_routing → {flags.toggle('auto_routing')} → {flags.is_on('auto_routing')}")

    print("\n📋 按分类:")
    for cat in s["categories"]:
        flist = flags.list(category=cat)
        enabled = sum(1 for f in flist if f["enabled"])
        print(f"  {cat}: {len(flist)}个, {enabled}启用")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _test()
