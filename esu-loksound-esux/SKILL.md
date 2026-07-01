---
name: esu-loksound-esux
description: 用于解析 ESU LokSound `.esux` 音效工程文件，提取 meta.xml 功能/AUX 映射、列出声音文件表，并判断音频加密状态；不承诺离线解码 ESU 音频。
metadata:
  version: "v0.1"
---

# ESU LokSound .esux 音效包解析

## 概述

`.esux` 是 ESU LokProgrammer 5 的音效工程文件（LokSound V4/V5 解码器）。**不是 ZIP**，是 ESU 私有二进制容器：魔数 `"ESU "` + 块结构 + 命名文件表。功能映射存在**未压缩的 meta.xml**（直接可读），音频载荷呈强加密随机特征，纯静态离线不可还原为 WAV。

## 何时使用

- 收到 `.esux` 文件需要提取功能键/AUX/灯光映射
- 需要列出声音槽(slot)及其音频文件
- 需要列出音频条目、导出加密载荷或判断音频是否可离线解码
- 逆向 ESU LokSound 项目结构

## 文件物理布局

```
偏移 0:  [魔数 "ESU "(4B)][版本头(8B)]
         之后是 [u16 type][u32 len][data] 块序列：
  type=16 : meta.xml          ← 未压缩明文 XML（功能描述，金矿）
  type=17 : BMP 机车图片       ← 未压缩 BMP
  type=34 : 数据块             ← 私有
  之后    : 命名文件表          ← 每个文件为私有编码、压缩或加密载荷
```

## 命名文件表条目格式（已破解）

每个条目（从 name 前 8 字节起）：

```
[u32 A][u32 B=nameLen+16][文件名(nameLen字节)][u32 fileId][12字节0][u16 flag][u32 size][u32 nextId][12字节0][数据区]
```

**关键字段**：
- `B`（name 前 4 字节）= **nameLen + 16** —— 用此校验条目边界
- `size`（name 后第 18 字节处的 u32）= **下一个文件的数据区大小**（错位！见下）
- 数据区从 name 后第 38 字节开始

### ★ 数据区错位规则（最重要）

**wav fileId=N 的音频数据，物理上在 fileId=N-1 条目的数据区里**（错位一个）。

即：遍历按 offset 排序的条目，条目 `i` 的数据区 `[nameEnd_i+38 : nameStart_{i+1}-8]` 装的是**文件 i+1** 的内容。

验证：hs1 条目 size 字段=8532 ≈ hs2 显示大小 8491；s-loop 条目 size=100852 ≈ hs-aus-panto 显示 100807。

## 功能键 / AUX 映射（从未压缩的 meta.xml）

meta.xml 是 type=16 块，长度在文件头偏移 14（u32 LE），数据从偏移 18 起，**明文 XML**。含 `<function id="N">` 元素，每个有德语/英语 `<description>`：

```xml
<function id="0" user="true">
  <description xml:lang="de">Licht vorne</description>
  <description xml:lang="en">headlight front</description>
</function>
```

**AUX 物理输出**（LokSound V4：FL/RL + AUX1–6）：
- `AUX_FL`/`AUX_RL` = F0 + 方向位（前进/后退灯，LokSound 标准）
- 功能描述里直接写 `AUX1`/`AUX2`… 的，即该功能键驱动对应 AUX（如 F8→AUX1）
- 其余 AUX2–6 绑定在压缩的 `ls4_project.xml` 里（离线难读）

## 音频：ESU 强加密（离线不可解码）

每个 `.wav` 数据区经**重合指数(IC)分析为完美随机（IC=1/256=0.0039）**，是**强加密**，非编码/压缩。

**已排除的所有方案**（均经实测）：
- PCM/μ-law/A-law：8-bit 音频熵上限 7.5，但数据熵 8.0；IC 无幅度集中
- IMA ADPCM 4-bit@31250：解码无真实静音段
- XOR 循环 key：IC 分析 keylen 1–16 无峰
- zlib/lzma/bz2/lz4/zstd：全部解压失败

**★ 关键教训：警惕解码随机数据的假信号**
- "A-law 解码熵降到 6.0" 是 A-law 非线性映射对均匀输入的数学特性，**非真信号**
- "IMA ADPCM 出现静音段" 是随机 nibble 经步长表产生的慢变假象
- **真判据只有 IC**：>0.005 有结构（可解码），=0.0039 完美随机（强加密）。先用 IC 再谈解码。

**采样率信息**（软件显示，用于容量估算）：15625 B/s，4096KB≈268s，等长存储（不压缩）→ 印证是加密（保长）而非压缩。

**KPA 实测验证**（导入已知静音/正弦 wav 对比密文）：
- 两个**内容完全相同**的静音 wav（仅采样率不同）→ 密文 **99.6% 不同** → 每次加密用**随机 IV/nonce**
- silence 密文 XOR sine 密文 = 随机（非正弦 PCM）→ 非 XOR/流密码（或 nonce 各异）
- 即便已知明文，因随机 IV，**无法还原密钥或解密其他文件**

**结论**：ESU 用强加密（AES-CBC + 随机 IV）保护音效 IP，**纯静态离线无法还原 WAV**（KPA 亦无效）。需 ESU LokProgrammer（含密钥）播放/导出，或动态逆向。**容器结构、功能映射(meta.xml)、AUX 可离线提取。**

