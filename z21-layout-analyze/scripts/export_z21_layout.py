#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import re
import sqlite3
import struct
import tempfile
import zipfile
from pathlib import Path


DEFAULT_OUTPUT_ROOT = Path.home() / "Downloads"


def sanitizeFilename(value: str, fallback: str) -> str:
  value = (value or "").strip() or fallback
  value = re.sub(r"[\\/:*?\"<>|]+", "_", value)
  value = re.sub(r"[\r\n\t]+", " ", value)
  value = re.sub(r"\s+", " ", value).strip()
  value = value.rstrip(". ")
  return value[:120] or fallback


def uniquePath(directory: Path, stem: str, suffix: str, used: set[str]) -> Path:
  stem = sanitizeFilename(stem, "未命名")
  path = directory / f"{stem}{suffix}"
  key = path.name.casefold()
  if key not in used and not path.exists():
    used.add(key)
    return path
  index = 2
  while True:
    path = directory / f"{stem} ({index}){suffix}"
    key = path.name.casefold()
    if key not in used and not path.exists():
      used.add(key)
      return path
    index += 1


def uniqueDirectory(parent: Path, name: str) -> Path:
  path = parent / sanitizeFilename(name, "z21_export")
  if not path.exists():
    return path
  index = 2
  while True:
    candidate = parent / f"{path.name} ({index})"
    if not candidate.exists():
      return candidate
    index += 1


def vehicleNumber(vehicle: dict) -> str:
  address = vehicle.get("address")
  if address is not None and str(address).strip() != "":
    return str(address).strip()
  return str(vehicle.get("id") or "unknown")


def vehicleFileStem(vehicle: dict) -> str:
  name = sanitizeFilename(str(vehicle.get("name") or ""), "")
  number = sanitizeFilename(vehicleNumber(vehicle), str(vehicle.get("id") or "unknown"))
  if name:
    return f"{name}_{number}"
  return number


def mdEscape(value: object) -> str:
  if value is None:
    return ""
  return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


def mdTarget(path: str) -> str:
  return f"<{path}>"


def tableMarkdown(headers: list[str], rows: list[list[object]]) -> str:
  lines = ["| " + " | ".join(headers) + " |"]
  lines.append("|" + "|".join("---" for _ in headers) + "|")
  for row in rows:
    lines.append("| " + " | ".join(mdEscape(item) for item in row) + " |")
  return "\n".join(lines)


def sqliteRows(con: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
  return [dict(row) for row in con.execute(sql, params).fetchall()]


def pngMeta(data: bytes) -> dict:
  width = height = None
  if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
    width, height = struct.unpack(">II", data[16:24])
  return {
    "width": width,
    "height": height,
    "sha256": hashlib.sha256(data).hexdigest(),
    "bytes": len(data),
  }


def vehicleTypeLabel(value: object) -> str:
  labels = {
    0: "普通车辆/机车",
    1: "车厢/控制车",
    3: "重联/编组",
  }
  try:
    return labels.get(int(value), f"未知类型 {value}")
  except (TypeError, ValueError):
    return f"未知类型 {value}"


def controlTypeLabel(value: object) -> str:
  # 名称来自本文件状态数、地址字段和几何关系的推断，原始 type 数值始终保留。
  labels = {
    0: "直轨/普通轨道段（推断）",
    1: "两态道岔 A（推断）",
    2: "两态道岔 B（推断）",
    4: "三态道岔/双地址道岔（推断）",
    8: "两态控制件 type=8（未确认）",
    23: "两态控制件 type=23（未确认）",
    24: "弯轨/曲线轨道段（推断）",
  }
  try:
    return labels.get(int(value), f"未知控件 type={value}")
  except (TypeError, ValueError):
    return f"未知控件 type={value}"


def loadArchive(source: Path) -> tuple[str, bytes, dict[str, dict]]:
  with zipfile.ZipFile(source) as zf:
    dbNames = [name for name in zf.namelist() if name.endswith("Loco.sqlite")]
    if len(dbNames) != 1:
      raise RuntimeError(f"期望 1 个 Loco.sqlite，实际 {len(dbNames)} 个: {dbNames}")
    dbName = dbNames[0]
    dbData = zf.read(dbName)
    pngs: dict[str, dict] = {}
    for info in zf.infolist():
      if not info.filename.lower().endswith(".png"):
        continue
      data = zf.read(info.filename)
      base = Path(info.filename).name
      meta = pngMeta(data)
      meta.update({
        "zip_path": info.filename,
        "mtime": "%04d-%02d-%02d %02d:%02d:%02d" % info.date_time,
        "data": data,
      })
      pngs[base] = meta
  return dbName, dbData, pngs


def connectSqliteData(dbData: bytes) -> sqlite3.Connection:
  con = sqlite3.connect(":memory:")
  if hasattr(con, "deserialize"):
    con.deserialize(dbData)
  else:
    with tempfile.TemporaryDirectory() as tempDir:
      tempDb = Path(tempDir) / "Loco.sqlite"
      tempDb.write_bytes(dbData)
      sourceCon = sqlite3.connect(str(tempDb))
      try:
        sourceCon.backup(con)
      finally:
        sourceCon.close()
  con.row_factory = sqlite3.Row
  return con


def writeCsv(path: Path, rows: list[dict]) -> None:
  if not rows:
    path.write_text("", encoding="utf-8")
    return
  with path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)


