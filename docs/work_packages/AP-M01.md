# AP-M01 – eingefrorene interne Message- und Topic-Verträge

```yaml
work_package: AP-M01
status: complete
contract_version: 1
baseline_date: 2026-09-02
branch: orin
head: 7df2f36f1a8d00ff6080dbec1ae1263aa5948f2b
environment: local_ros_jazzy_container
working_tree_clean_before: false
working_tree_clean_after: false
hardware_accessed: false
usb_bridge_started: false
real_vehicle_validation: false
```

## 1. Ergebnis und Geltungsbereich

AP-M01 friert die Verträge ein, gegen die AP-D01, AP-C01, AP-P02 und AP-P03
parallel implementieren dürfen. Die kleinste tragfähige Auswahl lautet:

| Sachverhalt | Entscheidung |
|---|---|
| geometrischer Referenz-, Renn- und lokaler Pfad | `nav_msgs/msg/Path` direkt verwenden |
| autonomer SI-Fahrbefehl | `ackermann_msgs/msg/AckermannDriveStamped` direkt verwenden |
| reine Zustandsbeobachtung und Evaluationsausgabe | `diagnostic_msgs/msg/DiagnosticArray` direkt verwenden |
| bildbasierte Pylonbeobachtung für den Planer | neue kleine `rc_car_interfaces/msg/PylonObservationArray` mit `PylonObservation` |
| Trajektorie mit Solltempo/Beschleunigung je Stützpunkt | jetzt **nicht** einführen; Bedarf erst in AP-V01 nachweisen und gegebenenfalls in AP-I01 zentral ergänzen |

Damit beschreiben keine zwei Message-Typen denselben Sachverhalt. Insbesondere
wird kein eigener Path-, Ackermann-, Status- oder Metriktyp angelegt. JSON und
freie `std_msgs/String`-Verträge sind nicht zulässig.

Diese Vereinbarung ändert keinen Produktionscontroller, keinen Launch, keine
Fahrbefehls- oder Safety-Kette und nicht `docs/ros_graph.md`. Sie erteilt keine
Hardware- oder Realfahrzeugfreigabe.

## 2. Reuse-Gate

Die Prüfung erfolgte vor der Interfaceänderung gegen die im Jazzy-Container
installierten Definitionen:

| Paket | Stand | Eignung |
|---|---|---|
| `nav_msgs` | 5.3.8 | `Path` trägt gemeinsamen Timestamp/Frame und geordnete `PoseStamped`-Stützpunkte; ausreichend für reine Geometrie |
| `ackermann_msgs` | 2.0.2 | `AckermannDriveStamped` trägt Timestamp, Frame, Geschwindigkeit, Lenkwinkel sowie optionale Änderungsgrenzen in SI-Einheiten |
| `diagnostic_msgs` | 5.3.8 | `DiagnosticArray`/`DiagnosticStatus` reichen für beobachtbaren Health-/State-Text und Schlüsselwerte, sofern kein Consumer daraus Freigaben ableitet |
| `vision_msgs` | 4.1.1 | `Detection2DArray` bietet Header, Klassenhypothese, Konfidenz, Pixel-Bounding-Box und ID, aber keinen expliziten Peilwinkel, dessen Unsicherheit oder eine gültige/typisierte Reichweitenquelle |

Reproduzierbare Quellen des direkt verwendeten Binärstands:

| Pakete | Upstream/Pin | Lizenz |
|---|---|---|
| `nav_msgs`, `diagnostic_msgs` | <https://github.com/ros2/common_interfaces>, Release `5.3.8` | Apache-2.0/BSD-Anteile gemäß Paket |
| `ackermann_msgs` | <https://github.com/ros-drivers/ackermann_msgs>, Release `2.0.2` | BSD-3-Clause |
| `vision_msgs` | <https://github.com/ros-perception/vision_msgs>, Release `4.1.1` | Apache-2.0 |

