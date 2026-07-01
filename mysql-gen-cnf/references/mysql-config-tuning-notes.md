# MySQL 测试配置调参依据

## 内存

- MySQL 官方文档说明 `innodb_buffer_pool_size` 定义 InnoDB buffer pool，通常建议为系统内存 50%-75%；过小会频繁换入换出，过大可能与系统内存竞争导致 swap。
- MySQL 默认配置目标是能在约 512MB RAM 的虚拟机上启动；功能测试应使用小 buffer pool 和小连接数。
- Percona 强调每个连接会拥有自己的多种 buffer；`sort_buffer_size` 这类全局默认/session 变量不应设得过大，最好按会话或查询放大。
- Percona 也指出 `read_buffer_size`、`sort_buffer_size`、`join_buffer_size` 等通常在查询需要时才分配，但一旦需要就分配完整大小，复杂查询还可能多次分配。
- Google Cloud 文档对 MySQL session buffers 的分类较清晰：`sort_buffer_size`、`join_buffer_size`、`read_buffer_size`、`read_rnd_buffer_size` 按需分配；开启 binlog 时 `binlog_cache_size` 为每个 client 分配。

## Redo / Binlog

- MySQL 官方文档建议增大 redo log：redo 太小时，InnoDB 写满后需要 checkpoint，把 buffer pool 中的脏页写到磁盘，造成不必要的磁盘写。
- MySQL 8.0.30 起使用 `innodb_redo_log_capacity` 控制 redo 总容量；旧版本用 `innodb_log_file_size * innodb_log_files_in_group`。
- MySQL 8.0.1 引入 `binlog_expire_logs_seconds`；目标版本低于 8.0.1 时继续使用 `expire_logs_days`。
- MySQL 官方文档说明最大持久性复制配置是 `sync_binlog=1` 且 `innodb_flush_log_at_trx_commit=1`。
- 阿里云 RDS 文档把 `innodb_flush_log_at_trx_commit=1`、`sync_binlog=1` 归为高安全配置；把 `innodb_flush_log_at_trx_commit=2`、`sync_binlog=1000` 归为高性能配置，并提示可能丢失数据。
- 淘宝数据库内核月报多篇 InnoDB 文章解释了 buffer pool、redo log、checkpoint 和日志文件结构；调参时用官方文档确定参数语义，用月报辅助理解实现机制。

## 复制和多实例唯一性

- `server_id` 必须是 1 到 4294967295 的唯一正整数；复制拓扑或复制出来的测试实例不能重复。脚本强制要求 `--server-id`，推荐 `--server-id random`。
- `server_uuid` 不写入 `my.cnf`；MySQL 会在数据目录 `auto.cnf` 中生成和读取。复制 datadir 创建测试实例时，删除拷贝里的 `auto.cnf`，避免 UUID 重复。
- 同一主机多实例还必须分离 `port`、`socket`、`datadir`、`tmpdir`、binlog、relay log、error log 和 slow log。脚本通过 `base-dir` 分离路径，但 `port` 默认相同，复制配置时必须改。
- 显式生成 `relay_log` 和 `relay_log_index`，避免默认 hostname 派生文件名在复制 datadir 或改主机名后导致 relay log 初始化失败。
- `report_host`、`report_port` 只在实例作为 replica 且需要拓扑可见身份时设置；当前测试配置不默认生成，避免普通功能/性能测试暴露伪复制身份。

## 版本兼容

- 最低实际支持 MySQL 5.6.2；官方 Release Notes 标记 5.6.0/5.6.1 为未发布，5.5、5.1 等更早版本不支持。
- 早于最低实际支持版本的参数统一标记为 `since <=5.6.2`。
- `binlog_row_image` 和 `binlog_checksum` 在第一版已发布 5.6.2 中存在，可以从 5.6.2 起生成。
- `innodb_io_capacity_max` 在 5.6.7 起使用；5.6.6 叫 `innodb_max_io_capacity`，5.6.2-5.6.5 不生成该 max 参数。
- 目标版本从 5.6.2 起使用 `transaction_isolation` 启动选项；本 Skill 不生成旧系统变量名 `tx_isolation`。
- 目标版本低于 8.0.1 时使用 `expire_logs_days`；8.0.1 及以上使用 `binlog_expire_logs_seconds`。
- 目标版本低于 8.0.30 时使用 `innodb_log_file_size` 和 `innodb_log_files_in_group`；8.0.30 及以上使用 `innodb_redo_log_capacity`。
- `loose_` 不能用于掩盖已知改名参数。只有目标版本无法确认、且参数非关键时，才考虑对人工补充项使用 `loose_`。

## 磁盘和 I/O

- MySQL 官方文档说明 `innodb_io_capacity` 应按写入工作负载和设备能力调整，用于后台脏页刷新等 I/O 任务。
- Percona 建议关注 `innodb_flush_method`：使用 `O_DIRECT` 可减少文件系统缓存带来的额外内存压力，常用于专用 MySQL 测试实例。

## 参考链接

- MySQL 8.0 Memory Use: https://dev.mysql.com/doc/refman/8.0/en/memory-use.html
- MySQL 8.0 Buffer Pool Configuration: https://dev.mysql.com/doc/refman/8.0/en/innodb-performance-buffer-pool.html
- MySQL 8.0 Server System Variables: https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html
- MySQL 8.4 Server System Variables: https://dev.mysql.com/doc/refman/8.4/en/server-system-variables.html
- MySQL 8.4 InnoDB System Variables: https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html
- MySQL Binary Logging Options: https://dev.mysql.com/doc/refman/8.4/en/replication-options-binary-log.html
- MySQL Replication Options: https://dev.mysql.com/doc/mysql/en/replication-options.html
- MySQL 8.0 Optimizing InnoDB Redo Logging: https://dev.mysql.com/doc/mysql/8.0/en/optimizing-innodb-logging.html
- MySQL 8.0 Redo Log: https://dev.mysql.com/doc/mysql/8.0/en/innodb-redo-log.html
- MySQL 8.0.1 Release Notes: https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-1.html
- MySQL 8.0.30 Release Notes: https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-30.html
- MySQL 5.6 Release Notes PDF: https://downloads.mysql.com/docs/mysql-5.6-relnotes-en.a4.pdf
- MySQL 5.7 Server Command Options: https://dev.mysql.com/doc/refman/5.7/en/server-options.html
- MySQL 8.0 InnoDB I/O Capacity: https://dev.mysql.com/doc/refman/8.0/en/innodb-configuring-io-capacity.html
- Percona: Adjusting MySQL 8.0 Memory Parameters: https://www.percona.com/blog/adjusting-mysql-8-0-memory-parameters/
- Percona: MySQL server memory usage troubleshooting tips: https://www.percona.com/blog/mysql-server-memory-usage-2/
- Aliyun RDS: innodb_flush_log_at_trx_commit 和 sync_binlog: https://help.aliyun.com/zh/rds/apsaradb-rds-for-mysql/innodb-flush-log-at-trx-commit
- Alibaba Cloud RDS: innodb_flush_log_at_trx_commit and sync_binlog: https://www.alibabacloud.com/help/en/rds/apsaradb-rds-for-mysql/innodb-flush-log-at-trx-commit
- 淘宝数据库内核月报入口: http://mysql.taobao.org/monthly/
