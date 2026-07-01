# RailCom, Fail-Safe, Advanced Packets, and Tests

来源：NMRA S-9.2.1.1、S-9.2.4、S-9.3.2、RailCommunity RCN-217。

## RailCom physical layer

- RailCom 是 DCC 反向通信扩展；正常 DCC 从 booster 到 decoder，RailCom 在 packet 之后由 booster 产生 cutout，让 decoder 通过电流环回传。
- Cutout device 在 DCC packet end 后断开/短接轨道输出；decoder 使用内部储能供电并向 detector 注入电流。
- Cutout device 在最大 34 mA 时压降不应超过约 10 mV。
- Decoder RailCom transmitter：
  - 发送 `0`：提供约 30 mA 电流，容差约 +4/-6 mA，轨道压降到约 2.2 V 仍需工作。
  - high-current RailCom 启用时发送 `0`：约 60 mA，容差约 +8/-12 mA。
  - 发送 `1`：电流接近 0，通常不超过约 +/-0.1 mA。
  - transmitter 必须防护 cutout 期间意外轨道电压。
- Detector：
  - 中间 50% bit 时间内，电流 >10 mA 判为 `0`，<6 mA 判为 `1`。
  - 最大 34 mA 时 detector 压降不应超过约 200 mV。
  - 最多两个 detector 串联，含 global detector。
- RailCom UART-like bit：
  - 每 byte 1 个 start bit `0`，8 个 data bit LSB-first，1 个 stop bit `1`。
  - 速率 250 kbit/s +/-2%。
  - 上升/下降 10%-90% 不超过约 0.5 us。
- Timing 以 DCC packet end bit 最后一个过零点为基准：
  - Cutout start 约 26-32 us。
  - Cutout end 约 454-488 us。
  - Channel 1 start 约 80 us，detector 建议 75 us 就绪；Channel 1 end 不晚于约 177 us。
  - Channel 2 start 约 193 us；Channel 2 end 不晚于约 454 us。
  - Channel 1 可传 2 byte，Channel 2 可传 6 byte。
- 约 450 us cutout 不应影响不支持 RailCom 的 decoder；真实轨道接触中断可能远大于该值。

## RailCom coding and packet layer

- 每个 RailCom 传输 byte 使用 4-out-of-8 coding：8 bit 中必须恰好 4 个 `1` 和 4 个 `0`。
- 64 个 code 映射 6-bit payload；额外 code 用于 ACK/NACK/reserved。
- ACK 有两个 code，均表示“命令理解并将执行/YES”；NACK 表示否定或不支持。
- Channel 1 净载 12 bit；Channel 2 净载最多 36 bit。
- Datagram 长度可为 6、12、18、24、36 payload bits；除特殊说明外，以 4-bit ID 开头。
- 12-bit datagram：`ID[3:0] + D[7:6] + D[5:0]`。
- 18-bit datagram：`ID[3:0] + D[13:12] + D[11:6] + D[5:0]`。
- 24-bit datagram：`ID[3:0] + D[19:18] + D[17:12] + D[11:6] + D[5:0]`。
- 36-bit datagram：`ID[3:0] + D[31:30] + D[29:24] + D[23:18] + D[17:12] + D[11:6] + D[5:0]`。
- Channel 2 可组合多个 datagram，总长度不超过 36 bit。
- ACK/NACK 出现在 RailCom response 开头时是特殊消息，不算普通 datagram；若以 ACK/NACK 开头，不应再跟普通 datagram，但后续 ACK/NACK 仍可处理。
- 自动注册可合并 Channel 1/2 为 48-bit 数据块；具体见 RCN-218 / NMRA S-9.2.1.1 相关 address partition。

## RailCom address contexts

