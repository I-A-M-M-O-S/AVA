# AVAJ RC-Car – lokale, reuse-first Codex-Arbeitspakete

**Überarbeitet:** 2. September 2026  
**Repository:** `/home/avaj/ros2_jazzy`  
**Geprüfte Basis:** Branch `orin`, HEAD `7df2f36f1a8d00ff6080dbec1ae1263aa5948f2b` plus bestehende uncommittete Änderungen

## 1. Ziel und verbindlicher Umfang

Dieser Plan beschreibt ausschließlich lokale ROS-2-Entwicklung für die
autonome Fahrsteuerung. Tests erfolgen mit Unit-Tests, synthetischen ROS-
Nachrichten, Rosbag-Replay und bei Bedarf Gazebo Harmonic.

Erlaubt sind:

- Lesen der vorhandenen Sensor-, Karten-, TF- und Zustands-Topics;
- Erzeugen interner Planungs-, Wahrnehmungs-, Diagnose- und Evaluations-Topics;
- Publizieren von Fahrbefehlen ausschließlich als
  `ackermann_msgs/msg/AckermannDriveStamped` auf
  `/control/autonomous_ackermann_cmd`;
- neue lokale ROS-Pakete und Messages, wenn ein Standardtyp den Vertrag nicht
  korrekt ausdrückt;
- externe Open-Source-Komponenten und kleine, dokumentierte Adapter;
- Simulation und Offline-Auswertung.

Ausdrücklich nicht erlaubt sind:

- Änderungen an ESP32-Firmware, ESP-Protokoll oder USB-Transport;
- Öffnen von `/dev/ttyUSB*`, `/dev/ttyACM*`, I²C-, Kamera- oder LiDAR-Geräten;
- Änderungen an `rc_car_usb_bridge`, `docs/esp_feedback_protocol.md` oder
  `/vehicle/*`-Feedbackverträgen;
- direkte Publikation auf `/drive_commands`, `/control/autonomous_cmd` oder
  `/cmd_vel` durch neue Fahralgorithmen;
- Änderungen an `drive_commander`, dessen Safety-Freigabe oder dem
  Ackermann-zu-DriveRequest-Adapter, sofern ein Paket dies nicht ausdrücklich
  als reinen, lokalen Regressionstest liest;
- reale, aufgebockte oder angetriebene Fahrzeugtests;
- Ground Truth als Eingang für Lokalisierung, Planung oder Regelung.

Die vorhandene Kette hinter dem Controller bleibt unangetastet:

```text
neuer lokaler Controller
  -> /control/autonomous_ackermann_cmd  [m/s, rad]
  -> vorhandener ackermann_to_drive_request
  -> vorhandener drive_commander
  -> vorhandener Gazebo-Adapter
```

Dieser Plan ersetzt für den aktuellen Auftrag die ESP-, Hardware- und
Realfahrzeugpakete des früheren Entwurfs. Er hebt die Sicherheitsgrenzen aus
`AGENTS (1).md` und `CURRENT_STATE.md` nicht auf.

## 2. Festgestellter Ausgangspunkt

- Der aktive Quellbaum ist `workspace/src`, nicht die ältere verschachtelte
  Kopie unter `ros2_jazzy/workspace`.
- `control_center` liest bereits `/scan`, `/odometry/filtered`, `/map` und
  `/planning/racing_line`, verwendet die Rennlinie aber noch nicht.
- Sein einziger physischer Ausgang ist bereits
  `/control/autonomous_ackermann_cmd`.
- Der bestehende Adapter und `drive_commander` bilden die nachgelagerte
  Simulationskette. `/drive_commands` muss genau einen Publisher behalten.
- Gazebo, Sensor-Preprocessing, Simulations-EKF und `slam_toolbox` sind als
  Grundlage vorhanden; Queue-Drops und Shutdown-Fehler sind noch offen.
- Eine gespeicherte-Karte-Lokalisierung, Referenzbahn, Bahnfolger,
  Rundenerkennung und reproduzierbare geschlossene Runde fehlen.
- Kamera- und Pylonenpfad sind optional und dürfen parallel zum Racing-Pfad
  entstehen, aber nicht in `control_center` eingebaut werden.
- Die in den Repository-Anweisungen genannte Datei
  `DEVELOPMENT_PLAN.md — AVAJ RC-Car.md` ist derzeit nicht vorhanden. Codex
  darf ihr Vorhandensein nicht behaupten und nicht auf sie als Voraussetzung
  verweisen.

## 3. Reuse-first ist eine Abnahmebedingung

Vor neuem Algorithmuscode muss jedes Paket diese Reihenfolge abarbeiten:

