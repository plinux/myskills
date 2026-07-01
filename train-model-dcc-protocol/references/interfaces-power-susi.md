# Interfaces, Power Station Interface, SUSI, and Related DCC Buses

来源：NMRA S-9、S-9.1.1.x、S-9.1.2/TN-9.1.2、TI-9.2.3、S-9.4.x drafts、RCN-200、RCN-600/601/602/620。

## Interface Scope

- 这些内容属于 DCC 协议族的接口/总线层，不是 DCC 轨道 packet。
- Decoder connector standards define mechanical/electrical pin assignments and allowable signal roles; they are relevant when debugging DCC decoder behavior or mapping functions to hardware pins.
- Power Station Interface defines command station to booster/power station signal interchange.
- SUSI/Train Bus defines an internal decoder-to-module bus used by sound/function modules and some decoder interfaces.

## Decoder interfaces

Common DCC interface rules:

- Interface goal: allow decoder exchange between vehicle system board and decoder while preserving rail pickup, motor, function outputs, speaker, and optional SUSI/Train Bus lines.
- Wire colors for harness decoders follow S-9.1.1:
  - red/black: right/left rail pickup.
  - orange/gray: motor + / motor -.
  - white/yellow: front/rear light outputs.
  - blue: common positive for functions.
  - green/violet/brown and additional colors: auxiliary functions by connector-specific table.
- For plug-in decoders such as 21MTC, PluX, and Next18, do not infer harness colors; use connector pin table.
- Motor polarity should be wired so forward direction moves cab/end 1 forward under standard direction.
- Function-only decoders may omit motor behavior but must keep pin electrical limits and function mapping semantics.

Connector families:

| Standard | Interface | Protocol-relevant notes |
| --- | --- | --- |
| S-9.1.1.1 | six/eight pin | Baseline small decoder connector; maps rails, motor, lights, function common, optional AUX. |
| S-9.1.1.2 | JST-9 | Compact harness/socket with rail, motor, function and common assignments. |
| S-9.1.1.3 | 21MTC | 21-pin interface; supports multiple AUX outputs, logic-level outputs and optional sound/SUSI-related signals depending variant. |
| S-9.1.1.4 | PluX16/PluX22 | Pin family with rail, motor, speaker, AUX, Train Bus clock/data alternatives; PluX22 may be used as SUSI interface with only SUSI-relevant pins. |
| S-9.1.1.5 | Next18/Next18-S | Next18 is non-sound; Next18-S includes speaker pins; AUX3/TBCLK and AUX4/TBDAT can carry Train Bus/SUSI style signals. |

Implementation rules:

- Check connector-specific current and logic-level limits before mapping DCC function commands to outputs.
- AUX3/AUX4 and similar pins may be logic-level, not load-driving outputs; require system board drivers where specified.
- Speaker pins are not function outputs.
- When an interface is used as SUSI, track connections must not be used as SUSI lines unless the connector standard explicitly defines that mode.

## Power Station Interface

Power Station Interface (PSI) connects a Command Station signal generator to one or more Power Stations/boosters.

- It carries the DCC waveform intent at lower power; the power station amplifies it to track voltage/current.
- It does not define power station feedback from booster to command station; feedback remains implementation-specific unless another standard applies.
- Two interface options exist; a product needs only one:
  - Full Scale Interface.
  - Driver/Receiver Interface based on differential drivers/receivers such as TIA/EIA-422 or TIA/EIA-485 style signaling.
- Common characteristics:
  - Signal polarity must preserve DCC positive polarity so booster output matches the command station's intended rail phase.
  - Power Station Common must be documented and is required when the power station input is not electrically isolated.
  - Isolation and common-mode tolerance matter because command station and booster may have different references.
- Driver/Receiver option:
  - Uses differential positive/negative signal pair plus reference ground/common.
  - Must account for receiver sensitivity, driver differential output level, input resistance, common-mode voltage, short-circuit current limit, and load.
  - RS-422 and RS-485 style electrical characteristics are similar but not automatically interchangeable; document which is used.
- Full Scale option:
  - Mirrors a full DCC-like signal as command-station output for the booster input.
  - Requires short-circuit behavior and input compatibility tests because the signal can be closer to track waveform semantics.
- Documentation requirements include interface type, connector/pinout, maximum cable assumptions, receiver input resistance for Driver/Receiver, and Power Station Common guidance.
- RailCom cutout support must be considered at booster level; PSI itself is not the RailCom return channel.

## Decoder power modes draft

NMRA S-9.1.3 is draft material. Use it for current design awareness, not as an approved conformance claim.

- Three decoder/module power modes:
  - Standard: normal operation; motor/function/accessory outputs enabled; high consumption devices such as energy storage charging disabled.
  - Low power: decoder and connected modules minimize current; total current must be below 250 mA per S-9.2.3 service-mode expectation; all outputs disabled except ACK pulses; energy storage, smoke units, and other powered devices disabled so ACK current can be detected.
  - High power: decoder may draw required operating power, including energy storage charging.
