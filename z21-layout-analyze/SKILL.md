---
name: z21-layout-analyze
description: Use when analyzing Roco/Fleischmann Z21 .z21 layout export files, including vehicle rosters, locomotive images, function maps, track layout tables, routes, and SQLite/ZIP structure.
metadata:
  version: "v0.1"
---

# Z21 Layout Analyze

Analyze Roco/Fleischmann Z21 `.z21` exports as ZIP containers with PNG assets and an embedded `Loco.sqlite` database. Use this skill to inspect, explain, and export vehicle rosters, vehicle images, function tables, train consists, and control-station track layout data.

## Quick Start

Prefer the bundled script for repeatable exports. It uses only Python 3 standard-library modules and works in both Codex and Claude Code.

```bash
python3 "$SKILL_DIR/scripts/export_z21_layout.py" /path/to/Layout.z21 --output-dir ~/Downloads
```

Set `SKILL_DIR` to this skill directory. In Claude Code, `${CLAUDE_SKILL_DIR}` may already be available; in Codex, use the directory containing the loaded `SKILL.md`.

The script creates a new export directory containing:

- `Summary.md` root summary with links to concrete files
- `Loco.sqlite` extracted database copy
- `tables/*.csv` for every SQLite table
- `vehicles/<vehicle-name>_<number>.md`, same-stem PNG image, and same-stem CSV function table
- `station/Summary.md`, `station/station.json`, `station/station.svg`, and `station/station.html`

## Workflow

1. Treat `.z21` as a ZIP archive. Do not modify the original file.
2. Locate exactly one `Loco.sqlite`; if there are multiple or none, report the archive is not a normal Z21 layout export.
3. Inspect SQLite `PRAGMA user_version`, `layout_data`, table counts, and PNG dimensions.
4. Determine whether track layout exists from structured tables, not from file name or user expectation:
   - layout present when `control_station_controls`, `control_station_rails`, `control_station_routes`, or related tables contain rows.
   - vehicle-only export when these tables are empty but `vehicles` and `functions` contain rows.
5. Export to a new directory when the user asks for files; otherwise summarize counts and representative rows.
6. Clearly label inferred meanings, especially `vehicles.type`, `control_station_controls.type`, and `button_type`.

## Z21 Format Reference

Read `references/z21-sqlite-format.md` when you need field meanings, table relationships, or uncertainty boundaries. Keep final answers concise; link or mention exported files instead of pasting large tables.

## Interpretation Rules

- `vehicles.image_name` references PNG basenames in the ZIP. Save vehicle Markdown and image files in `vehicles/` using `<name>_<address>` when possible; if no name exists, use the address or id. Markdown and PNG should share the same stem.
- Save each vehicle function table as `vehicles/<same-stem>.csv`. Include a CSV link in the vehicle Markdown and root `Summary.md`.
- Do not create a separate `images/` directory by default. Ignore unreferenced ZIP PNGs unless the user explicitly asks to inspect them.
- `functions.image_name` is usually a built-in Z21 function icon name, not a PNG filename.
- `functions.function` is the DCC function number (`F0`..), `position` is UI ordering, and `shortcut` is the user-visible function label when present.
- `train_list` maps type-3 consist/group vehicles to member vehicles.
- `control_station_controls` stores layout controls with coordinates, angle, type, and accessory addresses.
- `control_station_control_states` stores state-to-address output values; `-1` means that address slot is unused.
- `control_station_rails` stores connections between controls and outlet numbers.
- `control_station_routes` stores route buttons; `control_station_route_list` stores ordered route actions.

## Common Mistakes

- Do not assume every `.z21` contains track layout. Some exports are vehicle-only.
- Do not treat unreferenced large PNGs as track maps without checking hashes and database references.
- Do not claim official control type names unless a Z21 source confirms them. Use “推断” for type labels derived from state counts and geometry.
- Do not drop empty control-station tables; their emptiness is important evidence.
- Do not require external Python packages. Use `zipfile`, `sqlite3`, `csv`, `json`, and standard XML/HTML text generation.

## Verification

After exporting, verify:

```bash
python3 -m py_compile "$SKILL_DIR/scripts/export_z21_layout.py"
python3 "$SKILL_DIR/scripts/export_z21_layout.py" /path/to/Layout.z21 --output-dir /tmp
```

Then check that vehicle Markdown count equals `SELECT COUNT(*) FROM vehicles`, each vehicle Markdown with an image has a same-stem PNG in `vehicles/`, and `station/station.json` counts match the SQLite layout tables.