1. Prüfen, ob das benötigte ROS-Jazzy-Paket bereits im Container installiert
   ist.
2. Offizielle ROS-/Gazebo-Komponenten bevorzugen.
3. Danach einen gepflegten ROS-2-Upstream mit passender Lizenz und klarer API
   prüfen.
4. Danach einen kleinen, testbaren Algorithmuskern aus einem externen Projekt
   übernehmen oder adaptieren.
5. Eigenen Algorithmuscode nur schreiben, wenn keine geeignete Quelle passt.
   Die konkrete Ablehnung der geprüften Quellen wird dokumentiert.

Eigener AVAJ-Code soll sich primär auf Adapter, Topic-/Frame-Verträge,
Parameter, Tests, Orchestrierung und projektspezifische Logik beschränken.

Jede externe Quelle erhält vor Übernahme einen Eintrag in `THIRD_PARTY.md` mit:

- Repository-URL und unveränderlichem Commit SHA oder Release-Tag;
- Lizenz und erforderlicher Attribution;
- übernommene Dateien/Algorithmen und lokale Änderungen;
- ROS-Distribution, Architektur und Abhängigkeiten;
- Eingabe, Ausgabe und AVAJ-Adaptergrenze;
- ausgeführtem Build-/Testnachweis;
- Entscheidung `USE`, `ADAPT`, `REFERENCE ONLY` oder `REJECT` samt Grund.

Keine Laufzeit-Downloads. Keine unversionierten Kopien. Kein Import eines
kompletten VESC-, Safety- oder Fahrzeugstacks. Lizenzunklare Repositories sind
`REJECT`, nicht „vorläufig übernommen“.

### Bevorzugte Kandidaten

| Bedarf | Zuerst prüfen | Geplante Nutzung |
|---|---|---|
| Kamerakalibrierung/-entzerrung | ROS `camera_calibration`, `image_proc` | direkt verwenden |
| Mapping/Lokalisierung | vorhandenes `slam_toolbox`; alternativ Nav2 `map_server` + AMCL | vorhandenes Paket konfigurieren, nicht nachbauen |
| Bahnfolger | Nav2 Regulated Pure Pursuit (RPP) | installierten Jazzy-Stand hinter Ackermann-Adapter testen |
| einfacher F1TENTH-Bahnfolger | `tum-phoenix/f1tenth_ros`, `f1tenth-dev/pure_pursuit` | Mathematik/Tests als Referenz; keine fremde Fahrzeugkette übernehmen |
| Rennlinie | TUMFTM `global_racetrajectory_optimization` und `trajectory_planning_helpers` | offline, erst nach stabiler Mittellinie |
| Bildverarbeitung | ROS `vision_opencv`/OpenCV | direkt verwenden |
| Simulation | Gazebo Harmonic SDF und `ros_gz` | vorhandene Welt/Bridge erweitern |

Wichtige Upstreams:

- <https://docs.ros.org/en/jazzy/p/image_pipeline/>
- <https://github.com/ros-navigation/navigation2/tree/main/nav2_regulated_pure_pursuit_controller>
- <https://github.com/tum-phoenix/f1tenth_ros>
- <https://github.com/f1tenth-dev/pure_pursuit>
- <https://github.com/TUMFTM/global_racetrajectory_optimization>
- <https://github.com/TUMFTM/trajectory_planning_helpers>
- <https://gazebosim.org/docs/harmonic/sdf_worlds/>
- <https://gazebosim.org/docs/harmonic/sensors/>

Ein Link auf `main` genügt nur zur Vorauswahl. AP-R01 muss vor Codeübernahme
einen konkreten Commit und die Lizenz festhalten.

## 4. Topic- und Zuständigkeitsvertrag

### Vorhandene Eingänge für lokale Algorithmen

| Topic | Typ | Regel |
|---|---|---|
| `/scan` | `sensor_msgs/msg/LaserScan` | verarbeiteter Scan; kein `/sim/*` abonnieren |
| `/camera/image_raw` | `sensor_msgs/msg/Image` | nur mit passender `CameraInfo` räumlich auswerten |
| `/camera/camera_info` | `sensor_msgs/msg/CameraInfo` | Kalibrierstatus prüfen |
| `/imu/data` | `sensor_msgs/msg/Imu` | nur bei dokumentierter Nutzung |
| `/odometry/filtered` | `nav_msgs/msg/Odometry` | lokale Schätzung; keine Ground Truth |
| `/map` | `nav_msgs/msg/OccupancyGrid` | genau eine aktive globale Quelle |
| `/tf`, `/tf_static` | TF2 | `map -> odom -> base_link -> sensor` |
| `/clock` | `rosgraph_msgs/msg/Clock` | alle Simulationsnodes verwenden `use_sim_time` |
| `/planning/racing_line` | `nav_msgs/msg/Path` | bestehender Baseline-Vertrag |

