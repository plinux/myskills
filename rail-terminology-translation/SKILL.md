---
name: rail-terminology-translation
description: 用于轨道交通、铁路、城市轨道交通和模型铁路/火车模型专业词汇的中英互译、术语统一和译文审校；在翻译线路、轨道、车辆、牵引供电、信号通信、运营安全、DCC 数码控制和模型铁路设备文档或术语表时使用。
metadata:
  version: "v0.1"
---

# Rail Terminology Translation

用于轨道交通和模型铁路专业词汇的中英互译、术语表整理和译文一致性审校。

## 使用流程

1. 先判断语境：铁路工程、城市轨道交通、车辆、牵引供电、信号通信、运营客运、安全合规、国际互操作，或模型铁路/火车模型。
2. 需要权威来源或最新标准时，先读 `references/source-map.md`，确认采用国内标准、国际术语库或行业资料。
3. 先读 `references/translation-rules.md`，再按语境读取对应术语表：
   - 线路、轨道、土建、车站和工程：`references/glossary-core-infrastructure.md`。
   - 车辆、制动、轮轨、牵引供电和接触网：`references/glossary-rolling-stock-power.md`。
   - 信号、通信、列控、联锁和检测：`references/glossary-signalling-communication.md`。
   - 运营、客运、票务、安全和环境：`references/glossary-operations-safety.md`。
   - 模型铁路、DCC 数码控制、数字指挥站、解码器和模型比例：`references/glossary-model-railway.md`。
4. 若同一中文术语有多个译法，按用户文档领域、目标读者和标准来源选择首选译法，并保留必要备选。
5. 若术语表没有命中，先用来源索引中的权威材料核对；仍无法确认时，给出建议译法、适用范围和不确定点。

## 输出要求

- 默认用中文说明；术语本身保留中英双语。
- 批量翻译时用表格输出：`中文术语`、`推荐英文`、`可选译法`、`适用语境`、`说明/来源`。
- 审校译文时只改术语、搭配和一致性问题；不要重写与术语无关的句子。
- 对标准、规范或合同文本，优先采用已发布标准中的英文名称；不要把口语化译法写成官方术语。
- 对首次出现的缩写写出全称，例如 `CBTC (Communications-Based Train Control)`。

## 关键约束

- `rail` 通常是钢轨，`track` 通常是轨道结构或线路上的轨道；不要混用。
- `line`、`route`、`alignment`、`track` 按语境区分，不要把中文“线路”固定译成一个词。
- `gauge` 在真实铁路工程中可能是轨距或限界；在模型铁路产品文档中通常指模型比例/规格，按 `N 比例`、`H0 比例`、`G 比例`、`1 号比例` 等处理，不译作 `N 规`、`G 规`。
- `metro`、`subway`、`underground railway` 受地区和文体影响；国际技术文本优先用 `metro`，美国语境可用 `subway`。
- `urban rail transit` 指城市轨道交通体系，不等同于单一地铁线路。
- 不要把厂家用语、项目内部缩写或地区口径伪装成国家标准或国际标准。

## 术语参考

详细来源、翻译规则和术语表见 `references/` 下的 Markdown 文件。