| DCC address context | Channel 1 | Command type |
| --- | --- | --- |
| `0x00` broadcast | 无 | mobile broadcast，不得因 broadcast 在 Channel 2 回应。 |
| `0x01`-`0x7F` short mobile | ID1/ID2 address | MOB。 |
| `0x80`-`0xBF` accessory | SRQ without ID | STAT。 |
| `0xC0`-`0xE7` long mobile | ID1/ID2 address | MOB；long address 0 也可作为 programming address。 |
| `0xE8`-`0xFC` reserved | 无 | 不定义。 |
| `0xFD` | 无 | NMRA S-9.2.1.1 数据传输，寻址通过 packed DCC address。 |
| `0xFE` | bundled channel | DCC-A / automatic logon / unique ID context。 |
| `0xFF` idle | 无；RailComPlus 可用 ID14/15 | idle packet 不应触发通用 RailCom response。 |

- Service mode packet 不应触发 RailCom response。
- Channel 2 只能由被前置 DCC packet 寻址的 decoder 发送。
- 为了在没有车辆地址流时仍能获取 Channel 1，中心可交替 idle 和长地址 10239。

## MOB identifiers

Channel 1 mobile：

| ID | 用途 |
| --- | --- |
| 1 | `app:adr_high`，必需。 |
| 2 | `app:adr_low`，必需。 |
| 3 | `app:info1`，可选，CV28 bit3 启用。 |
| 14/15 | RailComPlus，不供 RailCommunity 通用定义。 |

Channel 2 mobile：

| ID | 长度 | 用途 |
| --- | --- | --- |
| 0 | 12 bit | POM result，必需。 |
| 1/2 | 12 bit | 地址搜索/上轨搜索。 |
| 3 | 18 bit | EXT/orientation/location。 |
| 4 | 36 bit | 当前行车信息，保留。 |
| 7 | 18 bit，可两次 | DYN dynamic variables。 |
| 8-11 | 36 bit | XPOM result，对应 SS=00..11。 |
| 12 | 36 bit | CV-auto background CV transfer。 |
| 13 | 36 bit | Block，可选，见技术说明。 |
| 14 | 12 bit | Search timing。 |

Channel 2 多 datagram 时推荐 ID 顺序：`1 2 0 3 4 7 8 9 10 11 13 14 5 6 15 12`，以便旧 detector 跳过未知新 datagram。

## STAT identifiers

Accessory Channel 1：

- SRQ 是 12-bit 值，无 4-bit ID。
- bit 11 区分 basic/extended accessory，后 11 bit 是 accessory address。
- SRQ 可在任意 accessory packet 后发送，或在 NOP 后若自身地址小于等于 NOP 地址则发送。
- SRQ 必须重复，直到中心用自身地址上的清除命令处理：
  - basic：coil off。
  - extended：absolute stop / aspect 0。
- 若上电后约 5 s 内没有看到 NOP，可认为中心不支持 RailCom accessory SRQ，不应让 SRQ 阻塞业务。

Accessory Channel 2：

| ID | 长度 | 用途 |
| --- | --- | --- |
| 0 | 12 bit | POM result。 |
| 3 | 36 bit | `stat4`，可选。 |
| 4 | 12 bit | `stat1`，必需。 |
| 5 | 12 bit | time。 |
| 6 | 12 bit | error，必需。 |
| 7 | 18 bit，可两次 | DYN。 |
| 8-11 | 36 bit | XPOM / stat2 legacy。 |
| 12 | variable | test feature ID。 |
| 13 | 36 bit | block，预留/未完全定义。 |

## RailCom CVs and DCC helper commands

- RailCom decoder 必须向后兼容非 RailCom 中心和非 RailCom decoder。
- RailCom 系统不允许通过 stretched zero 控制模拟车辆。
- RailCom decoder 必须支持 ACK；车辆还必须支持 Channel 1 ADR high/low 和 Channel 2 POM；附件还必须支持 `stat1` 和 `fehler`。
- Decoder 只有被寻址时才可在 Channel 2 回答；broadcast 不得回答。
- CV28 mobile：
  - bit0 Channel 1 address broadcast。
  - bit1 Channel 2 data/ack。
  - bit2 dynamic Channel 1 auto-disable。
  - bit3 send ID3/info1 in Channel 1。
  - bit4 programming address 0000。
  - bit5 reserved。
  - bit6 high-current RailCom。
  - bit7 automatic logon。
