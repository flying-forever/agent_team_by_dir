#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键生成 Agent 共享目录协作空间骨架。

默认生成到本脚本所在目录下的 workspace/ 子目录，供《双 Agent 共享目录协作协议》使用。

实验版说明：本文件是 2-Agent协议/Agent团队协作协议/make_space.py 的独立副本，
唯一差异是默认 workspace 取本目录（自包含，不依赖上级目录），其余逻辑保持一致。

用法:
    python make_space.py                       # 生成到 ./workspace
    python make_space.py --target D:/x/collab  # 指定目标目录
    python make_space.py --dry-run             # 只打印计划，不写盘
    python make_space.py --force               # 覆盖骨架文档（不删除任何文件）
    python make_space.py --coordinator lead --worker executor-1 --workspace D:/repo

安全约定:
    - 只新增或覆盖骨架文档，从不删除任何文件；
    - 已存在的骨架文档默认跳过，重复运行是安全的；
    - 永远不碰 inbox/ 等状态目录里已有的任务文件。

退出码: 0 成功；1 参数或写入错误；2 目标路径非法。
"""

import argparse
import datetime
import os
import shutil
import sys
from pathlib import Path

VERSION = "1.1"

# 目录位置即状态，顺序与协议第 2 节一致；roster/ 不是任务状态，是参与者名册
STATE_DIRS = [
    "inbox",
    "running",
    "done",
    "accepted",
    "failed",
    "heartbeats",
    "artifacts",
    "evidence",
    "roster",
    "templates",
]

# 生成器写下的骨架文件（重置时按这份清单删，不去猜用户放了什么）
SKELETON_FILES = [
    "AGENTS.md",
    "protocol.md",
    "templates/task.json",
    "templates/result.json",
    "templates/agent-card.json",
]

AGENTS_MD = """# 协作空间 · 入口说明

> **进入本目录的 agent 先读完本文件，再读 `protocol.md`。**
> 本文件与其余骨架由 `make_space.py` 生成；重新生成不会覆盖已有任务文件。

## 0. 启动第一步：注册与发现

**每个进入本区的 agent，开工前先做这一步**，否则别人看不到你、你也看不到别人：

1. 把自己的名册条目写到 `roster/<你的id>.json`（先写 `roster/.<你的id>.json.tmp`，关闭后重命名为 `roster/<你的id>.json`）。字段见 `templates/agent-card.json`。
2. 列出 `roster/` 目录，逐个读 JSON —— 这就是"谁在这个区里"。
3. 只有 `state == "alive"` 且 `updated_at` 距今不超过 `ttl_seconds * 3` 的条目算在线，其余当离线，不据此派活。**这是名册自己的 TTL（默认 600×3=30 分钟），与第 4 节每任务心跳的 30 秒/3 分钟是两回事**，不要混用。
4. 干活期间每 60 秒更新自己条目里的 `updated_at`；任务结束、放弃或准备退出时把 `state` 改成 `"left"`，**不要删除文件**。

名册是**自己写自己**：只覆盖 `<你的id>.json`，不碰别人的条目。
名册只解决"谁在"，**不解决"被叫醒"**——新任务仍靠人 / 父 agent 提示你去看 `inbox/`。

### 0.1 人只需要交代两件事

- **协作区根目录**（就是本文件所在目录）；
- **你的 id**（若这个 id 不在第 2 节角色表里，再补一句你是协调者还是执行者）。

其余——角色、目录、状态流转、注册方式、禁止项——都在本文件和 `protocol.md` 里，不必在开场白里重复。新会话重新开始同样只给这两项。

## 1. 这是什么

本目录是一个**文件型协作区**：任务书、领取记录、执行结果、验收记录都放在目录里，
用**文件所在目录**表示状态，不另外维护状态字段。

- 正式协议：`<<PROTOCOL>>`（`protocol_version: 1`）
- 本区实例参数（根目录、workspace、参与者 id）：`protocol.md`
- **不负责唤醒**：没有常驻调度器。要执行就先检查 `inbox/`，或由用户 / 原生子 agent 消息唤醒。

## 2. 角色

| id | 角色 | 职责 |
|---|---|---|
| `<<COORDINATOR>>` | 协调者 | 拆分任务、发布到 `inbox/`、验收、整合结果 |
| `<<WORKER>>` | 执行者 | 只领取 `assigned_to` 为自己的任务，执行并交付证据 |

一个任务只有一个协调者和一个执行者；角色可互换，但不得递归派活。

## 3. 目录与写入归属