Die tatsächlich gefundenen Debian-Binärversionen waren
`ros-jazzy-nav-msgs 5.3.8-1noble.20260612.082120`,
`ros-jazzy-diagnostic-msgs 5.3.8-1noble.20260612.081536`,
`ros-jazzy-ackermann-msgs 2.0.2-6noble.20260612.092601` und
`ros-jazzy-vision-msgs 4.1.1-3noble.20260612.085240` auf ARM64.

`vision_msgs/Detection3DArray` allein wäre ebenfalls kein sauberer Ersatz: Es
verliert die geforderte Pixel-Bounding-Box; die parallele Veröffentlichung von
2-D- und 3-D-Arrays würde Identitäts-, Synchronisations- und
Fehlerzustandssemantik auf die Consumer verlagern. Das Überladen einer
`PoseWithCovariance` mit Polarwerten wäre nicht standardkonform. Deshalb wird
nur diese nachweisliche Domänenlücke neu beschrieben. Die Pixelbox wird dabei
als Standardtyp `vision_msgs/msg/BoundingBox2D` wiederverwendet.

Es wurde kein externer Quellcode kopiert. Die neuen Messages und Tests stehen
unter der vorhandenen Apache-2.0-Lizenz von `rc_car_interfaces`.

## 3. Gemeinsame Regeln

- Alle Header-Zeitstempel sind Messzeit in ROS-Zeit; in Simulation gilt
  `/clock` und `use_sim_time=true`. Receipt time ersetzt keine verfügbare
  Messzeit.
- Pfade und Beobachtungen verwenden REP-103-konforme Frames ohne führenden
  Slash. Ein leerer oder nicht transformierbarer Frame ist ungültig.
- QoS-Angaben sind Teil des Vertrags. Publisher und Subscriber dürfen die
  History-Tiefe erhöhen, aber nicht Reliability oder Durability inkompatibel
  ändern.
- Produzenten validieren vor Publikation alle endlichen Werte, Enumwerte,
  Größen und fachlichen Invarianten. Consumer validieren externe Eingaben
  erneut und reagieren fail-safe.
- Ground Truth darf diese Topics nicht speisen. Sie bleibt ausschließlich ein
  Eingang der Evaluation.
- Neue Fahrcontroller publizieren nur
  `/control/autonomous_ackermann_cmd`. Sie publizieren nie direkt auf
  `/drive_commands`, `/control/autonomous_cmd` oder `/cmd_vel`.

Die QoS-Kurzformen in den folgenden Tabellen bedeuten:

```text
latched:  reliable, transient_local, keep_last(1)
state:    reliable, volatile, keep_last(5)
command:  reliable, volatile, keep_last(1)
```

## 4. Pfadverträge

### 4.1 `/planning/reference_path`

| Eigenschaft | Vertrag |
|---|---|
| Typ | `nav_msgs/msg/Path` |
| Publisher | AP-D01-Referenzpfad-Publisher, genau einer |
| Subscriber | AP-C01; AP-G01/AP-V01 dürfen den Pfad offline lesen |
| Einheit/Frame | Position m, Orientierung als normiertes Quaternion; `header.frame_id=map` |
| Timestamp | Erzeugungs-/Ladezeit des vollständigen Pfads; alle Pose-Header verwenden denselben Frame und denselben Stamp |
| QoS | `latched` |
| Rate | ereignisgetrieben bei erfolgreichem Laden/Ändern; keine periodische Wiederholung nötig |
| Timeout | statisches, validiertes Artefakt altert nicht nur durch verstrichene Zeit; ein Controller benötigt aber nach seiner Aktivierung mindestens eine gültige Instanz aus dieser Durability-Domain |
| Fehlerverhalten | kein Pfad bei NaN/Inf, leerem/falschem Frame, zu wenigen Punkten, offenem oder selbstschneidendem Pfad; Consumer erzeugt keine Bewegung ohne gültigen Pfad |

Die Reihenfolge der Posen ist die Fahrtrichtung. Ein geschlossener Pfad enthält
den geometrischen Startpunkt nicht doppelt; der implizite letzte Abschnitt
führt vom letzten zum ersten Stützpunkt. `PoseStamped.pose.orientation`
beschreibt die Tangentenrichtung. Die genaue Mindestpunktzahl, der
Schließtoleranzwert und das Sampling sind Parameter von AP-D01 und werden dort
zusätzlich geprüft.

