# DXDCNet V3.11 协议蒸馏

来源：《DXDCNet 协议说明》V3.11，发布日期 2025-12-23；官方 `DigsightDemo_2025_12` C# Demo；官方 Android D9000 App 反编译源码；2026-06-20 对 `10.10.200.98` 的只读 UDP 状态/版本实测。本文是供 Agent 执行任务使用的压缩参考，不是原文逐字转写。

证据优先级：厂家已说明文档可能不准确；遇到 PDF/网页文档、旧 Demo、App 反编译和真实抓包互相冲突时，以实机抓包和真实设备回包为最高优先级。App 反编译可用于推测待测命令，PDF/网页文档用于补充字段名和背景，但不能覆盖已验证回包。

## 导航

- 基础结构：物理层、CAN 标准帧、CAN 扩展帧和网络 ID。
- 命令字速查：按网络管理、模型控制、设备状态、参数升级分类。
- 载荷定义：机车、附件、设备状态、参数和 D9000 地址。
- UDP 封装：官方 Demo、Android App 与实机确认过的 UDP 字节布局、校验、端口和测试向量。

## 基础结构

### 物理层

| 项 | 定义 |
| --- | --- |
| 上位机通讯 | 网络接口，UDP 数据包传输 |
| 模块间通讯 | CAN 总线，RJ45 接口 |
| CAN 速率 | 250000 b/s |
| RJ45 线序 | 1 DCC_L，2 +12V，3 GND，4 CAN-H，5 CAN-L，6 GND，7 +12V，8 DCC_R |

### MAC 和网络 ID

- 每个器件有 96 bit / 12 byte MAC。
- 文档把 MAC 分成 `MAC-U`、`MAC-H`、`MAC-L`，每组 4 byte。
- 网络 ID/器件地址常用 7 bit 表示为 `0aaaaaaa`。
- 设备类型是 4 bit，和网络 ID 分开编码。

### CAN 标准帧

常见标准帧头在表格中写为：

```text
SIDH = aaaaaaaB
SIDL = 00000BBB
```

可按下列方式理解：

```text
sourceId   = aaaaaaa          # 7 bit
deviceType = BBBB             # 4 bit
SIDH = (sourceId << 1) | ((deviceType >> 3) & 0x01)
SIDL = deviceType & 0x07      # 高 5 bit 为 0
```

文档总览写法为：

```text
0 aaaaaaaBBBB 0 00LLLL CCCCCCCC ... DDDDDDDD
```

其中 `LLLL` 是 CAN DLC，`CCCCCCCC` 是命令字。表格中的 `DLC` 包含命令字本身。

### CAN 扩展帧

中继型扩展帧为预留格式：

```text
0 aaaaaaa0100 11 000000BBBBAAAAAAAA 0 00LLLL 0CCCCCCC...
```

字段含义：

| 字段 | 含义 |
| --- | --- |
| `aaaaaaa` | 源设备地址 |
| `CCCCCCC` | 命令字 |
| `BBBB` | 中继转发命令的源设备类型 |
| `AAAAAAAA` | 中继设备地址 |

特定型扩展帧用于器件申请 DXDCNet ID。29 bit 标识符取 MAC_U 的部分位：

```text
SID_EXT = (MAC_U & 0x1FFF) | ((MAC_U & 0xFFFF0000) >> 3)
```

申请网络 ID 的专用扩展帧数据区装载剩余 64 bit MAC，即 `MAC_H` 和 `MAC_L`。

## 设备类型

| 代码 | 设备类型 |
| --- | --- |
| `0x0` | Command Station / NMT，网络中只能有一个 |
| `0x1` | 手柄/电脑，支持 128 个 |
| `0x2` | 信号控制模块，支持 128 个 |
| `0x3` | 反馈检测接收，支持 128 个 |
| `0x4` | 中继设备 XpressNet，支持 128 个 |
| `0x5` | 中继设备 LocoNet，支持 128 个 |
| `0x6` | 道岔控制模块，支持 128 个 |
| `0x7` | Booster，支持 128 个 |
| `0x8` | 无线命令中心，支持多个 |
| `0xC` | 汽车控制模块 |
| `0xD` | 电源板及通讯中心 1003 |
| `0xE` | 红外信号发射模块，支持 127 个 |
| `0xF` | 特殊设备类型；地址 0 表示编程器，其他保留 |

`0x9`、`0xA`、`0xB` 在文档中为空白保留。

## 命令字速查

### 网络管理类

| 命令 | 代码 | 说明 |
| --- | --- | --- |
| NMT 问询 | `0x00` | 扩展帧，使用 Command Station MAC 派生 SID_EXT |
| NMT 问询应答 | `0x01` | 标准帧，Command Station 类型和地址 |
| 申请网络 ID | `0x02` | 专用扩展帧，携带 MAC_H/MAC_L |
| 申请网络 ID 应答 | `0x03` | 分配 `0AAAAAAA` 网络 ID |
| 请求机车控制 | `0x04` | 按机车地址请求控制权 |
| 强制机车控制 | `0x05` | 强制取得控制 |
| 解除机车控制 | `0x06` | 指定被解除控制权的设备 ID |
| 机车控制应答 | `0x07` | 返回获得控制权的设备类型和 ID |
| 释放机车控制 | `0x08` | 主动释放指定机车 |
| 请求网络器件 ACK | `0x09` | 按目标类型和 ID 请求 ACK |
| 网络器件 ACK | `0x0A` | 设备回应存在 |
| 请求目标器件 MAC 地址 | `0x0B` | 按目标类型和 ID 请求 |
| 目标器件广播自身 MAC 地址 | `0x0C` | 分两包广播 12 byte MAC |
| 总线数据错误包 | `0x0D` | 表示先前数据无法处理 |
| 数据包传输 | `0x0E` | 命令表如此写；正文第 15 项也把 RailCom 信息上报写成 `0x0E` |
| RAILCOM 数据下发 / 设置网络 ID | `0x0F` | 命令表对 `0x0F` 有重复定义，需按设备和抓包确认 |

