# ESP-Feedbackprotokoll V1

Stand: 1. September 2026. Dieses Dokument ist der verbindliche Vertrag für den
hardwareunabhängigen ESP-zu-Jetson-Rückkanal. Im Repository existiert noch keine
passende ESP-Firmware; V1 wurde daher ausschließlich mit synthetischen Bytes und
Pseudo-Terminals geprüft.

## Abgrenzung zum ausgehenden Legacy-Format

Jetson-zu-ESP bleibt unverändert:

```text
CMD,<sequence>,<speed>,<steering>,<enabled>*<CRC16-CCITT>\n
```

`CMD` besitzt absichtlich kein `V1`-Präfix. Der Decoder akzeptiert `CMD` nicht
als Feedback und interpretiert Legacy-Zeilen niemals als V1. Ein zukünftiges
versioniertes Command-Format ist nicht Bestandteil dieses Vertrags und wird
ohne passende Firmware nicht aktiviert.

## Gemeinsames Framing

- Ein Frame besteht ausschließlich aus druckbarem 7-Bit-ASCII (`0x20..0x7e`),
  gefolgt von LF (`0x0a`). Vor LF ist optional genau ein CR (`0x0d`) zulässig.
- Die maximale Länge vor LF, einschließlich optionalem CR, Payload, `*` und
  CRC, beträgt 128 Byte. Nach Überschreitung wird bis zum nächsten LF verworfen.
- Leere LF- oder CRLF-Zeilen werden ignoriert.
- Die Payload beginnt mit `V1,<TYPE>` und enthält komma-separierte Felder. Leere
  Felder, Whitespace, zusätzliche Felder und fehlende Felder sind ungültig.
- Der Drahtframe ist `<payload>*<crc>\n`. Die CRC deckt exakt die ASCII-Bytes
  der Payload ab, nicht `*`, die vier CRC-Ziffern, CR oder LF.
- CRC-Variante: CRC-16/CCITT-FALSE, Polynom `0x1021`, Initialwert `0xffff`,
  kein Reflect, kein XOR-out. Prüfvektor `123456789` ergibt `0x29b1`.
- Die CRC wird als genau vier große Hexziffern `0000..FFFF` übertragen.
- Unsigned Integer sind kanonische Dezimalzahlen ohne Vorzeichen und ohne
  führende Null (außer `0`). Signed Integer verwenden optional genau `-`, nie
  `+`; `-0` und führende Nullen sind ungültig. Dezimalüberlauf wird verworfen.

Unbekannte Versionen und unbekannte Frametypen werden vollständig verworfen.
Es gibt keine Vorwärtsinterpretation unbekannter Felder.

## Frametypen und Feldreihenfolge

### `STA` — Fahrzeugstatus und ACK

```text
V1,STA,<accepted_sequence>,<owner>,<jetson_locked>,<armed>,<enabled>,<fault_flags>*CCCC\n
```

| Feld | Format und Semantik |
|---|---|
| `accepted_sequence` | `uint32`, zuletzt vom ESP akzeptierte Legacy-CMD-Sequenz, Wrap modulo `2^32` |
| `owner` | `0=SAFE`, `1=MANUAL`, `2=JETSON`; andere Werte ungültig |
| `jetson_locked` | `0/1`; bei MANUAL zwingend `1`, bei JETSON zwingend `0` |
| `armed` | `0/1`; ESP-Arming-Zustand, keine Jetson-Fahrfreigabe |
| `enabled` | `0/1`; tatsächlicher Low-Level-Enable; `1` erfordert `armed=1` und Owner ungleich SAFE |
| `fault_flags` | `uint32`-Bitmaske; in V1 sind nur Bits 0 bis 10 definiert, reservierte Bits sind ungültig |

Faultbits:

| Bit | Wert | Bedeutung |
|---:|---:|---|
| 0 | 1 | Jetson-Command-Timeout |
| 1 | 2 | ungültige Command-CRC |
| 2 | 4 | ungültiges Command-Format/-Feld |
| 3 | 8 | Manual-Controller-Timeout |
| 4 | 16 | Motorcontrollerfehler |
| 5 | 32 | Lenkungsfehler |
| 6..9 | 64..512 | Encoderfehler vorne links/rechts, hinten links/rechts |
| 10 | 1024 | Protokollfehler |

