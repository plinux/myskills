# Mobile and Accessory Decoder Commands

来源：NMRA S-9.2.1、RailCommunity RCN-212/213。

## 车辆 decoder packet 格式

- 7-bit short address：`{sync} 0 0AAA-AAAA 0 {instruction bytes} 0 PPPP-PPPP 1`。
- 14-bit long address：`{sync} 0 11AA-AAAA 0 AAAA-AAAA 0 {instruction bytes} 0 PPPP-PPPP 1`。
- 地址 bit 权重：
  - short：`A6..A0` 在 `0AAA-AAAA` 中。
  - long：第一 byte `11A13..A8`，第二 byte `A7..A0`。
- 指令长度可为 1-6 byte；末尾 XOR 校验 byte 不属于 instruction。
- 若支持 RailCom 且 Channel 2 已启用，除 CV access 和 broadcast 外，每个成功接收的寻址业务命令应以 RailCom ACK 或其他 Channel 2 消息确认。

## 车辆 instruction code map

| First instruction byte | 类别 | 长度 | 备注 |
| --- | --- | --- | --- |
| `0000-0000` | decoder reset | 1 | 同 reset packet 指令。 |
| `0000-0001` | decoder hard reset | 1 | 重置 CV29/CV31/CV32 到厂设、CV19=0，并执行 decoder reset。 |
| `0000-001x` | factory test | variable | 格式未标准化；command station 正常运行不得发送。 |
| `0000-101D` | set extended addressing | 1 | `D` 写入 CV29 bit 5。 |
| `0000-1111` | decoder ACK request | 1 | 只期待 RailCom ACK 或 Channel 2 消息。 |
| `0001-001R 0AAA-AAAA` | consist address set | 2 | 写 CV19，`R` 写 CV19 bit 7。 |
| `0011-1011 ...` | target speed | 2 | 不改变行为，只告知 decoder 目标速度，便于声效和内部状态。 |
| `0011-1100 ...` | speed, direction, functions | 3-6 | 组合速度和 F0-F31。 |
| `0011-1101 SSSS-SSSS DDDD-DDDD` | analog function group | 3 | 控制 0-255 模拟通道；不得用于车辆速度控制。 |
| `0011-1110 DDDD-DD00` | special operating modes | 2 | 编组位置、shunting、East/West、MAN。 |
| `0011-1111 RGGG-GGGG` | 128 speed steps | 2 | 126 个有效速度级。 |
| `01RG-GGGG` / `01RL-GGGG` | baseline speed/direction | 1 | 28-step 或旧式 14-step/F0 兼容。 |
| `100D-DDDD` | F0-F4 | 1 | F0 在 bit 4，F1-F4 在 bit 0-3。 |
| `1010-DDDD` | F9-F12 | 1 | bit 0 对应 F9。 |
| `1011-DDDD` | F5-F8 | 1 | bit 0 对应 F5。 |
| `1100-0000 DLLL-LLLL HHHH-HHHH` | long binary state | 3 | 1-32767，0 作为 broadcast set/clear。 |
| `1101-1000..1101-1100 DDDD-DDDD` | F29-F68 | 2 | 每组 8 个函数。 |
| `1101-1101 DLLL-LLLL` | short binary state | 2 | 1-127，0 作为 broadcast set/clear。 |
| `1101-1110 DDDD-DDDD` | F13-F20 | 2 | bit 0 对应 F13。 |
| `1101-1111 DDDD-DDDD` | F21-F28 | 2 | bit 0 对应 F21。 |
| `111x-xxxx` | CV access | 2-3+ | 见 `cv-programming.md`。 |
| `1111-1111` | idle | 1 | 见通用 packet。 |

未列出的 code 组合为 reserved 或 deprecated；decoder 应忽略，command station 不应发送。

## 速度和方向