### 模型控制类

| 命令 | 代码 |
| --- | --- |
| 控制机车速度 | `0x10` |
| 控制机车功能 | `0x11` |
| 控制附件解码器 | `0x12` |
| 控制道岔解码器 | `0x13` |
| 编程轨，标准模式 | `0x14` |
| 编程轨反馈 ACK | `0x15` |
| 编程轨，慢速模式 | `0x16` |
| 编程轨返回值 | `0x17` |
| 机车速度状态 ACK | `0x18` |
| 机车功能状态 ACK | `0x19` |
| 汽车状态反馈 | `0x1A` |
| LOCO BLOCK 反馈 | `0x1B` |
| 汽车速度功能控制 | `0x1E` |
| 直接封装 DCC 指令包 | `0x8A` |

命令表中 `0x19` 另有空白重复行，按冲突处理。

`0x8A` 来自官方 Demo `T_COMMAND_DCC_PACKET`，C# 注释标为 V2.2 增加；PDF 命令表未必列出该项，使用时注明来源。

### 设备状态类

| 命令 | 代码 |
| --- | --- |
| 设置轨道输出 | `0x20` |
| 设置 Booster 电流阀值 | `0x21` |
| 请求网络设备状态 | `0x22` |
| 网络设备回报状态 | `0x23` |
| Booster 报警 | `0x24` |
| 请求机车状态 | `0x2A` |
| 机车回报状态 | `0x2B` |

### 参数、升级和配置

| 命令 | 代码 |
| --- | --- |
| 设置网络器件参数 | `0x40` |
| 读取网络器件参数 | `0x41` |
| 网络器件返回参数 | `0x42` |
| 升级起始 | `0x80` |
| 升级数据发送 | `0x81` |
| RESET 目标网络器件 | `0x82` |
| RESET 目标器件 | `0x83` |
| 请求设备型号及软硬件版本 | `0x84` |
| 设备应答自身型号及软硬件版本 | `0x85` |
| 执行设备配置 | `0xE0` |
| 传输配置数据 | `0xE1` |
| 设备网络通讯控制 | `0xE3` |
| 设备执行反馈 | `0xEA` |

升级帧和设备配置帧在 PDF 中只列命令字，没有给出详细载荷。

## 载荷定义

以下 `data[n]` 指命令字之后的载荷字节；表格 `DLC` 仍以原文为准，包含命令字。

### 网络管理帧

| 编号 | 命令 | DLC | 载荷 |
| --- | --- | ---: | --- |
| 1 | NMT 问询 `0x00` | 1 | 使用扩展帧；SID_EXT 由 Command Station `MAC_U` 计算 |
| 2 | NMT 问询应答 `0x01` | 1 | 标准帧；Command Station 类型和地址为 0 |
| 3 | 申请网络 ID | 8 | 专用扩展帧；SID_EXT 由 MAC_U 计算；8 byte 数据为 MAC_H 和 MAC_L |
| 4 | 申请网络 ID 应答 `0x03` | 6 | `data[0..3]` 为等待回应器件的 SID_EXT 拆分，`data[4]=0AAAAAAA`；没有可分配 ID 时不回应 |
| 5 | 请求机车控制 `0x04` | 3 或 8 | 基本载荷为 `Addr_L, Addr_H`；扩展载荷增加厂家 ID 和机车 MAC |
| 6 | 强制机车控制 `0x05` | 3 | `Addr_L, Addr_H` |
| 7 | 解除机车控制 `0x06` | 4 | `Addr_L, Addr_H, 0aaaaaaa`，最后一字节是被解除控制权设备 ID |
| 8 | 机车控制应答 `0x07` | 4 | `Addr_L, Addr_H, 0000ssss, 0aaaaaaa`；`ssss` 为设备类型，ID 为 0 表示控制器无法处理新申请 |
| 9 | 释放机车控制 `0x08` | 3 | `Addr_L, Addr_H` |
| 10 | 请求网络器件 ACK `0x09` | 3 | `0000BBBB, 0aaaaaaa`，目标设备类型和 ID |
| 11 | 网络器件 ACK `0x0A` | 1 | 无额外载荷 |
| 12 | 获取目标器件 MAC `0x0B` | 3 | `0000BBBB, 0aaaaaaa`；当类型为特殊设备且目标是 D9000 时，第二字节表示 MAC 位置 |
| 13 | 目标器件广播 MAC `0x0C` | 8 | 两包：`data[0]=0` 携带 `Mac5..Mac0`，`data[0]=1` 携带 `Mac11..Mac6`；D9000 特殊值见下 |
| 14 | 总线错误包 `0x0D` | 3 | `0000BBBB, 0aaaaaaa`，表示先前该类型和 ID 的数据无法处理 |
| 15 | RailCom/数据包 | 6 | 正文写命令 `0x0E`；`data[0]=AXXXXXXX`，`A=0` 为数据包描述，`A=1` 为数据，`XXXXXXX` 为序列号 |

D9000 MAC 位置特殊值：

