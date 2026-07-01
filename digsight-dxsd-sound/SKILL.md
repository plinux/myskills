---
name: digsight-dxsd-sound
description: 用于解析动芯 Digsight `.dxsd` DCC 音效工程文件，提取功能键到 Slot/声音/AUX 的映射、节点图逻辑、CV 表，并导出 16-bit PCM 音频。
metadata:
  version: "v0.1"
---

# 动芯 Digsight .dxsd 音效包解析

## 概述

`.dxsd` 是动芯/Digsight（中国模型火车 DCC 解码器厂商）的音效工程文件。**内部是单个大 XML**（UTF-8/CRLF），用**可视化节点图**描述「功能键按键 → 条件判断 → 声音播放 / AUX 灯光输出」的完整事件流。音频以 **Base64 内嵌（16-bit PCM @ 44100Hz）**，可离线解码。

与 ESU `.esux` 相反：动芯**音频裸存（易提取）**，配置是节点图（需关联反推）。

## 何时使用

- 收到 `.dxsd` 文件需要提取功能键/AUX/声音映射
- 需要导出音频为可播放 WAV
- 逆向动芯音效包节点图逻辑
- 修改/重打包 .dxsd（注意 XML 结构）

## 文件物理布局

XML 1.0，`standalone="yes"`，UTF-8，CRLF。根元素 `<NewDataSet>`。典型 5–16 MB。

```xml
<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<NewDataSet>
  <Base_Info>...</Base_Info>
  <Slot_Table>...</Slot_Table>
  <Node_Table>...</Node_Table>
  ... (各表重复)
</NewDataSet>
```

顶层元素行首缩进 2 空格（grep `^  <[A-Za-z_]` 可提取表名）。

## 9 张表

| 表 | 数量级 | 角色 |
|----|--------|------|
| `Base_Info` | 1 | 音效包/解码器元信息 |
| `Slot_Table` | 64 | 声音槽（场景容器，如「劈相机」「升弓」） |
| `Node_Table` | ~120 | 节点（图顶点：触发节点 + 声音播放节点） |
| `Connector_Table` | ~120 | 端口+边（节点连线逻辑） |
| `Connector_PathTable` | ~300 | 连线几何折线点（仅编辑器渲染用，可忽略） |
| `Judgment_Table` | ~160 | 条件判断（挂在边上） |
| `Action_Table` | 少量 | 动作（挂在边上，触发时执行） |
| `SoundFile_Table` | ~40 | 音频文件（Base64 内嵌） |
| `Random_CV_Table` | ~9000 | CV 默认值（DCC 配置变量 1–N） |

## 节点图模型（核心）

6 张表共同表达有向图。**关键：`(Slot_ID, Node_ID)` 是节点复合键**（Node_ID 在 slot 内唯一，全局不唯一；每个 slot 有 Node[0] 作触发入口）。

```
Slot_Table ─包含─▶ Node_Table ─经─▶ Connector_Table ─连─▶ Node_Table
                       │                  │
                       ▼         ┌────────┴────────┐
                 SoundFile_Table  Judgment_Table   Action_Table
                  (音频)         (触发条件)        (执行动作)
```

**连线语义**：`Connector` 的 `Node[Node_ID]` 第 `Node_Index_ID` 个端口 → `Node[OUT_Node_ID]`。`Judgment`/`Action` 通过 `Connector_ID` 挂在边上。

### 表字段

- **Slot_Table**：`Slot_ID`, `Slot_Priority`, `Slot_StartNode`, `Is_Use`, `Start_Address`(Flash地址), `Slot_Name`(中文场景名)
- **Node_Table**：`Node_ID`(slot内), `Slot_ID`, `Node_Type`, `File_ID`(音频), `Node_Config`, `Repeat_Amount`(0=无限循环), `Sound_Volume`(0-255), `Node_X/Y/W/H`(画布坐标,可忽略), `Node_Name`, `Start_Address`
- **Connector_Table**：`Connector_ID`, `Connector_Type`, `Node_ID`(源), `Node_Index_ID`(源端口), `Slot_ID`, `OUT_Node_ID`(目标), `Start_Address`
- **Judgment_Table**：`Judgment_ID`, `Connector_ID`, `Register_Type`, `Operation_Type`, `Parameter_Value`
- **Action_Table**：`Action_ID`, `Connector_ID`, `Register_Type`, `Operation_Config`, `Parameter_Value`
- **SoundFile_Table**：`File_ID`, `File_Name`, `File_Length`, `Start_Address`, `File_Data`(Base64音频), `File_Flag`

## 按键 / AUX / 声音映射（三层）

**① 按键→场景**（`CV171–234`「SlotN响应功能」，值=功能键号 0–28=F0–F28；0=未分配）：
```
F1→Slot1劈相机, F2→Slot4短风笛, F3→Slot5长风笛, F4→Slot6短电笛,
F5→Slot7长电笛, F6-F9→Slot22-25灯开关声, F10→Slot8空压机, F11→Slot9撒沙,
F12→Slot10缓解, F14→Slot12关门, F15→Slot13红黄灯, F16→Slot14白灯,
F17→Slot15注意前方限速, F18→Slot16注意限速, F19→Slot18升降弓, F20→Slot19广播...
```

