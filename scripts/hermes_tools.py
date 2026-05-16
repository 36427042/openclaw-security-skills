#!/usr/bin/env python3
"""
hermes_tools.py — 统一工具接口系统
从 Claude Code 的 buildTool() + Zod schema + Permission model 借鉴

每个工具遵守:
  input_schema  → 参数验证
  check_permissions → 权限检查
  call         → 执行逻辑
  is_concurrency_safe → 是否可并行
  is_readonly  → 是否只读
"""

import inspect
import json
import logging
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

logger = logging.getLogger("hermes_tools")


class PermissionLevel(Enum):
    """权限等级（从 Claude Code 借鉴）"""
    AUTO = "auto"          # 全自动，不需审批
    NOTIFY = "notify"      # 执行后通知
    CONFIRM = "confirm"    # 执行前需确认
    ESCALATE = "escalate"  # 需升级到土豆/天赐审批


class ToolResult:
    """工具执行结果"""
    def __init__(self, success: bool, data: Any = None, error: str = None):
        self.success = success
        self.data = data
        self.error = error

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
        }

    @classmethod
    def ok(cls, data: Any = None) -> "ToolResult":
        return cls(True, data)

    @classmethod
    def fail(cls, error: str) -> "ToolResult":
        return cls(False, error=error)

    def __repr__(self):
        if self.success:
            return f"ToolResult(✅ {self.data})"
        return f"ToolResult(❌ {self.error})"


@dataclass
class ToolDef:
    """工具定义（类比 Claude Code 的 buildTool()）"""
    name: str
    description: str
    input_schema: dict                         # JSON Schema 格式
    call_func: Callable                        # 实际执行函数
    permission_level: PermissionLevel = PermissionLevel.AUTO
    is_concurrency_safe: bool = True           # 是否可并行
    is_readonly: bool = False                  # 是否只读
    tags: List[str] = field(default_factory=list)
    partner: str = ""                          # 归属伙伴

    def validate_input(self, params: dict) -> Tuple[bool, str]:
        """简化的输入验证（类 Zod schema）"""
        for key, spec in self.input_schema.get("properties", {}).items():
            if key in params:
                val = params[key]
                val_type = spec.get("type", "string")
                # 类型检查
                type_map = {
                    "string": str, "integer": int, "number": (int, float),
                    "boolean": bool, "array": list, "object": dict,
                }
                expected = type_map.get(val_type)
                if expected and not isinstance(val, expected):
                    return False, f"参数 '{key}' 需要 {val_type} 类型, 收到 {type(val).__name__}"
                # 枚举检查
                if "enum" in spec and val not in spec["enum"]:
                    return False, f"参数 '{key}' 必须是 {spec['enum']} 之一, 收到 {val}"
            elif spec.get("required", False):
                return False, f"缺少必填参数: '{key}'"
        return True, ""

    def check_permissions(self, params: dict, context: dict = None) -> Tuple[bool, str]:
        """权限检查"""
        if self.permission_level == PermissionLevel.AUTO:
            return True, ""
        if self.permission_level == PermissionLevel.ESCALATE:
            return False, f"工具 '{self.name}' 需要升级审批"
        return True, ""

    def call(self, params: dict, context: dict = None) -> ToolResult:
        """执行工具"""
        # 1. 验证输入
        valid, msg = self.validate_input(params)
        if not valid:
            return ToolResult.fail(msg)

        # 2. 检查权限
        allowed, reason = self.check_permissions(params, context)
        if not allowed:
            return ToolResult.fail(f"权限拒绝: {reason}")

        # 3. 执行
        try:
            result = self.call_func(**params)
            return ToolResult.ok(result)
        except Exception as e:
            logger.error("工具 %s 执行失败: %s\n%s", self.name, e, traceback.format_exc())
            return ToolResult.fail(f"{e}")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "permission_level": self.permission_level.value,
            "is_concurrency_safe": self.is_concurrency_safe,
            "is_readonly": self.is_readonly,
            "tags": self.tags,
            "partner": self.partner,
        }


class ToolRegistry:
    """工具注册中心"""
    def __init__(self):
        self._tools: Dict[str, ToolDef] = {}

    def register(self, tool: ToolDef):
        """注册工具"""
        if tool.name in self._tools:
            logger.warning("工具 %s 已存在，将被覆盖", tool.name)
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolDef]:
        return self._tools.get(name)

    def list(self, partner: str = None, tag: str = None) -> List[ToolDef]:
        """列出工具，可按伙伴/标签过滤"""
        tools = list(self._tools.values())
        if partner:
            tools = [t for t in tools if t.partner == partner]
        if tag:
            tools = [t for t in tools if tag in t.tags]
        return tools

    def call(self, name: str, params: dict, context: dict = None) -> ToolResult:
        """调用工具"""
        tool = self.get(name)
        if not tool:
            return ToolResult.fail(f"未知工具: '{name}'")
        return tool.call(params, context)

    def to_dict(self) -> dict:
        return {name: tool.to_dict() for name, tool in self._tools.items()}

    def __len__(self):
        return len(self._tools)


# === 全局注册中心 ===
registry = ToolRegistry()


def build_tool(
    name: str,
    description: str,
    input_schema: dict,
    permission_level: str = "auto",
    is_concurrency_safe: bool = True,
    is_readonly: bool = False,
    tags: List[str] = None,
    partner: str = "",
):
    """
    装饰器: @build_tool(name="xxx", description="xxx", ...)
    类比 Claude Code 的 buildTool()
    """
    def decorator(func):
        tool = ToolDef(
            name=name,
            description=description,
            input_schema=input_schema,
            call_func=func,
            permission_level=PermissionLevel(permission_level),
            is_concurrency_safe=is_concurrency_safe,
            is_readonly=is_readonly,
            tags=tags or [],
            partner=partner,
        )
        registry.register(tool)
        return func
    return decorator


# === 测试 ===
def _test():
    @build_tool(
        name="booster_analyze",
        description="分析选品数据",
        input_schema={
            "properties": {
                "country": {"type": "string", "enum": ["TH", "MY", "VN", "PH", "SG"]},
                "limit": {"type": "integer"},
            },
            "required": ["country"],
        },
        permission_level="auto",
        partner="booster",
        tags=["选品"],
    )
    def analyze_products(country: str, limit: int = 10):
        return {"country": country, "products": [f"商品{i}" for i in range(limit)]}

    @build_tool(
        name="bittergourd_check",
        description="风控审核文案",
        input_schema={
            "properties": {
                "text": {"type": "string"},
                "language": {"type": "string", "enum": ["th", "zh", "en", "vi", "id"]},
            },
            "required": ["text"],
        },
        permission_level="notify",
        partner="bittergourd",
        tags=["风控"],
    )
    def check_text(text: str, language: str = "zh"):
        # 模拟违禁词检查
        banned = {"治疗": "风险"}
        hits = {k: banned[k] for k in banned if k in text}
        return {"safe": len(hits) == 0, "hits": hits, "total_words": len(text)}

    print(f"已注册 {len(registry)} 个工具")
    for name, t in registry.to_dict().items():
        print(f"  {name} ({t['partner']}): {t['description']}")
    print()

    # 测试调用
    r1 = registry.call("booster_analyze", {"country": "TH", "limit": 3})
    print(f"booster_analyze: {r1}")

    r2 = registry.call("bittergourd_check", {"text": "这款产品能治疗痘痘"})
    print(f"bittergourd_check: {r2}")

    r3 = registry.call("booster_analyze", {"country": "JP"})  # 枚举错误
    print(f"booster_analyze(错误): {r3}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _test()