### Einziger erlaubter Fahrbefehlsausgang neuer Nodes

| Topic | Typ | Einheit/Frame | Eigentümer |
|---|---|---|---|
| `/control/autonomous_ackermann_cmd` | `ackermann_msgs/msg/AckermannDriveStamped` | Geschwindigkeit m/s, Lenkwinkel rad, `base_link` | genau ein aktivierter autonomer Controller |

### Zulässige neue interne Topics

Neue Topics sind nur anzulegen, wenn sie einen echten Komponentenvertrag
bilden. Bevorzugte Namen:

| Topic | Standardtyp, wenn ausreichend | Zweck |
|---|---|---|
| `/planning/reference_path` | `nav_msgs/msg/Path` | geometrische Centerline/Baseline |
| `/planning/local_path` | `nav_msgs/msg/Path` | lokaler Gate-/Slalompfad |
| `/perception/pylons` | neue typed Message nur bei Bedarf | Beobachtungen, keine Fahrbefehle |
| `/racing/status` | `diagnostic_msgs` oder kleine typed Message | Controller-/Lap-Zustand |
| `/pylon/status` | `diagnostic_msgs` oder kleine typed Message | Pylon-Zustand |
| `/evaluation/lap_metrics` | Diagnose/typed Message | reine Auswertung |

`nav_msgs/Path` bleibt die erste Wahl für reine Geometrie. Erst wenn
Geschwindigkeit, Krümmung und Beschleunigung pro Punkt wirklich benötigt
werden, darf AP-I01 einen kleinen `Trajectory`-Vertrag ergänzen.

## 5. Parallelitätsmodell

Parallele Arbeit erfolgt in getrennten Git-Worktrees/Branches oder mit einer
vorab exklusiv zugewiesenen Dateiliste. Im bestehenden schmutzigen Worktree
arbeiten nicht mehrere Agenten gleichzeitig an denselben Dateien.

Kein Fachpaket ändert direkt `CURRENT_STATE.md`. Es schreibt seine Übergabe in
`docs/work_packages/AP-<ID>.md`. Nur AP-I01 führt nach dem Merge die
Statusdokumentation zusammen. Dadurch wird `CURRENT_STATE.md` nicht zur
ständigen Merge-Konfliktfläche.

### Exklusive Eigentümer

| Fläche | Eigentümer während einer parallelen Welle |
|---|---|
| `rc_car_interfaces/msg/*` | AP-I01 |
| `docs/ros_graph.md` | AP-I01 |
| `workspace/simulation/worlds/*` und Modelle | jeweils ein Simulationspaket |
| `avaj_slam` Launch/Config/URDF | AP-S01 bzw. danach AP-L01 |
| neuer Racing-Controller | AP-C01 |
| neuer Pylon-Stack | AP-P02/AP-P03 mit getrennten Unterpaketen |
| gemeinsame Bringup-Launches | AP-I01 |

### Ausführungswellen

```text
Welle 0 (kurz, Verträge)
  AP-B01 Baseline/Testgrenze
  AP-R01 Reuse-Entscheidung
  AP-M01 interne Message-/Topic-Verträge

Welle 1 (parallel)
  AP-T01 Testharness        AP-S01 Gazebo/TF/SLAM
  AP-D01 Pfaddaten/Importer AP-P01 Pylonenwelt

Welle 2 (parallel, Verträge aus Welle 0/1 eingefroren)
  AP-L01 Lokalisierung      AP-C01 Bahnfolger-Benchmark
  AP-G01 Track/Centerline   AP-P02 Pylon-Perception

Welle 3 (parallel)
  AP-V01 Speedprofil        AP-R02 Racing-Supervisor
  AP-P03 Gate/Slalom-Planung

Welle 4 (Integrationsbesitz exklusiv)
  AP-I01 Topic-/Launch-Integration

Welle 5
  AP-E01 End-to-End- und Fault-Abnahme
```

Harte Abhängigkeiten:

```text
AP-B01 -> alle
AP-R01 -> AP-C01, AP-G01, AP-P02, AP-P03
AP-M01 -> AP-D01, AP-C01, AP-P02, AP-P03
AP-S01 -> AP-L01, AP-P01, AP-E01
AP-D01 -> AP-C01, AP-G01
AP-L01 + AP-C01 + AP-G01 -> AP-R02
AP-P02 -> AP-P03
AP-C01 + AP-P02 + AP-P03 -> PYLON-Integration
AP-V01 + AP-R02 + AP-P03 -> AP-I01 -> AP-E01
```