| Byte1 | 含义 |
| --- | --- |
| `0x01` | 有线网络 MAC |
| `0x02` | MT7620/76x8 无线模块 MAC |
| `0x03` | RT3070/MT7601 无线模块 MAC |

### 机车速度和功能

| 命令 | 代码 | DLC | 载荷 |
| --- | --- | ---: | --- |
| 控制机车速度 | `0x10` | 5 | `Addr_L, Addr_H, Dsssssss, 00000yyy` |
| 反馈机车速度 | `0x18` | 5 | 同控制机车速度 |
| 控制机车功能 | `0x11` | 5 | `Addr_L, Addr_H, nn0XFFFF, FFFFFFFF` |
| 反馈机车功能 | `0x19` | 5 | 同控制机车功能 |

机车地址字段：

- `Addr_L = address & 0xFF`。
- `Addr_H` 不是普通地址高字节。2026-06-22 对 `~/Downloads/nodejstest/src/function/index.ts` 的可工作实现核对显示，`address <= 127` 时 `Addr_H=0x00`；`address > 127` 时 `Addr_H = 0x80 | ((address >> 8) & 0x3F)`。
- 这与 NMRA DCC 车辆地址分区一致：7-bit short address 使用 `0AAA-AAAA`；14-bit long address 在原始 DCC packet 中是 `11A13..A8, A7..A0`，CV17 bits6..7 固定为 `11`、bits0..5 为 `A13..A8`，CV18 为 `A7..A0`。DXDCNet 的 `Addr_H` 可理解为把 DCC 长地址高 6 bit 保留在低位，并用 bit7 标记长地址；不要直接发送 `(address >> 8) & 0xFF`。
- 例：地址 `4945 / 0x1351`，DCC 长地址第一 byte 为 `0xD3`、第二 byte 为 `0x51`；DXDCNet 载荷地址字段应为 `Addr_L=0x51, Addr_H=0x93`。地址 `2042 / 0x07FA` 应为 `FA 87`，地址 `128` 应为 `80 80`，地址 `9999` 应为 `0F A7`。
- 请求速度或功能前应先通过 `0x04` 请求机车控制；若收到 `0x07` 且 `granted_id=0` 或授权设备不是当前 Throttle，表示控制器拒绝当前控制。官方 Android App 反解析确认，若未收到 `0x07` 控制权 ACK，App 仍允许继续发送后续 `0x10/0x11` 用户速度/功能操作；已知 `nodejstest` 的 Web 流程也是先发 `0x04`，再由用户后续动作发送速度或功能命令。实现动芯 App 兼容路径时应保留该容错行为，并把未收到 ACK 记录为调试字段；不要把它推广为通用 DCC 或其它控制器规则。

速度字段：

| 字段 | 含义 |
| --- | --- |
| `D` | 机车方向，0/1 |
| `sssssss` | 速度值 |
| `yyy=000` | 14 级 |
| `yyy=001` | 28 级 |
| `yyy=010` | 128 级 |

功能组字段：

| 组 | 第三字节 | 第四字节 |
| --- | --- | --- |
| `000X` | `XFFFF` 表示 F0,F4,F3,F2,F1 | F12..F5 |
| `010X` | `XFFFF` 保留 | F20..F13 |
| `1000` | 低位保留 | F28..F21 |
| `1001` + low `1000` | 分页 | F36..F29 |
| `1001` + low `1001` | 分页 | F44..F37；原文疑似重复写 F41 |
| `1001` + low `1010` | 分页 | F52..F45 |
| `1001` + low `1011` | 分页 | F60..F53 |
| `1001` + low `1100` | 分页 | F68..F61 |
| `11**` | 保留 | 保留 |

### 附件、道岔和汽车

附件解码器控制 `0x12`，DLC 4：

```text
data[0] = AAAAAAAA
data[1] = mknnnAAA
data[2] = xxxxxxxx
```

| 位 | 含义 |
| --- | --- |
| `m=0` | 操作 DXDCNet 设备 |
| `m=1` | 操作 DCC 设备 |
| `k=0` | 发送控制 |
| `k=1` | 问询状态 |
| `nnn=000` | 9 位附件解码器地址 |
| `nnn=100` | 11 位附件解码器地址 |
| `nn=11` | 附件设备板地址和端口 |
| `xxxxxxxx=Cd0000DD` | DCC 9 位地址控制；`DD` 输出口，`C` 开关，`d` 为 port 中 0/1 口 |
| `xxxxxxxx=CdMXXXXX` | DXDCNet 附件板；`M=0` 使用 C/d，`M=1` 使用设备指定模式 |

灯光控制模式：`C=开` 点亮 A 灯，`C=关` 点亮 B 灯。

道岔解码器控制 `0x13`，DLC 4：

```text
data[0] = AAAAAAAA
data[1] = nnAAAAAA
data[2] = xxxxxxxx
```

| `n/nn` | 含义 |
| --- | --- |
| `00` | 9 位附件解码器地址，`xxxxxxxx=Cd0000DD` |
| `01` | 11 位附件解码器地址，`xxxxxxxx=000XXXXXX` 为设备指定模式 |
| `11` | 附件设备板地址和端口，`xxxxxxxx=CdMXXXXX` |

电磁扳道器：`C=开` 驱动一次。舵机扳道器：`C=开` 向左，`C=关` 向右。

汽车控制和反馈：

