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
| `build_exe.bat` | 需要单文件 exe 时再构建（要能联网装 PyInstaller） |
| `workspace/` | 生成物，已写进 `.gitignore`，不入库 |

## 生成实验空间

```bat
cd /d "D:\WorkSpaces\gpt-root\临时\Agent团队协作协议"
一键生成协作空间.bat
```

默认：目标 `./workspace`，协议 `./双Agent共享目录协作协议.md`，workspace 取本目录，协调者 `codex`、执行者 `executor-1`（可 `--coordinator/--worker/--workspace/--target` 覆盖）。

`workspace/` 不进版本库：克隆后跑一次上面的命令即可重建，也避免把 `D:/...` 这类本机绝对路径写进提交历史。

## 与正式版的关系

1. 改协议、加实验记录都在本目录，正式版保持不动。
2. 实验结论确认要采纳时，把差异手工合回 `2-Agent协议/Agent团队协作协议/`，并在那边留一条变更记录（改了什么、为什么、依据哪次实验）。
3. 怀疑副本过期时，用 `fc` 比对同名文件，或对比 sha256。

```bat
fc "D:\WorkSpaces\gpt-root\临时\Agent团队协作协议\双Agent共享目录协作协议.md" ^
   "D:\WorkSpaces\gpt-root\2-Agent协议\Agent团队协作协议\双Agent共享目录协作协议.md"
```

## 推 Git

本目录可以直接 `git init` 当独立仓库推走。`workspace/`、`_build/`、`.tmp/`、`__pycache__/`、`make-space.exe` 都已在 `.gitignore` 里，仓库里只留协议文本和生成器源码。