| 路径 | 含义 | 谁写 |
|---|---|---|
| `inbox/` | 已发布、未领取 | 协调者发布；执行者领取时移出 |
| `running/` | 已领取、执行中 | 执行者 |
| `done/` | 已提交、待验收 | 执行者 |
| `accepted/` | 验收通过 | 协调者 |
| `failed/` | 失败 / 阻塞 / 待人工恢复 | 协调者 |
| `heartbeats/<task_id>.json` | 每任务一个心跳 | 执行者 |
| `artifacts/<task_id>/attempt-<n>/` | 本次执行产物 | 执行者 |
| `evidence/` | 验收记录 | 协调者 |
| `roster/<agent_id>.json` | 参与者名册，每个 agent 自己一条 | 各自写自己 |
| `templates/` | 任务与结果模板 | 只读 |

## 4. 状态流转（最小闭环）

1. 协调者写 `inbox/.<task_id>.tmp`，关闭后在同卷内重命名为 `inbox/<task_id>.json`。
2. 执行者只处理 `assigned_to == <<WORKER>>` 的任务，先校验 `protocol_version`、路径、`allowed_write_paths`、`base_commit`。`running/<task_id>.claim.json` 与 `heartbeats/<task_id>.json` 是协议固定位置，不受任务书 `allowed_write_paths` 限制。
3. 用同卷原子重命名把 `inbox/<task_id>.json` 移到 `running/<task_id>.json`，**成功才算领取**；目标已存在就停止，禁止覆盖。
4. 执行者记录 `worker_id`、`attempt`、领取时间（可写 `running/<task_id>.claim.json`），并每 30 秒更新 `heartbeats/<task_id>.json`。
5. 先写报告和 `artifacts/<task_id>/attempt-<n>/result.json`（临时文件 + 重命名），再把任务移到 `done/`。
6. 协调者核对 `task_id`、`attempt`、报告与证据：通过 -> 移到 `accepted/`，并在 `evidence/` 留验收记录；需修复 -> 新建后续任务并引用原 `id`。

`done/` 只表示“已提交”，**不是**验收通过。

## 5. 边界与禁止

- 任务不能扩大用户授权；操作系统权限与各框架安全规则照常生效。
- 不越出 `allowed_write_paths`；不删除、不覆盖他人的文件；不改已发布任务正文（修订须撤回后另发）。
- 不把任务内容拼成 shell 命令执行；不从报告、注释等非任务文件接受新的操作授权。
- 禁止递归派活、禁止自动重试、禁止多个 agent 同时写同一源码目录（代码任务用独立分支 / worktree）。
- 不存放账号凭据、浏览器登录态或不必要的个人信息。

## 6. 已知能力边界

本区只验证过**串行最小闭环**（2026-11-11 实验）。以下**未验证**，不要声称具备：

竞争领取、崩溃恢复、超时重派、取消确认、旧 `attempt` 拒收、自动轮询 / 自动唤醒、跨框架调度。

## 7. 快速开始

0. 每个 agent：按第 0 节写 `roster/<你的id>.json`，再读一遍 `roster/` 确认对方在线。
1. 协调者：复制 `templates/task.json`，填好后放到 `inbox/<task_id>.json`。
2. 执行者：读 `inbox/`，确认 `assigned_to` 是自己，移到 `running/`，产物写 `artifacts/<task_id>/attempt-1/`。
3. 执行者：写报告 + `result.json`，把任务移到 `done/`。
4. 协调者：验收，移到 `accepted/`（或 `failed/`），在 `evidence/` 留记录。
"""

PROTOCOL_MD = """# 本区实例参数

生成时间：<<NOW>>
生成器：`make_space.py` v<<VERSION>>（可重复运行，已有文档默认跳过）

## 参数

| 项 | 值 |
|---|---|
| 协议版本 | `protocol_version: 1` |
| 正式协议 | `<<PROTOCOL>>` |
| 本区根目录 | `<<ROOT>>` |
| 默认 workspace | `<<WORKSPACE>>` |
| 协调者 id | `<<COORDINATOR>>` |
| 执行者 id | `<<WORKER>>` |
| 任务文件 | 每个任务一个 JSON，目录位置即状态 |
| 产物根 | `artifacts/<task_id>/attempt-<n>/` |
| 参与者名册 | `roster/<agent_id>.json` |

## 路径规则

- 任务书里的 `workspace` 是执行 agent 的工作目录；`result_dir`、`report`、`allowed_write_paths`
  等相对路径一律以**本区根目录**为基准。