def writeVehicleFunctionCsv(path: Path, functions: list[dict]) -> None:
  headers = ["显示位置", "F 编号", "功能名称 shortcut", "图标 image_name", "按钮类型", "时间", "显示编号", "已配置"]
  with path.open("w", newline="", encoding="utf-8-sig") as handle:
    writer = csv.writer(handle)
    writer.writerow(headers)
    for functionRow in functions:
      writer.writerow([
        functionRow.get("position"),
        f"F{functionRow.get('function')}",
        functionRow.get("shortcut"),
        functionRow.get("image_name"),
        functionRow.get("button_type"),
        functionRow.get("time"),
        functionRow.get("show_function_number"),
        functionRow.get("is_configured"),
      ])


def writeVehicleMarkdown(
  path: Path,
  vehicle: dict,
  categories: str,
  functions: list[dict],
  trainMembers: list[dict],
  imageRel: str,
  imageMeta: dict | None,
  functionCsvRel: str,
) -> None:
  name = vehicle.get("name") or f"车辆 {vehicle['id']}"
  lines = [f"# {name}", ""]
  if imageRel:
    lines.extend([f"![{name}]({mdTarget(imageRel)})", ""])

  lines.extend([
    "## 基本信息",
    "",
    tableMarkdown(["字段", "值"], [
      ["车辆 ID", vehicle.get("id")],
      ["列表位置", vehicle.get("position")],
      ["类型", f"{vehicle.get('type')} ({vehicleTypeLabel(vehicle.get('type'))})"],
      ["DCC 地址/车号", vehicle.get("address")],
      ["名称", vehicle.get("name")],
      ["完整名称", vehicle.get("full_name")],
      ["分类", categories],
      ["铁路/路局", vehicle.get("railway")],
      ["货号/车型编号", vehicle.get("article_number")],
      ["解码器类型", vehicle.get("decoder_type")],
      ["最大速度", vehicle.get("max_speed")],
      ["速度显示", vehicle.get("speed_display")],
      ["激活状态", vehicle.get("active")],
      ["牵引方向", vehicle.get("traction_direction")],
      ["虚拟车辆 dummy", vehicle.get("dummy")],
      ["直接操控 direct_steering", vehicle.get("direct_steering")],
      ["吊车 crane", vehicle.get("crane")],
      ["IP", vehicle.get("ip")],
    ]),
    "",
    "## 模型与收藏信息",
    "",
    tableMarkdown(["字段", "值"], [
      ["实车缓冲梁间距 buffer_lenght", vehicle.get("buffer_lenght")],
      ["模型缓冲梁间距 model_buffer_lenght", vehicle.get("model_buffer_lenght")],
      ["实车重量 service_weight", vehicle.get("service_weight")],
      ["模型重量 model_weight", vehicle.get("model_weight")],
      ["最小半径 rmin", vehicle.get("rmin")],
      ["制造/入库年份 build_year", vehicle.get("build_year")],
      ["拥有时间 owning_since", vehicle.get("owning_since")],
      ["所有者 owner", vehicle.get("owner")],
    ]),
    "",
    "## 图片信息",
    "",
    tableMarkdown(["字段", "值"], [
      ["原始图片名", vehicle.get("image_name")],
      ["导出图片", imageRel],
      ["尺寸", f"{imageMeta.get('width')} x {imageMeta.get('height')}" if imageMeta else ""],
      ["SHA256", imageMeta.get("sha256") if imageMeta else ""],
    ]),
    "",
  ])

  description = (vehicle.get("description") or "").strip()
  if description:
    lines.extend(["## 说明", "", description, ""])

  if trainMembers:
    lines.extend(["## 编组成员", ""])
    lines.append(tableMarkdown(
      ["编组位置", "车辆 ID", "车辆名称", "DCC 地址", "类型"],
      [[m.get("position"), m.get("vehicle_id"), m.get("vehicle_name"), m.get("address"), vehicleTypeLabel(m.get("type"))] for m in trainMembers],
    ))
    lines.append("")

  lines.extend(["## 功能表", ""])
  lines.append(f"CSV 文件：[{functionCsvRel}]({mdTarget(functionCsvRel)})")
  lines.append("")
  if functions:
    lines.append(tableMarkdown(
      ["显示位置", "F 编号", "功能名称 shortcut", "图标 image_name", "按钮类型", "时间", "显示编号", "已配置"],
      [[f.get("position"), f"F{f.get('function')}", f.get("shortcut"), f.get("image_name"), f.get("button_type"), f.get("time"), f.get("show_function_number"), f.get("is_configured")] for f in functions],
    ))
  else:
    lines.append("此车辆没有 functions 表记录。")
  lines.append("")
  path.write_text("\n".join(lines), encoding="utf-8")


