#!/usr/bin/env python3
"""
hermes_tasks.py — 任务生命周期管理
从 Claude Code 的 Task System 借鉴 (TaskCreateTool / TaskGetTool / etc.)

任务生命周期: pending → running → completed | failed | cancelled
"""

import asyncio
import json
import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("hermes_tasks")


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """任务实体"""
    id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    partner: str = ""
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    result: Any = None
    error: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "partner": self.partner,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
            "duration_s": self.duration_seconds,
        }

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at)
            return (end - start).total_seconds()
        return None


class TaskManager:
    """任务管理器（类比 Claude Code 的 TaskCreateTool → TaskGetTool）"""

    def __init__(self, data_dir: str = None):
        self._tasks: Dict[str, Task] = {}
        self._lock = threading.Lock()
        self._data_dir = data_dir or os.path.expanduser(
            "~/.openclaw/workspace/data/tasks"
        )
        os.makedirs(self._data_dir, exist_ok=True)

    # === 任务 CRUD ===

    def create(
        self,
        name: str,
        partner: str = "",
        metadata: dict = None,
    ) -> Task:
        """创建任务 → pending"""
        task = Task(
            id=str(uuid.uuid4())[:12],
            name=name,
            partner=partner,
            metadata=metadata or {},
        )
        with self._lock:
            self._tasks[task.id] = task
        self._save(task)
        logger.info("任务创建: %s (%s)", task.id, task.name)
        return task

    def start(self, task_id: str):
        """开始执行 → running"""
        task = self._get(task_id)
        if not task:
            return None
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc).isoformat()
        self._save(task)
        return task

    def complete(self, task_id: str, result: Any = None):
        """完成 → completed"""
        task = self._get(task_id)
        if not task:
            return None
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc).isoformat()
        task.result = result
        self._save(task)
        return task

    def fail(self, task_id: str, error: str):
        """失败 → failed"""
        task = self._get(task_id)
        if not task:
            return None
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.now(timezone.utc).isoformat()
        task.error = error
        self._save(task)
        return task

    def cancel(self, task_id: str):
        """取消 → cancelled"""
        task = self._get(task_id)
        if not task:
            return None
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now(timezone.utc).isoformat()
        self._save(task)
        return task

    def get(self, task_id: str) -> Optional[dict]:
        """获取任务详情"""
        task = self._get(task_id)
        return task.to_dict() if task else None

    def list(
        self,
        status: TaskStatus = None,
        partner: str = None,
        limit: int = 50,
    ) -> List[dict]:
        """列出任务"""
        with self._lock:
            tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        if partner:
            tasks = [t for t in tasks if t.partner == partner]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return [t.to_dict() for t in tasks[:limit]]

    def output(self, task_id: str) -> Optional[Any]:
        """获取任务输出"""
        task = self._get(task_id)
        if not task:
            return None
        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            return task.result if task.status == TaskStatus.COMPLETED else {"error": task.error}
        return None

    def stop(self, task_id: str):
        """停止任务"""
        return self.cancel(task_id)

    # === 内部方法 ===

    def _get(self, task_id: str) -> Optional[Task]:
        with self._lock:
            return self._tasks.get(task_id)

    def _save(self, task: Task):
        """持久化到文件"""
        try:
            path = os.path.join(self._data_dir, f"{task.id}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(task.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("保存任务失败: %s", e)

    def _load(self):
        """从文件加载历史任务"""
        if not os.path.isdir(self._data_dir):
            return
        for fn in os.listdir(self._data_dir):
            if not fn.endswith(".json"):
                continue
            try:
                path = os.path.join(self._data_dir, fn)
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                task = Task(
                    id=data["id"],
                    name=data["name"],
                    status=TaskStatus(data["status"]),
                    partner=data.get("partner", ""),
                    created_at=data.get("created_at", ""),
                    started_at=data.get("started_at", ""),
                    completed_at=data.get("completed_at", ""),
                    result=data.get("result"),
                    error=data.get("error", ""),
                    metadata=data.get("metadata", {}),
                )
                with self._lock:
                    self._tasks[task.id] = task
            except Exception as e:
                logger.warning("加载任务文件失败 %s: %s", fn, e)

    def __len__(self):
        with self._lock:
            return len(self._tasks)


class TaskRunner:
    """
    任务执行器: create → start → run → complete/fail
    同步包装 sessions_spawn 等异步操作
    """

    def __init__(self, manager: TaskManager):
        self.manager = manager

    def run_sync(
        self,
        name: str,
        func: Callable,
        partner: str = "",
        metadata: dict = None,
        *args,
        **kwargs,
    ) -> dict:
        """同步执行并跟踪"""
        task = self.manager.create(name, partner, metadata)
        try:
            self.manager.start(task.id)
            result = func(*args, **kwargs)
            self.manager.complete(task.id, result)
        except Exception as e:
            self.manager.fail(task.id, str(e))
            raise
        return self.manager.get(task.id)

    async def run_async(
        self,
        name: str,
        func: Callable,
        partner: str = "",
        metadata: dict = None,
        *args,
        **kwargs,
    ) -> dict:
        """异步执行并跟踪"""
        task = self.manager.create(name, partner, metadata)
        try:
            self.manager.start(task.id)
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            self.manager.complete(task.id, result)
        except Exception as e:
            self.manager.fail(task.id, str(e))
            raise
        return self.manager.get(task.id)


# === 全局实例 ===
task_manager = TaskManager()
task_runner = TaskRunner(task_manager)
task_manager._load()


# === 测试 ===
def _test():
    def dummy_work(n: int):
        time.sleep(0.1)
        return {"processed": n}

    # 同步
    result = task_runner.run_sync("test_task", dummy_work, "booster", {"n": 42}, n=42)
    task_id = result["id"]
    print(f"✅ 同步任务: {result['name']} → {result['status']} ({result['duration_s']}s)")

    # 查询
    detail = task_manager.get(task_id)
    print(f"✅ 查询任务: {detail['id']}")

    # 列表
    all_tasks = task_manager.list()
    print(f"✅ 列出任务: {len(all_tasks)} 个")

    # 历史加载
    print(f"✅ 内存中总任务数: {len(task_manager)} (含历史)")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _test()