- CV28 accessory：RCN-225 中 bit1/6/7 有效，其他多为 reserved。
- RailCom block：CV31=0,CV32=255，CV257 起 256 byte。
  - byte 0-1：Manufacturer ID little-endian；对应 CV8 或 extended CV107/108。
  - byte 4-7：Product ID。
  - byte 8-11：Manufacturer Unique Number。
  - byte 12-15：生产日期，2000-01-01 起秒数，little-endian。
  - byte 16-63：厂家可用。
  - byte 64-127：DYN 对应动态变量镜像。
  - byte 128-129：RailCom version major/minor。
  - byte 130：test feature number。
  - byte 131：reserved。
  - byte 132-143：容器 1-12 的 specific consumption。
  - byte 144：写入可设置所有容器 fill level 0-100。
  - byte 145：速度表缩放，值 * 2 = 最高 km/h。
  - byte 146-255：reserved。
- RailCom 特殊 binary-state command：
  - XF1：请求 location EXT。
  - XF2：上轨搜索。
  - XF3：触发 CV-auto 全量 CV 输出。
  - XF4-XF15：reserved。

## RailCom APP details

- POM ID0：
  - 读/写/bit 写均以 12-bit ID0 返回 CV 当前值。
  - 读结果不必在同一 packet frame 返回；中心必须继续寻址 decoder。
  - 普通 CV 超时约 0.5 s；SUSI CV 897-1024 可等待约 2 s。
  - 写操作可先返回 ACK/ACK 或其他非命令相关消息；最终必须返回写后实际值。写只读或受限 CV 时，返回当前值。
- ADR ID1/ID2：
  - Channel 1 交替发送当前 active address 的 high/low。
  - active address 可是 base、long、consist 或 DCC-A address。
  - 7-bit base 使用 ADR1 全 0 + ADR2 低地址。
  - consist 以 ADR1 特殊 pattern + ADR2 含方向/地址。
  - long address 用 ADR1/ADR2 合并 14-bit。
  - 多机重联建议只让 leading unit 发送 ADR，其他关闭 Channel 1 address。
- Dynamic Channel 1：
  - CV28 bit2 启用后，decoder 在重启、地址变化、超过 5 s 未被寻址后发送 Channel 1 address。
  - 连续 8 次收到自身地址后可自动停止 Channel 1 address，减少冲突。
- Info1 ID3：
  - CV28 bit3 启用，且 Channel 1 address 也启用时，ID1/ID2/ID3 循环。
  - bit0 上轨方向/轨道相位，bit1 行驶方向相位，bit2 是否运动，bit3 是否 consist，bit4 是否请求中心寻址以便 Channel 2 上报，bit5-7 reserved。
- Search / rerailing XF2：
  - 车辆断电至少 1 s 后重新上电。
  - 30 s 内对 broadcast `XF2 off` 随机概率约 1:8 回答。
  - 建议中心约每秒 8 次发送 XF2 off。
  - response 含 ADR high、ADR low、上电到首次搜索命令秒数。
- EXT ID3：
  - XF1 off 请求 location。
  - decoder 可直接返回 11-bit location，或 detector 与 decoder 组合返回 location / fueling station 类型。
  - fueling 可通过写 RailCom block 中相关 CV 实现。
- DYN ID7：
  - 18-bit datagram：8-bit value + 6-bit subindex，可一次最多两个。
  - Subindex 0/1：真实速度两部分；高于 255 时用第二部分传差值/高 bit。
  - 2：load 或 speed normalized to 128。
  - 3：RailCom version。
  - 4：change flags。
  - 5/6：flag/input register，待定义。
  - 7：接收统计，错误 packet / 总 packet 百分比。
  - 8-19：容器 1-12 fill level 0-100。
  - 20：location address low/high 两个 datagram。
  - 21：warning/alarm；bit7 alarm，bit6 选择独立告警或 DV 相关告警。
  - 22：trip distance，待细化。
  - 23：maintenance interval。
  - 26：temperature，0=-50 C，255=+205 C。
  - 27：East/West direction state。
  - 34：control deviation。
  - 46：measured track voltage = 5 V + value * 100 mV。
  - 47：computed stopping distance，单位约 4 m prototype。
  - 其他 reserved。