def outletPoint(control: dict, outlet: int) -> tuple[float, float]:
  # 用控件中心点加粗略方向偏移来展示连接端口；这是可视化辅助，不替代原表字段。
  angle = float(control.get("angle") or 0)
  base = {
    0: 180,
    1: 0,
    2: 90,
    3: -90,
  }.get(int(outlet or 0), 0)
  radians = (angle + base) * 3.141592653589793 / 180
  length = 32
  return (
    float(control["x"]) + length * __import__("math").cos(radians),
    float(control["y"]) + length * __import__("math").sin(radians),
  )


def symbolSvg(control: dict, x: float, y: float) -> str:
  controlType = int(control.get("type") or 0)
  angle = float(control.get("angle") or 0)
  label = f"#{control['id']} t{controlType}"
  addressBits = [str(control.get(key) or "") for key in ["address1", "address2", "address3"] if control.get(key)]
  addressText = "/".join(addressBits)
  color = {
    0: "#2f6f4e",
    1: "#b4542d",
    2: "#b4542d",
    4: "#8b3f9e",
    8: "#3366aa",
    23: "#3366aa",
    24: "#2f6f4e",
  }.get(controlType, "#555555")
  parts = [f'<g transform="translate({x:.1f},{y:.1f})">']
  parts.append(f'<circle cx="0" cy="0" r="25" fill="#ffffff" stroke="{color}" stroke-width="2"/>')
  parts.append(f'<g transform="rotate({angle:.1f})" stroke="{color}" stroke-width="5" stroke-linecap="round" fill="none">')
  if controlType == 0:
    parts.append('<line x1="-26" y1="0" x2="26" y2="0"/>')
  elif controlType == 24:
    parts.append('<path d="M -22 20 Q -22 -20 22 -20"/>')
  elif controlType in (1, 2):
    branchY = -20 if controlType == 1 else 20
    parts.append('<line x1="-25" y1="0" x2="25" y2="0"/>')
    parts.append(f'<path d="M -5 0 Q 8 0 25 {branchY}"/>')
  elif controlType == 4:
    parts.append('<line x1="-25" y1="0" x2="25" y2="0"/>')
    parts.append('<path d="M -5 0 Q 8 0 25 -18"/>')
    parts.append('<path d="M -5 0 Q 8 0 25 18"/>')
  elif controlType == 8:
    parts.append('<line x1="-22" y1="-22" x2="22" y2="22"/>')
    parts.append('<line x1="-22" y1="22" x2="22" y2="-22"/>')
  elif controlType == 23:
    parts.append('<rect x="-16" y="-16" width="32" height="32" rx="3"/>')
    parts.append('<line x1="-20" y1="0" x2="20" y2="0"/>')
  else:
    parts.append('<rect x="-18" y="-18" width="36" height="36" rx="3"/>')
  parts.append("</g>")
  parts.append(f'<text x="0" y="44" text-anchor="middle" font-size="12" fill="#222">{html.escape(label)}</text>')
  if addressText:
    parts.append(f'<text x="0" y="58" text-anchor="middle" font-size="11" fill="#7a2d18">addr {html.escape(addressText)}</text>')
  parts.append("</g>")
  return "\n".join(parts)


