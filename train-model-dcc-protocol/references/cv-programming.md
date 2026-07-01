# CVs and Programming Commands

来源：NMRA S-9.2.2/S-9.2.3、NMRA S-9.2.2 draft、RailCommunity RCN-214/225。

## CV access modes

- Service mode：隔离编程轨/低能量环境；packet 通常无 operations address，first byte 是 programming command。
- Operations mode / POM：在主线轨道对已寻址 decoder 编程；必须避免误写同地址多 decoder。
- Long form CV access：可访问 10-bit CV 地址，即 CV1-CV1024。
- Short form CV access：只在 operations mode 对少数指定 CV 或 CV 对使用。
- XPOM：operations mode 高速扩展，可线性访问 24-bit CV 地址，最多一次读/写 4 byte，通常结合 RailCom 回读。
- Register mode：最旧的 8 register 访问方式；保留兼容，不推荐新实现使用。

## Long form CV access

格式：

| 模式 | Byte/bit pattern | 含义 |
| --- | --- | --- |
| Operations byte access | `1110-KKVV VVVV-VVVV DDDD-DDDD` | POM byte verify/write。 |
| Operations bit access | `1110-10VV VVVV-VVVV 111K-DBBB` | POM bit verify/write。 |
| Service byte access | `0111-KKVV VVVV-VVVV DDDD-DDDD` | Service mode byte verify/write。 |
| Service bit access | `0111-10VV VVVV-VVVV 111K-DBBB` | Service mode bit verify/write。 |

规则：

- CV 地址字段是 10-bit `VV VVVV-VVVV`，实际 CV 编号 = 地址字段 + 1。
- 编程设备必须支持整个 10-bit CV 地址范围。
- `KK=00` reserved。
- `KK=01` byte verify：比较 CV 当前 byte 与 `D`。
- `KK=11` byte write：用 `D` 替换 CV。
- `KK=10` bit manipulation：第三 byte `111K-DBBB`。
  - `BBB` 是 bit position 0-7。
  - `D` 是要验证/写入的 bit 值。
  - `K=0` bit verify，`K=1` bit write。
- 若支持 byte verify、byte write、bit manipulation 任意一种，则三者都应支持。

### Operations mode write sequence

- 写 CV 时，decoder 只有在收到两个相同 packet 后才允许改变 CV。
- 两个相同 packet 不要求紧邻，但第二个之前出现任何发给同一 decoder 的其他 packet 会取消这次写操作；broadcast 也会取消。
- 写操作开始后，其他命令可以发送，但新的写命令可能干扰；应等确认后再发，若无确认能力至少等待约 100 ms。
- 7-bit 地址必须是 base address；decoder 不应响应发给 consist address 的 CV access。
- Accessory decoder 配置通常通过该 decoder 响应操作命令的地址访问；标准默认使用 decoder 内第一地址，其他地址访问必须由厂家文档说明。

## Short form CV access

- Format：`1111-KKKK DDDD-DDDD` 或 `1111-KKKK DDDD-DDDD DDDD-DDDD`。
- 只用于 operations mode，只可寻址车辆 decoder 的 7-bit/14-bit base address。
- 两个数据 byte 时，第二 byte 对低编号 CV，第三 byte 对高编号 CV。

| `KKKK` | 目标 |
| --- | --- |
| `0000` | 不得使用。 |
| `0010` | CV23 consist acceleration trim；单 packet 即可修改。 |
| `0011` | CV24 consist deceleration trim；单 packet 即可修改。 |
| `0100` | 同时写 CV17/CV18，并设置 CV29 bit 5；需要两个相同 packet。 |
| `0101` | 同时写 CV31/CV32 index；需要两个相同 packet。 |
| `0110` | 同时写 CV19/CV20 consist address；需要两个相同 packet。 |
| `1001` | reserved / deprecated F9 command context；不要新发。 |

其余 `KKKK` reserved。写 CV17/18 时优先使用 short form，避免只改一半长地址。

