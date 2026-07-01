# DCC Protocol Family Coverage

最后核对日期：2026-06-20。用本文件定位 DCC 协议族的官方标准和对应内容文件。

## NMRA

| 文档 | 内容 | 查看 |
| --- | --- | --- |
| S-9 Electrical | 两轨/三轨基本电气安全和互换边界 | `interfaces-power-susi.md` |
| S-9.1 | DCC 轨道电气、bit timing、幅值、RailCom cutout 供电影响 | `electrical-bit-packet.md` |
| S-9.1.1 | Decoder interface 总则 | `interfaces-power-susi.md` |
| S-9.1.1.1 | Six and eight pin decoder interface | `interfaces-power-susi.md` |
| S-9.1.1.2 | JST-9 decoder interface | `interfaces-power-susi.md` |
| S-9.1.1.3 | 21MTC decoder interface | `interfaces-power-susi.md` |
| S-9.1.1.4 | PluX decoder interface | `interfaces-power-susi.md` |
| S-9.1.1.5 | Next18 / Next18-S decoder interface | `interfaces-power-susi.md` |
| S-9.1.2 / TN-9.1.2 | Command Station 到 Power Station Interface | `interfaces-power-susi.md` |
| S-9.1.3 draft | Decoder power modes | `interfaces-power-susi.md` |
| S-9.2 | DCC baseline packet | `electrical-bit-packet.md` |
| S-9.2.1 | mobile/accessory/CV access extended packet | `mobile-accessory-commands.md`, `cv-programming.md` |
| S-9.2.1.1 / TN-9.2.1.1 | address partition 253/254, CRC-8, DCC-A/data spaces | `railcom-failsafe-advanced.md` |
| S-9.2.2 | CV 表 | `cv-programming.md` |
| S-9.2.2 Appendix A | Manufacturer ID registry | `cv-programming.md`, `source-map.md` |
| S-9.2.3 | service mode programming | `cv-programming.md`, `programming-environment-function-mapping.md` |
| S-9.2.4 | fail-safe | `railcom-failsafe-advanced.md` |
| S-9.3.2 | basic decoder transmission / RailCom | `railcom-failsafe-advanced.md`, `railcom-coding-tables.md` |
| TI-9.2.3 | SUSI | `interfaces-power-susi.md` |
| S-9.4.1 draft | SUSI Bus Communication Interface | `interfaces-power-susi.md` |
| S-9.4.2 draft | SUSI Bus Configuration Variables | `interfaces-power-susi.md` |
| S-9.4.3 draft | SUSI Bus Bidirectional Extension | `interfaces-power-susi.md` |
| S-9.4.4 draft | SUSI Train Bus Extension Shift Register | `interfaces-power-susi.md` |

## RailCommunity / MOROP

| 文档 | 内容 | 查看 |
| --- | --- | --- |
| RCN-200 | multiprotocol decoder/central coexistence | `interfaces-power-susi.md` |
| RCN-210 | DCC bit representation | `electrical-bit-packet.md` |
| RCN-211 | DCC packet, address, global commands | `electrical-bit-packet.md` |
| RCN-212 | vehicle operating commands | `mobile-accessory-commands.md` |
| RCN-213 | accessory operating commands | `mobile-accessory-commands.md` |
| RCN-214 | DCC configuration commands | `cv-programming.md` |
| RCN-216 | programming track environment | `programming-environment-function-mapping.md` |
| RCN-217 | RailCom feedback | `railcom-failsafe-advanced.md`, `railcom-coding-tables.md` |
| RCN-218 | DCC-A automatic logon | `railcom-failsafe-advanced.md` |
| RCN-225 | DCC CVs | `cv-programming.md` |
| RCN-226 | special CV values | `programming-environment-function-mapping.md` |
| RCN-227 | extended function mapping | `programming-environment-function-mapping.md` |
| RCN-600 | SUSI bus module expansion interface | `interfaces-power-susi.md` |
| RCN-601 | SUSI bidirectional extension | `interfaces-power-susi.md` |
| RCN-602 | SUSI CVs | `interfaces-power-susi.md` |
| RCN-620 | Train Bus shift register extension | `interfaces-power-susi.md` |
| NEM 608 | user-facing function assignment | `programming-environment-function-mapping.md` |
| NEM 670 | DCC bit representation | `electrical-bit-packet.md` |
| NEM 671 | DCC baseline packet | `electrical-bit-packet.md` |
| NEM 672 | advanced accessory signal control | `programming-environment-function-mapping.md` |
