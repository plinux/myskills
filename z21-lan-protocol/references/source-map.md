# 来源映射

## 官方来源

- Z21 LAN Protocol specification V1.13: `https://www.z21.eu/media/Kwc_Basic_DownloadTag_Component/root-en-main_47-1652-959-downloadTag-download/default/d559b9cf/1628743384/z21-lan-protokoll-en.pdf`
  - 确认 LAN 协议基于 UDP。
  - 确认 dataset 由 little-endian `DataLen`、little-endian `Header` 和 payload 组成。
  - 确认 `LAN_X` 作为 X-BUS 隧道，覆盖电源、机车、道岔、CV 等命令。
  - 确认广播 flags、系统状态、RailCom、R-Bus、LocoNet、CAN 和硬件信息命令。
- Z21 official site: `https://www.z21.eu/`
  - 用于核对 Z21/z21 产品线、软件和协议资料来源。
- Z21 Maintenance Tool V1.18.3: `https://www.z21.eu/en/products/z21-maintenance-tool`
  - 手册确认 black Z21 可设置主轨电压和编程轨电压，white z21 / z21start 不支持硬件调压或独立编程轨调压。
  - 手册确认维护工具使用 UDP 端口 `21105`、`21106` 和 `34472`。
  - `Z21_Maintenance.exe` RTTI/反汇编确认 `CFG_ReadMMDCCSettings` 使用 dataset header `0x0016`，`CFG_WriteMMDCCSettings` 使用 dataset header `0x0017`。
  - `TMMDCCSettings` RTTI 确认 payload 长度为 `16`，`OutputVoltage` 位于 offset `0x0c`，`ProgrammingVoltage` 位于 offset `0x0e`，二者均为 little-endian mV。
  - 实机只读响应 `14 00 16 00 19 06 07 01 05 14 88 13 10 27 32 80 80 3e 80 3e` 确认 `0x0016` payload 的电压字段为 `16000mV`。

## 本地实现来源

这些项目位于 `~/Documents/Code/Train`，用于交叉验证官方协议在真实开源实现中的用法。

### JMRI

路径：

- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/roco/z21/Z21Message.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/roco/z21/Z21Reply.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/roco/z21/Z21Constants.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/roco/z21/Z21XNetMessage.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/roco/z21/Z21XNetReply.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/roco/z21/Z21Adapter.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/roco/z21/z21AdapterConfigurationBundle.properties`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/roco/z21/Z21HeartBeat.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/roco/z21/Z21SystemConnectionMemo.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/roco/z21/Z21SensorManager.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/roco/z21/Z21ReporterManager.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/roco/z21/Z21CanReporter.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/roco/z21/Z21CanSensor.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/roco/z21/Z21PredefinedMeters.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/roco/z21/messageformatters/`

提取内容：

- 报文结构：2 字节长度、2 字节 opcode/header、payload，全部外层数值 little-endian。
- 默认 IP `192.168.0.111`，默认 UDP 端口 `21105`，另有 `21106` 配置项。
- `LAN_GET_SERIAL_NUMBER`、`LAN_GET_HWINFO`、`LAN_LOGOFF`、`LAN_GET/SET_BROADCAST_FLAGS`、`LAN_SYSTEMSTATE_GETDATA`。
- XPressNet 隧道、机车、道岔、CV、RailCom、R-Bus、LocoNet、CAN 和 booster 相关消息。

### Traintastic

路径：

- `~/Documents/Code/Train/Traintastic/server/src/hardware/interface/z21interface.cpp`
- `~/Documents/Code/Train/Traintastic/server/src/hardware/interface/z21interface.hpp`
- `~/Documents/Code/Train/Traintastic/server/src/hardware/protocol/z21/messages.hpp`
- `~/Documents/Code/Train/Traintastic/server/src/hardware/protocol/z21/messages.cpp`
- `~/Documents/Code/Train/Traintastic/server/src/hardware/protocol/z21/clientkernel.cpp`
- `~/Documents/Code/Train/Traintastic/server/src/hardware/protocol/z21/clientkernel.hpp`
- `~/Documents/Code/Train/Traintastic/server/src/hardware/protocol/z21/iohandler/udpclientiohandler.cpp`
- `~/Documents/Code/Train/Traintastic/server/src/hardware/protocol/z21/iohandler/udpiohandler.cpp`
- `~/Documents/Code/Train/Traintastic/manual/docs/en/advanced/interface/z21.md`
- `~/Documents/Code/Train/Traintastic/utils/wireshark/z21.lua`

提取内容：

- 网络连接只走 UDP，默认端口 `21105`。
- black/white/start 作为相同网络配置处理。
- 报文分帧、X-BUS checksum、header 枚举、broadcast flags、hardware type 枚举。
- 机车速度/方向、F0-F31、普通道岔地址减一、扩展附件地址、R-Bus、LocoNet、系统状态和 CAN detector。
- pending reply 匹配逻辑：不同命令的回复 header、XHeader、DB0、地址或速度字段不同。
