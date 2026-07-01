# ECoS 硬件兼容性

## 结论

`50200`、`50210`、`50220` 不应被当作三套不同 PC Interface 协议处理。默认按同一 ECoS PC Interface 协议族实现，再通过控制器返回的能力字段、协议版本、固件版本和实际错误码做降级。

## 型号判断

| 型号 | 判断方式 |
| --- | --- |
| `50200` | 老款 ECoS 控制器；官方下载区仍与 ECoS 文档和 PC Interface 文档一起列出。 |
| `50210` | ECoS2/ECoS DCC system 相关型号；本地 C# ECoS 库把 `50200/50210` 写在同一协议支持范围。 |
| `50220` | 新一代 ECoS 控制器；官方下载区有手册和固件补充说明，但未体现为独立 PC Interface 协议。 |

本地 JMRI、Traintastic 和 C# ECoS 实现均没有按 `50200`、`50210`、`50220` 写协议分支，而是按对象、字段和返回码工作。

## 连接后必须探测

优先发送：

```text
request(1, view)
get(1, commandstationtype, protocolversion, hardwareversion, applicationversion, applicationversionsuffix, railcom, railcomplus)
```

兼容旧固件时可退回：

```text
get(1, info)
get(1, status)
```

记录字段：

| 字段 | 使用原则 |
| --- | --- |
| `commandstationtype` | 用于展示控制器类型，不单独驱动协议分支。 |
| `protocolversion` | 兼容判断的首要字段。 |
| `hardwareversion` | 用于记录硬件，不单独判断功能存在。 |
| `applicationversion` | 用于判断固件能力和问题复现条件。 |
| `applicationversionsuffix` | 记录固件后缀，缺失时保持为空。 |
| `railcom` | 判断 RailCom 相关字段是否可用。 |
| `railcomplus` | 判断 RailComPlus 相关字段是否可用。 |

## 分支规则

可以分支：

- 控制器返回 `UnknownOption`，说明该字段在当前固件不可用。
- 控制器返回 `UnknownObject`，说明对象不存在或模块未配置。
- `protocolversion` 明确低于实现所需能力。
- `applicationversion` 已知存在固件缺陷，需要兼容规避。
- 实际对象字段缺失，例如反馈模块没有 `railcom` 字段。

不要分支：

- 仅因为用户说控制器是 `50200`、`50210` 或 `50220`。
- 仅因为 `hardwareversion` 数值不同。
- 仅因为官方手册或补充说明版本不同。

## 兼容实现建议

- 启动阶段把控制器能力写入日志，便于后续问题定位。
- 把字段读取做成可选能力探测，不要让一个未知字段导致初始化失败。
- 对 `railcom`、`railcomplus`、ECoSDetector、路线/转盘等扩展能力使用懒加载。
- 保留未知字段原文，便于支持新固件或第三方扩展。
- 命令失败时输出原始命令、完整回复块和 `<END>` 状态码。

## 真实设备安全

- `set(1, go)` 会上电，`set(1, stop)` 会停车或断轨道电。
- 机车 `speed`、`speedstep`、`dir`、`func` 会立即影响车辆。
- 附件 `state` 或管理器 `switch[...]` 会立即动作。
- `writedccdirect` 会写入解码器 CV。

除非用户明确要求执行，分析和测试代码应默认只读。
