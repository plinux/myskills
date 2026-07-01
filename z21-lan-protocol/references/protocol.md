# Z21 LAN 协议

## 传输层

- 协议：UDP。
- 控制器默认 IP：常见出厂地址 `192.168.0.111`。
- 控制器默认端口：`21105`。
- JMRI 还保留 `21106` 配置项；常规客户端实现应默认使用 `21105`，除非目标系统明确要求其他端口。
- 客户端可以绑定任意本地 UDP 端口；控制器按客户端源地址和源端口返回响应和广播。
- 客户端结束会话时可发送 `LAN_LOGOFF`，该命令无响应。

## Dataset 结构

一个 UDP datagram 可包含一个或多个 dataset。每个 dataset：

```text
uint16 DataLenLE
uint16 HeaderLE
uint8  Data[DataLen - 4]
```

规则：

- `DataLen` 是整个 dataset 长度，包含 `DataLen`、`Header` 和 `Data`。
- `DataLen` 最小为 `4`。
- 外层所有多字节整数使用 little-endian。
- 解码 UDP datagram 时循环读取 dataset：偏移加 `DataLen`，直到 datagram 结束。
- 若剩余字节不足 `4`、`DataLen < 4` 或 `offset + DataLen` 超过 datagram 长度，判定为截断或非法帧。

## Header

| Header | 名称 | 方向 | 用途 |
| --- | --- | --- | --- |
| `0x0010` | `LAN_GET_SERIAL_NUMBER` | C->Z21 / Z21->C | 读取序列号。 |
| `0x0016` | `LAN_GET_MMDCC_SETTINGS` | C->Z21 / Z21->C | 读取 Z21 Maintenance Tool 使用的 MMDCC 设置 payload。 |
| `0x0017` | `LAN_SET_MMDCC_SETTINGS` | C->Z21 | 写入 Z21 Maintenance Tool 使用的 MMDCC 设置 payload，会修改控制器配置。 |
| `0x0018` | `LAN_GET_CODE` | C->Z21 / Z21->C | 读取控制器代码/授权状态。 |
| `0x001A` | `LAN_GET_HWINFO` | C->Z21 / Z21->C | 读取硬件类型和固件版本。 |
| `0x0030` | `LAN_LOGOFF` | C->Z21 | 注销客户端，无响应。 |
| `0x0040` | `LAN_X` | 双向 | X-BUS/XPressNet 隧道。 |
| `0x0050` | `LAN_SET_BROADCASTFLAGS` | C->Z21 | 设置广播标志，无普通响应。 |
| `0x0051` | `LAN_GET_BROADCASTFLAGS` | C->Z21 / Z21->C | 读取广播标志。 |
| `0x0060` | `LAN_GET_LOCO_MODE` | C->Z21 / Z21->C | 读取机车地址模式。 |
| `0x0061` | `LAN_SET_LOCO_MODE` | C->Z21 | 设置机车地址模式。 |
| `0x0070` | `LAN_GET_TURNOUTMODE` | C->Z21 / Z21->C | 读取道岔地址模式。 |
| `0x0071` | `LAN_SET_TURNOUTMODE` | C->Z21 | 设置道岔地址模式。 |
| `0x0080` | `LAN_RMBUS_DATACHANGED` | Z21->C | R-Bus 反馈变化。 |
| `0x0081` | `LAN_RMBUS_GETDATA` | C->Z21 | 请求 R-Bus 组数据。 |
| `0x0082` | `LAN_RMBUS_PROGRAMMODULE` | C->Z21 | 编程 R-Bus 模块地址，会修改模块。 |
| `0x0084` | `LAN_SYSTEMSTATE_DATACHANGED` | Z21->C | 系统状态数据。 |
| `0x0085` | `LAN_SYSTEMSTATE_GETDATA` | C->Z21 | 请求系统状态数据。 |
| `0x0088` | `LAN_RAILCOM_DATACHANGED` | Z21->C | RailCom 数据变化。 |
| `0x0089` | `LAN_RAILCOM_GETDATA` | C->Z21 | 请求 RailCom 数据。 |
| `0x00A0` | `LAN_LOCONET_Z21_RX` | Z21->C | Z21 从 LocoNet 收到的数据。 |
| `0x00A1` | `LAN_LOCONET_Z21_TX` | Z21->C | Z21 发往 LocoNet 的数据。 |
| `0x00A2` | `LAN_LOCONET_FROM_LAN` | C->Z21 | LAN 客户端注入 LocoNet 数据。 |
| `0x00A3` | `LAN_LOCONET_DISPATCH_ADDR` | 双向 | LocoNet 地址 dispatch。 |
| `0x00A4` | `LAN_LOCONET_DETECTOR` | 双向 | LocoNet 探测器。 |
| `0x00C4` | `LAN_CAN_DETECTOR` | 双向 | CAN 检测器反馈。 |
| `0x00C8` | `LAN_CAN_GET_DESCRIPTION` | C->Z21 / Z21->C | 读取 CAN 模块描述。 |
| `0x00C9` | `LAN_CAN_SET_DESCRIPTION` | C->Z21 | 设置 CAN 模块描述，会修改设备。 |
| `0x00CB` | `LAN_CAN_SET_BOOSTER_TRACK_POWER` | C->Z21 | 设置 CAN booster 输出，会改变轨道电源。 |