## 逆向 LokProgrammer 找音频 key（进展与障碍）

LokProgrammer.exe 是 **.NET 程序集**（`Mono/.Net assembly`），可用 dnfile/monodis/ilspycmd 逆向。已定位：

- **加密算法 = AES-CBC**：用 .NET `System.Security.Cryptography.AesManaged`，`Mode=CBC`（确认，非猜测）
- **配置解密类**（类名被混淆为零宽字符，解密 ls4_project.xml 等 XML 字符串）：
  - `.ctor(byte[] key)`：构造时存 key，配 AesManaged（Key/KeySize/BlockSize/Mode=CBC/Padding）
  - 解密方法 `instance byte[] '(string)`：输入 string→byte[]，**IV = 前 16 字节**，密文 = 其余，`CreateDecryptor(key, IV)` → CryptoStream 解密
  - static 入口 `byte[] '(byte[] key, string data)`
- **key 来源**：AES 类的 key 是某类的**静态 `uint8[]` 字段**，用 `RuntimeHelpers.InitializeArray` 从 PE **FieldRva** 初始化（`ldsfld uint8[]` 加载）

**障碍（静态逆向到此卡住）**：
1. 该 AES 类**只解密 string（XML 配置）**，**无 byte[] 音频解密方法** → 音频 byte[] 走另一条未定位的加密路径
2. 用 dnfile 读出 23 个 FieldRva、41 个候选 key（16/32 字节）测试 AES-CBC 解密 .esux 音频（IV=前16字节）→ **全部失败**（输出 IC=0.0039 随机，非 PCM）。这些 FieldRva 是字符串混淆表/查找表，非音频 key
3. LokProgrammer 用**商业级混淆**（疑似 ConfuserEx）：类名/方法名/字段名→零宽字符、字符串运行时解密（`ldc.i4 <idx>; call 解密(int32)`）、控制流打乱（switch+xor 反篡改）

**IC 判据提醒**（避免误判）：随机=0.0039±0.0005，PCM 必 >0.01。曾因阈值 <0.005 误把 0.0039 当"有结构"。

**下一步（动态分析，最有效）**：用 **dnSpy/dnSpyEx**（免费 .NET 调试器）：
1. 打开 LokProgrammer.exe → 调试→开始执行
2. 在 `System.Security.Cryptography.AesManaged.CreateDecryptor` 或 `SymmetricAlgorithm.set_Key` 设断点
3. LokProgrammer 里打开 .esux
4. 断点命中时查看 **Key/IV 实际字节**（混淆挡不住运行时值）+ 调用栈定位音频解密类
5. 拿到 key 后用 PyCryptodome `AES.new(key, MODE_CBC, iv).decrypt(ct[16:])` 解全部音频

## 工具命令

```bash
# 解析容器 + 功能映射 + 导出加密音频载荷
python3 scripts/esu_parse.py file.esux [out_dir]
# dnfile 读 .NET 元数据
python3 -c "import dnfile; pe=dnfile.dnPE('LokProgrammer.exe'); ..."
# monodis 反汇编（大 exe 可能 segfault，部分输出可用）
monodis LokProgrammer.exe | grep -A8 'CreateDecryptor'
```

## 完整解析脚本

可运行的整合脚本在 `scripts/esu_parse.py`：解析容器 → 提取 meta.xml 功能表 → 列出文件表 → 导出 `.wav` 条目的加密载荷和随机性指标。它不会把 ESU 音频伪解码成可播放 WAV。

```bash
/opt/homebrew/bin/python3 scripts/esu_parse.py file.esux [out_dir]
```

## 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| 当 ZIP 解压失败 | `.esux` 是私有容器非 ZIP | 按块结构解析 |
| 条目解析漏文件 | 德语名含变音符(äöü=UTF-8 0xC3..)打断 ASCII 正则 | 用 `[\x20-\xff]` 正则 + `B=nameLen+16` 校验 |
| 提取的 wav 是噪声 | ESU 音频载荷强加密，不能当 PCM/A-law 解码 | 只导出 encrypted payload；需要 LokProgrammer 或动态逆向 key |
| A-law/μ-law 似乎有波形 | 随机数据经非线性表会产生假信号 | 先看 IC；接近 0.0039 即随机密文 |
| size 字段当本文件大小 | size 实际是**下个**文件大小 | 用物理边界 `[nameEnd_{i-1}+38 : nameStart_i-8]` |
| 把 ls4_project.xml 当明文读 | 配置 XML 被压缩，只有 meta.xml 未压缩 | AUX/功能只从 meta.xml 读 |

## 与动芯 .dxsd 对比

| 维度 | ESU .esux | 动芯 .dxsd |
|------|-----------|-----------|
| 容器 | 二进制+命名文件表 | 单一大 XML |
| 音频 | 强加密载荷（离线不可解码） | 16-bit PCM@44100（明文） |
| 配置 | 压缩 | 节点图明文 |
| 功能描述 | meta.xml 未压缩双語 | 需三跳关联反推 |

## 参考

- 容器魔数 `"ESU "` + 块 type=16/17/34 + 文件表 B=nameLen+16 字段经逆向确认
- 音频部分受 ESU 商业保护；本 skill 只做容器解析、功能映射提取和加密状态判断