| 命令 | 代码 | DLC | 载荷 |
| --- | --- | ---: | --- |
| 汽车控制 | `0x1E` | 4 | `carAddr, speed, function`，function 为 F8..F1 |
| 汽车反馈 | `0x1A` | 5 | `carAddr, positionH, positionL, coulomet`；地址大于等于 N 时表示其他无线设备状态/位置，N 通常为 50 |

### LOCO BLOCK 反馈

命令 `0x1B`，DLC 8：

```text
data[0] = Gtttpppp
data[1] = N0xxxxxx
data[2] = xxxxxxxx
```

| 字段 | 含义 |
| --- | --- |
| `G` | 1 占用，0 空闲 |
| `ttt` | 反馈数据类型；`000` 车号，`111` 区间短路，其他待定 |
| `ppppppp` | 端口号；第一字节低 4 位和第二字节相关位共同使用时需按抓包确认 |
| `N=0` | 7 位车头地址在第三字节 |
| `N=1` | 14 位车头地址在第二字节低 6 位和第三字节 |
| 地址为 0 | 车号不定，仅表示区间占用 |

### 设备状态

轨道输出开关控制 `0x20`，DLC 4：

```text
data[0] = 0aaaaaaa    # 目标设备 ID
data[1] = Abcd----    # 输出状态位
data[2] = xxxxxxxx    # 输出量 0-255
```

| 位 | 含义 |
| --- | --- |
| `A` | 轨道上电状态，0 未上电，1 已上电 |
| `B` | DCC 模式 0，DC 模式 1 |
| `C` | DC 模式下电流方向 |
| `D` | 是否自动发送报告 |

PDF/旧 Demo 输出量参考：G 比例 `0xF9` 约 18.01 V，HO 比例 `0xF3` 约 15.2 V，N 比例 `0xE8` 约 12 V。

官方 Android App V3 `_DXDCNET_BOOSTER_OUTPUT_V` 输出枚举：N `0x78`，HO `0xA0`，G `0xB4`，OFF `0x00`；设置菜单还出现 N `0x6E`、HO `0x8C`、G `0xAA`。该值与 PDF/旧 Demo 冲突，当前 D9000 App 兼容实现优先按 Android V3 枚举处理，并在结果中标注版本冲突。

2026-06-22 使用 `~/Downloads/nodejstest` 可工作程序核对，并对 `10.10.200.98`、HO 地址 3 实车做最小控制验证：DCC 轨道输出命令的状态位不应设置 DC 方向位 `C/0x20`。N/HO/G DCC 通电的 `data[1]` 应为 `0x90`，不是 `0xB0`；DC 方向位只用于 DC 模式。参考帧：

- N DCC 通电：`ff ff 17 01 20 01 90 78 df`。
- HO DCC 通电：`ff ff 17 01 20 01 90 a0 07`，实机返回 `0x23` 且 `power_on=True`。
- G DCC 通电：`ff ff 17 01 20 01 90 b4 13`。
- HO 地址 3 控制申请：`ff ff 16 01 04 03 00 10`；F0 开：`ff ff 18 01 11 03 00 10 00 1b`；F0 关：`ff ff 18 01 11 03 00 00 00 0b`。实机返回 `0x19` 功能状态 true/false。

Booster 电流保护阀值 `0x21`，DLC 4：`targetId, threshold`。请求网络设备状态 `0x22`，DLC 3：`targetType, targetId`。

官方 Demo/App 的 `0x22` / `0x84` 请求 UDP 载荷均为 2 字节：`targetType & 0x0F, targetAddress`。发送方设备类型使用手柄/电脑 `0x1`；Android App 源地址使用 `ThrottleID=1`，PC Demo/实机手工测试也见过源地址 `0x00`。

网络设备回报状态 `0x23`，DLC 8：

| 设备 | 数据含义 |
| --- | --- |
| Infrared | 文档写 NULL |
| 6103 | byte1 开关状态 8..1，byte2 短路状态 8..1 |
| Detector | byte1 占用状态 15..8，byte2 占用状态 7..0 |
| Command Station ID 0x00 | byte1 总线电压，byte2 总线电流，byte3 编程轨电压，byte4 编程轨电流，byte5 编程轨状态：`0x00` 空闲，`0x80` 忙 |
| Booster | PDF 写作 byte1 设置电压，byte2 输出电压乘 0.1185，byte3 输入电压乘 0.1185，byte4 输出电流乘 0.0111，byte5 温度，byte6 状态位；Android App V3 `DeviceFeedback` 实际读取 data[5] 设置电压、data[6] 输出电压、data[7] 输出电流、data[8] 温度、data[11] 状态位，显示公式使用 `*0.1` V/A |

Booster 状态位 byte6：

| 位 | 含义 |
| --- | --- |
| A | 轨道上电 |
| B | DCC/DC 模式 |
| C | DC 电流方向 |
| D | 自动发送报告 |
| E | 预留 |
| F | 输入电压报警 |
| G | 温度报警 |
| H | 过电流报警 |

请求机车状态 `0x2A`，DLC 3：`Addr_L, Addr_H`。

机车回报状态 `0x2B`，DLC 8：

| 字节 | 含义 |
| --- | --- |
| data0 | Addr_L |
| data1 | Addr_H |
| data2 | `Dvvvvvvv`，方向和速度 |
| data3 | `KKKABCDE`，速度模式和 F0,F4,F3,F2,F1 |
| data4 | F5..F12 |
| data5 | F13..F20 |
| data6 | F21..F28 |

Booster 报警 `0x24`，DLC 2：`000000xx`。原文说明报警内容对应网络设备回报状态中的报警位，具体位映射需按设备确认。

