# RailCom Coding Tables

来源：RCN-217 RailCom。与 `railcom-failsafe-advanced.md` 一起使用。

## 4-out-of-8 coding

RailCom 每个传输 byte 使用 4-out-of-8 code；每个 code byte 必须正好有 4 个 `1` 和 4 个 `0`。64 个 code 映射 6-bit payload `0x00..0x3F`，额外 code 用作 ACK/NACK/reserved。

| Value | Code | Value | Code | Value | Code | Value | Code |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `0x00` | `10101100` | `0x10` | `10110010` | `0x20` | `01010110` | `0x30` | `11000110` |
| `0x01` | `10101010` | `0x11` | `10110100` | `0x21` | `01001110` | `0x31` | `11001100` |
| `0x02` | `10101001` | `0x12` | `10111000` | `0x22` | `01001101` | `0x32` | `01111000` |
| `0x03` | `10100101` | `0x13` | `01110100` | `0x23` | `01001011` | `0x33` | `00010111` |
| `0x04` | `10100011` | `0x14` | `01110010` | `0x24` | `01000111` | `0x34` | `00011011` |
| `0x05` | `10100110` | `0x15` | `01101100` | `0x25` | `01110001` | `0x35` | `00011101` |
| `0x06` | `10011100` | `0x16` | `01101010` | `0x26` | `11101000` | `0x36` | `00011110` |
| `0x07` | `10011010` | `0x17` | `01101001` | `0x27` | `11100100` | `0x37` | `00101110` |
| `0x08` | `10011001` | `0x18` | `01100101` | `0x28` | `11100010` | `0x38` | `00110110` |
| `0x09` | `10010101` | `0x19` | `01100011` | `0x29` | `11010001` | `0x39` | `00111010` |
| `0x0A` | `10010011` | `0x1A` | `01100110` | `0x2A` | `11001001` | `0x3A` | `00100111` |
| `0x0B` | `10010110` | `0x1B` | `01011100` | `0x2B` | `11000101` | `0x3B` | `00101011` |
| `0x0C` | `10001110` | `0x1C` | `01011010` | `0x2C` | `11011000` | `0x3C` | `00101101` |
| `0x0D` | `10001101` | `0x1D` | `01011001` | `0x2D` | `11010100` | `0x3D` | `00110101` |
| `0x0E` | `10001011` | `0x1E` | `01010101` | `0x2E` | `11010010` | `0x3E` | `00111001` |
| `0x0F` | `10110001` | `0x1F` | `01010011` | `0x2F` | `11001010` | `0x3F` | `00110011` |

## Special code words

| Meaning | Code | Rule |
| --- | --- | --- |
| ACK | `00001111` | Command understood and will be executed / YES. |
| ACK | `11110000` | Same ACK meaning; either ACK code is valid. |
| Reserved | `11100001` | Do not emit; ignore or treat as reserved. |
| Reserved | `11000011` | Do not emit; ignore or treat as reserved. |
| Reserved | `10000111` | Do not emit; ignore or treat as reserved. |
| NACK | `00111100` | Optional; command or CV unsupported. |

NACK notes:

- NACK may indicate unsupported command or unsupported/nonexistent CV.
- For POM nonexistent CV, do not send NACK as the first response; send ACK first, then NACK, preferably in the same Channel 2 window.
- ACK/NACK is not allowed in Channel 1.

## Datagram packing

- Channel 1 can carry 2 encoded bytes = 12 payload bits.
- Channel 2 can carry 6 encoded bytes = 36 payload bits.
- Payload datagrams normally start with 4-bit ID followed by data bits.
- Datagram sizes:
  - 12 bit: `ID[3:0] D[7:6] D[5:0]`.
  - 18 bit: `ID[3:0] D[13:12] D[11:6] D[5:0]`.
  - 24 bit: `ID[3:0] D[19:18] D[17:12] D[11:6] D[5:0]`.
  - 36 bit: `ID[3:0] D[31:30] D[29:24] D[23:18] D[17:12] D[11:6] D[5:0]`.
- Channel 2 may concatenate datagrams up to 36 bits.
- ACK/NACK at the start of a Channel 2 response is a special message, not a datagram. If a response starts with ACK/NACK, normal datagrams should not follow; subsequent ACK/NACK codes still need evaluation.
- Optional padding can fill Channel 2 with ACK bytes to 36 bits.

## Required decoder support

- All RailCom decoders: ACK.
- Mobile decoders: Channel 1 `app:adr_high`, Channel 1 `app:adr_low`, Channel 2 `app:pom`.
- Accessory decoders: Channel 2 `app:stat1`, Channel 2 `app:fehler`.
- Addressed decoder should send Channel 2 feedback, at least ACK, to confirm error-free DCC packet reception; this does not prove the command was accepted or executed.