### 4.2 `/planning/racing_line`

Dieser bestehende Name bleibt während der Migration ein kompatibler Alias von
`/planning/reference_path`, ebenfalls `nav_msgs/msg/Path` mit exakt derselben
Instanz und Semantik. `/planning/reference_path` ist kanonisch. AP-D01 darf
denselben validierten Pfad zusätzlich auf dem Alias publizieren; kein Consumer
darf die beiden Topics zu zwei Pfaden kombinieren oder unterschiedliche Daten
auf ihnen erwarten. AP-I01 darf den Alias erst entfernen, nachdem alle
Bestandsconsumer migriert sind.

### 4.3 `/planning/local_path`

| Eigenschaft | Vertrag |
|---|---|
| Typ | `nav_msgs/msg/Path` |
| Publisher | AP-P03-Pylonplaner, genau einer im PYLON-Profil |
| Subscriber | gemeinsamer AP-C01-Bahnfolger im PYLON-Profil |
| Einheit/Frame | Position m, normiertes Quaternion; bevorzugt `base_link` zum Messzeitpunkt, alternativ ein vollständig transformierbarer lokaler Frame |
| Timestamp | Planerzeugungszeit; alle Pose-Header stimmen mit dem Path-Header überein |
| QoS | `state` |
| Rate | mindestens 10 Hz solange ein PYLON-Bewegungsziel aktiv erneuert wird; zusätzlich sofort bei Zustandsänderung |
| Timeout | 0,5 s, gemessen in ROS-Zeit |
| Fehlerverhalten | bei Ambiguität, Beobachtungsverlust oder ungültiger Geometrie keinen alten Pfad erneuern; Controller neutralisiert oder beendet Publikation vor Ablauf seines Downstream-Timeouts |

Ein lokaler Pfad ist absichtlich nicht geschlossen. Seine Pose-Reihenfolge ist
vorwärts gerichtet. Pixelkoordinaten dürfen niemals in diesem Topic stehen.

## 5. Pylonbeobachtungsvertrag

### 5.1 Warum ein eigener Typ erforderlich ist

AP-P03 benötigt für jede zusammengehörige Beobachtung Klasse/Farbe,
Konfidenz, Pixelbox, Peilwinkel samt Unsicherheit und eine explizit optionale
Reichweite samt Quelle. Kein geprüftes Standard-ROS-Message bildet diese
Kombination ohne semantisches Überladen oder unsynchronisierte Parallelarrays
ab. Neu eingeführt sind deshalb genau:

- `rc_car_interfaces/msg/PylonObservation.msg`
- `rc_car_interfaces/msg/PylonObservationArray.msg`

### 5.2 `/perception/pylons`

| Eigenschaft | Vertrag |
|---|---|
| Typ | `rc_car_interfaces/msg/PylonObservationArray` |
| Publisher | AP-P02-Pylondetektor, genau einer pro aktivem Backend |
| Subscriber | AP-P03-Gate-/Slalominterpretation; Evaluator darf mithören |
| Einheit/Frame | Pixel für `bbox`; rad für Peilwinkel/Standardabweichung; m für optionale Reichweite/Standardabweichung; räumlicher Frame normalerweise `base_link` |
| Timestamp | exakt der Timestamp des ausgewerteten Quellbilds |
| QoS | `state` |
| Rate | bildgetrieben, Ziel mindestens 10 Hz in der definierten Gazebo-Szene |
| Timeout | 0,3 s seit Messzeit in ROS-Zeit |
| Fehlerverhalten | ein valides leeres Array bedeutet explizit „in diesem Bild keine Detektion“; bei stale/ungültigem Bild oder TF-Fehler nicht mit neuem Stamp erneut publizieren; Consumer verwirft das Array und erneuert keinen Bewegungsplan |

`header.frame_id` ist der REP-103-Fahrzeugframe, in dem Peilwinkel und
optionale Reichweite ausgedrückt sind, normalerweise `base_link`. Die Peilung
ist null nach vorn und positiv nach links. Das Quellbild wird über denselben
Timestamp auf `/camera/image_raw` identifiziert; die Bounding Box bleibt in
dessen Pixelkoordinaten.

