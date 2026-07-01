# Electrical, Bitstream, and Packet Format

来源：NMRA S-9.1/S-9.2、MOROP NEM 670/671、RailCommunity RCN-210/211。

## 电气层和 bit 编码

- DCC 轨道信号是双极性方波：两个幅值相等、极性相反的电压状态交替出现。
- bit 由过零点之间的时间编码，不由绝对电平编码；所有 timing 以过零点为测量基准。
- decoder 不能假设机车朝向，因此接收数据必须与轨道极性无关。
- 若应用需要轨道相位，RCN 约定：
  - 正相位：第一半 bit `V(right rail) > V(left rail)`，第二半 bit 相反。
  - 负相位：第一半 bit `V(right rail) < V(left rail)`，第二半 bit 相反。
- `1` bit：
  - 半 bit 名义值 58 us，整 bit 名义值 116 us。
  - 轨道输出半 bit 通常 55-61 us；两半差异不超过约 3 us。
  - decoder 接收应接受 52-64 us；两半差异可放宽到约 6 us。
- `0` bit：
  - 半 bit 名义值 100 us。
  - 轨道输出半 bit 最小约 95 us；接收最小约 90 us。
  - 为兼容模拟或其他扩展，可拉长 `0`，单半 bit 接收上限约 10000 us，整 bit 总时长不超过约 12000 us。
  - 为维持直流分量为零，两个半 bit 通常等长；为特殊控制目的可只拉长一个半 bit。
- 信号质量：
  - 过零区间约 `-4 V..+4 V` 内，发射过零斜率至少约 2.5 V/us。
  - decoder 应能在约 2.0 V/us 以上过零斜率下解码。
  - 过零附近允许有限非单调失真；RCN 对轨道输出以总幅值约 20% 为上限，接收侧应抗约 25% 干扰。
  - decoder 在规定噪声下对正确寻址包的解码概率目标为约 95%。

## 电压和供电

- DCC 轨道信号同时供电和传输数据，因此 bit 流应连续发送；停顿只允许在标准规定位置。
- NMRA S-9.1 按轨距给出 power station 和 decoder 的峰值电压范围；小比例尺低一些，大比例尺高一些。
- RCN-210 建议轨道输出幅值：
  - Z 或更小：9-12 V。
  - N 和 TT：14-16 V。
  - H0 到 0：15-18 V。
  - 1 号及更大：19-22 V。
  - 轨道 DCC 幅值不应超过约 +/-22 V；decoder 耐压 N 及以下至少 24 V，N 以上至少 27 V。
- RailCom cutout 期间 decoder 不应从轨道信号取电，必须有足够储能跨过 cutout。
- 直接暴露在 DCC 信号下的电机要注意高精密空心杯电机和高幅值场景；应按电机 stall rating 和阻抗评估。

## 通用 DCC packet

通用 packet 由以下元素组成：

1. Preamble / sync：连续 `1` bit。
2. Packet start bit：紧随 preamble 的第一个 `0`。
3. First byte：operations mode 通常是 address byte；service mode 可作为 command byte。
4. Data byte start bit：每个后续 byte 前置 `0`。
5. Data byte：8 bit，可承载地址、指令、数据或校验。
6. Packet end bit：`1`，标记 packet 结束。

约束：

- 每个 byte MSB-first 发送；bit 7 是最高位，bit 0 是最低位。
- 最后一个 data byte 是 error detection byte，按前面所有 data byte 逐位 XOR 得到。
- decoder 必须校验 XOR；失败时忽略 packet。
- 不满足 packet 结构的数据流不应被当作 DCC packet。
- NMRA S-9.2：command station 至少发送 14 个完整 preamble `1`；decoder 不应接受少于 10 个完整 `1` 的 preamble，也不应要求超过 12 个才可正确接收。
- RCN-211：command station 至少发送 17 个 sync `1`；decoder 必须能接收 12 个或更多 sync `1`；少于 10 个不得判定有效。
- Packet end bit 可作为下一个 packet 的第一个 sync bit；若后续不是 DCC packet 或存在中断，end bit 后至少 26 us 不得切换极性或断电。
- DCC packet 至少 3 个 byte：地址/命令、指令/数据、XOR 校验。
- 常规扩展包可到 6 byte；S-9.2.1.1 对 253/254 地址分区定义更长包和 CRC-8。