### 器件参数

| 命令 | 代码 | DLC | 载荷 |
| --- | --- | ---: | --- |
| 参数设置 | `0x40` | 原表写 3，但列出 4 个载荷字段 | `targetType, targetId, paramAddress, value` |
| 参数读取 | `0x41` | 3 | `targetType, targetId, paramAddress` |
| 参数返回 | `0x42` | 3 | `paramAddress, value` |

参数设置的 DLC 与表格列数存在冲突：命令字加 4 个载荷字节应为 5。实现前需用抓包或设备验证。

### 编程轨 Programmer

官方 Android App V3 `digsight.Netpacket.V3.Programmer` 确认 CV 编程使用命令 `0x14`，发送方设备类型为手柄/电脑 `0x1`，源地址使用 `ThrottleID`，App 默认 `1`。

普通 service-mode direct read/write 的 `0x14` 载荷为 3 字节：

```text
data[0] = mmmooorr
data[1] = register_low
data[2] = value
```

| 字段 | 含义 |
| --- | --- |
| `mmm` | programmer mode：direct read `4`，direct write `7`，direct bit `6`，direct check `5` |
| `ooo` | programmer op：normal `0`，accessory `1`，decoder MAC `3`，main loco POM `6`，main accessory POM `7` |
| `rr` | CV register 高 2 bit；CV register 为 `cv_number - 1` |
| `register_low` | CV register 低 8 bit |
| `value` | direct read 为 `0`；direct write 为写入值 `0..255` |

测试向量：

| 操作 | UDP 帧 |
| --- | --- |
| CV1 direct read，ThrottleID 1 | `FF FF 17 01 14 80 00 00 82` |
| CV1 direct write `3`，ThrottleID 1 | `FF FF 17 01 14 E0 00 03 E1` |
| CV8 direct read，ThrottleID 1 | `FF FF 17 01 14 80 07 00 85` |

官方 Android App V3 还确认主轨 POM 使用同一个 `0x14` Programmer 命令。`digsight.Netpacket.V3.Programmer(int, op, mode, pomAddress, register, value)` 对 `T_MAIN_LOCO_POM=6` 或 `T_MAIN_ACCE_POM=7` 使用 11 字节 UDP 包，载荷在普通 3 字节后追加两字节 POM 目标地址：

```text
data[0] = mmmooorr
data[1] = register_low
data[2] = value
data[3] = pom_address_low
data[4] = pom_address_high
```

App `TabCv5` 主轨 CV 页面在勾选主轨后构造 `new Programmer(1, T_MAIN_LOCO_POM, T_DIRECT_READ_MODE, pomAddress, cv - 1, 0)` 读取，写入使用 `T_DIRECT_WRITE_MODE`，写入后延迟约 `200 ms` 再用同一 POM 地址读取回校验。App 主轨读写等待循环为 `200 * 10 ms`，即约 `2 s`。主轨 POM 前 UI 要求轨道已上电、车辆地址 `1..9999`、CV 地址 `1..1024`。

主轨 POM 测试向量：

| 操作 | UDP 帧 |
| --- | --- |
| 车辆地址 1000，CV8 direct read，ThrottleID 1 | `FF FF 19 01 14 98 07 00 E8 03 78` |
| 车辆地址 12，CV1 direct write `3`，ThrottleID 1 | `FF FF 19 01 14 F8 00 03 0C 00 FB` |

`0x15` Programmer ACK 回包载荷至少 3 字节：

```text
data[0] = ack_mode
data[1] = programmer_device_type
data[2] = programmer_device_id
```

ACK mode：busy `0`，overload `1`，noack `2`，ack `3`，nopower `4`，noloc `7`。

`0x17` Programmer value 回包载荷至少 5 字节：

```text
data[0] = mmm000rr
data[1] = register_low
data[2] = value
data[3] = programmer_device_type
data[4] = programmer_device_id
```

App CV 读取逻辑会匹配 `programmer_device_id == ThrottleID`，并把 `register + 1` 作为 CV 编号。主轨 POM 的 `0x17` value 回包可为 7 字节，`data[5]=pom_address_low`、`data[6]=pom_address_high`；主轨实现应同时匹配 CV、ThrottleID 和 POM 地址。

### RailCom / RailCom+

命令 `0x0E` 为 RailCom/数据包上报。官方 Android App V3 `RailComData` 解析 11 字节包：`data[5]` 高位为 `isData`，低 7 bit 为分片位置；`data[6]` 在首包表示分片数量，在数据包中同时作为 4 字节片段的第 1 字节；`data[6..9]` 为 4 字节数据片段。

App `MainActivityData.COMMAND_RAILCOM` 逻辑为：首个 `isData=false` 包创建 `railcomplusdata(size)`；后续 `isData=true` 包按 `position` 写入 4 字节片段；收满后按 `railcomplusdata` 解析 RailCom+ 数据。`railcomplusdata` 当前确认字段：

| 偏移 | 字段 |
| --- | --- |
| `0` | 厂商 ID / factory id，1 字节 |
| `4..7` | decoder id，低字节在前 |
| `8` | CV1 |
| `9` | CV17 |
| `10` | CV18 |
| `11` | CV29 |
| `14..15` | loco image，高字节在前 |
| `16..43` | decoder name，最长 28 字节，以 `0x00` 截断 |

D9000 参数 `0x03` 是 RailCom 开关，App 写入 `0x80` 表示开，`0x00` 表示关；读取时按 `value & 0x80` 判断。


## D9000 参数地址