Pro Beobachtung gelten:

- `track_id=0`: kein zeitlicher Track; positive IDs dürfen erst nach einem
  tatsächlichen Tracker und nie nur aus dem Arrayindex erzeugt werden;
- `object_class`: nur die definierten Konstanten; AP-P02 publiziert nur
  `CLASS_TRAFFIC_CONE`, unbekannte Kandidaten werden verworfen;
- `color`: definierte Farbklasse oder `COLOR_UNKNOWN`;
- `bbox`: positive endliche Größe und Mittelpunkt innerhalb des Quellbilds;
- `confidence`: endlich und geschlossen in `[0, 1]`;
- `bearing_rad`: endlich; `bearing_stddev_rad` endlich und nicht negativ;
- `range_valid=false`: `range_m=0`, `range_stddev_m=0` und
  `range_source=RANGE_NONE`;
- `range_valid=true`: positive endliche Reichweite, endliche nichtnegative
  Standardabweichung und eine andere definierte Quelle als `RANGE_NONE`.

Monokulare Reichweite darf nur mit gültiger Kamerakalibrierung und einer
dokumentierten realen/Simulations-Objektgröße als
`RANGE_MONOCULAR_SIZE` markiert werden. AP-P03 darf ungültige oder fehlende
Reichweite nicht selbst aus der Pixelbox schätzen.

## 6. Fahrbefehlsvertrag

### `/control/autonomous_ackermann_cmd`

| Eigenschaft | Vertrag |
|---|---|
| Typ | `ackermann_msgs/msg/AckermannDriveStamped` |
| Publisher | genau ein aktivierter autonomer Controller; in Welle 2 AP-C01 |
| Subscriber | vorhandener `ackermann_to_drive_request` |
| Einheit/Frame | `speed` m/s, `steering_angle` rad, `steering_angle_velocity` rad/s, `acceleration` m/s², `jerk` m/s³; `header.frame_id=base_link` |
| Timestamp | Erzeugungszeit des Befehls in ROS-Zeit |
| QoS | `command` |
| Rate | 20–50 Hz während der Aktivierung; AP-C01 misst und dokumentiert die konkrete Rate |
| Timeout | bestehender Downstream-Adapter neutralisiert nach 0,3 s ohne frischen Ackermann-Befehl |
| Fehlerverhalten | nichtfinite/außerhalb konfigurierter Grenzen liegende Werte, stale Pose/Path, TF-Fehler und Reverse im ersten Baselinecontroller führen zu neutralem SI-Befehl oder zum Ende der Publikation innerhalb 0,3 s |

`steering_angle` ist der virtuelle mittlere Vorderradwinkel gemäß
`ackermann_msgs` und positiv nach links. Negative Geschwindigkeit bedeutet
Reverse und wird von der ersten AP-C01-Baseline ausdrücklich abgelehnt.
Nullwerte in `acceleration`, `jerk` und `steering_angle_velocity` bedeuten nach
der Standardmessage „so schnell wie möglich“, nicht zwingend eine physische
Nullgrenze. AP-C01 muss Lenkwinkel und Änderungsraten trotzdem über seine
Parameter begrenzen.

## 7. Status- und Evaluationsverträge

Diese Topics dienen nur Beobachtung, Logging und Abnahme. Kein Safety-,
Supervisor- oder Controllerpfad darf Freigabeentscheidungen durch Parsen der
`DiagnosticStatus.values`-Strings treffen. Interne Zustände bleiben typisierte
Enums im jeweiligen Node beziehungsweise Lifecyclezustände. Wenn später eine
prozessübergreifende, maschinenlesbare Freigabe benötigt wird, muss AP-I01 den
Bedarf gesondert nachweisen und einen kleinen typed Vertrag ergänzen.

### 7.1 `/racing/status`

