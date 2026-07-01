# 来源映射

## 官方来源

- ESU Digital Systems instruction manuals: `https://www.esu.eu/en/downloads/instruction-manuals/digital-systems/`
  - 同一下载区列出 ECoS 50200、ECoS 50210、ECoS 50220 相关手册和 PC Interface Specification。
- ESU ECoS PC Interface specification: `https://www.esu.eu/uploads/tx_esudownloads/ECoS_PC-Schnittstellenbeschreibung_ESUKG_DE_Auflage_I.pdf`
  - 确认 PC 到 ECoS 使用 TCP/IP 文本命令。
  - 确认命令形态、`get`/`set` 示例、`<REPLY>` 块、`<END code(message)>` 结束行、状态查询和编程轨示例。
  - 说明从计算机视角 ECoS 与 Central Station 兼容协议没有本质差异。
- ESU ECoS2 English user manual: `https://www.esu.eu/uploads/tx_esudownloads/01211-10059_ECoS_2_Handbuch_ESUKG_EN_User_manual_Edition_II_March_2011_eBook.pdf`
  - 确认 ECoS 提供 PC 通信协议，支持机车、附件、编程和模型数据库管理。
- ESU ECoS product/update pages:
  - `https://www.esu.eu/en/products/digital-control/ecos-50210-dcc-system/what-ecos-can-do/`
  - `https://www.esu.eu/en/support/warranty-repair/reparaturen/servicepauschalen/software-updates/`
  - 用于核对 ECoS2/50220 和 50200/50210 的产品、固件更新信息。

## 本地实现来源

这些项目位于 `~/Documents/Code/Train`，用于交叉验证官方协议在真实开源实现中的用法。

### ECoS C# library

路径：

- `~/Documents/Code/Train/ECoS/ECoSConnector/TcpClient.cs`
- `~/Documents/Code/Train/ECoS/ECoSUtils/CommandFactory.cs`
- `~/Documents/Code/Train/ECoS/ECoSUtils/Command.cs`
- `~/Documents/Code/Train/ECoS/ECoSUtils/Replies/ECoSReply.cs`
- `~/Documents/Code/Train/ECoS/ECoSEntities/Locomotive.cs`
- `~/Documents/Code/Train/ECoS/ECoSEntities/Accessory.cs`
- `~/Documents/Code/Train/ECoS/ECoSEntities/DataProvider.cs`

提取内容：

- TCP 连接、按行收发、命令构造、`<REPLY>`/`<EVENT>` 解析。
- `get(1, info/status)`、`ProtocolVersion`、`ApplicationVersion`、`HardwareVersion` 的旧式信息读取。
- 机车和附件对象的 `request`、`set`、`queryObjects`、`create`、`delete` 用法。
- 项目元数据写明支持 ESU ECoS `50200/50210` 通讯协议，但代码没有硬件型号分支。

### JMRI

路径：

- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/ecos/EcosMessage.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/ecos/EcosReply.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/ecos/EcosTrafficController.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/ecos/networkdriver/NetworkDriverAdapter.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/ecos/EcosDccThrottle.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/ecos/EcosTurnout.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/ecos/EcosSensorManager.java`
- `~/Documents/Code/Train/JMRI/java/src/jmri/jmrix/ecos/EcosProgrammer.java`

提取内容：

- 默认网络端口 `15471`。
- 机车 throttle、道岔、传感器、RailCom reporter 和编程轨流程。
- `request(..., control)`、`force`、控制权错误、创建等待状态等实践行为。
- 未见按 `50200`、`50210`、`50220` 的协议分支。

### Traintastic

路径：

- `~/Documents/Code/Train/Traintastic/server/src/hardware/protocol/ecos/ecosmessages.hpp`
- `~/Documents/Code/Train/Traintastic/server/src/hardware/protocol/ecos/ecosmessages.cpp`
- `~/Documents/Code/Train/Traintastic/server/src/hardware/protocol/ecos/iohandler/ecostcpiohandler.cpp`
- `~/Documents/Code/Train/Traintastic/server/src/hardware/protocol/ecos/object/ecos.cpp`
- `~/Documents/Code/Train/Traintastic/server/src/hardware/protocol/ecos/object/ecoslocomotive.cpp`
- `~/Documents/Code/Train/Traintastic/server/src/hardware/protocol/ecos/object/ecosswitch.cpp`
- `~/Documents/Code/Train/Traintastic/server/src/hardware/protocol/ecos/object/ecosfeedback.cpp`
- `~/Documents/Code/Train/Traintastic/manual/docs/en/advanced/interface/ecos.md`

提取内容：

- 默认端口 `15471`、命令换行、`<REPLY>`/`<EVENT>`/`<END>` 块解析。
- 对象 ID、常见选项、状态码、ECoSDetector、RailCom、机车、附件和基础对象发现流程。
- `get(1, commandstationtype, protocolversion, hardwareversion, applicationversion, applicationversionsuffix, railcom, railcomplus)` 能力探测。
- 未见按硬件型号的协议分支。
