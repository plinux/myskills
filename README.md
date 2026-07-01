# My Skills

这个仓库用于版本化管理个人创建的 Agent Skills。

## Skills

| Skill | 用途 | 最新版本 |
| --- | --- | --- |
| `agent-md-lint` | 整理 AGENTS.md、CLAUDE.md 等项目级智能体提示文件，消除重复、冲突、歧义和冗长规则 | `v0.1` |
| `commit-history-cleanup` | 在新 worktree 和新 branch 中整理 Git 提交历史，合并无效反复修改并输出清晰的功能提交 | `v0.1` |
| `digsight-dxdcnet-protocol` | 解析、实现和调试动芯 Digsight DXDCNet V3.11 通讯协议帧、命令字和设备状态 | `v0.1` |
| `digsight-dxsd-sound` | 解析动芯 Digsight `.dxsd` 音效工程文件，提取功能键、Slot、声音、AUX、节点图和 CV 映射 | `v0.1` |
| `esu-loksound-esux` | 解析 ESU LokSound `.esux` 音效工程文件，提取 meta.xml 功能/AUX 映射、文件表和加密音频状态 | `v0.1` |

## 本地安装

安装到 Codex：

```bash
mkdir -p ~/.codex/skills
rsync -a --delete agent-md-lint/ ~/.codex/skills/agent-md-lint/
rsync -a --delete commit-history-cleanup/ ~/.codex/skills/commit-history-cleanup/
rsync -a --delete digsight-dxdcnet-protocol/ ~/.codex/skills/digsight-dxdcnet-protocol/
rsync -a --delete digsight-dxsd-sound/ ~/.codex/skills/digsight-dxsd-sound/
rsync -a --delete esu-loksound-esux/ ~/.codex/skills/esu-loksound-esux/
```

安装到 Claude Code：

```bash
mkdir -p ~/.claude/skills
rsync -a --delete agent-md-lint/ ~/.claude/skills/agent-md-lint/
rsync -a --delete commit-history-cleanup/ ~/.claude/skills/commit-history-cleanup/
rsync -a --delete digsight-dxdcnet-protocol/ ~/.claude/skills/digsight-dxdcnet-protocol/
rsync -a --delete digsight-dxsd-sound/ ~/.claude/skills/digsight-dxsd-sound/
rsync -a --delete esu-loksound-esux/ ~/.claude/skills/esu-loksound-esux/
```