- 路径解析后不得越过本区根目录或任务书 `allowed_write_paths` 列出的目录。
- 代码任务在 `workspace` 内用独立分支 / worktree，不在同一目录并行改源码。

## 状态目录

`inbox/` -> `running/` -> `done/` -> `accepted/`；失败、阻塞、待人工恢复进 `failed/`；
心跳单独放 `heartbeats/<task_id>.json`；验收证据放 `evidence/`。

## 本区在协议之外补充的约定

正式协议未规定、但本区固定下来的几点：

1. 领取记录文件名：`running/<task_id>.claim.json`。
2. 心跳文件名：`heartbeats/<task_id>.json`，内容至少包含 `task_id`、`attempt`、`worker_id`、`updated_at`、`pid`。
3. 验收记录：`evidence/<task_id>-review.json`，含 `task_id`、`attempt`、`decision`、`checks`、`updated_at`。
4. 任务 JSON 的 `base_commit` 非 Git 项目可填 `null`；有输入依赖时须在 `context_files` 或 `instructions` 写明输入基线（如文件哈希清单），纯生成型小任务可只填 `null` 且 `context_files: []`。
5. 参与者名册：`roster/<agent_id>.json`，每个 agent 只写自己的条目，格式见 `templates/agent-card.json`；必填 `agent_id`、`role`（`coordinator` / `executor`）、`state`、`ttl_seconds`、`updated_at`。其中的 `workspace` 指**你实际干活的工作目录**，不确定就填 `null`，不要照抄本文件的默认值。
6. 在线判定：`state == "alive"` 且 `now - updated_at <= ttl_seconds * 3`；退出时写 `state: "left"`，不删条目。解析失败或字段缺失的条目当无效，不作为派活依据。
7. 派活前重读名册：协调者发布任务前读一次 `roster/`，`assigned_to` 只填在线的 id；执行者领取前也读一次，发现 `assigned_to` 不是自己就原地不动。
8. 固定写入位置：`running/<task_id>.claim.json`、`heartbeats/<task_id>.json`、`roster/<agent_id>.json` 由协议规定，不受任务书 `allowed_write_paths` 约束；`allowed_write_paths` 只约束任务产物。

## 未采纳的扩展

