# My Skills

这个仓库用于版本化管理个人创建的 Agent Skills。

## Skills

| Skill | 用途 | 最新版本 |
| --- | --- | --- |
| `agent-md-lint` | 整理 AGENTS.md、CLAUDE.md 等项目级智能体提示文件，消除重复、冲突、歧义和冗长规则 | `v0.1` |

## 本地安装

安装到 Codex：

```bash
mkdir -p ~/.codex/skills
rsync -a --delete agent-md-lint/ ~/.codex/skills/agent-md-lint/
```

安装到 Claude Code：

```bash
mkdir -p ~/.claude/skills
rsync -a --delete agent-md-lint/ ~/.claude/skills/agent-md-lint/
```