## 基础只读命令

序列号：

```text
04 00 10 00
```

硬件信息：

```text
04 00 1A 00
```

硬件信息响应 payload 通常包含：

```text
uint32 hardwareTypeLE
uint32 firmwareVersionLE
```

固件版本需要按官方文档和实现约定格式化；本地实现通常转成 major/minor 展示。

读取系统状态：

```text
04 00 85 00
```

`LAN_SYSTEMSTATE_DATACHANGED` payload：

| 偏移 | 字段 | 单位 |
| --- | --- | --- |
| `0` | Main track current | mA |
| `2` | Programming track current | mA |
| `4` | Filtered main track current | mA |
| `6` | Internal temperature | 摄氏度 |
| `8` | Supply voltage | mV |
| `10` | VCC/internal voltage | mV |
| `12` | Central state | bit mask |
| `13` | Central state extension | bit mask |

`Central state`：

| Bit | 含义 |
| --- | --- |
| `0x01` | Emergency stop active。 |
| `0x02` | Track voltage off。 |
| `0x04` | Short circuit。 |
| `0x20` | Programming mode active。 |

`Central state extension`：

| Bit | 含义 |
| --- | --- |
| `0x01` | Temperature too high。 |
| `0x02` | Input voltage too low / power lost。 |
| `0x04` | External booster short circuit。 |
| `0x08` | Main/programming track internal short circuit。 |

## MMDCC 设置

Z21 Maintenance Tool V1.18.3 对 black Z21 的 DCC/MM 与编程轨设置使用 `CFG_ReadMMDCCSettings` / `CFG_WriteMMDCCSettings`，对应 Z21 LAN dataset header `0x0016` / `0x0017`。该命令未出现在公开 Z21 LAN Protocol PDF 的常用命令表中，但通过官方维护工具手册、维护工具 EXE RTTI/反汇编和真实 Z21 只读回包确认。

读取：

```text
04 00 16 00
```

写入：

```text
14 00 17 00 <16-byte MMDCC payload>
```

`LAN_GET_MMDCC_SETTINGS` 返回同样的 `0x0016` header，payload 固定为 16 字节：

| 偏移 | 字段 | 单位/含义 |
| --- | --- | --- |
| `0` | Startup reset packet count | CV 编程序列起始 reset packet 数。 |
| `1` | Continue reset packet count | CV 编程序列中间 reset packet 数。 |
| `2` | Program packet count | CV read/write packet 数。 |
| `3` | Bit verify to one | bit verify 方向/模式。 |
| `4` | External short-circuit increment | 外部短路检测增量。 |
| `5` | Internal short-circuit increment | 内部短路检测增量。 |
| `6` | External short-circuit limit | little-endian word。 |
| `8` | Internal short-circuit limit | little-endian word。 |
| `10` | Programming ACK current | mA 级阈值字段，真实含义按维护工具为准。 |
| `11` | MMDCC flags | bit mask，具体 bit 需继续用维护工具或实机证据确认。 |
| `12` | Output voltage | 主轨输出电压，little-endian mV。 |
| `14` | Programming voltage | 编程轨电压，little-endian mV。 |