- Default after connecting to DCC signal may be Standard or Low depending configuration; remains until a switching condition occurs.
- Switch to Low power:
  - Recognize two or more reset packets as service-mode entry preparation.
  - Immediately enter Low power.
  - Inform Train Bus/SUSI modules, for example SUSI command `0x6C 0x00`; modules immediately enter Low power.
- Switch to High power:
  - Mobile decoder may switch after packet addressed to primary address or consist address.
  - Broadcast packet does not authorize High power.
  - Connected Train Bus/SUSI modules may be told to enter High power.
  - Accessory decoder with high DCC power demand should use randomized delay before High power to reduce inrush.
- Power mode remains valid until next switching event; energy storage may bridge short DCC interruptions without changing mode.

## RCN-200 multiprotocol behavior

- Use RCN-200 when a decoder or command station supports DCC plus other track formats.
- Decoder must not treat non-DCC formats as valid DCC packets.
- When switching formats, fail-safe and packet timeout behavior must prevent stale DCC commands from causing unsafe motion.
- RailCom must not be used inside non-DCC track formats unless that format explicitly supports it.
- Multi-protocol output must preserve DCC packet boundaries, reset semantics, and valid sync detection when DCC resumes.

## SUSI / Train Bus overview

SUSI is a decoder-internal serial interface for sound/function modules.

- Host: main decoder.
- Module: SUSI sound/function extension; up to 3 modules are commonly addressed by RCN conventions.
- Legacy NMRA source is TI-9.2.3; newer NMRA S-9.4.x documents are drafts. RailCommunity RCN-600/601/602/620 provide current implementable detail.
- SUSI CVs occupy CV897-CV1024 in the DCC CV map.
- Module-specific CV windows:
  - Module 1: CV900-CV939.
  - Module 2: CV940-CV979.
  - Module 3: CV980-CV1019.
  - CV897-CV899 and CV1020-CV1024 apply across modules.
- CV897 selects module number; bits 0-1 values `01`, `10`, `11` map to module 1, 2, 3. `00` should be treated as module 1.
- CV898 is legacy volatile banking; not recommended for new implementations.
- CV1021 is recommended nonvolatile banking; banked module-specific CVs provide up to `256 * 40 = 10240` CVs per module.
- CV900/940/980 bank 0 stores manufacturer ID; bank 1 stores manufacturer hardware ID; bank 254 is reserved for extended manufacturer ID use.
- CV901/941/981 bank 0/1 store version/subversion; bank 254 stores supported SUSI version.
- CV1020 is status and WAIT support; host can wait while module indicates busy/ack.

## SUSI-BiDi

- SUSI-BiDi is backward-compatible with standard SUSI and lets modules answer over the data line.
- Host periodically polls registered modules; if data is available, module returns ACK then host clocks out 32 bits.
- A BiDi message is 2 x 2 byte. Bytes 1 and 3 are special BiDi identifiers so non-BiDi modules can ignore them as unknown command bytes.
- After startup, host calls the three possible BiDi modules; responding modules are considered registered.
- If a module has no useful data, it sends the function empty response `0x81 0x00` twice.
- Host must poll each registered BiDi module at least periodically; answer data should appear no later than about 2 ms after the last falling clock edge.
- ACK pulse:
  - Module produces 1-2 ms ACK.
  - Host accepts ACK pulse >= 0.5 ms.
  - After ACK ends, host sends 32 clocks.
  - Module changes data after rising clock edge and releases data line after transfer.
- CV-bank read:
  - Host sends module-specific bank-read command.
  - Module ACKs if bank available.
  - Module returns values as `0x8F + CV-value`; unsupported CV uses `0x8E + 0x01`.
  - CRC uses polynomial `x^8 + x^5 + x^4 + 1`, initial 0, not inverted.
  - After block read, host waits about 9 ms before next SUSI command to resynchronize modules.

## RCN-620 shift-register function extension

- RCN-620 defines a shift-register based function expansion for SUSI/Train Bus environments.
- It is for additional function outputs, not DCC track packet encoding.
- Do not mix RCN-620 and other function extension modes on the same pins unless the interface explicitly permits it.
- Treat RCN-620 output state as hardware-mapped function state driven by DCC function/binary-state semantics from the main decoder.
- NMRA S-9.4.4 draft aligns this as Train Bus extension Shift Registers / SIO:
  - SIO Data connects to Train Bus Data; SIO Clock connects to Train Bus Clock.
  - Data transfers on positive clock edge.
  - Shift clock frequency 400 kHz to 4 MHz.
  - Clock interruption of at least 30 us frames a transfer.
  - Shift register length maximum 16 bits.
  - Highest function data bit transmits first, lowest last, so misconfigured clock count does not offset lower functions.

## Tests

- Interface: verify rail/motor polarity, function common, speaker isolation, AUX logic vs power output, and connector-specific pin table.
- PSI: test polarity preservation, differential pair inversion, common-mode tolerance, short-circuit current limit, and documented Power Station Common.
- SUSI: test module count, CV897 assignment, CV900/940/980 manufacturer ID, CV1021 banking, CV1020 busy/wait, BiDi ACK timing, 32-clock response, CRC, 9 ms recovery gap.
- Multi-protocol: inject non-DCC frames between DCC packets and verify decoder resync/fail-safe behavior.