- XPOM ID8-11：见 `cv-programming.md`，RailCom 返回连续 4 CV 值。
- CV-auto ID12：
  - XF3 on 触发后台输出全部 CV；XF3 off 停止。
  - 36-bit response 携带 24-bit CV 地址和 8-bit CV value。

## NMRA S-9.2.1.1 advanced extended packets

### Shared framing

- Address partition 253 uses first byte `0xFD`; partition 254 uses first byte `0xFE`.
- If total packet length including traditional XOR checksum is <= 6 bytes, use normal DCC XOR only.
- If total packet length is > 6 bytes, insert CRC-8 before the traditional XOR byte; decoder must validate both CRC-8 and XOR.
- CRC-8 polynomial is `x^8 + x^5 + x^4 + 1` (Dallas/Maxim 1-Wire), initial value 0, not inverted.
- CRC validation covers the message including CRC byte and excluding the XOR byte; expected final CRC result is 0.
- System must not send 7-byte packets to 253/254; decoder must ignore 7-byte packets to 253/254.
- Maximum 253/254 packet length is 32 bytes unless a command definition explicitly says otherwise.
- A 253 addressed message only allows the addressed decoder to respond in Channel 2; Channel 1 is reserved and mobile decoders must not respond there even if CV28 bit0 enables unsolicited transmission.
- All 254 messages combine Channels 1 and 2 into one extended feedback channel; decoder respects both channel timing windows. CV28 bit1 alone gates whether 254 feedback is allowed.
- Feedback payload must align to 6-bit boundaries; pad with 0 bits to the next boundary, then fill remaining cutout capacity with ACK bytes.
- Variable length feedback format is `{header} {payload bytes} {CRC-8}`. Header `XRCLLLLL`:
  - `X=0` regular header; `X=1` special single-cutout format.
  - `R=0` response to system request; `R=1` unsolicited decoder message.
  - `C=0` first message; `C=1` continuation in same decoder context.
  - `LLLLL` payload byte count; total byte count is header + payload + CRC.
- Addressed 253/254 messages must be acknowledged:
  - Bad checksum: no feedback.
  - Any specified response counts as acknowledgement.
  - 254 with no specific response: fill combined channel with 8 ACK bytes.
  - 253 with no specific response: fill Channel 2 with 6 ACK bytes.
- Messages are not periodic refresh traffic; repeat only when not acknowledged unless the command explicitly says otherwise.
- Sequenced operations require an uninterrupted contiguous DCC sequence without checksum errors and without alternative track protocol packets interleaved.
- General error codes:
  - `0x1000` permanent unspecified.
  - `0x1040` unimplemented.
  - `0x1042` command not supported.
  - `0x1080` invalid arguments.
  - `0x1081` unknown data space.
  - `0x1082` write offset out of bounds.
  - `0x1083` data space read-only.
  - `0x2000` temporary unspecified.
  - `0x2010` timeout.
  - `0x2020` buffer unavailable / decoder busy.
  - `0x2040` unexpected operation sequence or internal inconsistency.
  - `0x2041` decoder internal state reset, such as power loss.

### Extended address format

S-9.2.1.1 uses two address bytes after 253 for traditional DCC-addressed decoder commands:

| Address type | Encoded form |
| --- | --- |
| 14-bit mobile | first byte `xx000000`-`xx100111`, low 6 bits from `CV17 & 0x3F`; second byte CV18. |
| 11-bit accessory | first byte `xx101000`-`xx101111`, based on CV521 bits0-2 plus type marker; second byte CV1. |
| 9-bit accessory | first byte `xx110000`-`xx110111`, based on CV521 bits0-2 plus type marker; second byte contains `A6..A2` and output-pair bits. |
| 7-bit mobile | first byte `xx111000`, second byte `0AAAAAAA` from CV1. |
| Broadcast | first byte `xx111000`, second byte `00000000`. |
| Reserved | first byte `xx111001`-`xx111111`. |