**② AUX 输出**：
- `CV33–52`「AUX_x功能分配」：值 N(1-28)=AUX 由 FN 控制（如 CV35=6→AUX_1 由 F6 控制）。**特殊码** 127/126=AUX_FL/RL方向联动灯，117/208=厂商复合输出（需文档确认）
- `CV131–150`「输出效果」，`CV151–170`「输出最大亮度」，`CV261–300`「AND/OR逻辑」，`CV521+`「组1/2/3叠加配置」
- 标准：AUX_FL/RL = F0+方向位（前/后大灯）

**③ 声音链**：`SoundFile_Table.File_ID` → `Node_Table.File_ID` → `Slot_Table`。按键经 CV 进 Slot，沿节点图播放。

**Slot 音量**：`CV317–380`。**总音量**：`CV113`。

## Register / Operation 语义（推断）

Judgment/Action 操作的寄存器（基于上下文推断，缺厂商文档时标注）：

| Register | 含义 | 依据 |
|----------|------|------|
| 1 | 功能键状态（最常用） | 值 0/65535，Op 多 128 |
| 3 | 速度 | 值 20/45/50，op2(>)比较 |
| 8 | 方向/模式 | 值 0/65535 |
| 30/31 | AUX 输出（Action） | Action 赋值 65535/0 |
| 255 | 播放完成 | 用于声音→Node[0]出口 |

Operation_Type（比较）：`128`=等于/位测试(最常用), `0`=≥/始终, `2`=大于, `4/5`=< /≤。
Operation_Config（动作）：`128`=赋值, `0`=清零。

## 音频解码（16-bit PCM @ 44100Hz）★

`SoundFile_Table.File_Data` 是 **Base64**，解码后为 **16-bit little-endian signed PCM 裸流（单声道，无 WAV 头）**，采样率 **44100 Hz**（CD 音质，经试听确认）。

**判据**（区分编码/加密）：PCM 必有静音段（连续低幅样本）+ 值域用满 ±32768 + 熵 6–7。动芯数据**符合**（明文 PCM，非加密）。

**解码**（Base64 解码后字节即 WAV 帧数据，只需加头）：
```python
import base64, wave
raw = base64.b64decode(fileDataStr)        # Base64 解码
frames = raw[:len(raw)//2*2]               # 16-bit 对齐
with wave.open("out.wav","wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2) # 16-bit = sampwidth 2
    wf.setframerate(44100)                 # 试听确认的采样率
    wf.writeframes(frames)                 # 16-bit LE PCM 字节即 WAV 帧
```

> 与 ESU 相反：动芯音频是明文 16-bit PCM，**无需 key**，直接解码可播放。

## CV 表（Random_CV_Table）

`CV_Address` / `CV_Value` / `CV_Description`(中文)。覆盖 CV1–~9000（每 50 个一段完整预填）。关键 CV：
- CV1=主地址, CV3/4=加减速度, CV7=固件版本, CV8=厂家编号, CV29=配置寄存器
- CV33–52=AUX 分配, CV113=总音量, CV171–234=按键映射, CV317–380=Slot音量

## 完整解析脚本

`scripts/dxsd_parse.py`：流式解析 XML（defusedxml 防 XXE）→ 输出功能映射 + 按键链 + 批量解码音频。

```bash
python3 scripts/dxsd_parse.py file.dxsd [out_dir]
```

## 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| Node_ID 当全局主键 | Node_ID 在 slot 内唯一，全局重复 | 用 `(Slot_ID, Node_ID)` 复合键 |
| 当 WAV 处理 File_Data | 是 Base64，解码后是裸 PCM 无 RIFF 头 | Base64 解码 + 加 WAV 头 |
| 用错采样率 | 文件不存采样率 | 默认 44100，时长语义合理即对 |
| 忽略 Connector_PathTable | 是画布折线坐标 | 与逻辑无关，解析时跳过 |
| stdlib xml.etree 解析 | XXE/billion-laughs 风险 | 用 defusedxml |
| 大 XML 一次性载入 | 16MB 膨胀内存 | iterparse 流式 + clear |

## 与 ESU .esux 对比

| 维度 | 动芯 .dxsd | ESU .esux |
|------|-----------|-----------|
| 容器 | 单一大 XML | 二进制+命名文件表 |
| 音频 | Base64 16-bit PCM@44100（**可解码**） | AES-CBC 强加密（不可离线解） |
| 配置 | 节点图 XML（明文） | 压缩+加密 |
| 按键映射 | CV171–234 + 节点图三跳关联 | meta.xml 直接给描述 |

## 参考

- 经 `8004_HW2_SS7C_V37_KF.dxsd`（中国电力机车，劈相机/升降弓/风笛等）实战验证
- 复合键、采样率 44100、CV 映射均经 ground-truth 确认
- 关联 skill：`esu-loksound-esux`（ESU 同类文件）