Für das erste belastbare Ergebnis ist der Racing-Pfad prioritär:

```text
AP-B01/R01/M01 -> AP-T01/S01/D01 -> AP-L01/C01/G01
-> AP-V01/R02 -> AP-I01 -> AP-E01
```

AP-P01/P02/P03 sind ein optionaler, parallel vorbereitbarer Pylon-Pfad. Sie
dürfen den Abschluss der ersten simulierten Racing-Runde nicht blockieren.

## 6. Gemeinsame Definition of Done

Ein Arbeitspaket ist nur abgeschlossen, wenn:

1. `AGENTS.md`, `CURRENT_STATE.md`, `AGENTS (1).md` und die betroffenen Dateien
   gelesen wurden; die fehlende Development-Plan-Datei wird nicht vorausgesetzt.
2. `git status --short` und `git diff --stat` vor und nach der Arbeit erfasst
   wurden; fremde Änderungen blieben erhalten.
3. Die Reuse-Recherche und Entscheidung nachvollziehbar ist.
4. Der Umfang auf lokale Software/Simulation begrenzt blieb.
5. Neue Controller nur `/control/autonomous_ackermann_cmd` publizieren.
6. Tests eine eigene `ROS_DOMAIN_ID` verwenden und keine realen Geräte öffnen.
7. Unit-, Lint- und relevante Integrationstests bestanden oder konkret
   klassifiziert sind.
8. Topics jeweils Typ, Publisher, Subscriber, Einheit, Frame, Rate, Timeout
   und Fehlerverhalten dokumentieren.
9. Ground Truth nur in der Auswertung vorkommt.
10. Eine Übergabe unter `docs/work_packages/` Quellen, Commit, Dateien,
    Befehle, Ergebnisse, Einschränkungen und Folgearbeiten enthält.

Globale Invarianten für jede Abnahme:

- genau ein Publisher auf `/drive_commands`: der vorhandene `drive_commander`;
- höchstens ein aktiver Publisher für `map -> odom`;
- höchstens ein aktiver Publisher auf
  `/control/autonomous_ackermann_cmd`;
- bei stale/ungültigem Pose-, Path- oder Sensorinput wird neutraler SI-Befehl
  publiziert oder die Publikation endet innerhalb des vereinbarten Timeouts;
- kein Test beansprucht Hardware-, ESP- oder Realfahrzeugvalidierung.

## 7. Arbeitspakete

### AP-B01 – Baseline und unveränderliche Grenzen

**Ziel:** Den tatsächlichen lokalen Ausgangszustand und die verbotenen Flächen
für alle Folgepakete maschinenlesbar festhalten.

**Änderungen:** Nur `docs/work_packages/AP-B01.md` und optional ein
read-only Prüfskript unter `tools/`; kein Produktionscode.

**Auftrag an Codex:**

> Lies die Repository-Anweisungen und prüfe Branch, HEAD, Worktree,
> Paketbestand, vorhandene Topics und Testregistrierung. Verifiziere besonders
> den einzigen `/drive_commands`-Publisher und den Ackermann-Ausgang des
> `control_center`. Greife auf keine Geräte zu. Dokumentiere exakte erlaubte
> und verbotene Dateien für die nächste parallele Welle.

**Abnahme:** Reproduzierbarer Baselinebericht; keine Arbeitsbaumänderung außer
der Übergabe; aktuelle Abweichungen sind benannt.

### AP-R01 – Reuse- und Lizenzentscheidung

**Ziel:** Für Bahnfolger, Lokalisierung, Rennlinie und Pylonpfad konkrete
Upstreams auswählen, bevor Implementierung beginnt.

**Änderungen:** `THIRD_PARTY.md`, `docs/work_packages/AP-R01.md`; höchstens
kleine isolierte Probes unter `tools/upstream_probes/`.

**Auftrag an Codex:**

> Prüfe zuerst installierte Jazzy-Pakete. Untersuche danach Nav2 RPP,
> `tum-phoenix/f1tenth_ros`, `f1tenth-dev/pure_pursuit`, TUMFTM
> `global_racetrajectory_optimization`/`trajectory_planning_helpers` und für
> den Pylonpfad offizielle ROS/OpenCV-Komponenten. Halte Commit, Lizenz,
> Maintenance, ROS-/Python-Version, ARM64-Relevanz, API und Adapteraufwand fest.
> Klone nur zur Prüfung außerhalb von `workspace/src`. Importiere noch keinen
> Gesamtstack. Liefere pro Bedarf eine klare USE/ADAPT/REFERENCE/REJECT-
> Entscheidung.

