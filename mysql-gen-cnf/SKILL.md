---
name: mysql-gen-cnf
description: Use when generating MySQL 5.6+ test my.cnf for functional or resource-aware performance tests, with version-aware parameters, concurrency sizing, durability, and data directory selection.
metadata:
  version: "v0.1"
---

# MySQL 测试配置初始化

为当前测试机器生成 MySQL `my.cnf`，支持功能测试和性能测试两种场景。优先使用本 Skill 附带脚本 `scripts/render_mysql_test_config.py` 生成配置和摘要。运行脚本前先定位 Skill 目录：Claude Code 可用 `${CLAUDE_SKILL_DIR}`，Codex 使用当前读取到的 `SKILL.md` 所在目录。

## 场景判断

- 功能测试：用户要求功能测试、最小配置、能启动即可、CI/MTR/单元测试环境时使用。不要询问，直接生成低资源配置。
- 性能测试：用户要求性能测试、benchmark、压测、尽量利用机器资源、指定并发或需要高吞吐时使用。必须先检查主机资源并完成交互确认。
- 版本范围：支持 MySQL 5.6 及以上；5.5、5.1 等更早版本不生成配置。官方 5.6.0/5.6.1 未发布，脚本最低实际版本按 5.6.2 处理。

## 功能测试流程

1. 选择输出路径；用户未指定时使用当前目录 `my.cnf`。
2. 选择数据根目录；用户未指定时使用当前目录下 `mysql-test-data/`。
3. 调用脚本；如果本机没有 `mysqld`，脚本默认按最低支持版本 `5.6.2` 生成：

   ```bash
   python3 "$SKILL_DIR/scripts/render_mysql_test_config.py" \
     --mode functional \
     --target-version auto \
     --server-id random \
     --base-dir ./mysql-test-data \
     --output ./my.cnf
   ```

4. 输出生成路径和最小配置摘要，不再追问。

## 性能测试流程

1. 确认目标 MySQL 版本；用户未指定时用 `mysqld --version` 检测，检测不到则按 `5.6.2` 保守生成。
2. 检查主机剩余资源：
   - 内存：Linux 优先读 `/proc/meminfo` 的 `MemAvailable`；否则用系统命令估算。
   - CPU：记录逻辑核数。
   - 磁盘：检查当前目录、`/data`、`/mnt`、`/var/lib/mysql`、`/tmp` 中存在且可写路径的剩余空间。
3. 问用户要支持的最大并发连接数。
4. 根据连接数估算 session 级内存，避免 OOM：
   - 一直预留：`thread_stack + net_buffer_length + binlog_cache_size + binlog_stmt_cache_size`。
   - 按 25% 概率预留：`sort_buffer_size + read_buffer_size + read_rnd_buffer_size + join_buffer_size`。
   - 不把 `tmp_table_size` / `max_heap_table_size` 按每连接全额预留；只在摘要中标为突发风险。
5. 问用户选择事务安全策略：
   - 安全：`sync_binlog=1`，`innodb_flush_log_at_trx_commit=1`。
   - 高性能：`sync_binlog=1000`，`innodb_flush_log_at_trx_commit=2`，必须提示崩溃时可能丢失最近事务/binlog。
6. 根据磁盘剩余空间推荐数据目录；用户可以修改。
7. 选择唯一 `server_id`：默认用 `--server-id random`；如果用户提供固定拓扑 ID，必须确认没有和其他测试实例重复；已知占用 ID 用 `--reserved-server-id` 传给脚本。
8. 生成候选配置和重点摘要：

   ```bash
   python3 "$SKILL_DIR/scripts/render_mysql_test_config.py" \
     --mode performance \
     --target-version <auto|5.6|5.6.x|5.7.x|8.0.x|8.4.x> \
     --server-id <唯一正整数|random> \
     --max-connections <连接数> \
     --durability <safe|performance> \
     --base-dir <推荐或用户确认的目录> \
     --output ./my.cnf
   ```

9. 只展示重点配置：目标版本、`server_id`、数据目录、端口、`max_connections`、buffer pool、redo、log buffer、binlog/redo 刷盘策略、主要 session 内存估算、磁盘占用估算。
10. 最后询问用户是否要修改关键项；用户确认后再把最终文件写到目标路径。如果脚本已经写出候选文件，把未确认文件称为“候选配置”。

## 生成规则

- 性能测试尽量使用更多资源，但必须保留 OS 和其他进程余量。
- `innodb_buffer_pool_size` 优先使用剩余内存中扣除 session 预留和全局小缓存后的主体部分，通常不超过可用内存的 75%。
- 每个生成的配置参数前必须带 `# <参数名>: since <版本>` 注释。早于最低实际支持版本的参数统一标记为 `since <=5.6.2`。
- 按目标版本生成参数，不输出目标版本尚不支持的参数。
- 参数改名时必须按目标版本使用正确名称，不用 `loose_` 掩盖：`expire_logs_days` / `binlog_expire_logs_seconds`，`innodb_log_file_size + innodb_log_files_in_group` / `innodb_redo_log_capacity`。
- `loose_` 只可用于非关键、非改名参数且目标版本无法确认的人工补充场景；默认脚本不使用 `loose_`。
- MySQL 8.0.30 及以上优先使用 `innodb_redo_log_capacity`；旧版本使用 `innodb_log_file_size` 和 `innodb_log_files_in_group`。
- redo 容量按 buffer pool 的约 25% 起步，并受磁盘剩余空间约束；小 redo 会增加 checkpoint 写盘压力。
- 不默认开启 `query_cache_*`；MySQL 8.0 已移除 Query Cache。
- 不设置会影响初始化后不可轻易改变的参数，除非用户明确要求，例如 `lower_case_table_names`。
- `performance_schema` 默认 `OFF`，除非用户要用 Performance Schema 做观测。
- 每个实例必须有唯一 `server_id`；不要复制已生成配置后不改 `server_id`。
- 同一主机多实例必须使用不同 `port` 和 `base-dir`，从而分离 socket、datadir、tmpdir、binlog、relay log、error log 和 slow log 路径。
- 不在 `my.cnf` 写 `server_uuid`。如果复制已有 datadir 做测试实例，启动前必须删除拷贝中的 `auto.cnf`，让 MySQL 重新生成唯一 UUID。

## 参考资料

需要解释调参依据时读取 `references/mysql-config-tuning-notes.md`。不要把参考资料全文塞进最终报告；只引用和当前配置决策有关的条目。

## 验证

- 生成后检查配置文件存在且非空。
- 如果本机有目标 `mysqld`，优先运行 `mysqld --defaults-file=<my.cnf> --validate-config`；不支持该参数时，至少运行 `mysqld --help --verbose --defaults-file=<my.cnf>` 做语法烟测。
- 验证失败时修正配置，不要把失败配置交给用户。
