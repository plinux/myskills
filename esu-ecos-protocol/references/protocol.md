# ESU ECoS PC Interface 协议

## 传输层

- 连接方式：TCP。
- 默认端口：`15471`。
- 编码：ASCII/文本命令；实现中通常按行读取。
- 结束符：命令以换行结束；解析端应兼容 `\n` 和 `\r\n`。
- 并发：同一连接上可能收到请求响应和异步事件，不能假定每次读取只对应一个请求。

## 命令语法

基本形式：

```text
command(objectId[, option[, option[value]...]])
```

常见命令：

| 命令 | 用途 |
| --- | --- |
| `get` | 读取对象属性。 |
| `set` | 设置对象属性或触发动作。 |
| `request` | 申请 `view` 事件订阅或 `control` 独占控制。 |
| `release` | 释放 `view` 或 `control`。 |
| `queryObjects` | 查询管理器对象下的对象列表。 |
| `create` | 在管理器下创建对象。 |
| `delete` | 删除对象。 |

选项形式：

```text
status
speed[42]
func[0,1]
name["BR 218"]
```

实现要点：

- 选项名大小写按协议原样处理。
- 带字符串的字段可能包含空格，生成命令时保留引号。
- 响应字符串内部的双引号可能以 `""` 表示，解析时应还原为单个 `"`。
- 多值选项使用逗号分隔，例如 `cv[1,3]`、`func[7,1]`。
- 不认识的扩展选项应保留原文或安全忽略，不能破坏整块解析。

## 回复和事件

请求响应：

```text
<REPLY get(1, status)>
1 status[GO]
<END 0 (OK)>
```

订阅事件：

```text
<EVENT 1>
1 status[STOP]
<END 0 (OK)>
```

解析规则：

- 块起始行为 `<REPLY ...>` 或 `<EVENT ...>`。
- 块结束行为 `<END code (message)>`。
- 中间行通常以对象 ID 开头，后接多个选项。
- `<EVENT ...>` 不是请求失败；它来自 `request(objectId, view)` 的订阅。
- 等待某个 `<REPLY>` 时仍要处理或缓存同时到达的 `<EVENT>`。

常见状态码：

| 代码 | 含义 |
| --- | --- |
| `0` | OK。 |
| `6` | 不支持的命令或语法错误。 |
| `11` | 未知选项。 |
| `15` | 未知对象。 |
| `22` | 目标不是管理器对象或管理器不可用。 |
| `25` | 控制权问题，常见于对象已被其他客户端控制。 |
| `35` | 创建操作仍在等待或已存在未完成创建。 |

## 基础对象和发现

基础对象 `1` 代表控制站。连接后先读取能力：

```text
request(1, view)
get(1, commandstationtype, protocolversion, hardwareversion, applicationversion, applicationversionsuffix, railcom, railcomplus)
```

旧固件或兼容路径可使用：

```text
get(1, info)
get(1, status)
```

重要字段：

| 字段 | 用途 |
| --- | --- |
| `commandstationtype` | 控制站类型，例如 ECoS/ECoS2/Central Station 兼容形态。 |
| `protocolversion` | PC Interface 协议版本，优先用于兼容判断。 |
| `hardwareversion` | 硬件版本，记录但不要单独作为协议分支。 |
| `applicationversion` | 控制器固件/应用版本。 |
| `applicationversionsuffix` | 固件后缀，可能为空。 |
| `railcom` | RailCom 能力或开关状态。 |
| `railcomplus` | RailComPlus 能力或开关状态。 |
| `status` | 电源状态，常见 `GO` 或 `STOP`。 |

## 对象 ID

| 对象 ID | 含义 |
| --- | --- |
| `1` | ECoS 基础对象和电源控制。 |
| `5` | 编程轨对象。 |
| `10` | 机车管理器。 |
| `11` | 道岔/附件管理器。 |
| `12` | Shuttle train control。 |
| `20` | 设备管理器。 |
| `25` | Sniffer。 |
| `26` | 反馈管理器。 |
| `27` | Booster。 |
| `31` | Control desk。 |
| `100..199` | S88 反馈模块。 |
| `200..299` | ECoSDetector 反馈模块。 |
| `20000..29999` | 道岔/附件对象。 |
| `30000..39999` | 路线、转盘或扩展附件对象；具体含义按返回字段判断。 |

## 视图和控制权

订阅对象事件：

