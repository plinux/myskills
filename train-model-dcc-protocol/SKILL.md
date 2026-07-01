---
name: train-model-dcc-protocol
description: 用于解析、实现、审查和调试模型铁路 DCC 数码控制协议族，包括轨道波形、packet、车辆/附件命令、CV/编程、RailCom、DCC-A、Power Station Interface、decoder interface、SUSI/Train Bus 和标准来源核对。
metadata:
  version: "v0.1"
---

# Train Model DCC Protocol

用于处理模型铁路 Digital Command Control（DCC）协议族相关任务。

## 使用流程

1. 先判定任务范围：标准覆盖矩阵、轨道电气波形、DCC 数据包、机车/附件命令、CV/编程、编程轨环境、函数映射、信号附件、RailCom、DCC-A、Fail-Safe、Power Station Interface、decoder interface、SUSI/Train Bus。
2. 需要给出标准结论、实现兼容性或“最新规范”时，先核对官方来源；优先使用 NMRA 已批准标准，再按任务需要查看 RailCommunity RCN、MOROP NEM 或 NMRA draft。
3. 按任务读取对应 Markdown reference：
   - 官方入口、标准清单、内容索引：`references/source-map.md`。
   - DCC 协议族标准覆盖矩阵：`references/dcc-family-coverage.md`。
   - 轨道电气、bit 编码、通用 packet、地址分区、全局命令：`references/electrical-bit-packet.md`。
   - 车辆命令、附件命令、速度/函数/二进制状态/道岔与信号：`references/mobile-accessory-commands.md`。
   - CV 表、CV 编程、POM/XPOM、service/register mode：`references/cv-programming.md`。
   - 编程轨环境、CV7/CV8 特殊值、扩展函数映射、NEM 672 信号附件：`references/programming-environment-function-mapping.md`。
   - RailCom、Fail-Safe、S-9.2.1.1 高级扩展包、测试矩阵：`references/railcom-failsafe-advanced.md`。
   - RailCom 4-out-of-8 码表、ACK/NACK、datagram 编码细节：`references/railcom-coding-tables.md`。
   - Power Station Interface、decoder connector/interface、SUSI/Train Bus：`references/interfaces-power-susi.md`。
4. 生成代码、测试向量或协议解释时，保留原始 bit/byte 表达、十六进制值和字段含义；不要只给自然语言解释。
5. 明确区分“已批准标准”“草案/征求意见”“RCN/NEM 协调规范”“实现约定或推断”。

## 输出要求

- 默认用中文输出。
- 引用标准时写出发布组织、文档编号、标题和版本/日期。
- 实现建议必须附带测试点：有效包、无效包、边界地址、XOR 校验、reset/idle、安全状态和不支持命令的忽略行为。
- 涉及真实轨道供电、编程轨或硬件测试时，先提示隔离、限流和误动作风险，不要默认直接运行。

## 关键约束

- DCC 轨道信号、Power Station Interface、RailCom、SUSI/Train Bus 是不同协议层；不要混用。
- 不要把草案当作已批准标准；若用户要求“最新”，可以同时说明已批准版本和正在修订的 draft。
- 不要推断厂家专用 CV、私有扩展或总线协议为 NMRA 标准，除非标准明确给出。
- Manufacturer ID、DCC-A image/icon number 等滚动注册表只记录查询方法；需要具体编号时打开官方最新表。

## 协议参考

各类 DCC 内容见 `references/` 下的 Markdown。