**Abnahme:** Keine unbestimmten GitHub-Empfehlungen; jeder gewählte Baustein
ist reproduzierbar gepinnt und lizenzseitig nachvollziehbar.

### AP-T01 – Deterministisches lokales Testharness

**Ziel:** Wiederholbare Tests ohne fremde DDS-Teilnehmer oder Hardware.

**Änderungen:** Test-/CI-Dateien und `tools/`; keine Fahrlogik.

**Auftrag an Codex:**

> Erstelle wiederverwendbare Teststarts mit eigener `ROS_DOMAIN_ID`,
> `use_sim_time`, Zeitlimit und sauberem Shutdown. Registriere bereits
> vorhandene Tests korrekt. Ergänze Graphassertions für die drei globalen
> Publisher-Invarianten. Hardwaredienste und USB-Bridge werden nicht gestartet.

**Abnahme:** Build/Test/Test-result sind reproduzierbar; ein absichtlich
zweiter Publisher lässt den Graphtest scheitern; Ctrl-C hinterlässt keinen
unklassifizierten Fehler.

### AP-M01 – Interne Message- und Topic-Verträge einfrieren

**Ziel:** Vor paralleler Implementierung die kleinsten stabilen Verträge für
Pfad, optionale Trajektorie, Pylonbeobachtung und Status festlegen.

**Änderungen:** Zunächst nur ein Interface-Entscheidungsdokument. Falls ein
Standardtyp nachweislich nicht genügt, besitzt dieses Paket exklusiv
`rc_car_interfaces/msg/*`, dessen Builddateien und die zugehörigen
Interface-Tests.

**Auftrag an Codex:**

> Prüfe zuerst `nav_msgs/Path`, `ackermann_msgs/AckermannDriveStamped`,
> `diagnostic_msgs` und – falls installiert – `vision_msgs`. Verwende einen
> Standardtyp, wenn Timestamp, Frame und Semantik ausreichen. Definiere nur
> fehlende Domäneninformationen neu; keine generischen JSON-/String-Verträge.
> Halte Topic, Typ, Publisher, Subscriber, Einheit, Frame, QoS, Rate, Timeout
> und Fehlerverhalten fest. Stimme die Verträge mit AP-D01, AP-C01, AP-P02 und
> AP-P03 ab, bevor diese Pakete Code schreiben.

**Abnahme:** Folgepakete können gegen unveränderte Verträge testen; keine zwei
Messages beschreiben denselben Sachverhalt; alle neuen Interfaces bauen und
haben Import-/Grenzwerttests.

### AP-S01 – Gazebo-, TF- und SLAM-Basis stabilisieren

**Ziel:** Ein rein lokales Profil mit kanonischen Topics, Simzeit,
`/odometry/filtered`, TF und stabiler `/map`-Erzeugung.

**Änderungen:** `workspace/simulation`, `avaj_slam` und zugehörige Tests;
keine Controller- oder ESP-Dateien.

**Auftrag an Codex:**

> Reproduziere die dokumentierten SLAM-Queue-Drops und Shutdown-Ausnahmen.
> Prüfe zuerst Zeitstempel, TF-Verfügbarkeit, QoS und `scan_queue_size`, statt
> nur Queues zu vergrößern. Nutze Gazebo-Ground-Truth ausschließlich für
> Fehlermetriken. Liefere einen headless Start und kontrollierten Shutdown.

**Abnahme:** `/scan`, `/odometry/filtered`, TF und `/map` sind über einen
definierten Lauf stabil; genau ein `map -> odom`; Ursache der Drops behoben
oder mit belastbarer Reproduktion isoliert.

### AP-D01 – Referenzpfadformat und Offline-Importer

**Ziel:** Einen validierten, geschlossenen Baselinepfad als
`nav_msgs/msg/Path` auf `/planning/reference_path` und kompatibel auf
`/planning/racing_line` bereitstellen.

**Änderungen:** Neues kleines Paket, bevorzugt `avaj_racing`, mit Importer,
Validator, Beispieldaten und Tests.

**Auftrag an Codex:**

> Prüfe vorhandene F1TENTH-/TUMFTM-Dateiformate. Schreibe nur den AVAJ-Adapter:
> CSV/Upstream-Ausgabe laden, endliche Werte, Frame, monotone Bogenlänge,
> Mindestpunktabstand, Schleifenschluss und Fahrtrichtung validieren. Noch
> keine automatische Trackextraktion und kein Controller.

**Abnahme:** Gültiger Pfad wird latched publiziert; offene, selbstschneidende,
zu kurze, NaN-haltige oder falsch gerahmte Daten werden mit klarem Grund
abgelehnt.

