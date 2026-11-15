# 协议实验版（独立仓库，自包含）

**正式版在 `2-Agent协议/Agent团队协作协议/`，不受本目录影响。本目录是独立的实验副本，可以随便改，改完再决定是否合回正式版。**

- 建立时间：2026-11-15（+08:00）
- 协议正文：拷贝自正式版，逐字节一致（sha256 校验过）
- 生成器：`make_space.py` / `一键生成协作空间.bat` / `build_exe.bat`，拷自正式版
- 与正式版生成器的**唯一差异**：`default_workspace()` 返回脚本所在目录（自包含），正式版则向上查找最外层含 `AGENTS.md` 的目录

## 目录内容

| 文件 | 用途 |
|---|---|
| `双Agent共享目录协作协议.md` | 协议正文（实验可改） |
| `双Agent共享目录协作协议_附录.md` | task.json / result.json 字段说明 |
| `Agent协作协议_优化与精简备忘.md` | 候选优化清单，尚未采纳 |
| `make_space.py` | 骨架生成器源码（Python 3.8+，仅标准库） |
| `一键生成协作空间.bat` | 双击生成 `workspace/`（优先 exe，没有就用 python） |
| `一键重置协作空间.bat` | 双击把 `workspace/` 还原成生成前（默认保留任务数据） |
| `build_exe.bat` | 需要单文件 exe 时再构建（要能联网装 PyInstaller） |
| `实验记录_发现与注册_20261115.md` | 名册机制的设计、单会话验证与未解决项 |
| `实验记录_发现与注册_20261116.md` | 两个独立会话并行实测：各自注册、互相发现、发布→领取→交付 |
| `workspace/` | 生成物，已写进 `.gitignore`，不入库 |

## 生成实验空间

```bat
cd /d "<克隆目录>"
一键生成协作空间.bat
```

默认：目标 `./workspace`，协议 `./双Agent共享目录协作协议.md`，workspace 取本目录，协调者 `lead`、执行者 `executor-1`（可 `--coordinator/--worker/--workspace/--target` 覆盖）。

`workspace/` 不进版本库：克隆后跑一次上面的命令即可重建，也避免把 `D:/...` 这类本机绝对路径写进提交历史。

## 命令速查

日常就这几条，双击 `.bat` 和命令行等价；`.bat` 里已经处理好 Python 探测与 TEMP 重定向。

| 想干什么 | 双击 | 命令行 |
|---|---|---|
| 生成协作区 | `一键生成协作空间.bat` | `python make_space.py` |
| 换协调者/执行者 id | — | `python make_space.py --coordinator codex --worker executor-1 --force` |
| 生成到别处 | — | `python make_space.py --target D:/x/collab` |
| 先看会写什么 | — | `python make_space.py --dry-run` |
| 重写骨架文档（不删任务） | `一键生成协作空间.bat --force` | `python make_space.py --force` |
| 重置（保留任务数据） | `一键重置协作空间.bat` | `python make_space.py --reset` |
| 彻底清空目录 | `一键重置协作空间.bat --purge --yes` | `python make_space.py --reset --purge --yes` |
| 构建 exe（发布用） | `build_exe.bat` | 见该脚本；构建机要 Python+联网，产物机不用 |

退出码：`0` 成功、`1` 参数或写入错误、`2` 目标路径不可用或安全校验没通过。

关于 exe：`build_exe.bat` 用 PyInstaller 把脚本打成一个 `make-space.exe`，**打包的机器必须有 Python 3.8+ 和网络**（PyInstaller 本身是 Python 包），打包后把 exe 拷到没装 Python 的机器上才不用解释器。

注意优先级：`一键生成协作空间.bat` 是"目录里有 `make-space.exe` 就用它，没有才跑 `.py`"。所以 exe 一旦存在就会**遮蔽脚本**——改了 `make_space.py` 必须重新打包，或者干脆删掉 exe，否则生成出来的是旧逻辑。当前仓库不带 exe（二进制不进 git，发布时挂 Release 附件更合适）。

## 重置（v1.2）

`--reset` 把协作区还原成生成前的样子，分两档：