| 地址 | 含义 |
| --- | --- |
| `0x03` | RailCom：`0x80` 开，`0x00` 关 |
| `0x04` | `0x00..0xFF * 20` 为实际电流保护值 mA |
| `0x7E` | 屏幕亮度；2026-06-20 实测 `0x80` 对应 App 亮度 128 |
| `0x80` | OLED 方向；2026-06-20 实测用户设为“右”后回包 `0x02`，并由用户确认 App 方向按顺时针递增循环，映射为 `0x02=右`、`0x03=下`、`0x00=左`、`0x01=上` |
| `0x81` | N 模式电流保护值；2026-06-20 实测原始值按 `40 mA` 倍数换算 |
| `0x82` | HO 模式电流保护值；2026-06-20 实测原始值按 `40 mA` 倍数换算 |
| `0x83` | G 模式电流保护值；2026-06-20 实测原始值按 `40 mA` 倍数换算 |
| `0x84` | DC 模式电流保护值；2026-06-20 实测原始值按 `40 mA` 倍数换算 |

注：D9000 `0x81..0x84` 的旧文档 `1/50 A` 或 `20 mA` 倍数与 2026-06-20 用户 App 设置和实机回包对比冲突。协议实现当前应以实测 `40 mA` 为准，并在需要兼容旧设备时单独标注版本证据。

### 直接封装 DCC 指令包

官方 Demo `enpkgDccPacket` 构造 `0x8A` UDP 包：

```text
FF FF BBBBLLLL sourceId 8A <raw DCC packet bytes> checksum
```

已确认字段：

| 字段 | 含义 |
| --- | --- |
| 设备类型 | `0x1`，手柄/电脑 |
| 源地址 | Demo 构造时常用 `0x00` |
| 命令字 | `0x8A`，完整 8 bit 保留 |
| 载荷 | 从 UDP 字节 5 开始直接复制原始 DCC packet |
| 长度 | 整个 UDP 数据报长度减去 2 字节 `FF FF` 包头 |
| 校验 | 按“UDP 封装”中的 XOR 规则计算 |

该构造只确认“如何承载原始 DCC packet”。官方 Android App 的 CV service-mode 路径已确认使用上文 `0x14` Programmer，不使用 `0x8A`；除非厂商明确要求兼容旧路径，不要用 `0x8A` 替代 CV 读写。

## UDP 封装

UDP 帧结构：

```text
0xFF 0xFF BBBBLLLL aaaaaaaa CCCCCCCC ... DDDDDDDD XXXXXXXX
```

| 字段 | 含义 |
| --- | --- |
| `0xFF 0xFF` | 包头 |
| `BBBB` | 设备类型 |
| `LLLL` | 数据长度，等于 UDP 数据报总长度减去 2 字节包头 |
| `aaaaaaaa` | 源器件地址；常规网络 ID 使用低 7 bit |
| `CCCCCCCC` | 命令字，完整 8 bit 保留 |
| `DDDDDDDD` | 包数据，最多 9 字节 |
| `XXXXXXXX` | XOR 校验字节 |

已确认 UDP 证据：

- 官方 Demo `DigsightDemo_2025_12` 的 `DxdcNet_Packet.VerifyData()` 从 `Data[0]` 开始 XOR 到倒数第二个字节，并写入最后一个字节；因此 XOR 包含 `FF FF` 包头。
- 官方 Demo 构造函数把 `Packet_Length` 设为 `Data.Length - 2`，即长度低 4 bit 不含 2 字节包头，但包含设备/长度字节、源地址、命令、载荷和校验。
- 官方 Demo `Command_Type` 直接读写 `Data[4]`，因此 `0x80`、`0x84`、`0x85`、`0x8A`、`0xE0` 等高位命令不得屏蔽为 7 bit。
- 官方 Android App 默认服务端端口 `12000`、本地端口 `6667`、ThrottleID `1`；官方 PC Demo 主程序默认服务端端口 `12000`、本地端口 `12001`；DigsightServer 代理默认设备端口 `11999`、客户端端口 `12000`。直连控制器优先向设备 `12000/udp` 发送。

实测测试向量，目标 `10.10.200.98:12000`，本地绑定 `12001/udp`，时间 2026-06-20：

| 操作 | 方向 | 原始 UDP 帧 |
| --- | --- | --- |
| 请求命令站状态 `0x22` | 发送 | `FF FF 16 00 22 00 00 34` |
| 命令站状态 `0x23` | 接收 | `FF FF 0B 00 23 00 00 00 00 00 00 00 28` |
| Booster 状态广播 `0x23` | 接收 | `FF FF 7B 01 23 00 0B 00 22 00 00 F0 80` |
| 请求命令站版本 `0x84` | 发送 | `FF FF 16 00 84 00 00 92` |
| 命令站版本 `0x85` | 接收 | `FF FF 06 00 85 1E 16 8B` |

按 Android App `ThrottleID=1` 构造的只读请求向量：

| 操作 | UDP 帧 |
| --- | --- |
| 请求命令站状态 `0x22` | `FF FF 16 01 22 00 00 35` |
| 请求 Booster 1 状态 `0x22` | `FF FF 16 01 22 07 01 33` |
| 请求命令站版本 `0x84` | `FF FF 16 01 84 00 00 93` |
| 读取 N 限流参数 `0x81` | `FF FF 17 01 41 00 00 81 D6` |
| 读取 HO 限流参数 `0x82` | `FF FF 17 01 41 00 00 82 D5` |
| 读取 G 限流参数 `0x83` | `FF FF 17 01 41 00 00 83 D4` |
| 读取 DC 限流参数 `0x84` | `FF FF 17 01 41 00 00 84 D3` |
| 读取屏幕亮度参数 `0x7E` | `FF FF 17 01 41 00 00 7E 29` |
| 读取屏幕方向参数 `0x80` | `FF FF 17 01 41 00 00 80 D7` |