def buildLayoutSvg(controls: list[dict], rails: list[dict], routes: list[dict], routeList: list[dict]) -> str:
  controlsById = {int(row["id"]): row for row in controls}
  xs = [float(row["x"]) for row in controls + routes]
  ys = [float(row["y"]) for row in controls + routes]
  if not xs or not ys:
    return "\n".join([
      '<svg xmlns="http://www.w3.org/2000/svg" width="760" height="220" viewBox="0 0 760 220">',
      '<style>text{font-family:"Microsoft YaHei",Arial,sans-serif}.small{font-size:12px}.title{font-size:18px;font-weight:700}</style>',
      '<rect width="100%" height="100%" fill="#f7f4ef"/>',
      '<text x="24" y="42" class="title" fill="#222">Z21 控制台 Layout 示意图</text>',
      '<text x="24" y="76" class="small" fill="#555">该文件没有 control_station_controls 或 control_station_routes 坐标记录。</text>',
      '<text x="24" y="104" class="small" fill="#555">这通常表示当前导出是车辆/功能表数据，未保存可编辑轨道 Layout。</text>',
      '</svg>',
    ])
  minX, maxX = min(xs), max(xs)
  minY, maxY = min(ys), max(ys)
  margin = 90
  width = int(maxX - minX + margin * 2 + 160)
  height = int(maxY - minY + margin * 2 + 80)

  def point(x: float, y: float) -> tuple[float, float]:
    return x - minX + margin, y - minY + margin

  parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
    '<style>text{font-family:"Microsoft YaHei",Arial,sans-serif}.small{font-size:12px}.title{font-size:18px;font-weight:700}</style>',
    '<rect width="100%" height="100%" fill="#f7f4ef"/>',
    '<text x="24" y="34" class="title" fill="#222">Z21 控制台 Layout 示意图</text>',
    '<text x="24" y="56" class="small" fill="#555">节点位置来自 control_station_controls；连线来自 control_station_rails；控件图形为按 type 推断的辅助示意。</text>',
  ]

  for rail in rails:
    left = controlsById.get(int(rail["left_control_id"]))
    right = controlsById.get(int(rail["right_control_id"]))
    if not left or not right:
      continue
    lx, ly = outletPoint(left, int(rail.get("left_outlet") or 0))
    rx, ry = outletPoint(right, int(rail.get("right_outlet") or 0))
    x1, y1 = point(lx, ly)
    x2, y2 = point(rx, ry)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#4c6272" stroke-width="8" stroke-linecap="round" opacity="0.55"/>')
    parts.append(f'<text x="{mx:.1f}" y="{my - 8:.1f}" text-anchor="middle" font-size="11" fill="#314250">rail {rail["id"]}</text>')

  for control in controls:
    x, y = point(float(control["x"]), float(control["y"]))
    parts.append(symbolSvg(control, x, y))

  for route in routes:
    x, y = point(float(route["x"]), float(route["y"]))
    parts.append(f'<g transform="translate({x:.1f},{y:.1f})">')
    parts.append('<rect x="-42" y="-18" width="84" height="36" rx="6" fill="#ffe6a8" stroke="#8c6c1f" stroke-width="2"/>')
    parts.append(f'<text x="0" y="-2" text-anchor="middle" font-size="12" fill="#403000">Route {route["id"]}</text>')
    parts.append(f'<text x="0" y="13" text-anchor="middle" font-size="11" fill="#403000">{html.escape(route.get("name") or "")}</text>')
    parts.append("</g>")

  parts.extend([
    f'<g transform="translate({width - 230},80)">',
    '<rect x="0" y="0" width="200" height="190" rx="6" fill="#ffffff" stroke="#c8c2b8"/>',
    '<text x="12" y="24" font-size="14" font-weight="700" fill="#222">图例</text>',
    '<line x1="14" y1="48" x2="58" y2="48" stroke="#2f6f4e" stroke-width="5" stroke-linecap="round"/><text x="70" y="52" font-size="12">轨道段/曲轨</text>',
    '<line x1="14" y1="76" x2="58" y2="76" stroke="#b4542d" stroke-width="5" stroke-linecap="round"/><text x="70" y="80" font-size="12">两态道岔</text>',
    '<line x1="14" y1="104" x2="58" y2="104" stroke="#8b3f9e" stroke-width="5" stroke-linecap="round"/><text x="70" y="108" font-size="12">三态/双地址道岔</text>',
    '<line x1="14" y1="132" x2="58" y2="132" stroke="#4c6272" stroke-width="8" stroke-linecap="round" opacity="0.55"/><text x="70" y="136" font-size="12">rails 表连接</text>',
    '<rect x="14" y="150" width="44" height="24" rx="5" fill="#ffe6a8" stroke="#8c6c1f"/><text x="70" y="167" font-size="12">route 按钮</text>',
    "</g>",
    "</svg>",
  ])
  return "\n".join(parts)