## XPOM

- General format：`1110-KKSS VVVV-VVVV VVVV-VVVV VVVV-VVVV {DDDD-DDDD...}`。
- 只用于 operations mode；寻址同 long form operations mode。
- `KK=01` read bytes，不发送 data byte，RailCom 返回连续 4 个 CV 值。
- `KK=11` write byte(s)，后接 1-4 个 data byte，写入起始 CV 及后续 CV；RailCom 返回连续 4 个 CV 当前值。
- `KK=10` bit write，第五 byte `1111-DBBB`，仍返回连续 4 个 CV 当前值。
- `SS` 是 sequence number；无 RailCom 时建议置 `00`。
- 写 XPOM 时 decoder 只有在 back-to-back 收到两次相同命令后才接受。
- `VVV...` 是 24-bit CV 地址，最高 byte 先传：
  - byte 1 对应 CV31。
  - byte 2 对应 CV32。
  - byte 3 对应 long form 的低 8-bit CV offset。
  - 理论空间 16,777,216 个 CV。
- RailCom XPOM response 使用 ID 8-11 对应 `SS=00..11`。
- decoder 应实现 4 项 XPOM queue；同 sequence 重复包只入队一次，收到对应 response 后释放。
- 快速连续读时，第 1 个 XPOM read 的响应最迟应在第 3 个 XPOM read 的 cutout 中返回，第 2 个最迟在第 4 个中返回，依此类推。

## Register mode

- Format：`0111-KVVV DDDD-DDDD`，只在 service mode 有效，无地址。
- `VVV=000..111` 选 register 1-8。
- `K=0` verify，`K=1` write。
- Register 对 CV 的映射：
  - Register 1-4 通常映射 CV1-CV4，但受 register 6 page 影响。
  - Register 5 映射 CV29。
  - Register 6 是 page register。
  - Register 7/8 映射 CV7/CV8。
- Address Only Mode：通过 register 1 访问 CV1，是最小编程能力的一部分。
- Decoder Factory Reset：写 register 8 值 8，可触发厂家默认值恢复；实际写回可能跨后续上电周期完成，期间 CV8 可临时返回 255。
- Paged mode：
  - Register 6 作为页号，每页 4 个 CV。
  - Register 1 对应 `Register6 * 4 - 3`；register 2-4 是后续 3 个 CV。
  - 进入 operations mode 时 register 6 应复位为 1。

## Service mode acknowledgment

- 成功写操作和 verify 命中必须确认；确认机制由 service mode 规范定义，常见为电流脉冲。
- 读取未实现 CV 的建议行为：
  - bit verify 对 bit=0 和 bit=1 都响应。
  - byte verify 不响应。
  - 这样可区分“未实现 CV”和“任意值 CV”。
- Service mode 必须作为隔离低能量环境处理，不要在主线轨道执行未知写入。

## Vehicle CV table