| Eigenschaft | Vertrag |
|---|---|
| Typ | `diagnostic_msgs/msg/DiagnosticArray`, genau ein `DiagnosticStatus` mit `name=avaj/racing` |
| Publisher / Subscriber | AP-R02 Racing-Supervisor / UI, Recorder, AP-E01 |
| Frame | Header-Frame leer; numerische Pose-/Pfaddaten gehören nicht hierher |
| QoS / Rate / Timeout | `state`; 2 Hz und sofort bei Übergang; nach 1,0 s STALE |
| Fehlerverhalten | `level=STALE` bei fehlenden Inputs, `ERROR` bei FAULT; Diagnose bleibt beobachtbar, erzeugt aber selbst keine Bewegung |

Pflichtschlüssel sind `state` (`IDLE|READY|RACING|FINISHED|FAULT`), `reason`,
`lap_count`, `pose_age_s`, `path_age_s`, `controller_age_s` und
`path_valid` (`true|false`). Werte sind kanonische, locale-unabhängige ASCII-
Darstellungen. Zusätzliche Schlüssel sind erlaubt; Pflichtschlüssel dürfen
nicht umgedeutet werden.

### 7.2 `/pylon/status`

| Eigenschaft | Vertrag |
|---|---|
| Typ | `diagnostic_msgs/msg/DiagnosticArray`, genau ein `DiagnosticStatus` mit `name=avaj/pylon` |
| Publisher / Subscriber | späterer Pylon-Supervisor/AP-P03 / UI, Recorder, AP-E01 |
| Frame | Header-Frame leer |
| QoS / Rate / Timeout | `state`; 2 Hz und sofort bei Übergang; nach 1,0 s STALE |
| Fehlerverhalten | `STALE` bei alten Bildern/Detektionen, `ERROR` bei FAULT; Diagnose ist kein Fahrbefehl |

Pflichtschlüssel sind `state`
(`IDLE|SEARCHING|TRACKING|GATE|SLALOM|STOP|FAULT`), `reason`,
`detection_age_s`, `local_path_age_s` und `observation_count`.

### 7.3 `/evaluation/lap_metrics`

| Eigenschaft | Vertrag |
|---|---|
| Typ | `diagnostic_msgs/msg/DiagnosticArray`, genau ein `DiagnosticStatus` mit `name=avaj/evaluation/lap` |
| Publisher / Subscriber | AP-R02/AP-E01 Evaluator / Recorder, UI |
| Frame | Header-Frame leer |
| QoS / Rate / Timeout | `latched`; ereignisgetrieben genau einmal pro abgeschlossener/abgebrochener Runde; kein Freshness-Timeout |
| Fehlerverhalten | unvollständige Runde wird mit `WARN` oder `ERROR` und `completed=false` sichtbar publiziert, nicht ausgelassen oder als Erfolg gezählt |

Pflichtschlüssel sind `run_id`, `lap_index`, `completed`, `reason`,
`lap_time_s`, `distance_m`, `mean_cross_track_error_m`,
`max_cross_track_error_m`, `mean_speed_mps` und `max_speed_mps`. Ground Truth
darf nur der Evaluator zur Bildung dieser Werte lesen und nie in Planer oder
Controller zurückgeführt werden.

## 8. Verantwortungsübergabe an Folgepakete

- **AP-D01:** implementiert nur die Validierung und Veröffentlichung von
  `/planning/reference_path` plus identischem Kompatibilitätsalias
  `/planning/racing_line`; keine Interfaceänderung.
- **AP-C01:** konsumiert `nav_msgs/Path` und publiziert ausschließlich den
  festgelegten Ackermann-Befehl; keine Interfaceänderung.
- **AP-P02:** produziert das typisierte Pylonarray, validiert jede Invariante
  vor Veröffentlichung und publiziert keine Fahrbefehle.
- **AP-P03:** konsumiert das Pylonarray, verwirft es nach 0,3 s oder bei
  Vertragsfehler und publiziert ausschließlich `/planning/local_path`.
- **AP-I01:** übernimmt später Integrationsbesitz. Eine zusätzliche typed
  `Trajectory` ist nur zulässig, wenn AP-V01/AP-C01 nachweisen, dass getrennte
  per-point Geschwindigkeit/Krümmung/Beschleunigung tatsächlich benötigt
  werden und nicht durch Pfad plus Controllerparameter ausgedrückt werden
  können.

