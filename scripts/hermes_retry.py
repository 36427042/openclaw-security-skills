#!/usr/bin/env python3
"""
hermes_retry.py — 统一指数退避重试工具
从 Claude Code QueryEngine 的 retry logic 借鉴

用法:
    from hermes_retry import retry, RetryConfig

    @retry(max_attempts=3, base_delay=1.0)
    def call_api(): ...

    # 或者直接调用
    result = await retry_call(func, max_attempts=3, base_delay=1.0)
"""

import asyncio
import functools
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, TypeVar, Union

logger = logging.getLogger("hermes_retry")

T = TypeVar("T")


@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3              # 最大尝试次数（含首次）
    base_delay: float = 1.0            # 基础延迟（秒）
    max_delay: float = 60.0            # 最大延迟（秒）
    jitter: bool = True                # 是否加随机抖动
    backoff_factor: float = 2.0        # 退避因子
    retryable_exceptions: tuple = (    # 可重试的异常类型
        ConnectionError,
        TimeoutError,
        OSError,
    )
    on_retry: Optional[Callable] = None  # 每次重试前的回调


class MaxRetriesError(Exception):
    """超过最大重试次数"""
    pass


async def retry_call(
    func: Callable[..., T],
    *args,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple = None,
    config: Optional[RetryConfig] = None,
    **kwargs,
) -> T:
    """
    异步函数重试包装
    用法: result = await retry_call(my_func, arg1, max_attempts=3)
           result = await retry_call(my_func, arg1, config=cfg)
    """
    if config:
        cfg = config
    else:
        cfg = RetryConfig(
            max_attempts=max_attempts,
            base_delay=base_delay,
            max_delay=max_delay,
            jitter=jitter,
            backoff_factor=backoff_factor,
            retryable_exceptions=retryable_exceptions or (ConnectionError, TimeoutError, OSError),
        )
    last_exc = None

    for attempt in range(1, cfg.max_attempts + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)
        except cfg.retryable_exceptions as e:
            last_exc = e
            if attempt >= cfg.max_attempts:
                raise MaxRetriesError(
                    f"函数 {func.__name__} 在 {cfg.max_attempts} 次尝试后仍失败: {e}"
                ) from e

            delay = _calc_delay(attempt, cfg)
            logger.warning(
                "重试 %s (第%d/%d次), 等待 %.1fs: %s",
                func.__name__, attempt, cfg.max_attempts, delay, e,
            )
            if cfg.on_retry:
                cfg.on_retry(attempt, delay, e)
            await asyncio.sleep(delay)

    raise MaxRetriesError(f"未知错误: {last_exc}")


def retry(
    func=None,
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple = None,
):
    """
    装饰器用法:
        @retry(max_attempts=3, base_delay=1.0)
        async def fetch_data(): ...
    """
    if retryable_exceptions is None:
        retryable_exceptions = (ConnectionError, TimeoutError, OSError)

    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        jitter=jitter,
        backoff_factor=backoff_factor,
        retryable_exceptions=retryable_exceptions,
    )

    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            return await retry_call(fn, *args, config=config, **kwargs)

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            return _sync_retry(fn, *args, config=config, **kwargs)

        if asyncio.iscoroutinefunction(fn):
            return wrapper
        return sync_wrapper

    if func is not None:
        return decorator(func)
    return decorator


def _calc_delay(attempt: int, cfg: RetryConfig) -> float:
    """计算退避延时: base * factor^(attempt-1) + jitter"""
    delay = min(cfg.base_delay * (cfg.backoff_factor ** (attempt - 1)), cfg.max_delay)
    if cfg.jitter:
        delay += random.uniform(0, delay * 0.5)
    return delay


def _sync_retry(
    func, *args,
    max_attempts=3, base_delay=1.0, max_delay=60.0,
    jitter=True, backoff_factor=2.0, retryable_exceptions=None,
    config=None, **kwargs,
):
    """同步重试（同步函数用）"""
    if config:
        cfg = config
    else:
        cfg = RetryConfig(
            max_attempts=max_attempts, base_delay=base_delay,
            max_delay=max_delay, jitter=jitter,
            backoff_factor=backoff_factor,
            retryable_exceptions=retryable_exceptions or (ConnectionError, TimeoutError, OSError),
        )
    last_exc = None
    for attempt in range(1, cfg.max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except cfg.retryable_exceptions as e:
            last_exc = e
            if attempt >= cfg.max_attempts:
                raise MaxRetriesError(
                    f"函数 {func.__name__} 在 {cfg.max_attempts} 次尝试后仍失败: {e}"
                ) from e
            delay = _calc_delay(attempt, cfg)
            logger.warning("重试 %s (第%d/%d次), 等待 %.1fs", func.__name__, attempt, cfg.max_attempts, delay)
            time.sleep(delay)
    raise MaxRetriesError(f"未知错误: {last_exc}")


# === 便捷包装器 ===
async def retry_video_api(func, *args, **kwargs):
    """视频API专用重试：3次+1s基础延迟，最长60s"""
    cfg = RetryConfig(max_attempts=3, base_delay=1.0, max_delay=30.0)
    return await retry_call(func, *args, config=cfg, **kwargs)


async def retry_http_call(func, *args, **kwargs):
    """HTTP API专用重试：3次+1s基础延迟"""
    cfg = RetryConfig(max_attempts=3, base_delay=1.0, max_delay=10.0)
    return await retry_call(func, *args, config=cfg, **kwargs)


async def retry_feishu_push(func, *args, **kwargs):
    """飞书推送专用重试：5次+0.5s基础延迟"""
    cfg = RetryConfig(max_attempts=5, base_delay=0.5, max_delay=5.0)
    return await retry_call(func, *args, config=cfg, **kwargs)


# === 测试 ===
async def _test():
    """临时测试"""
    call_count = 0

    async def flaky_api():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TimeoutError(f"第{call_count}次超时")
        return {"status": "ok", "attempts": call_count}

    result = await retry_call(flaky_api, max_attempts=5, base_delay=0.1)
    print(f"✅ 测试通过: {result} (调用{call_count}次)")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_test())