## 地址分区

| 第一地址字节 | 含义 |
| --- | --- |
| `0x00` | broadcast，发送给所有车辆 decoder；reset broadcast 也必须被附件 decoder 处理。 |
| `0x01`-`0x7F` | 7-bit multifunction/mobile decoder address。 |
| `0x80`-`0xBF` | accessory decoder 分区：basic accessory、extended accessory 和 NOP。 |
| `0xC0`-`0xE7` | 14-bit mobile address，第一 byte 携带高 6 bit，第二 byte 携带低 8 bit。 |
| `0xE8`-`0xFC` | 预留。 |
| `0xFD` | NMRA S-9.2.1.1 Address Partition 253，高级 addressed / chained / data space 包。 |
| `0xFE` | NMRA S-9.2.1.1 Address Partition 254，高级 logon / unique ID / data transfer 包；RCN-218 DCC-A 协调。 |
| `0xFF` | idle packet；RailComPlus 可能在此地址定义更长私有包，但不是 NMRA/RCN 通用 DCC idle。 |

## 特殊 packet 和全局命令

- Reset packet：`{sync} 0 00000000 0 00000000 0 00000000 1`。
  - 清除 decoder 易失状态，包括速度和方向。
  - 运动中的车辆执行急停。
  - 进入上电初始状态；准备 service mode 时关闭外部负载。
  - 对车辆和附件 decoder 都有效。
  - reset 后 10 个 packet 时间内不要向地址 112-127 发送 operations mode packet，避免误入 service mode。
- Idle packet：`{sync} 0 11111111 0 00000000 0 11111111 1`。
  - decoder 不应产生业务动作。
  - 用于无业务数据时维持轨道供电，或在对某 decoder 的两个命令之间制造超过 5 ms 间隔。
- Broadcast 地址 `0x00` 的全局命令只发送到 broadcast，包头/校验照常；可被车辆和附件 decoder 使用。
- 时间命令 `1100-0001 CCxx-xxxx xxxx-xxxx xxxx-xxxx`：
  - `CC=00` 模型时间：分钟 0-59、星期 0-6/7 unsupported、小时 0-23、update bit、加速因子 0-63。
  - `CC=01` 日期：日 1-31、月 1-12、年 0-4095。
  - `CC=10` 时间倍率：16-bit float，含 sign、5-bit exponent、10-bit mantissa；发送后模型时间包内加速因子应忽略。
  - `CC=11` 预留。
  - 模型时间最多每模型分钟发送一次；日期和时间倍率只在变化时发送，可重复。
- 系统时间 `1100-0010 MMMM-MMMM MMMM-MMMM`：
  - 16-bit 毫秒计数，约 65.5 s 回绕。
  - 时间戳以 start bit 开始为基准。
  - 建议每 30 s 重复；主要服务固定检测器时间标记。
- Command station capabilities `1100-0011 1111-IIII DDDD-DDDD DDDD-DDDD`：
  - `IIII=1111`：车辆功能能力，如 100-127 长地址、10000-10239 长地址、128 speed、组合速度/函数、POM/XPOM 写、F13-F28、F29-F68、短/长 binary state、模拟函数、特殊运行模式。
  - `IIII=1110`：附件和 broadcast 能力，如地址表偏移、extended accessory、POM 写、模型时间/日期/倍率、系统时间。
  - `IIII=1101`：RailCom/DCC-A/读能力，如 RailCom、DCC-A、accessory NOP、POM/XPOM 读、DYN 类别、RailComPlus。
  - `IIII=0000`：新功能测试组，不应用于量产互操作。
  - 未定义 bit 均为 reserved。

## 重复和错误恢复

- packet 应尽可能重复发送，因为轨道接触和噪声会造成丢失。
- packet end 到下一 packet start 之间可断开 DCC 或插入其他控制格式。
- decoder 必须在两个 packet 间隔至少 5 ms 时仍能响应所有寻址给自己的 packet。
- 如果缺失/错误 byte-start `0`、packet-end `1` 或 XOR 错误，decoder 必须能用后续 sync 重新同步。
