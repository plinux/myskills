#!/usr/bin/env python3
"""Render a version-aware MySQL my.cnf candidate for test environments."""

from __future__ import annotations

import argparse
import os
import platform
import re
import secrets
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


KIB = 1024
MIB = 1024 * KIB
GIB = 1024 * MIB
MAX_SERVER_ID = 2**32 - 1

Version = tuple[int, int, int]
# MySQL 5.6.0 and 5.6.1 are listed in Oracle release notes as not released;
# 5.6.2 is the first released 5.6 version covered by this skill.
MIN_SUPPORTED_VERSION: Version = (5, 6, 2)
AUTO_VERSION_FALLBACK: Version = MIN_SUPPORTED_VERSION


def parse_size(value: str) -> int:
  text = value.strip().lower()
  units = {
    "k": KIB,
    "kb": KIB,
    "m": MIB,
    "mb": MIB,
    "g": GIB,
    "gb": GIB,
  }
  for suffix, multiplier in sorted(units.items(), key=lambda item: -len(item[0])):
    if text.endswith(suffix):
      return int(float(text[:-len(suffix)]) * multiplier)
  return int(text)


def parse_server_id(value: str) -> int | str:
  text = value.strip().lower()
  if text in {"random", "auto"}:
    return "random"
  try:
    server_id = int(text)
  except ValueError as error:
    raise argparse.ArgumentTypeError("--server-id must be a positive integer or 'random'") from error
  if server_id < 1 or server_id > MAX_SERVER_ID:
    raise argparse.ArgumentTypeError(f"--server-id must be between 1 and {MAX_SERVER_ID}")
  return server_id


def parse_reserved_server_ids(values: list[str]) -> set[int]:
  reserved: set[int] = set()
  for value in values:
    for item in value.split(","):
      text = item.strip()
      if not text:
        continue
      parsed = parse_server_id(text)
      if parsed == "random":
        raise SystemExit("--reserved-server-id accepts only numeric IDs")
      reserved.add(parsed)
  return reserved


def resolve_server_id(choice: int | str, reserved: set[int]) -> tuple[int, str]:
  if choice == "random":
    for _ in range(128):
      candidate = secrets.randbelow(MAX_SERVER_ID) + 1
      if candidate not in reserved:
        return candidate, "random"
    raise SystemExit("could not generate a random server_id outside the reserved set")
  if choice in reserved:
    raise SystemExit(f"--server-id {choice} is already listed in --reserved-server-id")
  return choice, "user"


def fmt_size(value: int) -> str:
  if value >= GIB and value % GIB == 0:
    return f"{value // GIB}G"
  if value >= MIB and value % MIB == 0:
    return f"{value // MIB}M"
  if value >= KIB and value % KIB == 0:
    return f"{value // KIB}K"
  return str(value)


def mysql_size(value: int) -> str:
  return fmt_size(value)


def round_down(value: int, unit: int) -> int:
  return max(unit, value // unit * unit)


def version_label(version: Version) -> str:
  return ".".join(str(part) for part in version)


def normalize_version(value: str) -> Version:
  aliases = {
    "legacy": MIN_SUPPORTED_VERSION,
    "5.6": MIN_SUPPORTED_VERSION,
    "5.7": (5, 7, 44),
    "8.0": (8, 0, 44),
    "8.0.30+": (8, 0, 30),
    "8.4": (8, 4, 9),
  }
  text = value.strip().lower()
  if text in aliases:
    return aliases[text]
  match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text)
  if not match:
    raise argparse.ArgumentTypeError(f"invalid MySQL version: {value}")
  major, minor, patch = match.groups()
  version = (int(major), int(minor), int(patch or 0))
  if version < MIN_SUPPORTED_VERSION:
    raise argparse.ArgumentTypeError(
      "minimum supported MySQL version is 5.6.2; MySQL 5.5/5.1 and unreleased 5.6.0/5.6.1 are not supported"
    )
  return version


def mem_available_bytes() -> int | None:
  meminfo = Path("/proc/meminfo")
  if meminfo.exists():
    for line in meminfo.read_text().splitlines():
      if line.startswith("MemAvailable:"):
        return int(line.split()[1]) * KIB
  return None