### AP-P01 – Reproduzierbare Pylonen-, Tor- und Slalomwelten

**Ziel:** Optionale Gazebo-Szenarien für die spätere lokale PYLON-Kette.

**Änderungen:** Separate SDF-Welten/Modelle; keine gemeinsame Racing-Welt
umbauen, wenn sie parallel AP-S01 gehört.

**Auftrag an Codex:**

> Nutze Gazebo-SDF-Modelle und offizielle Beispiele. Erzeuge deterministische
> Szenen für ein Tor, einen einfachen Slalom, Verdeckung und ein ähnlich
> aussehendes Nicht-Pylonenobjekt. Ground-Truth-Positionen werden nur als
> Evaluationsdatei bereitgestellt, nicht als ROS-Eingang der Fahrkette.

**Abnahme:** Welten starten headless; Kamera und LiDAR sehen die Objekte;
Geometrie, Farben und Seeds sind dokumentiert.

### AP-L01 – Gespeicherte lokale Kartenlokalisierung

**Ziel:** Nach Map-Save und Neustart eine geschätzte Pose im `map`-Frame
bereitstellen, ohne parallele globale TF-Publisher.

**Änderungen:** `avaj_slam` Localization-Launch/Config und Tests.

**Auftrag an Codex:**

> Verwende zuerst den installierten `slam_toolbox`-Localization-Modus; vergleiche
> ihn nur bei messbarem Bedarf mit Nav2 `map_server` + AMCL. Implementiere
> keinen eigenen Lokalisierer. Trenne `MAPPING`, `LOCALIZATION` und `DISABLED`
> durch Launch/Lifecycle. Der Controller erhält Pose über TF plus
> `/odometry/filtered`, niemals aus Gazebo Ground Truth.

**Abnahme:** Save -> Shutdown -> Localization ist reproduzierbar; genau ein
`map -> odom`; definierter Poseverlust führt zu sichtbarem Fehlerstatus.

### AP-C01 – Reuse-Benchmark für Ackermann-Bahnfolger

**Ziel:** Den kleinsten geeigneten wiederverwendeten Bahnfolger auswählen und
an den AVAJ-Ackermann-Ausgang anbinden.

**Änderungen:** Neues Controller-Unterpaket; nicht `drive_commander`, Adapter,
USB oder ESP.

**Auftrag an Codex:**

> Vergleiche mindestens den installierten Nav2 Regulated Pure Pursuit mit dem
> in AP-R01 gewählten F1TENTH-Pure-Pursuit-Kern. Bevorzuge direkte
> Paketnutzung. Falls RPP `Twist` liefert, kapsle die kinematische Umsetzung
> `steering = atan(wheelbase * angular_z / linear_x)` mit sauberem Verhalten
> nahe Null, Vorzeichen-, Sättigungs- und Lenkratenprüfung. Publiziere nur
> `/control/autonomous_ackermann_cmd`. Schreibe keinen neuen Pure-Pursuit-
> Algorithmus, solange ein Upstream die Anforderungen erfüllt.

**Abnahme:** Gerade, Kreis, S-Kurve, Reverse-Ablehnung, stale Pose/Path und
Framefehler sind getestet; ausgewählter Upstream/Commit ist dokumentiert;
kein zweiter finaler Publisher.

### AP-G01 – Trackgrenzen und Centerline

**Ziel:** Aus einer Simulationskarte einen geschlossenen, validierten
Centerline-Pfad erzeugen.

**Änderungen:** Offline-Tooling im Racing-Paket; kein hochfrequenter Node.

**Auftrag an Codex:**

> Prüfe zuerst TUMFTM/F1TENTH-Werkzeuge und etablierte Bibliotheken für
> Occupancy-Grid-Verarbeitung, Distanztransform und Skeletonisierung. Nutze
> vorhandene Bibliotheksfunktionen statt eigener Bildverarbeitung. Liefere
> Grenzen, Centerline, Breiten und Unsicherheits-/Fehlerflags. Eine manuell
> geprüfte Centerline bleibt der zulässige Baseline-Fallback.

**Abnahme:** Geschlossenheit, Abstand zu Grenzen, Richtung, Sampling und
Selbstschnittfreiheit sind automatisiert geprüft; Ergebnisse sind in RViz
sichtbar; schlechte Maps werden nicht still akzeptiert.

### AP-P02 – Pylonbeobachtung mit austauschbarem Backend

**Ziel:** Aus simulierten Kamerabildern typisierte Pylonbeobachtungen erzeugen.