def buildLayoutMarkdown(
  layout: dict | None,
  pages: list[dict],
  controls: list[dict],
  states: list[dict],
  rails: list[dict],
  routes: list[dict],
  routeListJoined: list[dict],
) -> str:
  lines = ["# Z21 轨道 Layout 解析", ""]
  if layout:
    lines.append(tableMarkdown(["字段", "值"], [
      ["Layout 名称", layout.get("name")],
      ["control_station_type", layout.get("control_station_type")],
      ["control_station_theme", layout.get("control_station_theme")],
      ["z21_ip_address", layout.get("z21_ip_address")],
    ]))
    lines.append("")
  lines.append("## 页面")
  lines.append("")
  lines.append(tableMarkdown(["ID", "位置", "名称", "缩略图"], [[p.get("id"), p.get("position"), p.get("name"), p.get("thumb")] for p in pages]))
  lines.append("")
  lines.append("## 解析统计")
  lines.append("")
  typeCounts: dict[int, int] = {}
  for control in controls:
    typeCounts[int(control.get("type") or 0)] = typeCounts.get(int(control.get("type") or 0), 0) + 1
  lines.append(tableMarkdown(["项目", "数量"], [
    ["控制件 control_station_controls", len(controls)],
    ["状态 control_station_control_states", len(states)],
    ["连接 control_station_rails", len(rails)],
    ["路线 control_station_routes", len(routes)],
    ["路线动作 control_station_route_list", len(routeListJoined)],
  ]))
  lines.append("")
  lines.append("## 控件类型分布")
  lines.append("")
  lines.append(tableMarkdown(["type", "说明", "数量"], [[key, controlTypeLabel(key), typeCounts[key]] for key in sorted(typeCounts)]))
  lines.append("")
  lines.append("## 控件明细")
  lines.append("")
  lines.append(tableMarkdown(
    ["ID", "page", "x", "y", "angle", "type", "type 说明", "address1", "address2", "address3", "状态数"],
    [[c.get("id"), c.get("page_id"), c.get("x"), c.get("y"), c.get("angle"), c.get("type"), controlTypeLabel(c.get("type")), c.get("address1"), c.get("address2"), c.get("address3"), sum(1 for s in states if s.get("control_id") == c.get("id"))] for c in controls],
  ))
  lines.append("")
  lines.append("## 轨道控件")
  lines.append("")
  trackControls = [c for c in controls if int(c.get("type") or 0) in (0, 24)]
  if trackControls:
    lines.append(tableMarkdown(
      ["ID", "x", "y", "angle", "type", "说明"],
      [[c.get("id"), c.get("x"), c.get("y"), c.get("angle"), c.get("type"), controlTypeLabel(c.get("type"))] for c in trackControls],
    ))
  else:
    lines.append("未发现直轨/曲轨控件。")
  lines.append("")
  lines.append("## 道岔与附件控件")
  lines.append("")
  turnoutControls = [c for c in controls if int(c.get("type") or 0) not in (0, 24)]
  if turnoutControls:
    lines.append(tableMarkdown(
      ["ID", "x", "y", "angle", "type", "说明", "address1", "address2", "address3", "状态数"],
      [[c.get("id"), c.get("x"), c.get("y"), c.get("angle"), c.get("type"), controlTypeLabel(c.get("type")), c.get("address1"), c.get("address2"), c.get("address3"), sum(1 for s in states if s.get("control_id") == c.get("id"))] for c in turnoutControls],
    ))
  else:
    lines.append("未发现道岔或附件控件。")
  lines.append("")
  lines.append("## 控件状态")
  lines.append("")
  lines.append(tableMarkdown(
    ["状态 ID", "control_id", "state", "address1_value", "address2_value", "address3_value"],
    [[s.get("id"), s.get("control_id"), s.get("state"), s.get("address1_value"), s.get("address2_value"), s.get("address3_value")] for s in states],
  ))
  lines.append("")
  lines.append("## 轨道连接")
  lines.append("")
  lines.append(tableMarkdown(
    ["rail ID", "left_control", "left_outlet", "right_control", "right_outlet", "value"],
    [[r.get("id"), r.get("left_control_id"), r.get("left_outlet"), r.get("right_control_id"), r.get("right_outlet"), r.get("value")] for r in rails],
  ))
  lines.append("")
  lines.append("## 路线与动作")
  lines.append("")
  lines.append(tableMarkdown(["路线 ID", "名称", "x", "y", "angle"], [[r.get("id"), r.get("name"), r.get("x"), r.get("y"), r.get("angle")] for r in routes]))
  lines.append("")
  lines.append(tableMarkdown(
    ["动作 ID", "路线 ID", "顺序", "control_id", "control type", "address1", "state_id", "state", "address1_value", "address2_value", "wait_time"],
    [[r.get("id"), r.get("route_id"), r.get("position"), r.get("control_id"), r.get("control_type"), r.get("address1"), r.get("state_id"), r.get("state"), r.get("address1_value"), r.get("address2_value"), r.get("wait_time")] for r in routeListJoined],
  ))
  lines.append("")
  lines.append("## 说明")
  lines.append("")
  lines.append("- `control_station_controls` 是布局中的轨道/道岔/控制件，包含坐标、旋转角和地址。")
  lines.append("- `control_station_control_states` 是每个控制件可切换状态对应的地址输出值。`-1` 表示该地址位不参与。")
  lines.append("- `control_station_rails` 保存控制件之间的连接边和端口号。")
  lines.append("- `control_station_routes` 是路线按钮；`control_station_route_list` 是每条路线按顺序执行的控制件状态切换。")
  lines.append("- 控件 `type` 的中文含义未从官方文档验证，导出中同时保留原始数值和基于本文件结构的推断说明。")
  lines.append("")
  return "\n".join(lines)