2026-06-20 18:49:27 +0800 通过 Android App 风格 `ThrottleID=1` 只读请求实测新增回包：

| 操作 | 回包 |
| --- | --- |
| Booster 状态 `0x23` | `FF FF 7B 01 23 00 0B 00 21 00 00 F0 83` |
| N 限流参数 `0x81` | `FF FF 06 00 42 81 32 F7` |

2026-06-20 用户通过官方 App 将控制器从 DC 模拟模式调整为 HO 后，按本地 HO 期望模式只读复测新增回包：

| 操作 | 回包 |
| --- | --- |
| Booster 状态 `0x23` | `FF FF 7B 01 23 00 0D 00 21 00 00 30 45` |
| HO 限流参数 `0x82` | `FF FF 06 00 42 82 64 A2` |

2026-06-20 19:38:49 +0800 继续按 Android App 风格 `ThrottleID=1` 只读实测控制器 App 字段和编程轨 CV 信息，目标 `10.10.200.98:12000`，本地绑定 `6667/udp`：

| 操作 | 方向 | 原始 UDP 帧 |
| --- | --- | --- |
| 请求命令站版本 `0x84` | 发送 | `FF FF 16 01 84 00 00 93` |
| 命令站版本 `0x85` | 接收 | `FF FF 06 00 85 1E 16 8B` |
| 请求 App 内核版本 `T_SPECIAL/15` | 发送 | `FF FF 16 01 84 0F 0F 93` |
| App 内核版本 `0x85` | 接收 | `FF FF F6 0F 85 1E 13 71` |
| 请求 App 无线版本 `T_BOOSTER/1` | 发送 | `FF FF 16 01 84 07 01 95` |
| App 无线版本 `0x85` | 接收 | `FF FF 76 01 85 1E 16 FA` |
| 读取 RAILCOM 参数 `0x03` | 发送 | `FF FF 17 01 41 00 00 03 54` |
| RAILCOM 参数回包 | 接收 | `FF FF 06 00 42 03 FF B8` |
| 请求命令站 MAC `0x0B` | 发送 | `FF FF 16 01 0B 00 01 1D` |
| MAC 低段 `0x0C` | 接收 | `FF FF 0B 00 0C 00 34 35 38 31 1B 6B 7F` |
| MAC 高段 `0x0C` | 接收 | `FF FF 0B 00 0C 01 33 37 39 4A 0D 32 4E` |
| CV7 direct read | 发送 | `FF FF 17 01 14 80 06 00 84` |
| CV7 value | 接收 | `FF FF 0B 00 17 80 06 01 01 01 00 00 9B` |
| CV8 direct read | 发送 | `FF FF 17 01 14 80 07 00 85` |
| CV8 value | 接收 | `FF FF 0B 00 17 80 07 56 01 01 00 00 CD` |
| CV127 direct read | 发送 | `FF FF 17 01 14 80 7E 00 FC` |
| CV127 value | 接收 | `FF FF 0B 00 17 80 7E FF 01 01 00 00 1D` |
| CV128 direct read | 发送 | `FF FF 17 01 14 80 7F 00 FD` |
| CV128 value | 接收 | `FF FF 0B 00 17 80 7F FF 01 01 00 00 1C` |

2026-06-20 20:05:16 +0800 用户通过官方 App 变更 RAILCOM、N/HO 模式、亮度、屏幕方向和 N/HO/G/DC 限流后，按 Android App 风格 `ThrottleID=1` 只读复测新增证据，目标 `10.10.200.98:12000`，本地绑定 `6667/udp`：

| 操作 | App 当前值 | 回包 |
| --- | --- | --- |
| RAILCOM 参数 `0x03` | 关 | `FF FF 06 00 42 03 00 47` |
| 屏幕亮度参数 `0x7E` | 128 | `FF FF 06 00 42 7E 80 BA` |
| 屏幕方向参数 `0x80` | 右 | `FF FF 06 00 42 80 02 C6` |
| N 限流参数 `0x81` | `2000 mA` | `FF FF 06 00 42 81 32 F7` |
| HO 限流参数 `0x82` | `4000 mA` | `FF FF 06 00 42 82 64 A2` |
| G 限流参数 `0x83` | `7000 mA` | `FF FF 06 00 42 83 AF 68` |
| DC 限流参数 `0x84` | `2000 mA` | `FF FF 06 00 42 84 32 F2` |
| 未解释自动上报 | - | `FF FF F7 0F EA 0E 00 C0 DC` |

解码要点：