```text
request(objectId, view)
release(objectId, view)
```

申请独占控制：

```text
request(objectId, control)
request(objectId, control, force)
release(objectId, control)
```

规则：

- 读取和事件订阅使用 `view`。
- 改速度、方向、功能键、道岔、创建临时对象或删除对象前使用 `control`。
- `force` 会抢占控制权，只能在用户明确允许时使用。
- 控制完成后释放 `control`，长期监听完成后释放 `view`。

## 电源

查询电源：

```text
request(1, view)
get(1, status)
```

控制电源：

```text
set(1, go)
set(1, stop)
```

`go` 和 `stop` 会影响轨道电源。真实控制器联调时，必须先确认现场安全。

## 机车

查询机车对象：

```text
queryObjects(10, addr, name, protocol)
```

常见机车字段：

| 字段 | 用途 |
| --- | --- |
| `addr` | 机车地址。 |
| `protocol` | `DCC14`、`DCC28`、`DCC128`、`MM14`、`MM27`、`MM28`、`SX32` 等。 |
| `name` | 名称。 |
| `speed` | 速度值。 |
| `speedstep` | 速度级。 |
| `dir` | 方向，常见 `0` 正向、`1` 反向。 |
| `func` | 单个功能键状态。 |
| `funcset` | 功能键集合状态。 |
| `funcdesc` | 功能键描述。 |

控制流程：

```text
request(locoId, view)
request(locoId, control)
set(locoId, speedstep[42])
set(locoId, dir[0])
set(locoId, func[3,1])
release(locoId, control)
```

创建临时机车：

```text
create(10, addr[3], name["test"], protocol[DCC128], append)
```

创建响应通常从管理器对象 `10` 返回新对象 ID。删除前先停车并取得控制权。

## 道岔和附件

查询附件对象：

```text
request(11, view)
queryObjects(11, addr, protocol, type, addrext, mode, symbol, name1, name2, name3)
```

常见字段：

| 字段 | 用途 |
| --- | --- |
| `addr` | 地址。 |
| `addrext` | 扩展地址，例如红/绿输出组合。 |
| `protocol` | 常见 `DCC` 或 `MM`。 |
| `type` | `ACCESSORY`、`TURNTABLE` 等。 |
| `mode` | `SWITCH` 或 `PULSE`。 |
| `state` | 当前状态。 |
| `duration` | 脉冲时间。 |
| `variant` | 附件变体。 |
| `symbol` | 图标或附件类型符号。 |
| `name1`/`name2`/`name3` | 多段名称。 |

对象级控制：

```text
request(accessoryId, control)
set(accessoryId, state[1])
release(accessoryId, control)
```

管理器级切换示例：

```text
request(11, control, force)
set(11, switch[DCC1r])
release(11, control)
```

## 反馈和 RailCom

查询反馈模块：

```text
request(26, view)
queryObjects(26, ports)
```

读取模块状态：

```text
request(feedbackId, view)
get(feedbackId, state)
```

`state` 通常是十六进制位图。端口是否占用由对应位判断。

ECoSDetector/RailCom：

```text
get(feedbackId, railcom)
get(feedbackId, railcom[port])
```

事件字段可能形如：

```text
railcom[port,address,direction]
```

RailCom 和 RailComPlus 必须按基础对象返回的能力字段和反馈对象实际字段判断，不要只按硬件型号判断。

## 编程轨

编程轨对象是 `5`。常见 DCC direct byte 流程：

```text
request(5, view)
set(5, mode[readdccdirect], cv[1])
```

写 CV：

```text
request(5, view)
set(5, mode[writedccdirect], cv[1,3])
```

编程结果通过 `<EVENT 5>` 返回，检查 `state[...]` 是否为成功状态。完成后释放订阅：

```text
release(5, view)
```

CV 写入会修改解码器配置，真实设备上必须取得用户确认。

## 实现检查清单

- 连接默认端口 `15471`，支持自定义 IP/端口。
- 逐行累积 `<REPLY>`/`<EVENT>` 块，直到 `<END ...>`。
- 命令生成器正确处理字符串引号、多值选项和换行。
- 事件分发不阻塞同步请求。
- 对 `UnknownOption`、`UnknownObject`、控制权错误和创建等待状态有明确处理。
- 所有写操作都有控制权流程，结束后释放。
- 能力判断优先使用 `protocolversion`、`applicationversion` 和实际字段返回。
