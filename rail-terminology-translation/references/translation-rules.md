# Translation Rules

## 基本原则

- 先判定专业域，再选词；不要只按字面翻译。
- 技术文件优先使用名词短语，少用解释性长句。
- 同一文档内同一中文术语只保留一个主译名；只有跨语境时才保留多个译法。
- 标准号、线路号、设备型号、车站名和专有名词通常不翻译，必要时括注英文。
- 对不确定术语给出置信度和核查建议，不要伪造标准来源。

## 常见歧义

| 中文 | 推荐处理 |
| --- | --- |
| 铁路 | 普通铁路/国铁语境用 `railway`；北美行业语境可见 `railroad`；技术标准优先 `railway`。 |
| 轨道交通 | 体系或行业用 `rail transit`；城市公共交通体系用 `urban rail transit`；泛指铁路应用可用 `rail transport`。 |
| 城市轨道交通 | 标准译法用 `urban rail transit`。 |
| 地铁 | 国际技术文本优先 `metro`；美国乘客语境可用 `subway`；英国地下系统可用 `underground`。 |
| 线路 | 工程线形用 `alignment`；运营线路用 `line`；径路/路径用 `route`；轨道实体用 `track`。 |
| 轨道 | 轨道结构用 `track`；钢轨本体用 `rail`；轨道区段可用 `track section`。 |
| 区间 | 两站间运行范围用 `interstation section` 或 `section`；闭塞语境用 `block section`。 |
| 区段 | 运营管理范围可用 `section`、`district` 或 `division`，按上下文选用。 |
| 限界 | 先判断类型：建筑限界 `structure gauge`，装载限界 `loading gauge`，车辆限界 `vehicle gauge`，动态包络 `kinematic envelope`。 |
| 运行图 | 计划图形或铁路行车组织用 `train diagram`；面向运营计划成果可用 `working timetable`。 |
| 列控 | 中国技术语境常用 `train control`；安全防护系统用 `train protection`；具体系统保留 CTCS/ETCS/CBTC。 |
| 牵引供电 | 电力系统语境用 `traction power supply`；设备系统可用 `traction power supply system`。 |

## 模型铁路/火车模型语境

- 先确认文档是否为模型铁路设备、DCC 数码控制、机车解码器、数字指挥站、轨道供电或布局控制文档；此时不能直接套用真实铁路工程词汇。
- `gauge` 在模型铁路语境中优先按模型比例/规格处理：`N gauge` 译为 `N 比例`，`H0 gauge` 译为 `H0 比例`，`G gauge` 译为 `G 比例`，`1 gauge` 译为 `1 号比例`。不要译为 `N 规`、`G 规`、`1 号规`。
- `two-conductor track`、`two-rail track` 译为 `二轨轨道` 或 `二轨系统`；章节标题 `Wiring two-conductor tracks` 译为 `二轨轨道接线`。
- `three-conductor track`、`three-rail track` 译为 `三轨轨道` 或 `三轨系统`；章节标题 `Wiring three-conductor tracks` 译为 `三轨轨道接线`。不要按字面译成 `三导体轨道接线`。
- `Main track`、`Main-Track` 在数字指挥站接线端子和编程语境中译为 `主轨道`；`Prog-Track`、`programming track` 译为 `编程轨道`。
- `Programming on the Main`、`Programming On the Main`、`POM` 译为 `主轨编程 (POM)`，不要译为 `主控上编程` 或 `主轨节目`。
- 模型铁路文档中的 `layout` 通常译为 `模型铁路布局`，`turnout` 译为 `道岔`，`accessory` 译为 `配件`，`route` 译为 `进路`，`booster` 保留 `Booster`。

## 输出格式

批量术语翻译默认使用：

| 中文术语 | 推荐英文 | 可选译法 | 适用语境 | 说明/来源 |
| --- | --- | --- | --- | --- |

术语审校默认使用：

| 原译文 | 建议译文 | 问题类型 | 理由 |
| --- | --- | --- | --- |

## 质量检查

- 检查 `rail`/`track`、`line`/`route`/`alignment`、`gauge`/`clearance` 是否按语境选择。
- 检查缩写第一次出现是否展开。
- 检查同一术语是否前后译名一致。
- 检查是否把非标准参考材料写成“官方标准译法”。
- 检查中文工程术语是否因英文地区差异导致误解，并在必要时标注 UK/US/International。
