# My Skills

这个仓库用于版本化管理个人创建的 Agent Skills。

## Skills

| Skill | 用途 | 最新版本 |
| --- | --- | --- |
| `agent-md-lint` | 整理 AGENTS.md、CLAUDE.md 等项目级智能体提示文件，消除重复、冲突、歧义和冗长规则 | `v0.1` |
| `commit-history-cleanup` | 在新 worktree 和新 branch 中整理 Git 提交历史，合并无效反复修改并输出清晰的功能提交 | `v0.1` |
| `digsight-dxdcnet-protocol` | 解析、实现和调试动芯 Digsight DXDCNet V3.11 通讯协议帧、命令字和设备状态 | `v0.1` |
| `digsight-dxsd-sound` | 解析动芯 Digsight `.dxsd` 音效工程文件，提取功能键、Slot、声音、AUX、节点图和 CV 映射 | `v0.1` |
| `esu-ecos-protocol` | 解析、实现和调试 ESU ECoS/ECoS2 控制器 TCP 文本协议、对象模型和 50200/50210/50220 兼容性 | `v0.1` |
| `esu-loksound-esux` | 解析 ESU LokSound `.esux` 音效工程文件，提取 meta.xml 功能/AUX 映射、文件表和加密音频状态 | `v0.1` |
| `init-project-agent-md` | 初始化项目级智能体提示文件和文档骨架，支持 Codex、Claude Code 或双文件模式 | `v0.1` |
| `mysql-gen-cnf` | 为 MySQL 5.6+ 功能测试生成最小配置，或为性能测试按版本、资源、连接数和安全策略生成 my.cnf | `v0.1` |
| `performance-testing` | 串行执行性能测试、环境预检、轻量观测采集、结果分析和 Markdown 报告留档 | `v0.1` |
| `rail-terminology-translation` | 进行轨道交通、铁路和城市轨道交通专业词汇中英互译、术语统一和译文审校 | `v0.1` |
| `train-model-dcc-protocol` | 解析、实现、审查和调试模型铁路 DCC 协议族，覆盖轨道协议、CV/编程、RailCom/DCC-A、Power Station Interface、decoder interface、SUSI/Train Bus 和标准来源核对 | `v0.1` |
| `z21-lan-protocol` | 解析、实现和调试 Roco/Fleischmann Z21/z21 LAN UDP 协议、X-BUS 隧道和控制器兼容性 | `v0.1` |
| `z21-layout-analyze` | 解析 Roco/Fleischmann Z21 `.z21` 文件，导出车辆、图片、功能表和轨道 Layout | `v0.1` |

## 本地安装

安装到 Codex：

```bash
mkdir -p ~/.codex/skills
rsync -a --delete agent-md-lint/ ~/.codex/skills/agent-md-lint/
rsync -a --delete commit-history-cleanup/ ~/.codex/skills/commit-history-cleanup/
rsync -a --delete digsight-dxdcnet-protocol/ ~/.codex/skills/digsight-dxdcnet-protocol/
rsync -a --delete digsight-dxsd-sound/ ~/.codex/skills/digsight-dxsd-sound/
rsync -a --delete esu-ecos-protocol/ ~/.codex/skills/esu-ecos-protocol/
rsync -a --delete esu-loksound-esux/ ~/.codex/skills/esu-loksound-esux/
rsync -a --delete init-project-agent-md/ ~/.codex/skills/init-project-agent-md/
rsync -a --delete mysql-gen-cnf/ ~/.codex/skills/mysql-gen-cnf/
rsync -a --delete performance-testing/ ~/.codex/skills/performance-testing/
rsync -a --delete rail-terminology-translation/ ~/.codex/skills/rail-terminology-translation/
rsync -a --delete train-model-dcc-protocol/ ~/.codex/skills/train-model-dcc-protocol/
rsync -a --delete z21-lan-protocol/ ~/.codex/skills/z21-lan-protocol/
rsync -a --delete z21-layout-analyze/ ~/.codex/skills/z21-layout-analyze/
```

安装到 Claude Code：

```bash
mkdir -p ~/.claude/skills
rsync -a --delete agent-md-lint/ ~/.claude/skills/agent-md-lint/
rsync -a --delete commit-history-cleanup/ ~/.claude/skills/commit-history-cleanup/
rsync -a --delete digsight-dxdcnet-protocol/ ~/.claude/skills/digsight-dxdcnet-protocol/
rsync -a --delete digsight-dxsd-sound/ ~/.claude/skills/digsight-dxsd-sound/
rsync -a --delete esu-ecos-protocol/ ~/.claude/skills/esu-ecos-protocol/
rsync -a --delete esu-loksound-esux/ ~/.claude/skills/esu-loksound-esux/
rsync -a --delete init-project-agent-md/ ~/.claude/skills/init-project-agent-md/
rsync -a --delete mysql-gen-cnf/ ~/.claude/skills/mysql-gen-cnf/
rsync -a --delete performance-testing/ ~/.claude/skills/performance-testing/
rsync -a --delete rail-terminology-translation/ ~/.claude/skills/rail-terminology-translation/
rsync -a --delete train-model-dcc-protocol/ ~/.claude/skills/train-model-dcc-protocol/
rsync -a --delete z21-lan-protocol/ ~/.claude/skills/z21-lan-protocol/
rsync -a --delete z21-layout-analyze/ ~/.claude/skills/z21-layout-analyze/
```