实机只读样例：

```text
Request:  04 00 16 00
Response: 14 00 16 00 19 06 07 01 05 14 88 13 10 27 32 80 80 3e 80 3e
```

其中 `80 3e` = `16000mV`，主轨与编程轨电压均为 `16V`。写入时必须先读取当前 16 字节 payload，只修改已确认字段，再整体写回；不要构造缺省 payload 覆盖未理解字段。写入后必须再次读取 `0x0016` 校验目标字段一致。

真实设备风险：

- `LAN_SET_MMDCC_SETTINGS` 会修改控制器持久配置，属于写操作。
- 主轨电压和编程轨电压不应超过控制器电源适配器电压。
- Z21 Maintenance Tool UI 对 black Z21 使用 `11..23V` 范围；实现应在调用层限制到安全范围。
- white z21 / z21 start 不具备可调硬件输出电压；收到未知命令、无回包或读回不一致时必须降级为不支持，不能假定写入成功。
- RailCom 开关在 Maintenance Tool 中另属 common settings，本节 MMDCC payload 未确认 RailCom 写入 bit；不要用 `MMDCCFlags` 猜测 RailCom 写入。

## 广播标志

读取：

```text
04 00 51 00
```

设置：

```text
08 00 50 00 <uint32 flags little-endian>
```

常见 flags：

| Flag | 含义 |
| --- | --- |
| `0x00000001` | X-BUS 电源、机车、道岔相关广播；机车信息通常还需订阅或满足固件行为。 |
| `0x00000002` | R-Bus 变化。 |
| `0x00000004` | 旧式 RailCom 变化，官方和实现中都建议优先使用新版 RailCom 数据标志。 |
| `0x00000010` | Fast Clock 广播，固件 `1.43+`。 |
| `0x00000100` | 系统状态变化。 |
| `0x00010000` | 所有机车变化；固件 `1.20` 到 `1.23` 发送所有机车，`1.24+` 发送变化机车。 |
| `0x00020000` | CAN booster status，固件 `1.41+`。 |
| `0x00040000` | 新版 RailCom data changed，固件 `1.29+`。 |
| `0x00080000` | CAN detector，固件 `1.30+`。 |
| `0x01000000` | LocoNet 数据，不含机车和道岔。 |
| `0x02000000` | LocoNet 机车数据。 |
| `0x04000000` | LocoNet 道岔数据。 |
| `0x08000000` | LocoNet 占用检测器数据。 |

设置广播标志会改变控制器对该客户端的推送行为。真实控制器上默认先读取现有 flags；只有用户同意监听特定广播时才设置。

## LAN_X / X-BUS 隧道

`LAN_X` dataset：

```text
DataLenLE HeaderLE=40 00 XHeader DB... XOR
```

规则：

- `XHeader`、`DB` 和末尾 XOR checksum 属于 X-BUS/XPressNet 层。
- checksum 是 X-BUS payload 的异或校验；生成或校验时不要包含外层 `DataLen`/`Header`。
- 外层小端规则不改变 X-BUS payload 内的字段顺序；例如地址常按 high byte 再 low byte 放入。
- `LAN_X` 响应可能是直接回复，也可能是广播事件。

常见 `LAN_X`：