### Address partition 253 command types

General format:

`{sync} 0 11111101 0 TTAAAAAA 0 AAAAAAAA 0 {command byte} 0 {payload bytes} 0 {checksum} 1`

`TT` in the first address byte selects command type:

| `TT` | Type | Rules |
| --- | --- | --- |
| `11` | Addressed | First two address bytes contain destination decoder address; then command byte + payload. |
| `10` | Addressed Continue | Interpreted only in context of a previous addressed command to same decoder that explicitly permits continuation. |
| `01` | Addressed Control | Reserved; no messages currently defined. |
| `00` | Addressed S-9.2/S-9.2.1 Chained | Carries multiple ordinary multifunction decoder instruction byte sequences in one packet. |

Addressed command byte map:

| Command byte | Meaning |
| --- | --- |
| `0000HHHH` plus next `HHHHHHHH` | Manufacturer-specific command space using 12-bit NMRA manufacturer ID; total packet length including checksum <= 16 bytes, so manufacturer payload <= 9 bytes. |
| `00010000`-`11111011` | Reserved. |
| `11111100` | `WriteBlock`, data space write. |
| `11111101` | `ReadBackground`, background data space read. |
| `11111110` | `ReadBlock`, fast data space read. |
| `11111111` | Reserved. |

Chained ordinary command rules:

- Each instruction-byte sequence is a separate S-9.2/S-9.2.1 multifunction decoder command.
- Chained packet maximum length is 16 bytes including `0xFD` and checksum byte(s).
- Successful reception requires Channel 2 ACK or another appropriate feedback response.

### Address partition 254 command types

General format:

`{sync} 0 11111110 0 {command byte} 0 {parameter bytes} 0 {checksum} 1`

| Command byte | Meaning |
| --- | --- |
| `00000000` | `Get Data Start`, first sequenced request for decoder upstream data. |
| `00000001` | `Get Data Continue`, continue upstream data transfer. |
| `00000010` | `Set Data Start`, reserved for future definition. |
| `00000011` | `Set Data Continue`, reserved for future definition. |
| `00000100`-`10111111` | Reserved. |
| `1101HHHH` | `Select`, request metadata such as desired address from a decoder identified by DID. |
| `1110HHHH` | `Logon Assign`, assign a DCC address to a decoder identified by DID. |
| `11110000`-`11111011` | Reserved. |
| `111111GG` | `Logon Enable`, request registration from decoders in address group `GG`. |

CV28 bit7 must be set for decoder to accept partition 254 commands `0xE0..0xFF` such as Logon Assign and Logon Enable. It does not block Get Data or Select.

### Logon / automatic registration

- DID is a unique 44-bit decoder ID: 12-bit manufacturer ID followed by 32-bit unique ID, big-endian.
- CID is a 16-bit system ID; Session ID is 8-bit and increments on each system restart, wrapping after 255.
- Decoder logon states: Unselected or Selected.
- Procedure:
  1. Enumeration: system sends Logon Enable with CID/session; unselected decoders answer with DID, resolving collisions via back-off.
  2. Confirmation: system sends Select to DID; decoder enters Selected.
  3. Assignment: system sends Logon Assign with session DCC address; decoder responds with change flags/counter/capability flags.
  4. Configuration discovery: system may read CVs via POM/XPOM or data-space commands.
- Logon Enable:
  - Format command byte `111111GG` plus two CID bytes and one Session ID.
  - `GG=00` all, `01` mobile only, `10` accessory only, `11` NOW all regardless of back-off.
  - Send at least every 300 ms during registration; faster after system start is recommended.
  - Selected decoders never answer Logon Enable.
  - NOW resets current back-off and makes all matching decoders try again.
