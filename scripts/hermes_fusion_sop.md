# Hermes 融合工作流 SOP

> 所有伙伴执行任务时，必须按照此流程操作。  
> 来源: `scripts/hermes_coding.py` + `scripts/hermes_tasks.py` + ...  
> 版本: v1.0 · 2026-05-09

---

## 执行前（1 分钟）

```
① flag check <特性>           # 确认该特性是否启用
   例：flag check video_pipeline
   如果 OFF→ 先 flag on <特性> 再继续

② task create "<任务名>"      # 注册任务生命周期
   例：task create "泰国美白仪视频制作"
```

## 执行中

```
③ 所有API调用 → hermes_retry   # 自动重试
   from hermes_retry import retry_call
   或用装饰器: @retry()

④ 调其他伙伴 → hermes_messages # 走消息队列，不私下发
   messenger.send("玉米", "来跑美白仪视频")

⑤ 分不清该找谁 → hermes_routing # 自动路由
   router.route("搞个泰国上架")
```

## 执行后（1 分钟）

```
⑥ task complete/stop           # 关闭任务
⑦ watch ok/info                # 记录事件
   watcher.ok("task", "name", "完成")

⑧ compact analyze <自己>       # 检查记忆是否膨胀
   如果重复>5条 → compact run --apply <自己>
```

---

## 完整示例

```python
# 伙伴执行任务的标准流程

from hermes_retry import retry_call
from hermes_watch import watcher
from hermes_tasks import task_manager
from hermes_flags import flags

# 1. 检查Flag
if not flags.is_on("video_pipeline"):
    watcher.warn("task", "flag_disabled", "video_pipeline被关")

# 2. 创建任务
tid = task_manager.create("泰国美白仪视频", "video")
task_manager.start(tid)

try:
    # 3. 带重试的执行
    result = retry_call(my_api_function, attempts=3)
    
    # 4. 记录成功
    task_manager.complete(tid, {"result": result})
    watcher.ok("task", "video_done", "视频生成完成")

except Exception as e:
    # 5. 记录失败
    task_manager.fail(tid, str(e))
    watcher.err("task", "video_failed", str(e))
```

---

## 13 模块速查表

| 模块 | 文件 | 什么时候用 |
|:----|:----|:----------|
| retry | hermes_retry.py | 任何API调用+网络请求 |
| tools | hermes_tools.py | 注册/调用标准工具时 |
| tasks | hermes_tasks.py | 每个任务开始/结束 |
| messages | hermes_messages.py | 跨伙伴协作时 |
| skills | hermes_skills.py | 跑预注册工作流时 |
| perms | hermes_perms.py | 检查自己有没有权限 |
| tokens | hermes_tokens.py | 每月监控API费用 |
| memory | hermes_memory_extract.py | 学到新知识时自动存 |
| flags | hermes_flags.py | 执行前先检查开关 |
| routing | hermes_routing.py | 不知道任务该给谁时 |
| watch | hermes_watch.py | 每个操作都记录事件 |
| compact | hermes_compact.py | 每天收工前压缩记忆 |
| coding | hermes_coding.py | 改完代码跑self-review |
