# Programming Environment, Special CV Values, Function Mapping, and Signal Accessories

来源：NMRA S-9.2.3、RCN-216、RCN-226、RCN-227、MOROP NEM 608、NEM 672。

## RCN-216 programming track environment

- 编程轨用于配置 decoder，也可做低风险初始功能测试；service mode packet 不含业务地址，因此必须与主线物理隔离。
- 若编程轨可切换到 operations mode，进入编程模式前至少断电 1 s。
- 上电初期建议至少 100 ms 将电流限制在 250 mA +/-20%；若 100 ms 后 decoder 电流未降到 100 mA 以下，应判定短路并关闭轨道。
- 兼容较大 decoder 时可允许固定电流高到 1 A，但必须缩短高电流时间或给用户明确警告，保持损坏风险可控。
- 上电准备阶段发送 reset packet，至少 25 个 reset packet；编程轨电压 8-18 V。
- 编程模式 packet preamble/sync 至少 20 个 `1`，给 decoder 更多处理时间；额外 sync 不得作为进入编程模式的条件。
- 编程模式不得插入 RailCom cutout，不得发送其它协议。
- Decoder 收到 reset packet 后只进入“准备编程”状态；只有 reset packet 后立即收到 service-mode data packet 才切换到编程模式。
- Decoder 必须在上电和 reset packet 开始后 100 ms 内关闭非必要负载，把电流降到 100 mA 以下；多 decoder/SUSI 模块车辆建议降到 25 mA 以下。
- 150 ms 后 decoder 电流应稳定，变化小于 30 mA，便于 programmer 取 ACK 检测基线。
- Decoder 离开编程模式条件：
  - 收到不属于 service-mode 命令序列的 operations-mode packet。
  - 距最后 reset packet 或 service-mode packet 超过至少 30 ms。
  - 不应过早把 service-mode packet 当作 7-bit operations address 执行。
- Service mode ACK：
  - 默认通过 decoder 电流增加至少 60 mA，持续 5-7 ms。
  - 若用电机制造 ACK，脉冲极性应交替，尽量避免车辆移动。
  - ACK 只能在写入/校验及必要的非易失保存完成后产生。
  - paired CV（如 CV17/18）每个写入 packet 都要 ACK，即使第一个值先暂存在临时变量。

## RCN-226 special CV values

- CV8 写入 `8` 是唯一标准化 factory reset 值：
  - 只在编程模式中作为安全默认处理。
  - 必须把所有 CV 恢复到 decoder 手册声明的固定 factory default。
  - 默认值不得依赖此前编程状态或其它动态配置。
- CV8 的其它写入值不是标准值，可由厂家用于部分 reset、恢复配置表、载入 sound project 相关配置或选择预设；实现不得把这些值宣称为 NMRA/RCN 通用值。
- CV7 用于无地址设备的特殊配置：
  - 设备可在 operations mode 独立于地址识别 CV7 写命令，但只能使用不可变 CV7。
  - 必须先写入 key value 才允许随后写入实际配置值；超时或完成后重新锁定。
  - key value 使用厂家 ID；Lenz 历史设备可继续使用 `50`。
- 若 decoder 用 CV7 做特殊配置，operations mode 写 CV7 必须忽略，只允许 service/programming mode 写入，避免与无地址设备冲突。
- 已知厂商值列表只作信息参考；不得作为通用协议判断。

## RCN-227 extended function mapping

RCN-227 定义 CV31/CV32 选择的 indexed CV function mapping。CV96 选择 decoder 实现的映射方式；多个方式同时实现时，用户通过 CV96 选择。

### Method 2: CVs per function

- 选择块：`CV31=0`, `CV32=40`。
- CV257-512 提供 256 byte。
- 每个 function + direction 占 4 byte：
  - F0 forward: CV257-260。
  - F0 reverse: CV261-264。
  - F1 forward: CV265-268。
  - F1 reverse: CV269-272。
- 前 3 byte 的 bit 映射输出 1-24；bit=1 表示该 function/direction 激活该输出。
- 多个 function 控制同一输出时 OR 组合。
- 第 4 byte 是 inhibit function number；`255` 表示无 inhibit。

### Method 3.1: CVs per output, matrix

- 选择块：`CV31=0`, `CV32=41`。
- 每个 output + direction 占 4 byte。
- bit 映射：
  - byte 1 bits 0-7 = F0-F7。
  - byte 2 bits 0-7 = F8-F15。
  - byte 3 bits 0-7 = F16-F23。
  - byte 4 bits 0-7 = F24-F31。
- 最多 32 个输出；不支持 binary state 控制或 inhibit。

### Method 3.2: CVs per output, function number

- 选择块：`CV31=0`, `CV32=42`。
- 每个 output + direction 占 4 byte。
- 每个 byte 是 function number；`255` 表示 inactive。
- 前 3 byte 激活输出；第 4 byte 独立 inhibit。
- function number 大于 28（实现支持 F68 时可调整到 68）解释为 binary state number。
- 支持最多 32 个输出、每输出最多 4 个 function/binary-state 控制。

### Method 3.3: CVs per output, function or binary state number

