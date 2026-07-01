# Z21 `.z21` SQLite Format Notes

## Container

- `.z21` is a ZIP archive.
- Normal exports contain `export/<UUID>/Loco.sqlite` plus PNG files.
- PNG basenames are UUID-like asset names. Most vehicle images are referenced by `vehicles.image_name`.
- The database observed in current samples is SQLite 3 with `PRAGMA user_version = 17`.

## Core Tables

| Table | Meaning |
|---|---|
| `layout_data` | Layout name, control-station type/theme, optional Z21 IP. |
| `categories` | User categories such as locomotive class, country, or consist type. |
| `vehicles` | Vehicle roster, including DCC address, display name, image, model info, decoder info, description, and type. |
| `vehicles_to_categories` | Many-to-many mapping between vehicles and categories. |
| `functions` | Per-vehicle function buttons: UI position, DCC F number, label, built-in icon name, button type, timing, display flags. |
| `dc_functions` | Driver-cab-specific functions; may be empty. |
| `train_list` | Consist/group membership: `train_id` is the type-3 vehicle/group, `vehicle_id` is a member. |
| `update_history` | Z21 app/database migration history. |
| `paired_z21_pro_links` | Paired Z21 pro LINK devices. |

## Vehicle Fields

Important `vehicles` fields:

| Field | Meaning |
|---|---|
| `id` | Internal vehicle id. |
| `position` | Roster order. |
| `name` | Display name, often includes model brand and road number. |
| `address` | DCC decoder address; users may call this “车号” in control contexts. |
| `image_name` | PNG basename in ZIP. |
| `type` | Observed: `0` ordinary locomotive/vehicle, `1` coach/control car, `3` consist/group. Treat as inferred unless official docs are available. |
| `full_name`, `railway`, `article_number`, `decoder_type` | Model/railway metadata. |
| `buffer_lenght`, `model_buffer_lenght`, `service_weight`, `model_weight`, `rmin` | Physical/model attributes; spelling is `lenght` in schema. |
| `description` | Free text description. |

## Function Fields

`functions` rows are joined to `vehicles` by `vehicle_id`.

| Field | Meaning |
|---|---|
| `position` | UI button order. |
| `function` | DCC function number, render as `F<function>`. |
| `shortcut` | User-visible function label when non-empty. |
| `image_name` | Built-in Z21 function icon name, not normally a ZIP PNG. |
| `button_type` | Raw button mode. Do not over-label without confirmation. |
| `time` | Timing value as text. |
| `show_function_number` | Whether to show function number. |
| `is_configured` | Configuration flag. |

## Track Layout Tables

Track layout is structured data, not necessarily an image.

| Table | Meaning |
|---|---|
| `control_station_pages` | Layout pages; `thumb` may be null. |
| `control_station_controls` | Track/control elements: page, `x`, `y`, `angle`, raw `type`, accessory addresses, button timing. |
| `control_station_control_states` | Available states per control and the output values for `address1/2/3`. `-1` means unused. |
| `control_station_rails` | Connections between controls: left/right control ids and outlet numbers. |
| `control_station_routes` | Route buttons or route entries on a page. |
| `control_station_route_list` | Ordered route actions: route id, control id, target state id, wait time, signal fields. |
| `control_station_signals` | Signal objects; may be empty. |
| `control_station_images`, `control_station_notes` | Page images/notes; may be empty. |
| `control_station_response_modules` | Feedback/response modules; may be empty. |
| `control_station_turntables`, `control_station_turntable_exits` | Turntable data; may be empty. |

## Observed Control Type Heuristics

These are inferences from sample exports, not official labels:

| `control_station_controls.type` | Heuristic label |
|---:|---|
| `0` | straight/common track section |
| `24` | curved track section |
| `1`, `2` | two-state turnout variants |
| `4` | three-state or dual-address turnout |
| `8`, `23` | two-state accessory/control element; exact official meaning unknown |

Always preserve the raw `type`, `address1`, `address2`, `address3`, states, and rails in exports so the user can verify heuristics.

## Layout Presence Test

Use table counts:

```sql
SELECT COUNT(*) FROM control_station_controls;
SELECT COUNT(*) FROM control_station_rails;
SELECT COUNT(*) FROM control_station_routes;
SELECT COUNT(*) FROM control_station_route_list;
```

If all are zero, call it a vehicle-only export even if `control_station_pages` has one empty page.

## Export Recommendations

- Export every SQLite table to CSV for auditability.
- Export a root `Summary.md` that links to concrete vehicle and station files.
- Export a machine-readable `station/station.json`.
- Export `station/Summary.md` with controls, states, rails, routes, and route actions.
- Generate a simple SVG/HTML schematic from coordinates and rails, but label it as a helper visualization because exact Z21 control drawing semantics are inferred.
- Export vehicle Markdown files to `vehicles/<name>_<number>.md` and copy vehicle images beside them as same-stem PNG files.
- Export each vehicle function table to a same-stem CSV file in `vehicles/`.
- Do not create a separate `images/` directory by default; leave unreferenced PNG assets inside the original `.z21` archive unless the user explicitly requests them.
