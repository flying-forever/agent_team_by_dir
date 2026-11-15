# 双 Agent 共享目录协作协议：附录

配套[正式协议](双Agent共享目录协作协议.md)，沿用原草案的示例与代码任务约定，不增加新机制。

## A. 任务示例

示例路径、标识及提交哈希应替换为实际值。

```json
{
  "protocol_version": 1,
  "id": "note-012",
  "attempt": 1,
  "created_at": "2026-11-11T15:00:00+08:00",
  "created_by": "codex",
  "assigned_to": "deepseek",
  "title": "检查笔记搜索功能",
  "workspace": "D:/项目/note-demo-review",
  "base_commit": "填写实际提交哈希",
  "instructions": "检查搜索逻辑，提供问题清单，不修改代码。",
  "context_files": ["README.md", "src/search.ts"],
  "acceptance": [
    "覆盖中文、空关键词、无结果三种情况",
    "每个问题包含复现步骤和代码位置"
  ],
  "allowed_actions": ["read_files", "run_tests"],
  "allowed_write_paths": ["artifacts/note-012/attempt-1/"],
  "result_dir": "artifacts/note-012/attempt-1/"
}
```

## B. 结果示例

仅展示格式，不代表实际执行或测试结果。

```json
{
  "task_id": "note-012",
  "attempt": 1,
  "worker_id": "deepseek-worker-1",
  "outcome": "completed",
  "summary": "完成搜索逻辑审查，发现两处待修复问题。",
  "report": "artifacts/note-012/attempt-1/report.md",
  "changed_files": [],
  "commits": [],
  "checks": [
    {"name": "中文关键词搜索", "result": "passed"},
    {"name": "空关键词行为", "result": "failed", "evidence": "详见报告复现步骤"}
  ],
  "limitations": [],
  "finished_at": "2026-11-11T15:10:00+08:00"
}
```

## C. 代码任务：隔离与整合

共享任务和结果，不建议多个 Agent 同时修改同一源码目录。

- 并行开发优先各用独立 Git 分支与 worktree，或各自 clone。
- 任务记录基线提交，交付记录实际提交哈希和改动文件。
- 协调者统一审查、合并并运行集成验证。
- worktree 不消除逻辑冲突；端口、数据库等运行资源也需分别配置。
- 只读审查可共用固定源码快照，审查期间避免源码变化。
- 验收整合后，确认无未提交内容，再清理工作目录和功能分支；执行者不得自行扩大清理范围。

## D. 原草案内容去向

- 原第 8 节代码隔离与整合移至本附录 C；任务和结果 JSON 移至附录 A、B。
- 原第 10 节小米笔记实验计划属于具体实施背景，保留于原草案，不纳入通用正式协议。
- 原岗位收集/BOSS 业务背景不纳入通用协议；省略该段不构成任何新的操作授权。
- 背景说明和重复提醒已压缩合并。优化备忘中的新验收格式、输入哈希基线、修订流程等暂未采纳。