| CV | 名称 / 用途 | 关键规则 |
| --- | --- | --- |
| 1 | Short/base address | bits 0-6 是 1-127；bit 7 为 0；若 CV1=0 或 >127 且 CV29 bit5=0，DCC 运行地址禁用但仍可编程。默认 3。 |
| 2 | Vstart/min speed | speed step 1 的起始电机电压；0 表示无电压，255 表示全电压。 |
| 3 | Acceleration factor | 推荐公式 `(CV3 * 0.896) / speed_steps` 秒/级；0 表示无编程加速。 |
| 4 | Deceleration factor | 与 CV3 同类，用于制动。 |
| 5 | Vhigh/max speed | 最高速度时电机电压比例；0/1 表示不用作速度表计算。 |
| 6 | Vmid/mid speed | 中速点电机电压比例；0/1 表示不用作速度曲线计算。 |
| 7 | Decoder version | 厂家定义，只读；写入可被 RCN-226 等用于特殊无地址配置。 |
| 8 | Manufacturer ID | NMRA 分配，只读；写入特定值可触发 reset；238 表示 CV107/108 承载扩展 12-bit 厂商 ID。 |
| 9 | PWM period | 电机 PWM 周期。 |
| 10 | Manufacturer-specific | 原 Back-EMF cutout 含义已释放，厂家自定义。 |
| 11 | Packet timeout | 无数据仍保持数字模式的最长时间；0 表示无限；应支持至少到 20 s，且不低于约 30 ms。 |
| 12 | Allowed modes | bit0 DC、1 radio、2 DCC、3 Selectrix、4 AC、5 Motorola、6 mfx、7 reserved；0 禁止、1 允许。 |
| 13 | Analog/alternate F1-F8 | 无法数字控制函数时的替代函数状态，bit0=F1。 |
| 14 | Analog/alternate F0/F9-F12 | bit0=F0 forward，bit1=F0 reverse，bit2=F9，bit5=F12。 |
| 15/16 | Decoder lock | CV15 与 CV16 相等才允许访问被锁 decoder；CV15=255 触发复制 CV16 到 CV15 以解锁。CV16 240-255 不允许。 |
| 17/18 | Long address | CV17 bits0-5 是 A13-A8，bits6-7 必须为 1；CV18=A7-A0；地址 0 无效；默认长地址 1000。 |
| 19/20 | Consist address | CV19 bits0-6 短 consist；CV19 bit7 相对方向；CV20 支持长 consist 的高十进制部分和 leader 标记。 |
| 21 | Consist functions F1-F8 | bit=1 时对应函数由 consist address 控制；bit0=F1。 |
| 22 | Consist F0/F9-F28 | bit0 F0 forward，bit1 F0 reverse，bit2 F9，bit5 F12，bit6 F13-F20，bit7 F21-F28。 |
| 23/24 | Consist acceleration/deceleration trim | 7-bit magnitude + bit7 sign；用于对 CV3/CV4 做加减。 |
| 25 | Speed table selector | 选择速度表；CV67-94 与 CV29 bit4 相关。 |
| 26 | Reserved NMRA | 不要使用。 |
| 27 | Automatic stopping | 配置 decoder 对自动停车/制动方式的反应。 |
| 28 | RailCom config | 见 `railcom-failsafe-advanced.md`；bit0/2/3 车辆专用，bit1 Channel 2，bit6 high-current，bit7 auto logon。 |
| 29 | Decoder configuration | bit0 direction invert；bit1 speed-step mode；bit2 analog conversion；bit3 RailCom；bit4 speed table；bit5 long address；bit6/7 通常 reserved/扩展。 |
| 30 | Error information | 动态错误码；0 表示无错误。 |
| 31/32 | Index pointer | 指向 CV257-512 扩展页；CV31 高 byte，CV32 低 byte。 |
| 33-46 | Function mapping F0-F12 | 传统 14 输出矩阵；默认 F0 forward->LV、F0 reverse->LH、F1-F12 对输出 3-14。 |
| 47-64 | Manufacturer-specific | 厂家自定义。 |
| 65 | Kick start | 旧 NMRA 起步脉冲，现代 RCN 中释放为厂家自定义。 |
| 66 | Forward trim | 前进方向电机电压比例 `n/128`；0 表示未实现。 |
| 67-94 | 28-step speed table | 28 个速度表值；14/128 级时内部省略/插值；CV29 bit4 启用。 |
| 95 | Reverse trim | 后退方向电机电压比例 `n/128`；0 表示未实现。 |
| 96 | Function mapping method | bits0-2 选择映射方式；0 invalid，1 CV33-46，2-5 RCN-227 indexed methods，6 manufacturer，7 reserved。 |
| 97-104 | Manufacturer-specific | NMRA 曾 reserved，但 RCN 允许厂家使用。 |
| 105/106 | User ID | 用户自定义车辆标识。 |
| 107/108 | Extended manufacturer ID | 当 CV8=238 时，CV108 是低 8 bit，CV107 bits0-3 是高 4 bit；否则厂家自定义。 |
| 109-111 | Manufacturer-specific/version extension | 可用于厂家版本扩展或自定义。 |
| 112-256 | Manufacturer-specific | 厂家自定义。 |
| 257-512 | Indexed extended CV area | 由 CV31/32 选页；前 4096 页保留，4096 起可用。 |
| 513-768 | Manufacturer-specific | 原附件区域，车辆可厂家自定义。 |
| 769-896 | Reserved NMRA | 不要使用；892-896 原动态 RailCom 读区暂保留。 |
| 897-1024 | SUSI CVs | 由 SUSI/RCN-602 定义。 |