def disk_free(path: Path) -> int:
  return shutil.disk_usage(path).free


def existing_parent(path: Path) -> Path:
  current = path if path.exists() else path.parent
  while not current.exists() and current != current.parent:
    current = current.parent
  return current


def candidate_dirs() -> list[Path]:
  candidates = [Path("/data"), Path("/mnt"), Path("/var/lib/mysql"), Path.cwd(), Path("/tmp")]
  seen: set[str] = set()
  result: list[Path] = []
  for path in candidates:
    try:
      if not path.exists() or not os.access(path, os.W_OK):
        continue
      real = str(path.resolve())
      if real in seen:
        continue
      seen.add(real)
      result.append(path)
    except OSError:
      continue
  return result


def detect_target_version(choice: str) -> tuple[Version, str]:
  if choice != "auto":
    try:
      version = normalize_version(choice)
    except argparse.ArgumentTypeError as error:
      raise SystemExit(str(error)) from None
    return version, "user"

  mysqld = shutil.which("mysqld")
  if not mysqld:
    return AUTO_VERSION_FALLBACK, "fallback"

  try:
    result = subprocess.run(
      [mysqld, "--version"],
      check=False,
      capture_output=True,
      text=True,
      timeout=3,
    )
  except (OSError, subprocess.TimeoutExpired):
    return AUTO_VERSION_FALLBACK, "fallback"

  match = re.search(r"(\d+)\.(\d+)\.(\d+)", result.stdout + result.stderr)
  if not match:
    return AUTO_VERSION_FALLBACK, "fallback"
  version = tuple(int(part) for part in match.groups())
  if version < MIN_SUPPORTED_VERSION:
    raise SystemExit("detected MySQL is older than the minimum supported version 5.6.2")
  return version, "detected"


def supports(target: Version, since: Version) -> bool:
  return target >= since


def since_text(since: Version, exact: bool = False) -> str:
  if since <= MIN_SUPPORTED_VERSION and not exact:
    return "<=5.6.2"
  return version_label(since)


def add_option(
  lines: list[str],
  target: Version,
  name: str,
  value: Any = None,
  *,
  since: Version = MIN_SUPPORTED_VERSION,
  exact_since: bool = False,
  note: str = "",
) -> None:
  if not supports(target, since):
    return
  suffix = f"; {note}" if note else ""
  lines.append(f"# {name}: since {since_text(since, exact_since)}{suffix}")
  if value is None:
    lines.append(name)
  else:
    lines.append(f"{name} = {value}")


def add_blank(lines: list[str]) -> None:
  if lines and lines[-1] != "":
    lines.append("")


@dataclass
class Sizing:
  mem_available: int
  os_reserve: int
  max_connections: int
  always_session: int
  weighted_session: int
  session_budget: int
  global_overhead: int
  buffer_pool: int
  redo_capacity: int
  log_buffer: int
  tmp_table_size: int