| XHeader / DB | 名称 | 用途 |
| --- | --- | --- |
| `21 21` | `LAN_X_GET_VERSION` | 读取 X-BUS 版本。 |
| `21 24` | `LAN_X_GET_STATUS` | 读取中央状态。 |
| `21 80` | `LAN_X_SET_TRACK_POWER_OFF` | 关闭轨道电源。 |
| `21 81` | `LAN_X_SET_TRACK_POWER_ON` | 打开轨道电源。 |
| `61 00` | `LAN_X_BC_TRACK_POWER_OFF` | 轨道电源关闭广播。 |
| `61 01` | `LAN_X_BC_TRACK_POWER_ON` | 轨道电源打开广播。 |
| `61 08` | `LAN_X_BC_TRACK_SHORT_CIRCUIT` | 短路广播。 |
| `61 82` | `LAN_X_UNKNOWN_COMMAND` | 未知命令。 |
| `62 22 ...` | `LAN_X_STATUS_CHANGED` | 中央状态变化。 |
| `80` | `LAN_X_SET_STOP` | 全局 emergency stop。 |
| `81` | `LAN_X_BC_STOPPED` | emergency stop 广播。 |
| `E3 F0 ...` | `LAN_X_GET_LOCO_INFO` | 请求机车信息。 |
| `E4 10/12/13 ...` | `LAN_X_SET_LOCO_DRIVE` | 设置机车速度方向。 |
| `E4 F8 ...` | `LAN_X_SET_LOCO_FUNCTION` | 设置机车功能。 |
| `EF ...` | `LAN_X_LOCO_INFO` | 机车信息回复/广播。 |
| `43 ...` | `LAN_X_GET_TURNOUT_INFO` 或 `LAN_X_TURNOUT_INFO` | 请求/返回道岔状态。 |
| `53 ...` | `LAN_X_SET_TURNOUT` | 设置道岔输出。 |
| `44 ...` | `LAN_X_GET_EXT_ACCESSORY_INFO` 或 `LAN_X_EXT_ACCESSORY_INFO` | 扩展附件状态。 |
| `54 ...` | `LAN_X_SET_EXT_ACCESSORY` | 设置扩展附件。 |
| `F1 0A` | `LAN_X_GET_FIRMWARE_VERSION` | 读取固件版本。 |
| `F3 ...` | `LAN_X_GET_FIRMWARE_VERSION_REPLY` | 固件版本回复。 |

`LAN_X_GET_STATUS` 的常见响应为：

```text
LAN_X: 62 22 <central_state> <xor>
```

`central_state` 使用与 `LAN_SYSTEMSTATE_DATACHANGED` 相同的基础状态位，例如 `0x02` 表示 track voltage off。

## 机车

读取机车信息：

```text
LAN_X: XHeader=E3 DB0=F0 AddrHigh AddrLow XOR
```

地址编码：

- 短地址：`AddrHigh=0x00`，`AddrLow=address & 0x7F`。
- 长地址：`AddrHigh=0xC0 | (address >> 8)`，`AddrLow=address & 0xFF`。
- 解码地址时用 `(AddrHigh & 0x3F) << 8 | AddrLow`；`AddrHigh & 0xC0 == 0xC0` 表示长地址。

设置速度方向：

```text
LAN_X: XHeader=E4 DB0 AddrHigh AddrLow SpeedAndDirection XOR
```

`DB0`：

| DB0 | 速度级 |
| --- | --- |
| `0x10` | 14 speed steps |
| `0x12` | 28 speed steps |
| `0x13` | 126/128 speed steps |

`SpeedAndDirection`：

- `0x80` 方向位表示正向。
- 低 7 位是速度级；具体 emergency stop 和速度级映射按 X-BUS 规则处理。

设置功能：

```text
LAN_X: XHeader=E4 DB0=F8 AddrHigh AddrLow FunctionByte XOR
```

`FunctionByte`：

- bit `0..5` 是功能号，常用 `F0..F28`，新固件机车信息可到 `F31`。
- bit `6..7` 是操作类型：`00` off，`01` on，`10` toggle，`11` invalid。

机车信息 `LAN_X_LOCO_INFO`：

- 包含地址、速度级编码、busy 标志、速度方向、F0-F28。
- 固件 `1.42+` 的消息可增加 F29-F31；解析器必须按 `DataLen` 判断是否存在。

## 道岔和扩展附件