**Änderungen:** Eigenes Wahrnehmungsunterpaket gegen den von AP-M01
eingefrorenen Vertrag; keine Änderungen an `rc_car_interfaces` und keine
Fahrbefehle.

**Auftrag an Codex:**

> Nutze `image_proc` und OpenCV. Prüfe AP-R01 auf einen geeigneten gepflegten
> Detektor. Für die definierte Gazebo-Welt ist ein HSV-/Geometrie-Backend als
> testbarer Baseline-Adapter zulässig; behaupte keine Realübertragbarkeit.
> Ausgabe enthält Timestamp, Frame, Klasse/Farbe, Bounding Box, Konfidenz,
> Peilwinkel und Unsicherheit. Reichweite nur mit klar benannter Quelle.

**Abnahme:** Replay-Tests für Treffer, False Positive, leeres/stales Bild und
Verdeckung; gemessene Latenz/FPS; keinerlei Publikation auf Control-Topics.

### AP-V01 – Konservatives Geschwindigkeitsprofil

**Ziel:** Aus Centerline/Rennlinie ein begrenztes Solltempo erzeugen.

**Änderungen:** Offline- oder langsamer Planner im Racing-Paket.

**Auftrag an Codex:**

> Nutze zuerst die TUMFTM-Ausgabeformate und Helper. Beginne mit konstanter,
> niedriger Simulationsgeschwindigkeit; ergänze erst danach ein
> krümmungsbasiertes Profil mit konfigurierbarer Querbeschleunigungs-,
> Beschleunigungs- und Bremsgrenze. Minimum-Time-Optimierung ist kein MVP.

**Abnahme:** Einheiten, Grenzen und Übergänge sind getestet; Änderungen der
Limits erfordern keine neue Karte; Profil bleibt innerhalb aller Parameter.

### AP-R02 – Racing-Supervisor und Rundenauswertung

**Ziel:** `IDLE -> READY -> RACING -> FINISHED/FAULT` beobachtbar steuern,
ohne Hardwaremodus oder ESP-Ownership nachzubauen.

**Änderungen:** Racing-Supervisor und Evaluator; keine Änderungen am
Systemmodus/ESP-Pfad.

**Auftrag an Codex:**

> Aktiviere genau einen Racing-Controller nur bei frischer Pose, gültigem
> geschlossenem Pfad und gültigen Parametern. Erkenne Startlinienüberquerung
> mit Richtung und Mindestfortschritt, damit Stillstand/Jitter keine Runde
> zählt. Stoppe bei stale Pose/Path, TF-Fehler oder Controllerausfall. Nutze
> Ground Truth ausschließlich für CTE-/Lap-Evaluation.

**Abnahme:** Eine Runde wird genau einmal gezählt; Rückwärtskreuzen/Jitter
zählt nicht; Fehler führen innerhalb des festgelegten Timeouts zu neutralem
Ackermann-Befehl oder Controller-Deaktivierung.

### AP-P03 – Gate-/Slalominterpretation und lokaler Pfad

**Ziel:** Aus Pylonbeobachtungen einen lokalen `nav_msgs/Path` erzeugen, der
vom gemeinsamen Bahnfolger gefahren werden kann.

**Änderungen:** Eigenes Pylon-Planungsunterpaket; keine Wahrnehmungs- oder
Downstream-Command-Dateien.

**Auftrag an Codex:**

> Prüfe zuerst den in AP-R01 gewählten Cone-Planning-Upstream. Ein Gate wird
> aus zwei kompatiblen Pylonen gebildet; der Pfad führt durch den Mittelpunkt
> zu einem Ziel dahinter. Für den definierten Slalom ist eine kleine explizite
> Zustandsmaschine zulässig. Bei Ambiguität, Verlust oder hoher Unsicherheit
> wird kein Bewegungsziel erneuert. Ausgabe ist ausschließlich
> `/planning/local_path`; der gemeinsame Controller übernimmt die Regelung.

**Abnahme:** Gate, Slalom, Verdeckung, falsche Klasse, vertauschte Reihenfolge
und stale detections sind getestet; Pixelwerte gelangen nie direkt in die
Lenkregelung.

### AP-I01 – Verträge, Launches und Konfliktintegration

**Ziel:** Die getrennt entwickelten Pakete ohne Topic-/Publisherkonflikt in
reproduzierbare `racing_sim`- und optionale `pylon_sim`-Profile integrieren.

**Änderungen:** Zusammenführung der von AP-M01 festgelegten Interfaces,
`docs/ros_graph.md`, Bringup-Launches und Status. Dieses Paket besitzt diese
Integrationsflächen exklusiv.

**Auftrag an Codex:**