- Baseline speed/direction：`01RG-GGGG`，其中 `R=1` 表示 forward，`R=0` 表示 reverse；forward 指车辆端 1 在行进方向前方。
- 28-step baseline 的速度字段实际 bit 顺序为 `G0 G4 G3 G2 G1`：
  - `00000` 和 `10000` 为 stop。
  - `00001` 和 `10001` 为 emergency stop。
  - 其余映射到 1-28。
- 旧式兼容模式：`01RL-GGGG`，bit 4 作为 F0/light，不作为速度低 bit；对应 CV29 bit 1 清零，只剩 14 speed steps。
- Broadcast speed/direction 中的方向信息可被 decoder 忽略；旧式 F0 bit 在 broadcast 中也可忽略。
- 128 speed command：`0011-1111 RGGG-GGGG`：
  - 第二 byte bit 7 是方向。
  - `U000-0000` stop，`U000-0001` emergency stop。
  - 其余 126 个值为有效速度级。
- Target speed：`0011-1011 RGGG-GGGG` 用于 128-step；`0011-1011 00RG-GGGG` 用于 baseline；不改变牵引输出，只报告目标速度趋势。
- Special operating modes：`0011-1110 DDDD-DD00`：
  - bit 0-1 reserved，必须为 0。
  - bit 2-3 为牵引位置：`00` 非编组，`10` leading，`01` middle，`11` trailing。
  - bit 4 shunting，可降低速度/加减速。
  - bit 5/6 为 West/East 方向相关状态。
  - bit 7 MAN，可使本地限速或基于 DCC 信号修饰的停车命令失效。

## 函数、二进制状态、模拟函数

- 函数 bit 规则：值 1 为 active/on，0 为 inactive/off。
- F0-F4：`100D-DDDD`，bit 4=F0，bit 0-3=F1-F4。
- F5-F8：`1011-DDDD`，bit 0=F5，bit 3=F8。
- F9-F12：`1010-DDDD`，bit 0=F9，bit 3=F12。
- F13-F68：
  - `1101-1110` F13-F20。
  - `1101-1111` F21-F28。
  - `1101-1000` F29-F36。
  - `1101-1001` F37-F44。
  - `1101-1010` F45-F52。
  - `1101-1011` F53-F60。
  - `1101-1100` F61-F68。
  - 第二 byte bit 0 对应该组最低编号函数，bit 7 最高编号函数。
  - F29-F68 推荐但不强制持久化；command station 改变状态时至少重复 3 次。
  - 支持 F29-F68 的 decoder 也必须能通过 binary state 29-68 控制这些功能。
- Short binary state：`1101-1101 DLLL-LLLL`：
  - `LLLLLLL` 取值 1-127，bit 7 `D` 是状态。
  - 地址 0 是 broadcast，用于设置/清除 29-127；`D=0` 示例用于关闭。
  - 1-28 只供特殊用途；普通开关功能从 29 起用。
  - 1-15 预留给 RailCom 特殊功能。
- Long binary state：`1100-0000 DLLL-LLLL HHHH-HHHH`：
  - 低 7 bit 在第二 byte，bit 7 `D` 是状态，高 8 bit 在第三 byte。
  - 地址 1-32767 有效；地址 0 是 broadcast set/clear 29-32767。
  - 地址 1-127 必须使用 short form；支持 long form 的 decoder 也必须支持 short form。
  - binary state 不定期重复；状态推荐存入非易失存储。
  - command station 改变 binary state 时至少重复 3 次。
- Combined speed/direction/functions：`0011-1100 RGGG-GGGG DDDDDDDD {DDDDDDDD...}`：
  - 第 2 byte 同 128-step speed。
  - 第 3 byte F0-F7；第 4 byte F8-F15；第 5 byte F16-F23；第 6 byte F24-F31。
  - 缺省未发送的函数组保持原状态。
  - 若只支持 F0-F28 且支持 binary state，第 6 byte bit 5-7 应对应 binary states 29-31；否则清零。