Änderungen an diesen Verträgen erfordern ab jetzt eine explizite
Versions-/Migrationsentscheidung in AP-I01; stilles Umdeuten ist nicht
zulässig.

## 9. Geänderte Dateien

```text
workspace/src/rc_car_interfaces/CMakeLists.txt
workspace/src/rc_car_interfaces/package.xml
workspace/src/rc_car_interfaces/msg/PylonObservation.msg
workspace/src/rc_car_interfaces/msg/PylonObservationArray.msg
workspace/src/rc_car_interfaces/test/test_pylon_interfaces.py
docs/work_packages/AP-M01.md
```

Alle vorgefundenen fremden Änderungen blieben erhalten. Insbesondere wurden
Produktionscontroller, Launches, `drive_commander`, USB-/ESP-Dateien,
`docs/ros_graph.md` und `CURRENT_STATE.md` nicht angefasst.

## 10. Verifikation

Die Prüfung erfolgt ausschließlich in einem kurzlebigen ROS-Jazzy-Container,
mit `ROS_DOMAIN_ID=206` und separaten Build-/Install-/Log-Verzeichnissen unter
Container-`/tmp`. Dadurch kollidiert sie nicht mit parallelen Pakettests. Es
werden keine ROS-Nodes und keine Geräte gestartet.

```bash
docker compose run --rm -e ROS_DOMAIN_ID=206 jazzy bash -lc '
  cd /workspace
  source /opt/ros/jazzy/setup.bash
  colcon --log-base /tmp/ap_m01_final_log build \
    --build-base /tmp/ap_m01_final_build \
    --install-base /tmp/ap_m01_final_install \
    --packages-select rc_car_interfaces
  source /tmp/ap_m01_final_install/setup.bash
  colcon --log-base /tmp/ap_m01_final_test_log test \
    --build-base /tmp/ap_m01_final_build \
    --install-base /tmp/ap_m01_final_install \
    --test-result-base /tmp/ap_m01_final_results \
    --packages-select rc_car_interfaces
  colcon test-result --test-result-base /tmp/ap_m01_final_results --verbose
  python3 -m flake8 \
    /workspace/src/rc_car_interfaces/test/test_pylon_interfaces.py
'
```

Ergebnis:

- `rc_car_interfaces` baute mit den beiden neuen Messages erfolgreich;
- `vision_msgs` 4.1.1 wurde als vorhandene Standardabhängigkeit gefunden;
- die registrierte CTest-/Pytest-Suite bestand mit **3/3 Testfällen**;
- `colcon test-result` meldete **1 Suite, 0 Fehler, 0 Fehlschläge, 0 Skips**;
- der direkte Flake8-Lauf für den neuen Test war ohne Befund;
- getestet wurden stabile Enumwerte, die beiden Konfidenz-/Peilungsgrenzen,
  gültige und fehlende Reichweite, Standard-`BoundingBox2D`, Serialisierung/
  Deserialisierung sowie ein explizit leeres Detektionsergebnis.

## 11. Grenzen und Folgearbeit

- `.msg`-Definitionen können Wertebereiche nicht zur Laufzeit erzwingen;
  AP-P02 und AP-P03 müssen die dokumentierten Invarianten jeweils validieren.
- `DiagnosticArray` ist absichtlich nur Observability. Werden seine Stringwerte
  später als Steuer-API benötigt, reicht der Typ nicht mehr.
- Es wurde kein Pylondetektor, Planer, Controller oder Trajektorientyp
  implementiert.
- Es gab keine Simulation, keinen Rosbag-Lauf und keine Hardwarevalidierung.
- Die Sicherheitsgrenzen aus `CURRENT_STATE.md` bleiben vollständig bestehen.

## 12. Abschlussklassifikation

```yaml
implemented:
  - frozen standard path, command, status and metrics contracts
  - minimal typed pylon observation gap
tested:
  - isolated rc_car_interfaces build succeeded
  - 3/3 interface serialization and boundary cases passed
simulated: []
hardware_validated: []
```
