---
name: z21-lan-protocol
description: "用于解析、实现、审查或调试 Roco/Fleischmann Z21/z21 LAN UDP 协议、X-BUS 隧道、机车/道岔/反馈/RailCom/CAN 命令、广播事件或控制器兼容性。"
metadata:
  version: "v0.1"
---

# Z21 LAN 协议

用于处理 Roco/Fleischmann Z21/z21 控制器的 LAN 协议：UDP 报文、dataset 解析、X-BUS/XPressNet 隧道、机车、道岔、反馈、RailCom、LocoNet、CAN 和控制器型号兼容性。

## 资料选择

- 实现报文编解码、监听抓包、写网关或解析十六进制数据时，读 `references/protocol.md`。
- 问题涉及 black Z21、white z21、z21 start、Z21 XL、固件版本、解锁状态或硬件能力时，读 `references/hardware-compatibility.md`。
- 需要核对官方资料或本地开源实现依据时，读 `references/source-map.md`。

## 基本判断

- Z21 LAN 是 UDP 二进制协议，默认控制器端口 `21105`；外层 `DataLen` 和 `Header` 都是小端。
- 一个 UDP datagram 可以包含多个 dataset；必须按每个 dataset 的 `DataLen` 分帧，不能把整个 datagram 当成单帧。
- Header `0x0040` 是 `LAN_X`，其 payload 是 X-BUS/XPressNet 风格消息，需要独立校验 X-Header、DB 字节和 XOR checksum。
- 不要只按 black/white/start/XL 名称写死能力；先读取 `LAN_GET_HWINFO`、`LAN_X_GET_FIRMWARE_VERSION`、`LAN_GET_BROADCASTFLAGS`，再按实际返回和固件版本降级。
- 修改轨道电源、机车速度/功能、道岔、CV、R-Bus 模块、CAN 描述或 booster 输出前，真实设备场景必须确认用户授权。

## 输出要求

分析协议或代码时，输出应包含：

- UDP 端点、完整十六进制帧、dataset 长度、header 和 payload 解释。
- 对 `LAN_X` 消息的 X-Header、DB 字节、checksum 和对应业务动作解释。
- 是否只读、是否会改变控制器状态，以及真实设备风险。
- 控制器硬件类型、固件版本、广播标志和功能可用性判断。
- 与官方 Z21 LAN Protocol 和本地 JMRI/Traintastic 实现的对应依据。