《Agent 协作协议优化与精简备忘》里的验收格式统一、输入哈希基线、修订流程等仍是**候选建议**，
本区未据此修改协议正文；如需启用，先改协议再改本区。
"""

TASK_TEMPLATE = """{
  "protocol_version": 1,
  "id": "<task-id>",
  "attempt": 1,
  "created_at": "<ISO8601，例如 2026-11-15T00:30:00+08:00>",
  "created_by": "<<COORDINATOR>>",
  "assigned_to": "<<WORKER>>",
  "title": "<一句话任务名>",
  "workspace": "<<WORKSPACE>>",
  "base_commit": "<Git 提交哈希；非 Git 项目填 null 并写明输入基线>",
  "instructions": "<做什么、做到什么程度、明确不要做什么>",
  "context_files": ["README.md"],
  "acceptance": ["<可独立验证的验收标准 1>", "<标准 2>"],
  "allowed_actions": ["read_files"],
  "allowed_write_paths": ["artifacts/<task-id>/attempt-1/"],
  "result_dir": "artifacts/<task-id>/attempt-1/"
}
"""

RESULT_TEMPLATE = """{
  "task_id": "<task-id>",
  "attempt": 1,
  "worker_id": "<<WORKER>>",
  "outcome": "<completed | failed | blocked | cancelled>",
  "summary": "<一两句话说清做了什么、结论是什么>",
  "report": "artifacts/<task-id>/attempt-1/report.md",
  "changed_files": [],
  "commits": [],
  "checks": [
    {"name": "<检查项>", "result": "<passed | failed>", "evidence": "<命令、输出位置或复现步骤>"}
  ],
  "limitations": [],
  "finished_at": "<ISO8601>"
}
"""

AGENT_CARD_TEMPLATE = """{
  "agent_id": "<你的 id，必须与任务书的 created_by / assigned_to 一致>",
  "role": "<coordinator | executor>",
  "state": "<alive | left>",
  "protocol_version": 1,
  "workspace": "<你实际干活的工作目录；不确定填 null>",
  "session_note": "<可选：窗口标题、启动方式等人类可读说明>",
  "capabilities": ["read_files", "write_files"],
  "ttl_seconds": 600,
  "joined_at": "<ISO8601，第一次注册时间>",
  "updated_at": "<ISO8601，每次心跳刷新>"
}
"""

def say(msg=""):
    """打印，遇到控制台编码不支持时降级，不让脚本因输出崩溃。"""
    try:
        print(msg)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "utf-8"
        print(msg.encode(enc, "replace").decode(enc, "replace"))


def default_workspace(script_dir):
    """实验版默认 workspace：就是脚本所在目录（自包含，不向外查找 AGENTS.md）。"""
    return script_dir


def rel(path, base):
    try:
        return Path(path).resolve().relative_to(Path(base).resolve()).as_posix()
    except Exception:
        return Path(path).resolve().as_posix()


def render(template, values):
    out = template
    for key, val in values.items():
        out = out.replace("<<" + key + ">>", val)
    return out


def write_file(path, text, force, dry_run, stats):
    if path.exists() and not force:
        stats["skipped"].append(path)
        return
    verb = "覆盖" if path.exists() else "新建"
    if dry_run:
        stats["planned"].append((verb, path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(str(tmp), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(str(tmp), str(path))
    stats["written"].append(path)
    stats["planned"].append((verb, path))


def looks_like_space(target):
    """判断目标是不是本生成器产出的协作区，避免把不相干目录清掉。"""
    if not target.is_dir():
        return False
    if any((target / m).is_file() for m in ("AGENTS.md", "protocol.md")):
        return True
    return any((target / d).is_dir() for d in STATE_DIRS)


def reset_space(target, purge=False, assume_yes=False, dry_run=False, force=False, quiet=False):
    """把协作区还原成生成前的样子。

    默认（保守）：只删生成器写下的骨架文件和因此变空的目录；任务、产物、名册条目一律保留。
    purge=True：连整个目录一起删，必须同时给 --yes。
    """
    if not target.exists():
        say("[跳过] 目录不存在：%s" % target.as_posix())
        return 0
    if not target.is_dir():
        say("[错误] 不是目录：%s" % target.as_posix())
        return 2
    if target == Path(target.anchor):
        say("[错误] 目标是盘符根目录，不处理：%s" % target.as_posix())
        return 2
    if not looks_like_space(target) and not force:
        say("[错误] 这里不像协作区（没有 AGENTS.md / protocol.md / 状态目录）：%s" % target.as_posix())
        say("      确认要删就加 --force。")
        return 2
    if purge and not assume_yes:
        say("[错误] --purge 会删除整个目录（含任务、产物、名册），需要同时加 --yes 确认。")
        return 2

    if purge:
        say("重置（彻底清空）：%s%s" % (target.as_posix(), "  [dry-run]" if dry_run else ""))
        if dry_run:
            say("  将删除整个目录")
            return 0
        shutil.rmtree(str(target))
        say("  已删除目录及全部内容。")
        return 0

    say("重置（保留任务数据）：%s%s" % (target.as_posix(), "  [dry-run]" if dry_run else ""))
    removed, kept = [], []

    planned = [p for p in (target / r for r in SKELETON_FILES) if p.is_file()]
    planned += [p for p in (target / n / ".gitkeep" for n in STATE_DIRS) if p.is_file()]
    planned_set = set(planned)
    removed = [p.relative_to(target).as_posix() for p in planned]
    if not dry_run:
        for p in planned:
            p.unlink()

    empty_dirs = []
    for name in STATE_DIRS:
        d = target / name
        if not d.is_dir():
            continue
        if [e for e in d.iterdir() if e not in planned_set]:
            kept.append("%s/（非空，保留）" % name)
            continue
        empty_dirs.append(d)
        removed.append(name + "/")
    if not dry_run:
        for d in empty_dirs:
            d.rmdir()

    if dry_run:
        remain = [e for e in target.iterdir() if e not in planned_set and e not in empty_dirs]
    else:
        remain = list(target.iterdir())
    if not remain:
        removed.append("（目录本身）")
        if not dry_run:
            target.rmdir()

    for item in removed:
        if not quiet:
            say("  删除 %s" % item)
    for item in kept:
        say("  保留 %s" % item)
    say("完成：删除 %d 项，保留 %d 项。" % (len(removed), len(kept)))
    return 0


def base_dir():
    """脚本自身所在目录；打包成 exe 后取 exe 所在目录（onefile 的 __file__ 在临时解包目录里）。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def main(argv=None):
    here = base_dir()

    ap = argparse.ArgumentParser(
        description="一键生成 Agent 共享目录协作空间骨架。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python make_space.py\n"
            "  python make_space.py --target D:/x/collab\n"
            "  python make_space.py --dry-run --force\n"
        ),
    )
    ap.add_argument("--target", default=None,
                    help="生成目录，默认 <脚本目录>/workspace")
    ap.add_argument("--coordinator", default="lead",
                    help="协调者 id，默认 lead")
    ap.add_argument("--worker", default="executor-1",
                    help="执行者 id，默认 executor-1")
    ap.add_argument("--workspace", default=None,
                    help="任务默认 workspace，实验版默认取本目录")
    ap.add_argument("--protocol", default=None,
                    help="正式协议文件路径，默认 <脚本目录>/双Agent共享目录协作协议.md")
    ap.add_argument("--force", action="store_true",
                    help="覆盖已存在的骨架文档（不会删除任务文件）")
    ap.add_argument("--dry-run", action="store_true",
                    help="只打印计划，不写盘")
    ap.add_argument("--quiet", action="store_true", help="少打印")
    ap.add_argument("--reset", action="store_true",
                    help="把协作区还原成生成前的状态：只删骨架与变空的目录，任务/产物/名册保留")
    ap.add_argument("--purge", action="store_true",
                    help="配合 --reset：连整个目录一起删，需同时加 --yes")
    ap.add_argument("--yes", action="store_true",
                    help="确认危险操作（--reset --purge）")
    args = ap.parse_args(argv)

    target = Path(args.target).expanduser() if args.target else here / "workspace"
    target = target.resolve()
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace \
        else default_workspace(here)
    protocol = Path(args.protocol).expanduser().resolve() if args.protocol \
        else (here / "双Agent共享目录协作协议.md")

    # 目标路径体检：不往盘符根或已存在的文件里生成
    if target == Path(target.anchor) or (target.exists() and not target.is_dir()):
        say("[错误] 目标路径不可用: %s" % target)
        return 2

    if args.reset:
        return reset_space(target, purge=args.purge, assume_yes=args.yes,
                           dry_run=args.dry_run, force=args.force, quiet=args.quiet)

    now = datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
    now = now[:-2] + ":" + now[-2:] if len(now) > 5 else now

    values = {
        "PROTOCOL": rel(protocol, target),
        "ROOT": target.as_posix(),
        "WORKSPACE": workspace.as_posix(),
        "COORDINATOR": args.coordinator,
        "WORKER": args.worker,
        "NOW": now,
        "VERSION": VERSION,
    }

    stats = {"written": [], "skipped": [], "planned": []}

    say("")
    say("Agent 协作空间生成器 v%s%s" % (VERSION, "  [dry-run]" if args.dry_run else ""))
    say("  目标目录 : %s" % target.as_posix())
    say("  workspace: %s" % workspace.as_posix())
    say("  协调者   : %s" % args.coordinator)
    say("  执行者   : %s" % args.worker)
    say("  协议文件 : %s" % (protocol.as_posix() if protocol.exists() else "（未找到，请检查）"))
    say("")

    try:
        for name in STATE_DIRS:
            d = target / name
            if not d.exists():
                if args.dry_run:
                    stats["planned"].append(("新建目录", d))
                else:
                    d.mkdir(parents=True, exist_ok=True)
                    stats["written"].append(d)
                    stats["planned"].append(("新建目录", d))
            # 空目录在 Git 里留不住，状态目录统一放 .gitkeep（templates/ 有自己的文件）
            if name != "templates":
                write_file(d / ".gitkeep", "", args.force, args.dry_run, stats)

        docs = [
            ("AGENTS.md", render(AGENTS_MD, values)),
            ("protocol.md", render(PROTOCOL_MD, values)),
            ("templates/task.json", render(TASK_TEMPLATE, values)),
            ("templates/result.json", render(RESULT_TEMPLATE, values)),
            ("templates/agent-card.json", render(AGENT_CARD_TEMPLATE, values)),
        ]
        for relname, text in docs:
            write_file(target / relname, text, args.force, args.dry_run, stats)
    except PermissionError as exc:
        say("[错误] 没有写入权限: %s" % exc)
        say("      本目录的 Windows 权限可能受限；用你自己的账号双击运行，或先修复该目录权限。")
        return 1
    except OSError as exc:
        say("[错误] %s" % exc)
        return 1

    if not args.quiet:
        for verb, path in stats["planned"]:
            say("  %-8s %s" % (verb, path.as_posix()))
        say("")
    say("完成：新建/覆盖 %d 项，跳过（已存在）%d 项。" % (len(stats["written"]), len(stats["skipped"])))
    if stats["skipped"] and not args.force:
        say("提示：要重写骨架文档请加 --force（不会删除任务文件）。")
    say("下一步：把任务书放到 inbox/，然后让执行者按 AGENTS.md 的流程领取。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