- Analog function group：`0011-1101 SSSS-SSSS DDDD-DDDD`：
  - `S` 是 0-255 模拟通道，`D` 是 0-255 数据。
  - `S=1` 通常用于音量。
  - `S=0x10..0x1F` 用于位置控制。
  - `S=0x00..0x7F` 未定义值 reserved；`S=0x80..0xFF` 厂家可用。
  - 不得用于车辆速度控制。

## Consist / 多机重联

- Set consist address：`0001-001R 0AAA-AAAA`。
- 第二 byte bit 7 reserved，必须为 0。
- `AAA-AAAA` 写 CV19 bits 0-6；0 表示停用 consist。
- `R` 写 CV19 bit 7：0 正常方向，1 相反方向。
- Broadcast `0001-0010 0000-0000` 清除所有 decoder consist。
- consist active 后，decoder 忽略对 base address 的 speed/direction，除非 base address 等于 consist address。
- F0-F12 与 F13-F28 是否由 consist address 控制由 CV21/CV22 对应 bit 决定。

## Decoder control

- Reset instruction `0000-0000`：清易失状态，回到上电状态；broadcast 时即 reset packet。
- Hard reset `0000-0001`：CV29/CV31/CV32 回厂设，CV19=0，再执行 reset。
- Factory test `0000-001x`：厂测私有，正常 command station 不得发送。
- Set extended addressing `0000-101D`：`D` 写 CV29 bit 5，选择 CV17/18 长地址或 CV1 短地址。
- Decoder ACK request `0000-1111`：只期待 RailCom ACK/Channel 2 消息，不改变业务状态。

## Basic accessory decoder

- Format：`10AA-AAAA 1AAA-DAAR`。
- `D=1` activate，`D=0` deactivate；可用于中心控制输出保持时间。
- `R` 选择一对输出中的一路：
  - 常规含义：`R=0` turnout diverging/left 或 signal stop；`R=1` straight/right 或 signal proceed。
  - 固定连接 turnout 的 decoder 应可配置实际左右/直曲含义。
- 11-bit accessory 地址 bit 映射：
  - 第一 byte bits 5-0 是 `A7..A2`。
  - 第二 byte bits 6-4 是 `A10..A8` 的 ones-complement。
  - 第二 byte bits 2-1 是 `A1..A0`。
- RCN 线性用户地址：
  - 用户地址 1 对应 packet 地址 4，即 `1000-0001 1111-D00R`。
  - packet 地址 0-3 放到地址空间末端。
  - 新设计必须支持线性递增；可提供旧式非线性地址兼容。
- 纯瞬时线圈输出应有可配置自动断电时间；若中心要延长激活，需要重复 `D=1`。

## Extended accessory decoder

- Format：`10AA-AAAA 0AAA-0AA1 DDDD-DDDD`。
- 地址 bit 权重和 basic accessory 一致，第二 byte bit 3 为 0，避免和旧 programming packet 混淆。
- 每个地址对应一个设备，不是输出对。
- 第三 byte 表示 0-255 个 aspect/state：
  - 对信号机：`0` 表示绝对停车，其余 aspect 由信号系统或 NEM 694 等定义。
  - 对简单开关 decoder 的中心定时控制：第三 byte 可解释为 `RZZZ-ZZZZ`，`Z` 以 100 ms 为单位，0 关闭，127 持续到下一命令，`R` 选输出。

## Accessory NOP

- Format：`10AA-AAAA 0AAA-1AAT`。
- `T=0` basic accessory；`T=1` extended accessory。
- 用于 RailCom accessory decoder 发 SRQ，不改变当前状态。
- 非 RailCom basic/extended accessory decoder 应将其识别为无效并忽略。
- RailCom 中心可定期发送最大地址 NOP，让所有 accessory decoder 有机会发 SRQ；多 SRQ 时通过调整 NOP 地址做二分/逼近搜索。