`STA` ist zugleich ACK. Innerhalb einer Verbindung muss die Sequenz gemäß
serieller uint32-Arithmetik fortschreiten: `delta=(neu-alt) mod 2^32`.
`1 <= delta < 2^31` ist vorwärts; `delta=0` ist Duplikat; `delta>=2^31` ist
Rückschritt. Zusätzlich verwirft die aktuelle Bridge Sprünge über 1.000.000 als
unplausibel. `4294967295 -> 0` ist damit ein gültiger Wrap. Ein verworfenes ACK
ändert den gespeicherten Vergleichswert nicht.

### `ACT` — tatsächlich angewandter Aktorzustand

```text
V1,ACT,<applied_sequence>,<speed>,<steering>,<enabled>*CCCC\n
```

`applied_sequence` ist `uint32` mit Wrap modulo `2^32`. `speed` und `steering`
sind signed Dezimalwerte `-100..100`, dimensionslos und nach ESP-Begrenzung
tatsächlich angewandt: Speed negativ/rückwärts, positiv/vorwärts; Steering
negativ/links, positiv/rechts. `enabled` ist genau `0` oder `1`. Diese Werte sind
nicht mit den angeforderten Werten eines `DriveCommand` gleichzusetzen.

### `ENC` — vier absolute Encoderstände

```text
V1,ENC,<sample_counter>,<front_left>,<front_right>,<rear_left>,<rear_right>*CCCC\n
```

`sample_counter` ist `uint32` und wrappt modulo `2^32`. Jeder Radwert ist ein
signed `int32`-Zähler in Encodercounts. Nach ESP-seitiger Polaritätsnormierung
bedeutet positiv Vorwärts- und negativ Rückwärtsbewegung. Jeder Zähler wrappt
zweierkomplementär von `2147483647` nach `-2147483648` beziehungsweise
umgekehrt. Eine physische Distanz pro Count ist kalibrierungsabhängig und in V1
nicht behauptet. Die vier Kanäle werden nie vorzeitig zusammengeführt.

## Zeit, Reset und Fehlerverhalten

Das ESP liefert in V1 keine synchronisierte ROS-Zeit. Die Header aller
typisierten ROS-Nachrichten tragen deshalb die Jetson-ROS-Empfangszeit des
vollständig validierten Frames; `frame_id` bleibt leer. `sample_counter` und
Sequenzen sind ESP-Werte und ausdrücklich keine Zeitstempel.

Ein Frame wird erst nach LF ausgewertet. Ein Fragment ohne LF publiziert nichts.
Bei Disconnect, Reconnect oder Parserreset werden Fragmente, Overlength-
Verwerfzustand und ACK-Vergleichszustand gelöscht. Ein vorhandenes Fragment
erzeugt `truncated_frame`. Nach Reconnect ist das erste valide ACK die neue
Vergleichsbasis, weil ein ESP-Reset nicht anhand ungeprüfter Bytes unterschieden
werden kann. Leere Zeilen ändern weder Status noch ACK-Zustand.

Jede Ablehnung ist atomar: Kein Feld eines ungültigen Frames aktualisiert ein
typisiertes Topic oder frischt dessen Header auf. Nach dem nächsten LF kann der
Decoder wieder ein gültiges Frame verarbeiten. Diagnosegründe sind mindestens:
`unknown_version`, `unknown_frame_type`, `crc_error`, `field_count`,
`empty_field`, `invalid_integer`, `range`, `invalid_boolean`,
`unknown_fault_bits`, `invalid_status`, `non_ascii`, `overlong_frame`,
`truncated_frame`, `ack_duplicate`, `ack_regression` und `ack_implausible`.

## ROS-Abbildung und Sicherheitsgrenze

| Frame | Topic | Typ |
|---|---|---|
| `STA` | `/vehicle/status` | `rc_car_interfaces/msg/VehicleStatus` |
| `ACT` | `/vehicle/actuator_status` | `rc_car_interfaces/msg/ActuatorStatus` |
| `ENC` | `/vehicle/encoders` | `rc_car_interfaces/msg/WheelEncoderState` |

`/drive_usb/rx` darf jede abgeschlossene Zeile ausschließlich zur Diagnose
abbilden; Ersatzzeichen in dieser Stringdarstellung machen sie gerade nicht
vertrauenswürdig. `/drive_usb/status` meldet Transport- und Ablehnungsgründe.
Keines dieser Topics setzt in diesem Paket `/system/drive_enable`. Eine spätere
Watchdog-Kopplung setzt passende Firmware oder einen vertragstreuen Emulator
und eigene Sicherheitsvalidierung voraus.
