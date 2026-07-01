---
name: commit-history-cleanup
description: Use when reorganizing git branch history into clear feature commits on a new worktree/branch without rewriting the original; handles fixups, commit sizing, docs, tests, and verification.
metadata:
  version: "v0.1"
---

# Commit 历史整理

把当前分支或用户指定范围的提交历史整理成清晰、独立、可审查的功能提交。必须在新 worktree 和新 branch 中操作，保留原始分支不变。

## 范围选择

- 用户指定范围时按用户范围执行，例如 `A..B`、`main..HEAD`、最近 N 个提交或明确列出的提交。
- 用户未指定时，整理当前 branch 相对 upstream 的全部提交；没有 upstream 时用 `origin/main`、`main`、`origin/master`、`master` 中能和当前分支形成 merge-base 的第一个作为 base。
- 如果无法可靠确定 base，先只问一个问题：要整理哪个提交范围。
- 若用户范围没有覆盖到当前 `HEAD`，默认在整理该范围后继续按原顺序重放范围之后的提交，使新 branch 的最终内容等价于原分支；用户明确只整理到范围终点时除外。

## 安全边界

- 不在原 worktree 或原 branch 上重写历史。
- 不 force-push、不删除原 branch、不删除原 worktree。
- 只在新建 worktree 内使用 `reset --hard`、`rebase`、`cherry-pick -n` 等会改写历史的命令。
- 新 branch 命名使用 `cleanup/<原分支名>-history`；已存在时追加日期或短 hash。
- 工作完成后保留新 worktree，告知用户新 branch 名和 worktree 路径。

## 工作流程

1. 记录当前状态：当前 branch、upstream、base、整理范围、原始 `HEAD`。
2. 在原仓库只读分析历史：
   - `git log --reverse --stat <range>`
   - `git log --reverse --name-status <range>`
   - `git show --stat --numstat <commit>`
   - 必要时查看 `git show <commit> -- <path>`
3. 先输出整理计划，除非用户明确要求“立即执行”“直接整理”或等价指令。计划至少包含：
   - 拟生成的每个目标提交标题和顺序
   - 每个目标提交包含哪些旧 commit、旧 commit 范围或未提交变更
   - 每个目标提交的主要内容、影响文件和风险
   - 预估纯代码增删行数；测试代码单独列出
   - 测试用例数量、测试文件数量或无法精确统计的原因
   - 文档增删行数和验证命令
4. 若用户未要求立即执行，输出计划后停止，等待用户确认或修改。
5. 用户认可计划后，创建新 worktree：

   ```bash
   git worktree add -b <new-branch> <worktree-path> <base>
   ```

6. 在新 worktree 中先把计划写成计划文档，再实施。默认路径为 `docs/history-cleanup-plan.md`；若项目规则说明 `docs/` 或内部文档不可提交，计划文档只作本地管理，不纳入目标提交。
7. 按计划文档做提交分组和历史重建。计划文档至少标出：
   - 有公开设计文档、测试规范、架构说明等指导文档时，指导文档放入第一个提交
   - 没有公开指导文档时，项目基础框架放入第一个提交
   - 每个功能提交包含的旧 commit
   - 后续 bugfix 合入哪个功能提交
   - 哪些旧 commit 只产生中间实现、反复改写或最终废弃的代码
   - 测试用例回填到哪个被测功能提交
   - 无法回填的测试用例是否需要倒数第二个集中提交
   - 用户文档和测试结果文档放入哪个位置
   - 可能过大或过小的提交风险
8. 在重建历史前识别项目的编译和测试命令，例如 `make`、`npm test`、`cargo test`、`pytest` 或项目文档指定命令。无法确定时先从 README、AGENTS.md、CI 配置和构建脚本中查找；仍无法确定则把这作为阻塞，不要声称整理完成。
9. 在新 worktree 中重建历史。优先使用 `git cherry-pick -n <commits>` 聚合相关旧提交，再按目标提交切分、暂存和提交。
10. 实施中发现计划不合理时，先更新计划文档，再继续实施；最终提交分组必须能从计划文档追溯。
11. 每生成一个目标提交后检查：
   - 该提交是否是相对独立的功能点
   - 是否混入无关 feature
   - 测试是否跟随被测试的功能
   - 提交消息是否说明意图和主要内容
   - 该提交自身是否已经包含通过编译和测试所需的全部文件