def compute_sizing(args: argparse.Namespace, base_dir: Path) -> Sizing:
  mem_available = args.memory_bytes or mem_available_bytes() or 4 * GIB

  if args.mode == "functional":
    max_connections = args.max_connections or 32
    always_session = 256 * KIB + 16 * KIB + 128 * KIB + 32 * KIB
    optional_session = 256 * KIB * 4
    weighted_session = int(always_session + optional_session * args.optional_session_probability)
    return Sizing(
      mem_available=mem_available,
      os_reserve=min(mem_available // 2, 512 * MIB),
      max_connections=max_connections,
      always_session=always_session,
      weighted_session=weighted_session,
      session_budget=max_connections * weighted_session,
      global_overhead=128 * MIB,
      buffer_pool=128 * MIB if mem_available < GIB else 256 * MIB,
      redo_capacity=128 * MIB,
      log_buffer=16 * MIB,
      tmp_table_size=16 * MIB,
    )

  max_connections = args.max_connections
  if not max_connections:
    raise SystemExit("--max-connections is required for performance mode")

  thread_stack = parse_size(args.thread_stack)
  net_buffer_length = parse_size(args.net_buffer_length)
  binlog_cache_size = parse_size(args.binlog_cache_size)
  binlog_stmt_cache_size = parse_size(args.binlog_stmt_cache_size)
  sort_buffer_size = parse_size(args.sort_buffer_size)
  read_buffer_size = parse_size(args.read_buffer_size)
  read_rnd_buffer_size = parse_size(args.read_rnd_buffer_size)
  join_buffer_size = parse_size(args.join_buffer_size)

  always_session = thread_stack + net_buffer_length + binlog_cache_size + binlog_stmt_cache_size
  optional_session = sort_buffer_size + read_buffer_size + read_rnd_buffer_size + join_buffer_size
  weighted_session = int(always_session + optional_session * args.optional_session_probability)
  session_budget = max_connections * weighted_session

  os_reserve = max(2 * GIB, int(mem_available * 0.15))
  global_overhead = 512 * MIB
  usable_for_mysql = max(512 * MIB, mem_available - os_reserve - session_budget - global_overhead)
  buffer_pool_cap = int(mem_available * 0.75)
  buffer_pool = round_down(min(usable_for_mysql, buffer_pool_cap), 128 * MIB)
  buffer_pool = max(buffer_pool, 512 * MIB)

  free_disk = disk_free(existing_parent(base_dir))
  redo_target = max(2 * GIB, int(buffer_pool * 0.25))
  redo_disk_cap = max(512 * MIB, int(free_disk * 0.10))
  redo_capacity = round_down(min(redo_target, redo_disk_cap, 64 * GIB), 128 * MIB)
  log_buffer = min(max(64 * MIB, buffer_pool // 128), 512 * MIB)
  tmp_table_size = min(max(64 * MIB, buffer_pool // 256), 256 * MIB)

  return Sizing(
    mem_available=mem_available,
    os_reserve=os_reserve,
    max_connections=max_connections,
    always_session=always_session,
    weighted_session=weighted_session,
    session_budget=session_budget,
    global_overhead=global_overhead,
    buffer_pool=buffer_pool,
    redo_capacity=redo_capacity,
    log_buffer=log_buffer,
    tmp_table_size=tmp_table_size,
  )


def choose_base_dir(args: argparse.Namespace) -> Path:
  if args.base_dir:
    return Path(args.base_dir).expanduser().resolve()
  if args.mode == "functional":
    return (Path.cwd() / "mysql-test-data").resolve()
  dirs = candidate_dirs()
  if not dirs:
    return (Path.cwd() / "mysql-perf-data").resolve()
  best = max(dirs, key=disk_free)
  return (best / "mysql-perf-data").resolve()


def render_config(args: argparse.Namespace, base_dir: Path, sizing: Sizing) -> str:
  mysql_dir = base_dir / "mysql"
  datadir = base_dir / "dbs"
  tmpdir = base_dir / "tmp"
  socket = tmpdir / "mysql.sock"
  target = args.target_version_tuple
  durability_safe = args.durability == "safe"
  sync_binlog = 1 if durability_safe else 1000
  flush_log = 1 if durability_safe else 2
  performance_schema = "OFF" if args.performance_schema == "off" else "ON"
  io_threads = min(max((os.cpu_count() or 4) // 2, 4), 16)
  io_capacity = args.io_capacity or (200 if args.mode == "functional" else 2000)
  flush_method = "O_DIRECT" if args.mode == "performance" and platform.system() == "Linux" else "fsync"

  if args.mode == "functional":
    sort_buffer_size = "256K"
    read_buffer_size = "256K"
    read_rnd_buffer_size = "256K"
    join_buffer_size = "256K"
    table_open_cache = 256
    table_definition_cache = 256
    thread_cache_size = 16
  else:
    sort_buffer_size = args.sort_buffer_size
    read_buffer_size = args.read_buffer_size
    read_rnd_buffer_size = args.read_rnd_buffer_size
    join_buffer_size = args.join_buffer_size
    table_open_cache = 4096
    table_definition_cache = 2048
    thread_cache_size = min(max(sizing.max_connections // 4, 64), 512)

  lines = ["[mysqld]", ""]

  lines.append("#### Runtime ####")
  add_option(lines, target, "socket", socket)
  add_option(lines, target, "datadir", datadir)
  add_option(lines, target, "tmpdir", tmpdir)
  add_option(lines, target, "port", args.port)
  add_option(lines, target, "character_set_server", "utf8mb4")
  add_option(lines, target, "collation_server", "utf8mb4_general_ci")
  add_option(lines, target, "default_storage_engine", "InnoDB")
  add_option(lines, target, "skip_name_resolve")
  add_option(lines, target, "default_time_zone", '"+8:00"')
  add_blank(lines)

  lines.append("#### Replication Identity ####")
  add_option(
    lines,
    target,
    "server_id",
    args.server_id_value,
    note="must be unique in every replication topology and copied test instance",
  )
  add_blank(lines)

  lines.append("#### Connection ####")
  add_option(lines, target, "max_connections", sizing.max_connections)
  add_option(lines, target, "max_user_connections", sizing.max_connections)
  add_option(lines, target, "back_log", 3000)
  add_option(lines, target, "thread_stack", "256K")
  add_option(lines, target, "max_connect_errors", 100)
  add_option(lines, target, "max_allowed_packet", "1G")
  add_option(lines, target, "connect_timeout", 10)
  add_option(lines, target, "net_read_timeout", 30)
  add_option(lines, target, "net_write_timeout", 60)
  add_option(lines, target, "wait_timeout", 86400)
  add_option(lines, target, "interactive_timeout", 7200)
  add_blank(lines)

  lines.append("#### Session Buffer ####")
  add_option(lines, target, "sort_buffer_size", sort_buffer_size)
  add_option(lines, target, "read_buffer_size", read_buffer_size)
  add_option(lines, target, "read_rnd_buffer_size", read_rnd_buffer_size)
  add_option(lines, target, "join_buffer_size", join_buffer_size)
  add_option(lines, target, "net_buffer_length", "16K")
  add_option(lines, target, "binlog_cache_size", "128K")
  add_option(lines, target, "binlog_stmt_cache_size", "32K")
  add_blank(lines)

  lines.append("#### Global Cache ####")
  add_option(lines, target, "table_open_cache", table_open_cache)
  add_option(lines, target, "table_definition_cache", table_definition_cache)
  add_option(lines, target, "thread_cache_size", thread_cache_size)
  add_option(lines, target, "key_buffer_size", "16M")
  add_blank(lines)

  lines.append("#### Tmp Table ####")
  add_option(lines, target, "max_heap_table_size", mysql_size(sizing.tmp_table_size))
  add_option(lines, target, "tmp_table_size", mysql_size(sizing.tmp_table_size))
  add_blank(lines)

  lines.append("#### Binlog & Relay Log ####")
  add_option(lines, target, "binlog_format", "ROW")
  add_option(lines, target, "binlog_row_image", "FULL")
  add_option(lines, target, "binlog_checksum", "CRC32")
  add_option(lines, target, "max_binlog_size", "500M")
  add_option(lines, target, "sync_binlog", sync_binlog)
  if supports(target, (8, 0, 1)):
    add_option(
      lines,
      target,
      "binlog_expire_logs_seconds",
      2592000,
      since=(8, 0, 1),
      exact_since=True,
      note="new seconds-based name; replaces expire_logs_days for target >= 8.0.1",
    )
  else:
    add_option(
      lines,
      target,
      "expire_logs_days",
      30,
      note="legacy days-based binlog expiration for target < 8.0.1",
    )
  add_option(lines, target, "log_bin", mysql_dir / "mysql-bin.log")
  add_option(lines, target, "log_bin_index", mysql_dir / "mysql-bin.index")
  add_option(lines, target, "log_bin_trust_function_creators", 1)
  add_option(lines, target, "relay_log", mysql_dir / "mysql-relay.log")
  add_option(
    lines,
    target,
    "relay_log_index",
    mysql_dir / "mysql-relay.index",
    note="explicit path avoids hostname-derived relay log index after copied tests or host renames",
  )
  add_blank(lines)

  lines.append("#### Error & Slow Log ####")
  add_option(lines, target, "log_error", mysql_dir / "mysql-error.log")
  add_option(lines, target, "slow_query_log_file", mysql_dir / "slow_query.log")
  add_option(lines, target, "slow_query_log", "ON")
  add_option(lines, target, "long_query_time", 1)
  add_option(lines, target, "log_queries_not_using_indexes", "OFF")
  add_blank(lines)

  lines.append("#### Performance Schema ####")
  add_option(lines, target, "performance_schema", performance_schema)
  add_blank(lines)

  lines.append("#### InnoDB ####")
  add_option(lines, target, "innodb_data_home_dir", mysql_dir)
  add_option(lines, target, "innodb_data_file_path", "ibdata1:1G:autoextend")
  add_option(lines, target, "innodb_file_per_table", "ON")
  add_option(lines, target, "innodb_buffer_pool_size", mysql_size(sizing.buffer_pool))
  add_option(lines, target, "innodb_log_buffer_size", mysql_size(sizing.log_buffer))
  if supports(target, (8, 0, 30)):
    add_option(
      lines,
      target,
      "innodb_redo_log_capacity",
      mysql_size(sizing.redo_capacity),
      since=(8, 0, 30),
      exact_since=True,
      note="replaces innodb_log_file_size and innodb_log_files_in_group",
    )
  else:
    add_option(
      lines,
      target,
      "innodb_log_file_size",
      mysql_size(max(128 * MIB, sizing.redo_capacity // 2)),
      note="legacy redo sizing for target < 8.0.30",
    )
    add_option(
      lines,
      target,
      "innodb_log_files_in_group",
      2,
      note="legacy redo sizing for target < 8.0.30",
    )
  add_option(
    lines,
    target,
    "transaction_isolation",
    "READ-COMMITTED",
    note="accepted by MySQL option parsing from the 5.6.2 support floor",
  )
  add_option(lines, target, "innodb_flush_log_at_trx_commit", flush_log)
  add_option(lines, target, "autocommit", "ON")
  add_option(lines, target, "innodb_flush_method", flush_method)
  add_option(lines, target, "innodb_io_capacity", io_capacity)
  if supports(target, (5, 6, 7)):
    add_option(
      lines,
      target,
      "innodb_io_capacity_max",
      io_capacity * 2,
      since=(5, 6, 7),
      exact_since=True,
      note="renamed from innodb_max_io_capacity",
    )
  elif supports(target, (5, 6, 6)):
    add_option(
      lines,
      target,
      "innodb_max_io_capacity",
      io_capacity * 2,
      since=(5, 6, 6),
      exact_since=True,
      note="renamed to innodb_io_capacity_max in 5.6.7",
    )
  add_option(lines, target, "innodb_read_io_threads", io_threads)
  add_option(lines, target, "innodb_write_io_threads", io_threads)
  add_option(lines, target, "innodb_doublewrite", "ON")
  add_option(lines, target, "innodb_stats_on_metadata", "OFF")
  add_option(lines, target, "innodb_thread_concurrency", 0)
  add_option(lines, target, "innodb_open_files", 3000)
  add_blank(lines)

  lines.append("[mysql]")
  add_option(lines, target, "socket", socket)
  add_option(lines, target, "prompt", '"\\\\u@\\\\h:\\\\d \\\\r:\\\\m:\\\\s > "')
  lines.append("")
  return "\n".join(lines)


def render_summary(args: argparse.Namespace, base_dir: Path, sizing: Sizing) -> str:
  free_disk = disk_free(existing_parent(base_dir))
  durability = "安全配置 sync_binlog=1 / innodb_flush_log_at_trx_commit=1"
  if args.durability == "performance":
    durability = "高性能配置 sync_binlog=1000 / innodb_flush_log_at_trx_commit=2"
  version_source = {
    "detected": "自动检测",
    "fallback": "未检测到 mysqld，按最低支持版本回退",
    "user": "用户指定",
  }[args.target_version_source]
  return "\n".join([
    "重点配置摘要:",
    f"- 模式: {args.mode}",
    f"- 目标 MySQL 版本: {version_label(args.target_version_tuple)} ({version_source})",
    f"- 数据根目录: {base_dir}",
    f"- 数据目录: {base_dir / 'dbs'}",
    f"- server_id: {args.server_id_value} ({'随机生成' if args.server_id_source == 'random' else '用户指定'})",
    f"- 可用内存: {fmt_size(sizing.mem_available)}",
    f"- OS 预留: {fmt_size(sizing.os_reserve)}",
    f"- max_connections: {sizing.max_connections}",
    f"- 单连接常驻预留: {fmt_size(sizing.always_session)}",
    f"- 单连接加权预留: {fmt_size(sizing.weighted_session)}",
    f"- session 总预留: {fmt_size(sizing.session_budget)}",
    f"- innodb_buffer_pool_size: {fmt_size(sizing.buffer_pool)}",
    f"- redo 容量: {fmt_size(sizing.redo_capacity)}",
    f"- innodb_log_buffer_size: {fmt_size(sizing.log_buffer)}",
    f"- tmp_table_size/max_heap_table_size: {fmt_size(sizing.tmp_table_size)} (突发风险，不按每连接全额预留)",
    f"- binlog/redo 策略: {durability}",
    f"- 数据目录所在文件系统剩余空间: {fmt_size(free_disk)}",
  ])


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--mode", choices=["functional", "performance"], required=True)
  parser.add_argument("--output", default="-", help="Output my.cnf path, or '-' for stdout")
  parser.add_argument("--base-dir", help="MySQL test data root")
  parser.add_argument("--port", type=int, default=3001)
  parser.add_argument(
    "--server-id",
    required=True,
    type=parse_server_id,
    help="Unique MySQL server_id: positive integer, or 'random' to generate one",
  )
  parser.add_argument(
    "--reserved-server-id",
    action="append",
    default=[],
    help="Already-used server_id to avoid; repeat or pass comma-separated values",
  )
  parser.add_argument("--max-connections", type=int)
  parser.add_argument("--durability", choices=["safe", "performance"], default="safe")
  parser.add_argument(
    "--target-version",
    "--mysql-version",
    dest="target_version",
    default="auto",
    help="Target MySQL version: auto, 5.6, 5.6.x, 5.7.x, 8.0.x, 8.4.x; legacy aliases are accepted",
  )
  parser.add_argument("--memory-bytes", type=int)
  parser.add_argument("--optional-session-probability", type=float, default=0.25)
  parser.add_argument("--thread-stack", default="256K")
  parser.add_argument("--net-buffer-length", default="16K")
  parser.add_argument("--binlog-cache-size", default="128K")
  parser.add_argument("--binlog-stmt-cache-size", default="32K")
  parser.add_argument("--sort-buffer-size", default="1M")
  parser.add_argument("--read-buffer-size", default="1M")
  parser.add_argument("--read-rnd-buffer-size", default="512K")
  parser.add_argument("--join-buffer-size", default="512K")
  parser.add_argument("--io-capacity", type=int)
  parser.add_argument("--performance-schema", choices=["on", "off"], default="off")
  parser.add_argument("--summary", action="store_true", help="Print summary after config")
  args = parser.parse_args()

  args.target_version_tuple, args.target_version_source = detect_target_version(args.target_version)
  reserved_server_ids = parse_reserved_server_ids(args.reserved_server_id)
  args.server_id_value, args.server_id_source = resolve_server_id(args.server_id, reserved_server_ids)
  base_dir = choose_base_dir(args)
  sizing = compute_sizing(args, base_dir)
  config = render_config(args, base_dir, sizing)

  if args.output == "-":
    print(config)
  else:
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(config)
    print(f"Wrote {output}")

  if args.summary:
    print()
    print(render_summary(args, base_dir, sizing))

  if platform.system() != "Linux" and args.mode == "performance":
    print("\nNote: resource sizing outside Linux may be conservative because MemAvailable is unavailable.")

  return 0


if __name__ == "__main__":
  raise SystemExit(main())