- `FF FF 0B 00 23 ... 28`：设备类型 `0x0`，长度 `0x0B`，源地址 `0x00`，命令 `0x23`，载荷 7 字节，XOR 校验通过。
- `FF FF 7B 01 23 ... 80`：设备类型 `0x7`，长度 `0x0B`，源地址 `0x01`，命令 `0x23`，载荷按 Booster 状态解释，XOR 校验通过；按 Android App V3 状态位解读，`0xF0` 包含上电、DC 模式、方向和自动报告位，因此不能作为 DCC/CV 安全通过证据。
- `FF FF 7B 01 23 00 0D 00 21 00 00 30 45`：状态位 `0x30` 按 Android App V3 解读为 DCC 模式，轨道上电位为 0，方向位和自动报告位为 1；设置输出 raw 仍为 `0x00`，输出电压 raw `0x0D` 约 `1.3 V`。
- `FF FF 06 00 85 1E 16 8B`：设备类型 `0x0`，长度 `0x06`，源地址 `0x00`，命令 `0x85`，硬件版本原始值 `0x1E`，软件版本原始值 `0x16`，XOR 校验通过。
- `FF FF 06 00 42 81 32 F7`：命令站返回参数 `0x42`，载荷 `0x81 0x32`，表示 N 模式限流参数原始值 `0x32`；2026-06-20 用户 App 同步显示 N `2000 mA`，因此 D9000 `0x81` 换算为 `0x32 * 40 mA = 2000 mA`。
- `FF FF 06 00 42 82 64 A2`：命令站返回参数 `0x42`，载荷 `0x82 0x64`，表示 HO 模式限流参数原始值 `0x64`；2026-06-20 用户 App 同步显示 HO `4000 mA`，因此 D9000 `0x82` 换算为 `0x64 * 40 mA = 4000 mA`。
- `FF FF 06 00 42 83 AF 68`：命令站返回参数 `0x42`，载荷 `0x83 0xAF`，表示 G 模式限流参数原始值 `0xAF`；2026-06-20 用户 App 同步显示 G `7000 mA`，因此 D9000 `0x83` 换算为 `0xAF * 40 mA = 7000 mA`。
- `FF FF 06 00 42 84 32 F2`：命令站返回参数 `0x42`，载荷 `0x84 0x32`，表示 DC 模式限流参数原始值 `0x32`；2026-06-20 用户 App 同步显示 DC `2000 mA`，因此 D9000 `0x84` 换算为 `0x32 * 40 mA = 2000 mA`。
- App 的内核版本读取对应 `VersionRequest(1, T_SPECIAL, 15)`，回包设备类型 `0xF`、源地址 `0x0F`；`0x1E/0x13` 按 App 显示逻辑为 `3.0.1.9`。
- App 的无线版本读取对应 `VersionRequest(1, T_BOOSTER, 1)`，回包设备类型 `0x7`、源地址 `0x01`；`0x1E/0x16` 按 App 显示逻辑为 `3.0.2.2`。
- RAILCOM 参数地址为 `0x03`；回包 `0x03 0xFF` 中 `0x80` 位为 1，按 App 判断为开启；用户关掉后回包 `0x03 0x00`，判断时应使用 `value & 0x80`。
- 屏幕亮度参数地址为 `0x7E`；用户将亮度从 255 改为 128 后回包 `0x7E 0x80`。
- 屏幕方向参数地址为 `0x80`；用户将方向从上改为右后回包 `0x80 0x02`。用户后续确认 App 方向按顺时针旋转，且从“右”开始每次递增 1 并按 4 取模，因此完整映射为 `0x02=右`、`0x03=下`、`0x00=左`、`0x01=上`。
- 自动上报 `FF FF F7 0F EA 0E 00 C0 DC` 已多次出现，当前仅确认其 XOR 有效且设备类型/源地址为 `0xF/0x0F`，命令 `0xEA`；载荷含义待确认，不要在实现中解释为已知字段。
- `MacAddress.getMAC()` 按 `data[11]..data[6]` 反序取每段 6 字节；上述两段拼接得到 12 字节设备标识 `6B1B31383534320D4A393733`。
- App 的设备名称来自本地绑定表 `equip_alias + "(" + equip_type + ")"`，出厂编号来自本地绑定表 `equip_productcode` 解密；当前只确认 UDP 可直接读 MAC/设备标识，未确认独立“设备名称/出厂编号” UDP 查询命令。
- 动芯控制器有主轨和编程轨；用户已通过官方 App 确认支持主轨 CV 编程，且 2026-06-21 反编译 App V3 确认主轨机车 POM 使用 `0x14` Programmer op=`6`、两字节 POM 地址和 `0x17`/`0x15` 回包路径。主轨 Booster 输出值和 HO/N 主轨限流仍不应直接等价为编程轨 CV 安全状态，除非厂商确认保护共用。
- 编程轨 CV7 返回 `1`，CV8 返回 `86 / 0x56`；NMRA 2025 厂家表中 86 为 `Wekomm Engineering, GmbH`，不是 Digsight 的 `30 / 0x1E`。因此 CV127/CV128 返回 `255/255` 不应按 Digsight App 私有规则解析为有效模块型号/硬件版本。
- 以上 2026-06-20 实测确认只读状态、版本、参数、MAC 和编程轨 CV direct read；2026-06-21 App 反编译确认主轨 POM 编码和 App 写后读回流程，但仍建议真实主轨写入前优先用只读 POM 抓包或实机只读验证目标车辆地址。

## 实现建议

- 定义 `DeviceType`、`Command`、`SpeedMode`、`FunctionGroup`、`TrackOutputFlags`、`BoosterStatusFlags` 常量。
- 解码器返回结构至少包含：原始字节、传输层、源设备类型、源 ID、命令字、DLC/长度、载荷、解析字段、警告列表。
- 编码器必须字节级可测；每个命令用十六进制输入输出做 round-trip 测试，并优先覆盖上方 UDP 实测向量。
- 对文档冲突项使用 warning，不要静默选择一种解释。
- 对未知设备类型、保留命令、未定义升级/配置载荷，保留原始值并输出“未定义/需抓包确认”。