- Select:
  - Command byte `1101HHHH` plus DID and command byte.
  - `0xFF` ReadShortInfo: inline response contains suggested decoder address, function/output capability value, and protocol support flags.
  - `0xFE` ReadBlock: returns ACK, then must be followed immediately by Get Data Start.
  - `0xFB` Set Decoder Internal Status: `0xFF` clears all change flags.
  - `0xFC` WriteBlock is not currently defined under Select.
- Get Data:
  - Get Data Start allowed only immediately after a recognized command sequence requiring it.
  - Decoder starts variable-length feedback in Start cutout and continues over Get Data Continue.
  - Data space number seeds CRC-8 for the response.
  - Extra Continue after all payload+CRC transferred gets ACK.
- Logon Assign:
  - Assigns session address only; must not modify CV1/CV17/CV18/CV19 for mobile or CV1/CV9 for accessory.
  - Response ID13 includes change flags, 12-bit change counter, and protocol support flags.
  - Change flags include CV19 consist set, GUI data changed, function assignment changed, driving behavior changed, firmware changed, and change flags last reset by different system.
- Decoder startup:
  - If no Logon Enable within 700 ms after startup, decoder proceeds with permanent DCC address and CV19 consist if set.
  - If CID matches and Session ID is same or incremented by <4, decoder starts Selected and accepts prior assigned address.
  - If assigned address 0, or after three consecutive Logon Enable(NOW) responses no valid Assign is received, decoder remains zero speed and indicates error; mobile default indication is double blink front/rear lights with 1-2 s period if hardware supports it.
- Back-off:
  - If Select confirmation not received after response, skip random count of future Logon Enable messages.
  - Ranges increase 0-7, then 0-15, 0-31, 0-63, then stay at 0-63.
  - Random sequence should be uniform across same-manufacturer populations and differ sufficiently across decoders; TRNG may be used.
- CV19 consist with session addresses:
  - If decoder reverts to permanent address, honor programmed CV19.
  - Otherwise ignore CV19 until system reaffirms it by POM or consist control; then honor until returning to Unselected.

### Data spaces

- Data spaces support large data transfer between system and decoder.
- Data space number seeds CRC-8 for ReadBackground and ReadBlock feedback.
- WriteBlock:
  - Partition 253 addressed command `0xFC`.
  - Parameters: data space number, 24-bit offset MSB-first, payload bytes.
  - Immediate ACK means error-free packet reception only, not completed write.
  - Completion feedback uses Channel 2 ID13 with status:
    - success.
    - written data differs from sent data.
    - permanent error plus optional error code.
    - temporary busy/error plus optional error code.
    - still in progress.
  - If no write feedback for 700 ms, system assumes lost.
  - Decoder sends still-in-progress at least every 500 ms or next opportunity until complete/fail.
  - WriteBlock Continue may follow only after successful prior WriteBlock and with no intervening 253 addressed command; if continue fails, retry with explicit WriteBlock offset, not Continue.
- ReadBackground:
  - Partition 253 addressed command `0xFD`.
  - Parameters: data space number, optional 24-bit offset, optional byte count.
  - Missing offset means 0; missing count means read until data space exhausted.
  - First upstream chunk ID13, further chunks ID14, using variable-length feedback.
- ReadBlock:
  - Partition 253 addressed command `0xFE`.
  - Returns ACK, then system sends partition 254 Get Data Start/Continue to pull variable-length data.
- Data space definitions:
  - `0` Capabilities, read-only.
  - `1` Data Space Info, read-only.
  - `2` Short GUI, writable.
  - `3` Configuration Variables, writable.
  - `4..255` reserved.
- Capabilities data space:
  - byte0 bit6 XPOM supported; bit5 Select+ReadBlock; bit4 ReadBlock; bit3 ReadBackground.
  - byte1 bit3 CV read/write data space; bit2 Short GUI; bit1 Data Space Info; bit0 Capabilities.
  - byte2 bit7 chained S-9.2/S-9.2.1 supported.
  - byte3 bit0 extended capabilities supported if any nonzero byte from byte4 onward.
