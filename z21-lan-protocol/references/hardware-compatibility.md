# Z21 硬件兼容性

## 结论

black Z21、white z21、z21 start 和 Z21 XL 使用同一 LAN 协议族。实现不要按商品名写多套协议；应读取硬件类型、固件版本、广播 flags 和实际响应，再按能力降级。

Traintastic 文档明确把 `z21 start`、`z21 white`、`Z21 black` 作为相同网络配置处理：IP/hostname 加 UDP 端口 `21105`。JMRI 和 Traintastic 的协议代码也没有按这些商品名拆分帧结构。

## 硬件类型

`LAN_GET_HWINFO` 返回 hardware type。常见值：

| 值 | 含义 |
| --- | --- |
| `0x00000200` | black Z21，2012 硬件变体。 |
| `0x00000201` | black Z21，2013 硬件变体。 |
| `0x00000202` | SmartRail。 |
| `0x00000203` | white z21 starter set variant。 |
| `0x00000204` | z21 start starter set variant。 |
| `0x00000205` | Z21 Single Booster 10806。 |
| `0x00000206` | Z21 Dual Booster 10807。 |
| `0x00000211` | Z21 XL Series 10870。 |
| `0x00000212` | Z21 XL Booster 10869。 |
| `0x00000301` | Z21 SwitchDecoder 10836。 |
| `0x00000302` | Z21 SignalDecoder 10837。 |

未知 hardware type 应保留原始十六进制值，并继续做只读能力探测。

## 固件能力

按固件版本判断这些行为：

| 固件 | 行为 |
| --- | --- |
| `1.20..1.23` | `AllLocoChanges` 可能发送所有机车信息。 |
| `1.24+` | `AllLocoChanges` 发送变化过的机车信息。 |
| `1.29+` | 新版 RailCom data changed broadcast。 |
| `1.30+` | CAN detector broadcast。 |
| `1.41+` | CAN booster status broadcast。 |
| `1.42+` | `LAN_X_LOCO_INFO` 可携带 F29-F31。 |
| `1.43+` | Fast Clock broadcast。 |

实现中应始终按实际 `DataLen` 判断字段是否存在，不能仅凭版本假定 payload 长度。

## white z21 / z21 start 注意点

- white z21 和 z21 start 的网络协议入口仍是 UDP `21105`。
- 某些产品功能可能受固件、授权或解锁状态限制；读取 `LAN_GET_CODE`、`LAN_GET_HWINFO`、`LAN_GET_BROADCASTFLAGS` 后再决定能力。
- 不要因为型号是 white/start 就禁用所有高级命令；也不要因为连接成功就默认可用 LocoNet、CAN、RailCom 或 booster 功能。

## 功能探测顺序

只读初始化建议：

1. `LAN_GET_SERIAL_NUMBER`
2. `LAN_GET_HWINFO`
3. `LAN_X_GET_FIRMWARE_VERSION`
4. `LAN_GET_BROADCASTFLAGS`
5. `LAN_SYSTEMSTATE_GETDATA`
6. 按需读取 `LAN_GET_CODE`、`LAN_X_GET_VERSION`、`LAN_X_GET_STATUS`

写操作前必须确认：

- 目标硬件支持该功能。
- 固件版本满足字段或广播能力要求。
- 用户明确允许真实设备状态改变。
- 当前 track power、emergency stop、short circuit 状态不会导致危险动作。

## 降级规则

可以降级：

- 未收到响应或响应长度不符合当前功能预期。
- `LAN_X_UNKNOWN_COMMAND`。
- hardware type 未知但基础只读命令正常。
- 固件低于扩展能力要求。
- broadcast flag 设置后读取不含目标 bit。

不要降级：

- 仅因为商品名是 `z21 start`、`white z21`、`black Z21` 或 `Z21 XL`。
- 仅因为没有收到某类广播但未设置对应 broadcast flag。
- 仅因为没有 LocoNet/CAN 硬件模块。