- 选择块：`CV31=0`, `CV32=43`。
- 每个 output 占 8 byte。
- 前 4 byte 是 function + direction：
  - bits 0-5 是 function number 0-63。
  - bits 7..6 = `00`：不区分方向。
  - bits 7..6 = `01`：forward only，等价 function number + 64。
  - bits 7..6 = `10`：reverse only，等价 function number + 128。
  - bits 7..6 = `11`：inhibit，等价 function number + 192。
  - `255` 表示 inactive。
- 后 4 byte 是两个 2-byte selector：
  - 第一个 byte 低 7 bit 是高位，第二个 byte 是低 8 bit。
  - selector <= 28（或实现支持到 68）表示 function；更大表示 binary state。
  - 第一个 byte bit 7 置位表示 inhibit。
  - `255,255` 表示 inactive pair。
- 支持最多 32 个输出、每输出最多 6 个 function/binary-state 控制；binary-state 不带方向条件。

## NEM 608 user-facing function assignment

NEM 608 是用户层功能键建议，不定义 DCC packet 编码；用于判断车辆出厂功能号是否符合 MOROP 推荐。

- 目标：让不同牵引类型的模型在默认状态下用直觉一致的 function key 控制常见附加功能。
- 用户仍可重映射 function key；factory reset 应恢复 NEM 608 对应的出厂默认映射。
- 若模型没有某功能，按下对应 function key 时 decoder 应忽略。
- 牵引类型：steam、diesel/internal-combustion、electric、open/special。
- 功能类别：lighting、operation、sound、setup/arming。

### Operating mode 1

一层映射，前 10 个 functions：

| Function | Category | Steam | Diesel | Electric | Switch type |
| --- | --- | --- | --- | --- | --- |
| F0 | Lighting | direction lights | direction lights | direction lights | on/off |
| F1 | Lighting | rear light | rear/end light | rear/end light | on/off |
| F2 | Operation | whistle | whistle/horn | whistle | momentary |
| F3 | Sound | stand/start/run/brake | engine start/stand/start/run/brake/shutdown | stand/start/run/brake | on/off |
| F4 | Operation | uncoupling | uncoupling | uncoupling | momentary |
| F5 | Operation | shunting | shunting | shunting | on/off |
| F6 | Lighting | cab | cab | cab | on/off |
| F7 | Lighting | firebox | engine room/interior | engine room/interior | on/off |
| F8 | Setup | steam generator | exhaust generator | pantograph | on/off or up/down |
| F9 | Sound | air pump | compressor | compressor | on/off |

### Operating mode 2

- Level 1:
  - F0 lighting category.
  - F1 operation category.
  - F2 sound category.
  - F3 setup/arming category.
- Level 2:
  - F0 returns to level 1.
  - Lighting: direction lights, rear/end light, cab, firebox or engine-room/interior.
  - Operation: whistle/horn, uncoupling, shunting.
  - Sound: stand/start/run/brake or engine start/shutdown sequences, air pump/compressor.
  - Setup/arming: steam generator, exhaust generator, pantograph.
- Open traction type is reserved for wagons, non-powered vehicles, accessories, or special applications.

## NEM 672 advanced accessory signal control

- NEM 672 使用 RCN-213 extended accessory decoder packet 的第三 data byte 表达 signal concept；信号图像的具体灯光生成不是 NEM 672 范围。
- Data byte 高 4 bit 是 additional signal / modifier，低 4 bit 是 speed tens digit。
- 低 4 bit：
  - `0000` = stop。
  - `0001`-`1110` = 10 km/h 到 140 km/h 的十位速度。
  - `1111` = highest permitted speed / no explicit speed limit。
- 高 4 bit 与速度组合解释；常用编码：
  - `0000`: 无 additional signal，只显示允许速度。
  - `0001` + `0000`: replacement/auxiliary signal for limited time, usually with stop aspect.
  - `0010` + `XXXX`: direction indicator；后续同地址 packet 可用 ASCII `65`-`90` 表示字母。
  - `0011` + `0001`-`1111`: speed indicator，显示速度十位。
  - `0100` + `XXXX`: darken/switch off signal aspect for operational situations。
  - `0101` + `0001`-`1110`: shunting signal at reduced speed。
  - `0110` + `XXXX`: track-change symbol。
  - `0111` + `XXXX`: right/left running order signal。
  - `1000` + `XXXX`: wrong-track running symbol。
  - `1001` + `XXXX`: signal repeat / shortened braking distance / short block entry。
  - `1010` + `0000`: emergency red / second red; cleared by `1111` or shunting function depending system。
  - `1011` + `XXXX`: proceed on sight / enter occupied track。
  - `1100` + `XXXX`: switching time, 0.2 s steps from 0.2 s to 3.0 s。
- 若同一 mast 需要两个 signal concepts，例如 main signal + distant signal，需要 decoder 使用另一个 DCC address。

## Tests

- 编程轨：断电 1 s、25 reset packet、20 sync bits、无 RailCom cutout、8/18 V 边界、100 mA/250 mA/1 A 策略、ACK 5/7 ms。
- CV special：CV8=8 reset；CV8 非 8 不作通用解释；CV7 key-value flow；operations-mode CV7 ignore for normal decoder。
- Function mapping：NEM 608 default user mapping；CV31/32 = 40/41/42/43；CV96 select；inactive `255`；direction/inhibit encoding；binary-state boundaries 28/68/32767。
- NEM 672：stop/highest speed、direction ASCII follow-up、speed indicator、dark/shunt/wrong-track/proceed-on-sight/emergency red/switching time。