普通道岔地址：

- 协议内原始地址比用户看到的 Z21/WLANmaus 道岔号小 `1`。
- 用户道岔号范围通常按 `1..2048` 处理，发送前减 `1`。

请求道岔状态：

```text
LAN_X: XHeader=43 AddrMSB AddrLSB XOR
```

设置道岔：

```text
LAN_X: XHeader=53 AddrMSB AddrLSB DB2 XOR
```

`DB2`：

| Bit | 含义 |
| --- | --- |
| `0x01` | 输出端口/方向。 |
| `0x08` | 激活输出。 |
| `0x20` | 加入队列。 |
| `0x80` | 固定置位。 |

扩展附件：

- `LAN_X_EXT_ACCESSORY_INFO` 使用 XHeader `0x44`。
- `LAN_X_SET_EXT_ACCESSORY` 使用 XHeader `0x54`。
- 地址编码与普通道岔不同，本地实现对扩展附件地址使用 `address + 3` 的原始值；实现时必须单独处理。

## 编程和 CV

Service mode CV 读：

```text
LAN_X: XHeader=23 DB0=11 CVHigh CVLow XOR
```

Service mode CV 写：

```text
LAN_X: XHeader=24 DB0=12 CVHigh CVLow Value XOR
```

规则：

- 协议内 CV 地址通常发送 `cv - 1`。
- 读写结果通过 `LAN_X_CV_RESULT` 或 NACK 类消息返回。
- CV 写入会修改解码器；真实设备必须得到用户明确授权。

## R-Bus、RailCom、LocoNet、CAN

R-Bus：

- `LAN_RMBUS_GETDATA` 请求 group `0` 或 `1`。
- `LAN_RMBUS_DATACHANGED` 返回组内反馈位。
- `LAN_RMBUS_PROGRAMMODULE` 会给模块写地址，默认视为高风险写操作。

RailCom：

- `LAN_RAILCOM_GETDATA` 可用地址 `0` 请求下一条地址数据，或指定机车地址。
- `LAN_RAILCOM_DATACHANGED` 每条记录长度 `13` 字节，记录数为 `(DataLen - 4) / 13`。
- 记录包含地址、receive counter、error counter、options、可选 speed、可选 QoS。

LocoNet：

- `LAN_LOCONET_Z21_RX`、`LAN_LOCONET_Z21_TX` 是控制器侧收发事件。
- `LAN_LOCONET_FROM_LAN` 会把 LAN 客户端数据注入 LocoNet，总是写操作。
- LocoNet 广播需要对应 broadcast flags。

CAN：

- `LAN_CAN_DETECTOR` 用于 CAN 反馈/RailCom 类检测器消息。
- `LAN_CAN_GET_DESCRIPTION` 读取模块描述。
- `LAN_CAN_SET_DESCRIPTION` 修改模块描述。
- `LAN_CAN_SET_BOOSTER_TRACK_POWER` 改变 booster 输出电源状态。

## 只读测试建议

真实控制器只读探测优先使用：

```text
LAN_GET_SERIAL_NUMBER
LAN_GET_HWINFO
LAN_GET_BROADCASTFLAGS
LAN_SYSTEMSTATE_GETDATA
LAN_X_GET_VERSION
LAN_X_GET_STATUS
LAN_X_GET_FIRMWARE_VERSION
```

避免默认执行：

- `LAN_SET_MMDCC_SETTINGS`
- `LAN_SET_BROADCASTFLAGS`
- `LAN_X_SET_TRACK_POWER_ON/OFF`
- `LAN_X_SET_STOP`
- `LAN_X_SET_LOCO_*`
- `LAN_X_SET_TURNOUT`
- `LAN_X_SET_EXT_ACCESSORY`
- `LAN_X_CV_WRITE`
- `LAN_RMBUS_PROGRAMMODULE`
- `LAN_LOCONET_FROM_LAN`
- `LAN_CAN_SET_DESCRIPTION`
- `LAN_CAN_SET_BOOSTER_TRACK_POWER`