12. 全部提交完成后验证新 branch 最终内容等价于原范围目标：

   ```bash
   git diff --stat <original-target> <new-branch>
   git diff --exit-code <original-target> <new-branch>
   ```

13. 对新 branch 的每个目标提交逐个验证编译和测试。必须按提交顺序 checkout 后运行同一套项目编译和测试命令：

   ```bash
   for commit in $(git rev-list --reverse <base>..<new-branch>); do
     git checkout --detach "$commit"
     <build-command>
     <test-command>
   done
   git switch <new-branch>
   ```

   任一提交编译失败或测试失败时，把修复合回导致失败的目标提交并重新验证；不要把修复留在后续提交。

## 整理规则

- 每个目标提交都必须是可编译、可测试且测试通过的项目状态。
- 不允许出现“某个提交暂时编译失败，后续提交再修复”的历史；修复必须合并回第一个引入失败的提交。
- 指导文档提交、基础框架提交和测试结果文档提交也要通过项目定义的基础编译和测试；若项目对纯文档提交有明确轻量验证命令，使用该命令并记录依据。
- 反复修改同一片代码的提交合并到同一个目标提交。
- 反复被修改的代码不要在目标历史中呈现中间版本；直接在对应功能提交中使用最终有效版本。
- 后续被废弃、删除或替换的代码不要出现在整理后的提交记录中，除非最终 tree 仍需要其一部分；这种情况下只保留最终需要的部分。
- 某个 feature 的后续 bugfix 合入该 feature 提交，不保留“修一下”“follow-up”这类无效提交。
- 避免频繁几行的小提交；几行代码加上对应测试可以合入 feature 提交。
- 严禁纯代码超过 5000 行的提交。测试代码不计入这个大提交限制，但仍可用于判断提交是否过小。
- 约 2000 行代码加 5000 行测试不算超大提交；但如果代码本身超过 5000 行，必须继续拆分。
- 测试用例尽量回填到所测试代码产生的目标提交，除非依赖关系或项目规范使该提交无法独立通过。
- 因依赖关系无法回填的测试用例集中放入倒数第二个提交；该提交只处理这类测试补齐，不混入新功能。
- 有公开设计文档、测试规范、架构说明等指导文档时，全部整理到第一个提交，形成文档先行。
- 没有公开指导文档时，第一个提交必须是整个项目的基础框架，包含项目能够建立、启动、构建或执行基础验证所需的最小结构。
- 用户文档、使用说明、教程、README 面向用户的新增说明放在最后一个提交，除非用户明确要求跟随某个 feature。
- 测试结果文档若明确验证某个 feature，可跟随该 feature 或紧跟其后单独提交。
- 整体项目测试结果文档放在用户文档之前；若存在无法回填测试用例，可合入倒数第二个测试补齐提交。
- 文档不计入大提交限制。

## 输出要求

最终回复必须包含：

- 原始 branch 和原始目标 commit。
- 整理后的 branch 名和 worktree 路径。
- 提交映射摘要：目标提交对应哪些旧提交或旧提交范围。
- 逐 commit 结果：commit hash、内容摘要、旧 commit 映射、纯代码增删行数、测试用例/测试文件数量、测试代码行数、文档行数。
- 逐 commit 验证结果：编译命令、测试命令、是否通过；未验证时说明阻塞原因。
- 最终 tree diff 验证命令和结果。
- 无法运行编译或测试时的阻塞原因；这种情况下只能报告未完成，不能声称整理完成。

不要声称整理完成，除非新 branch 内容已和原始目标 tree 完全一致，或者明确说明用户要求的是部分范围且最终差异符合预期；同时每个目标提交都已逐个通过编译和测试。