def buildHtml(readmeMarkdown: str, svgText: str) -> str:
  return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>Z21 Layout 导出</title>
  <style>
    body {{ margin: 24px; font-family: "Microsoft YaHei", Arial, sans-serif; font-size: 14px; line-height: 1.55; color: #222; background: #fafafa; }}
    h1 {{ font-size: 24px; }}
    h2 {{ font-size: 18px; margin-top: 28px; }}
    pre {{ white-space: pre-wrap; font-family: "Microsoft YaHei", Arial, sans-serif; font-size: 12px; background: #fff; border: 1px solid #ddd; padding: 12px; overflow: auto; }}
    .svg-wrap {{ background: #fff; border: 1px solid #ddd; padding: 12px; overflow: auto; }}
  </style>
</head>
<body>
  <h1>Z21 Layout 导出</h1>
  <h2>轨道示意图</h2>
  <div class="svg-wrap">{svgText}</div>
  <h2>Markdown 原文</h2>
  <pre>{html.escape(readmeMarkdown)}</pre>
</body>
</html>
"""


def parseArgs() -> argparse.Namespace:
  parser = argparse.ArgumentParser(
    description="Export vehicles, vehicle images, per-vehicle function CSV files, SQLite tables, and control-station layout from a Roco/Fleischmann Z21 .z21 file.",
  )
  parser.add_argument("source", type=Path, help="Path to the .z21 file")
  parser.add_argument(
    "--output-dir",
    type=Path,
    default=DEFAULT_OUTPUT_ROOT,
    help="Parent directory for the generated export directory. Defaults to ~/Downloads.",
  )
  return parser.parse_args()


def main() -> int:
  args = parseArgs()
  source = args.source.expanduser().resolve()
  outputRoot = args.output_dir.expanduser().resolve()
  if not source.exists():
    raise FileNotFoundError(f"source .z21 file not found: {source}")
  outputRoot.mkdir(parents=True, exist_ok=True)

  dbName, dbData, pngs = loadArchive(source)
  con = connectSqliteData(dbData)

  timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
  safeStem = sanitizeFilename(source.stem, "layout")
  outDir = uniqueDirectory(outputRoot, f"{safeStem}_z21_export_{timestamp}")
  vehiclesDir = outDir / "vehicles"
  vehicleImagesDir = vehiclesDir
  stationDir = outDir / "station"
  tablesDir = outDir / "tables"
  for directory in [vehiclesDir, vehicleImagesDir, stationDir, tablesDir]:
    directory.mkdir(parents=True, exist_ok=True)

  tableNames = [row["name"] for row in sqliteRows(con, "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
  allTables = {name: sqliteRows(con, f'SELECT * FROM "{name}"') for name in tableNames}
  for name, rows in allTables.items():
    writeCsv(tablesDir / f"{name}.csv", rows)

  layoutRows = sqliteRows(con, "SELECT * FROM layout_data ORDER BY id")
  layout = layoutRows[0] if layoutRows else None
  pages = sqliteRows(con, "SELECT * FROM control_station_pages ORDER BY position, id")
  controls = sqliteRows(con, "SELECT * FROM control_station_controls ORDER BY id")
  states = sqliteRows(con, "SELECT * FROM control_station_control_states ORDER BY id")
  rails = sqliteRows(con, "SELECT * FROM control_station_rails ORDER BY id")
  routes = sqliteRows(con, "SELECT * FROM control_station_routes ORDER BY id")
  routeList = sqliteRows(con, """
    SELECT rl.*, c.type AS control_type, c.address1, c.address2, c.address3,
           s.state, s.address1_value, s.address2_value, s.address3_value
    FROM control_station_route_list rl
    LEFT JOIN control_station_controls c ON c.id = CAST(rl.control_id AS INTEGER)
    LEFT JOIN control_station_control_states s ON s.id = rl.state_id
    ORDER BY rl.route_id, rl.position, rl.id
  """)
  hasLayout = any([controls, rails, routes, routeList])

  layoutData = {
    "layout_data": layout,
    "control_station_pages": pages,
    "control_station_controls": controls,
    "control_station_control_states": states,
    "control_station_rails": rails,
    "control_station_routes": routes,
    "control_station_route_list_joined": routeList,
  }
  (stationDir / "station.json").write_text(json.dumps(layoutData, ensure_ascii=False, indent=2), encoding="utf-8")
  layoutMarkdown = buildLayoutMarkdown(layout, pages, controls, states, rails, routes, routeList)
  (stationDir / "Summary.md").write_text(layoutMarkdown, encoding="utf-8")
  layoutSvg = buildLayoutSvg(controls, rails, routes, routeList)
  (stationDir / "station.svg").write_text(layoutSvg, encoding="utf-8")
  (stationDir / "station.html").write_text(buildHtml(layoutMarkdown, layoutSvg), encoding="utf-8")

  vehicles = sqliteRows(con, "SELECT * FROM vehicles ORDER BY position, id")
  categories = {
    row["vehicle_id"]: row["categories"] or ""
    for row in sqliteRows(con, """
      SELECT vehicle_id, GROUP_CONCAT(name, '、') AS categories
      FROM (
        SELECT DISTINCT vc.vehicle_id, c.id, c.name
        FROM vehicles_to_categories vc
        JOIN categories c ON c.id = vc.category_id
        ORDER BY vc.vehicle_id, c.id
      )
      GROUP BY vehicle_id
    """)
  }
  functionsByVehicle = {
    vehicle["id"]: sqliteRows(con, """
      SELECT position, function, shortcut, image_name, button_type, time, show_function_number, is_configured
      FROM functions
      WHERE vehicle_id = ?
      ORDER BY position, function, id
    """, (vehicle["id"],))
    for vehicle in vehicles
  }
  trainMembersByVehicle = {
    vehicle["id"]: sqliteRows(con, """
      SELECT tl.position, tl.vehicle_id, v.name AS vehicle_name, v.address, v.type
      FROM train_list tl
      LEFT JOIN vehicles v ON v.id = tl.vehicle_id
      WHERE tl.train_id = ?
      ORDER BY tl.position, tl.id
    """, (vehicle["id"],))
    for vehicle in vehicles
  }

  usedImageFiles: set[str] = set()
  usedVehicleMdFiles: set[str] = set()
  vehicleImageRefs: dict[int, tuple[str, dict | None]] = {}
  vehicleMarkdownRefs: dict[int, str] = {}
  usedRawImages: set[str] = set()
  for vehicle in vehicles:
    imageName = vehicle.get("image_name") or ""
    meta = pngs.get(imageName)
    if not meta:
      vehicleImageRefs[vehicle["id"]] = ("", None)
      continue
    imagePath = uniquePath(vehicleImagesDir, vehicleFileStem(vehicle), ".png", usedImageFiles)
    imagePath.write_bytes(meta["data"])
    usedRawImages.add(imageName)
    vehicleImageRefs[vehicle["id"]] = (imagePath.name, meta)

  for vehicle in vehicles:
    mdPath = uniquePath(vehiclesDir, vehicleFileStem(vehicle), ".md", usedVehicleMdFiles)
    imageRel, imageMeta = vehicleImageRefs[vehicle["id"]]
    vehicleMarkdownRefs[vehicle["id"]] = mdPath.name
    functionCsvPath = mdPath.with_suffix(".csv")
    writeVehicleFunctionCsv(functionCsvPath, functionsByVehicle[vehicle["id"]])
    writeVehicleMarkdown(
      mdPath,
      vehicle,
      categories.get(vehicle["id"], ""),
      functionsByVehicle[vehicle["id"]],
      trainMembersByVehicle[vehicle["id"]],
      imageRel,
      imageMeta,
      functionCsvPath.name,
    )

  unreferencedImageCount = sum(1 for imageName in pngs if imageName not in usedRawImages)

  (outDir / "Loco.sqlite").write_bytes(dbData)
  functionStats = sqliteRows(con, """
    SELECT COUNT(*) AS total,
           COUNT(DISTINCT vehicle_id) AS vehicles_with_functions,
           MIN(function) AS min_function,
           MAX(function) AS max_function,
           SUM(CASE WHEN shortcut IS NOT NULL AND TRIM(shortcut) <> '' THEN 1 ELSE 0 END) AS named_functions,
           SUM(CASE WHEN shortcut IS NULL OR TRIM(shortcut) = '' THEN 1 ELSE 0 END) AS unnamed_functions
    FROM functions
  """)[0]
  typeCounts = sqliteRows(con, "SELECT type, COUNT(*) AS count FROM vehicles GROUP BY type ORDER BY type")
  controlTypeCounts = sqliteRows(con, "SELECT type, COUNT(*) AS count FROM control_station_controls GROUP BY type ORDER BY type")

  summaryRows = []
  for vehicle in vehicles:
    imageRel, _ = vehicleImageRefs[vehicle["id"]]
    summaryRows.append({
      "position": vehicle.get("position"),
      "id": vehicle.get("id"),
      "type": vehicle.get("type"),
      "type_label": vehicleTypeLabel(vehicle.get("type")),
      "address": vehicle.get("address"),
      "name": vehicle.get("name"),
      "full_name": vehicle.get("full_name"),
      "railway": vehicle.get("railway"),
      "article_number": vehicle.get("article_number"),
      "decoder_type": vehicle.get("decoder_type"),
      "categories": categories.get(vehicle["id"], ""),
      "function_count": len(functionsByVehicle[vehicle["id"]]),
      "markdown": f"vehicles/{vehicleMarkdownRefs[vehicle['id']]}",
      "image": f"vehicles/{imageRel}" if imageRel else "",
      "function_csv": f"vehicles/{Path(vehicleMarkdownRefs[vehicle['id']]).with_suffix('.csv').name}",
    })
  writeCsv(outDir / "vehicles-summary.csv", summaryRows)

  minFunction = functionStats.get("min_function")
  maxFunction = functionStats.get("max_function")
  functionRange = "" if minFunction is None or maxFunction is None else f"F{minFunction} - F{maxFunction}"

  summary = ["# Z21 导出汇总", ""]
  summary.extend([
    f"- 源文件：`{source}`",
    f"- 导出时间：`{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
    f"- ZIP 内数据库：`{dbName}`",
    f"- SQLite user_version：`{con.execute('PRAGMA user_version').fetchone()[0]}`",
    "",
    "## 核心结论",
    "",
  ])
  if hasLayout:
    summary.extend([
      "- 该文件包含结构化轨道 layout；至少一个 control-station layout 表有数据。",
      "- 轨道 layout 不是图片背景，而是 SQLite 表中的控件、状态、连线和路线动作。",
      "- 控件 `type` 的官方含义未在文件内给出；本导出按状态数、地址字段和几何连接做推断，并保留全部原始字段供复核。",
    ])
  else:
    summary.extend([
      "- 该文件未发现结构化轨道 layout；control-station layout 表为空。",
      "- 当前导出应按车辆、图片、功能表和编组数据解读，不要把未引用 PNG 当作轨道图。",
    ])
  summary.extend(["", "## 统计", ""])
  summary.append(tableMarkdown(["项目", "数量"], [
    ["ZIP PNG", len(pngs)],
    ["车辆", len(vehicles)],
    ["车辆图片", len(usedRawImages)],
    ["未被车辆引用 PNG（未导出）", unreferencedImageCount],
    ["功能表记录", functionStats.get("total")],
    ["有功能表车辆", functionStats.get("vehicles_with_functions")],
    ["功能号范围", functionRange],
    ["有 shortcut 的功能", functionStats.get("named_functions")],
    ["无 shortcut 的功能", functionStats.get("unnamed_functions")],
    ["Layout 页面", len(pages)],
    ["Layout 控件", len(controls)],
    ["Layout 控件状态", len(states)],
    ["Layout 轨道连接", len(rails)],
    ["Layout 路线", len(routes)],
    ["Layout 路线动作", len(routeList)],
  ]))
  summary.extend(["", "## 文件入口", ""])
  summary.append(tableMarkdown(["内容", "路径"], [
    ["沙盘信息", "[station/Summary.md](<station/Summary.md>)"],
    ["沙盘图示 HTML", "[station/station.html](<station/station.html>)"],
    ["沙盘图示 SVG", "[station/station.svg](<station/station.svg>)"],
    ["沙盘结构 JSON", "[station/station.json](<station/station.json>)"],
    ["原始表 CSV", "[tables/](<tables/>)"],
    ["车辆 Markdown", "[vehicles/](<vehicles/>)"],
    ["车辆图片", "[vehicles/](<vehicles/>)"],
    ["每车功能表 CSV", "[vehicles/](<vehicles/>)"],
    ["车辆汇总 CSV", "[vehicles-summary.csv](<vehicles-summary.csv>)"],
    ["原始 SQLite", "[Loco.sqlite](<Loco.sqlite>)"],
  ]))
  summary.extend(["", "## 车辆类型分布", ""])
  summary.append(tableMarkdown(["type", "说明", "数量"], [[row["type"], vehicleTypeLabel(row["type"]), row["count"]] for row in typeCounts]))
  summary.extend(["", "## Layout 控件类型分布", ""])
  summary.append(tableMarkdown(["type", "推断说明", "数量"], [[row["type"], controlTypeLabel(row["type"]), row["count"]] for row in controlTypeCounts]))
  summary.extend(["", "## 车辆列表", ""])
  summary.append(tableMarkdown(
    ["位置", "ID", "类型", "DCC 地址", "名称", "完整名称", "分类", "功能数", "车辆文件", "功能表 CSV", "图片"],
    [[r["position"], r["id"], r["type_label"], r["address"], r["name"], r["full_name"], r["categories"], r["function_count"], f"[{Path(r['markdown']).name}](<{r['markdown']}>)", f"[{Path(r['function_csv']).name}](<{r['function_csv']}>)", f"[{Path(r['image']).name}](<{r['image']}>)" if r["image"] else ""] for r in summaryRows],
  ))
  summary.append("")
  (outDir / "Summary.md").write_text("\n".join(summary), encoding="utf-8")
  (outDir / "export-info.txt").write_text(
    "\n".join([
      f"source={source}",
      f"source_size={source.stat().st_size}",
      f"output={outDir}",
      f"vehicles={len(vehicles)}",
      f"vehicle_images={len(usedRawImages)}",
      f"unreferenced_images_not_exported={unreferencedImageCount}",
      f"functions={functionStats.get('total')}",
      f"layout_controls={len(controls)}",
      f"layout_rails={len(rails)}",
      f"layout_routes={len(routes)}",
      "",
    ]),
    encoding="utf-8",
  )

  print(outDir)
  print(f"vehicles={len(vehicles)}")
  print(f"vehicle_images={len(usedRawImages)}")
  print(f"unreferenced_images_not_exported={unreferencedImageCount}")
  print(f"functions={functionStats.get('total')}")
  print(f"layout_controls={len(controls)}")
  print(f"layout_rails={len(rails)}")
  print(f"layout_routes={len(routes)}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