## Indexed extended CV pages

- CV31=0,CV32=0：对应 CV1-256 的镜像页。
- CV31=0,CV32=1：未另行分配区域。
- CV31=0,CV32=2：对应 CV513-768。
- CV31=0,CV32=3：对应 CV769-1024，含 SUSI 区。
- CV31=0,CV32=255：RailCom block，见 RailCom reference。
- CV31=2 的数据空间与 RCN-218 有关，存储时无 header/length，CV257 是数据空间第一个 byte。

## Accessory CV table

| CV | 可选旧号 | 用途 | 关键规则 |
| --- | --- | --- | --- |
| 1 | 513 | Address low bits | 6-bit decoder address 或 8-bit output-pair address low bits；配合 CV9。 |
| 2 | 514 | Additional activation | bit=1 允许外部输入激活对应输出。 |
| 3-6 | 515-518 | Output 1-4 active time | 0 表示持续到 off command。 |
| 7 | 519 | Version | 同车辆 CV7。 |
| 8 | 520 | Manufacturer ID | 同车辆 CV8。 |
| 9 | 521 | Address high bits | bits0-2 是 11-bit 地址高 3 bit，bits3-7 为 0。 |
| 10-14 | - | Reserved NMRA | 不要使用。 |
| 15/16 | - | Decoder lock | 同车辆 CV15/16。 |
| 17/18 | - | Mirrored address | CV1/9 镜像；可用于车辆命令方式寻址。 |
| 19-27 | - | Reserved NMRA | 不要使用。 |
| 28 | 540 | RailCom config | bit1 Channel 2/ACK，bit6 high-current，bit7 auto logon；其他多为 reserved。 |
| 29 | 541 | Accessory decoder config | bit3 RailCom；bit5 basic/extended；bit6 decoder vs output addressing；bit7 accessory vs vehicle command control。 |
| 31/32 | - | Index pointer | 同车辆。 |
| 33 | - | Output status | 可通过 RailCom 回读四个输出对状态。 |
| 34-81 | - | Manufacturer-specific | 厂家自定义。 |
| 82-106 | - | Reserved NMRA | 不要使用。 |
| 107/108 | - | Extended manufacturer ID | CV8=238 时使用。 |
| 109-111 | - | Reserved NMRA | 不要使用。 |
| 112-256 | - | Manufacturer-specific | 厂家自定义。 |
| 257-512 | - | Indexed extended area | 由 CV31/32 指向。 |
| 513-895 | - | Manufacturer-specific | 厂家自由使用；旧设备可能仍响应。 |

Accessory address notes：

- CV29 bit6 决定 decoder address 模式或 output-pair address 模式；厂家必须在手册/包装标明支持方式。
- 如果 CV1=1 且 CV9=0，两种 accessory decoder 的第一输出对都响应用户地址 1（packet 地址 4）。
- 多连续输出时，保存地址为第一输出地址。

## Deprecated / forbidden programming packets

- 旧 accessory CV access `10AA-AAAA 0AAA-11VV VVVV-VVVV DDDD-DDDD` 与 accessory NOP 冲突，decoder 不得支持，command station 不得发送。
- F9 address search command 只对地址 1-111 旧式有效；优先读取 CV1。
- Service Mode Decoder Lock Instruction 使用主线普通轨上的 service-mode 格式，有误写风险；不应作为新实现默认路径。