> Lies alle AP-Übergaben. Übernimm nur bestandene Verträge. Verwende Standard-
> Messages, sofern ausreichend; führe neue typed Messages zentral ein. Sorge
> dafür, dass Racing und Pylon getrennte Programme bleiben und nie gleichzeitig
> `/control/autonomous_ackermann_cmd` publizieren. Erzeuge ein eigenes
> Simulations-Bringup aus den vorhandenen lokalen Nodes, das `usb_bridge`
> weder startet noch benötigt; kopiere dabei keine Fahrlogik. Starte USB/ESP
> nicht. Prüfe
> alle Publisher, Frames, QoS, Simzeit und Shutdown. Aktualisiere erst jetzt
> `CURRENT_STATE.md` konfliktfrei mit den tatsächlich integrierten Ergebnissen.

**Abnahme:** Zwei getrennte Startprofile; je Profil höchstens ein Controller;
kein ESP-/USB-Zugriff; Graphdokumentation entspricht dem beobachteten Graphen.

### AP-E01 – End-to-End-, Replay- und Fault-Abnahme

**Ziel:** Reproduzierbar nachweisen, was lokal wirklich funktioniert.

**Änderungen:** Tests, Szenarien, Rosbagprofile und Ergebnisberichte; keine
neuen Produktionsalgorithmen.

**Auftrag an Codex:**

> Führe isolierte, wiederholte Gazebo- und Replay-Läufe aus. Racing:
> Mapping/Save/Localization/Path/Controller/Lap. Optional PYLON:
> Bild/Detection/LocalPath/Controller/Gate und definierter Slalom. Injiziere
> stale Scan, Pose, Path, Kamera, TF-Ausfall, Controllerstop und einen zweiten
> Publisher. Zeichne Inputs, Zwischenoutputs, Ackermann-Befehl, TF und Metriken
> auf. Greife auf keine Hardware zu und starte keine USB-Bridge.

**Abnahme:** Mindestens drei deterministische Läufe pro freigegebenem Szenario;
Erfolgsquote, Querfehler, Geschwindigkeit, Laufzeit/Latenz und Stopzeit sind
dokumentiert; Fehlschläge bleiben sichtbar; Abschluss heißt ausdrücklich
„software-/simulationsvalidiert“, niemals „fahrzeugvalidiert“.

## 8. Empfohlene Codex-Auftragsvorlage

```text
Bearbeite ausschließlich AP-<ID> aus Codex_Arbeitspaket.md.

Lies zuerst AGENTS.md, CURRENT_STATE.md und AGENTS (1).md sowie alle im Paket
genannten Dateien. Prüfe git status --short und git diff --stat. Erhalte alle
fremden Änderungen. Arbeite nur lokal; kein ESP, USB, I2C, reale Sensoren oder
angetriebenes Fahrzeug.

Führe vor eigener Implementierung das Reuse-Gate aus. Verwende bevorzugt den
in AP-R01 festgelegten Upstream und dokumentiere URL, Commit, Lizenz und lokale
Anpassungen. Neuer Fahralgorithmuscode ist nur nach begründeter Ablehnung der
geprüften Quellen erlaubt.

Halte dich an die exklusive Dateiliste des Pakets. Neue Fahrcontroller dürfen
nur ackermann_msgs/msg/AckermannDriveStamped auf
/control/autonomous_ackermann_cmd publizieren. Nie /drive_commands,
/control/autonomous_cmd oder /cmd_vel direkt publizieren und die vorhandene
Downstream-Kette nicht ändern.

Teste in einer isolierten ROS_DOMAIN_ID mit use_sim_time. Ground Truth nur zur
Auswertung. Schreibe die Übergabe nach docs/work_packages/AP-<ID>.md; ändere
CURRENT_STATE.md nur in AP-I01. Melde implementiert, getestet und simuliert
getrennt. Stoppe bei einer Scope-, Eigentums- oder Sicherheitsverletzung.
```

## 9. Bewusst entfernte Pakete des alten Plans

Folgende Themen sind nicht „später in dieser Serie“, sondern außerhalb des
aktuellen Auftrags:

- ESP-Firmware und `SAFE/MANUAL/JETSON`-Ownership;
- bidirektionaler ESP-Transport, ACK-/Actuator-/Encoder-Feedback;
- reale Encoder-Odometrie und realer EKF;
- Änderungen am hardwarebezogenen Safety-Watchdog;
- physischer Not-Aus, Bench-, HIL-, Lifted- und Bodenfahrtests;
- reale Fahrzeugfreigabe und Racing-Speed-Optimierung.

Sie dürfen nur durch einen neuen, ausdrücklichen Benutzerauftrag wieder in
einen Plan aufgenommen werden.