| 档位 | 命令 | 删什么 | 留什么 |
|---|---|---|---|
| 保守（默认） | `--reset` | `AGENTS.md`、`protocol.md`、`templates/*.json`、各目录 `.gitkeep`、因此变空的目录；全空了连 `workspace/` 本身一起删 | `inbox/` 里没干完的任务、`artifacts/` 产物、`roster/` 名册、任何非空目录 |
| 彻底 | `--reset --purge --yes` | 整个目录 | 什么都不留 |

安全闸：目标不像协作区（没有 `AGENTS.md`/`protocol.md`/状态目录）时拒绝执行，确认要删得加 `--force`；`--purge` 不给 `--yes` 直接报错退出；目标为盘符根目录一律拒绝。`--dry-run` 可以先看清单，不写盘。

删除是**单向**的，重置前先把要留的东西挪走，或先跑一次 `--dry-run` 核对。

## v1.1：发现与注册（实验）

v1.1 之前，协议把参与者写死在 `protocol.md` 和入口说明里，隐含前提是"人按清单开会话"。两个各自开着的会话互不知情时，"按 `assigned_to` 领取"就没法成立。v1.1 补的是这一环：生成器多产出两样东西。

- `roster/`：参与者名册。每个 agent **只写自己一条** `roster/<id>.json`（临时文件 + 同卷重命名），干活时每 60 秒刷新 `updated_at`，退出写 `state` 为 `"left"`，不删文件。
- `templates/agent-card.json`：名册条目模板与字段说明。

在线判定：`state == "alive"` 且 `updated_at` 距今不超过 `ttl_seconds × 3`（默认 600 秒 × 3 = 30 分钟）。协调者发布任务前读名册，`assigned_to` 只填在线 id；执行者领取前也读一次。

**入场只需要两句话**：协作区根目录 + 你的 id（id 不在角色表里再加一句角色）。其余都在 `AGENTS.md`（第 0 节注册、第 0.1 节交接要求）和 `protocol.md` 里。已实测：只给这两项、不给任何操作步骤，一个新会话能自己读到文档、按第 0 节注册、正确判断"无任务则待命"。

**并行实测（2026-11-16）**：两个同时启动、互不可见的子会话分别拿到「根目录 + id」，从注册到交付跑完一轮约 2 分钟——协调者首次读名册就发现执行者在线并发布 `t-001`，执行者用 `mv -n` 领取、写心跳与产物、移入 `done/`。过程中暴露的 5 处文档歧义（名册 TTL 与任务心跳混淆、`workspace` 字段三重含义、`role` 枚举不一致、`allowed_write_paths` 与固定写入位置冲突、基线要求过严）已全部修掉，详见 `实验记录_发现与注册_20261116.md`。

**名册只提供"看得见"，不提供"叫得醒"**：本协议没有常驻轮询，被派活的执行者仍需要人或上层 agent 一条"去看 inbox"的消息才会动。要真唤醒，就把执行者作为协调者会话派生的子 agent，走原生消息通道。

设计与验证细节见 `实验记录_发现与注册_20261115.md`。

## 与正式版的关系

1. 改协议、加实验记录都在本目录，正式版保持不动。
2. 实验结论确认要采纳时，把差异手工合回 `2-Agent协议/Agent团队协作协议/`，并在那边留一条变更记录（改了什么、为什么、依据哪次实验）。
3. 本区已经改了协议正文两处小地方（v1.1 微调，未合回）：版本行加注 `protocol_version: 1` 与"实验版增补见各区 protocol.md"；第 2 节目录树补 `evidence/`、`roster/`、`templates/` 并注明是实验版扩展。
4. 怀疑副本过期时，用 `fc` 比对同名文件，或对比 sha256。

```bat
fc "<克隆目录>\双Agent共享目录协作协议.md" ^
   "<正式版目录>\双Agent共享目录协作协议.md"
```

## 推 Git

本目录可以直接 `git init` 当独立仓库推走。`workspace/`、`_build/`、`.tmp/`、`__pycache__/`、`make-space.exe` 都已在 `.gitignore` 里，仓库里只留协议文本和生成器源码。