- Data Space Info is one bit per data space number; omit bytes beyond highest supported space.
- Short GUI:
  - bytes0-7 UTF-8 short name, NUL padded.
  - bytes8-9 image index, future-defined.
  - byte10 F0 function information and principal symbol.
  - bytes11-28 hold two bits per F1-F68 function, omit beyond highest configured function.
  - Principal symbols cover steam/diesel/electric locos, railcars, passenger/caboose, MOW, generic function, road vehicles, mobile/other, and accessory types turnout/signal/turntable/lighting/traffic light/other.
  - Function information: undefined, latching, momentary, trigger.
- Configuration Variables data space offset is indexed CV address; first byte maps to CV31, second to CV32, third to CV offset.
- Data spaces may be overlaid onto indexed CV space; CV mapping prepends length. A length of 0 or 255 means unimplemented.

## Fail-safe

- Fail-safe 关注 DCC 信号丢失、无效、反复 reset、重复命令中断和异常供电后的 decoder 行为。
- Decoder 必须区分：
  - 有效寻址包丢失但仍有 DCC 能量。
  - DCC 信号完全消失。
  - 轨道转入其他控制格式。
  - Service mode 或 reset 序列。
- CV11 / packet timeout 控制没有有效 packet 时保持 digital mode 的时长；0 通常表示无超时。
- 车辆安全策略：
  - 收到 reset 或 emergency stop 时按急停处理。
  - 信号丢失超过配置时间后应进入可预测状态，不应继续无限执行危险动作。
  - 恢复 DCC 后不要凭过期速度包恢复不可预期运动；应等待有效命令。
- 附件安全策略：
  - 瞬时线圈必须有超时保护，避免持续上电烧毁。
  - SRQ pending 时不应执行会掩盖故障的动作，除非收到标准清除命令。
- Command station / booster：
  - idle packet 可维持能量但不得触发 decoder 动作。
  - reset 后避免立刻发送 112-127 地址 operations packet。
  - RailCom cutout、其他格式插入和 DCC packet repetition 不得破坏 decoder fail-safe。

## 实现测试矩阵

- Bit layer：
  - `1` bit 52/58/64 us 边界。
  - `0` bit 90/100/10000 us 边界，整 bit 12000 us 上限。
  - 极性翻转、相位定义、过零斜率、噪声和半 bit 不对称。
- Packet layer：
  - preamble/sync 9/10/12/14/17 个 `1` 的 NMRA/RCN 差异。
  - byte start `0` 缺失、packet end `1` 缺失、end bit 作为下一 sync。
  - XOR 正确/错误；高级 253/254 包 CRC-8 正确/错误。
  - 连续 packet、gap 后 26 us 保持和 5 ms 响应间隔。
- Address layer：
  - broadcast、short mobile、long mobile、basic accessory、extended accessory、reserved、253、254、idle。
  - 112-127 reset 后禁发窗口。
  - accessory 线性/旧式非线性地址、地址 0-3 映射到末端。
- Command layer：
  - stop / emergency stop / reset / hard reset。
  - 14/28/128 speed steps 和 target speed。
  - F0-F68、short/long binary state、analog function。
  - consist CV19/CV20 和 CV21/CV22 函数归属。
  - basic/extended accessory activate/deactivate/aspect/timed output/NOP。
- CV layer：
  - long form byte verify/write、bit verify/write。
  - short form CV17/18、CV31/32、CV19/20。
  - XPOM read/write/bit write、sequence、queue、只读 CV 返回。
  - service mode ACK、未实现 CV 行为、register mode/page mode。
- RailCom layer：
  - cutout timing、Channel 1/2 容量、4-out-of-8 code、ACK/NACK。
  - MOB ADR high/low、dynamic Channel 1、Info1、POM、XPOM、DYN、CV-auto。
  - STAT SRQ、stat1/error、NOP 搜索和 SRQ 清除。
- Safety layer：
  - signal loss、invalid stream、format switching、reset burst、RailCom cutout with non-RailCom decoder。
  - 线圈输出超时和主线误写 CV 防护。
