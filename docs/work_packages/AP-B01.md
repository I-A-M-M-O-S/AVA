# AP-B01 – Baseline und unveränderliche Grenzen

```yaml
work_package: AP-B01
status: complete
baseline_date: 2026-09-02
environment: local_ros_jazzy_container
branch: orin
head: 7df2f36f1a8d00ff6080dbec1ae1263aa5948f2b
working_tree_clean_before: false
working_tree_clean_after: false
production_code_changed: false
hardware_accessed: false
usb_bridge_started: false
real_vehicle_validation: false
```

## Umfang und Sicherheitsgrenze

Dieses Paket erfasst nur den vorhandenen lokalen Stand. Es hat keinen
Produktionscode, keine Launchdatei, keinen Interfacevertrag und keine
Hardwarekonfiguration geändert. Die einzige durch AP-B01 neu angelegte Datei ist
dieser Bericht.

Nicht ausgeführt wurden Zugriffe auf USB, I²C, Kamera, LiDAR, ESP32 oder
Aktoren. Die USB-Bridge, Gazebo und reale Sensordienste wurden nicht gestartet.
Es gab keinen aufgebockten, angetriebenen oder autonomen Realfahrzeugtest.

Die in `AGENTS.md` verlangte Datei
`DEVELOPMENT_PLAN.md — AVAJ RC-Car.md` fehlt sowohl im Arbeitsbaum als auch in
`HEAD`. Das stimmt mit `Codex_Arbeitspaket.md` überein und ist keine durch
AP-B01 verursachte Abweichung.

## Repository-Baseline

| Merkmal | Beobachtung |
|---|---|
| Repository | `/home/avaj/ros2_jazzy` |
| Aktiver Quellbaum | `workspace/src` |
| Ältere, nicht aktive Kopie | `ros2_jazzy/workspace` |
| Branch | `orin` |
| HEAD | `7df2f36f1a8d00ff6080dbec1ae1263aa5948f2b` |
| Arbeitsbaum | bereits vor AP-B01 umfangreich geändert und untracked |
| AP-B01-Änderung | nur `docs/work_packages/AP-B01.md` |

Vor Beginn vorhandene Änderungen wurden weder verworfen noch überschrieben.
Insbesondere gehören die Ackermann-Adapterarbeit, die Verlagerung der
`control_center`-Quelle nach `src/control_center.cpp`, Launch-Änderungen,
Dokumentationsänderungen und die lokalen Vendor-Repositories zum vorgefundenen
Arbeitsstand. Der vollständige Status ist mit folgendem Befehl reproduzierbar:

```bash
cd /home/avaj/ros2_jazzy
git status --short
git diff --stat
```

## Paketbestand

`colcon list` im ROS-Jazzy-Container meldet acht Pakete:

| Paket | Pfad | Buildtyp | Einordnung |
|---|---|---|---|
| `avaj_car_control` | `workspace/src/avaj_car_control` | `ament_cmake` | eigener Downstream-Command-Stack |
| `avaj_sensor_processing` | `workspace/src/avaj_sensor_processing` | `ament_python` | eigene Sensorvorverarbeitung |
| `avaj_slam` | `workspace/src/avaj_slam` | `ament_cmake` | eigenes SLAM-/TF-Paket |
| `control_center` | `workspace/src/controll center` | `ament_cmake` | eigener Simulations-Baselinecontroller |
| `rc_car_interfaces` | `workspace/src/rc_car_interfaces` | `ament_cmake` | eigene Interfaces |
| `rc_car_usb_bridge` | `workspace/src/rc_car_usb_bridge` | `ament_python` | eigener, für Folgepakete gesperrter USB-Pfad |
| `bno08x_driver` | `workspace/src/bno08x_driver` | `ament_cmake` | Vendor-Repository mit lokaler Änderung |
| `ldlidar_stl_ros2` | `workspace/src/ldlidar_stl_ros2` | `ament_cmake` | Vendor-Repository mit lokaler Änderung |

Die sechs eigenen Pakete
`rc_car_interfaces`, `rc_car_usb_bridge`, `avaj_sensor_processing`,
`avaj_car_control`, `control_center` und `avaj_slam` bauen zusammen erfolgreich.

## Verifizierte Topic- und Publisher-Baseline

Die Laufzeitprüfung startete unter `ROS_DOMAIN_ID=203` ausschließlich
`drive_commander` und `control_center` mit `logic_enabled:=false`. Damit wurden
keine Sensor-, Simulations-, USB- oder Hardwareprozesse benötigt.

| Topic | Typ | Publisher | Subscriber im vollständigen Bestand | Einheit/Frame | Rate und Fehlerverhalten |
|---|---|---|---|---|---|
| `/control/autonomous_ackermann_cmd` | `ackermann_msgs/msg/AckermannDriveStamped` | `control_center`, beobachtet genau 1 | `ackermann_to_drive_request` | `speed` m/s, `steering_angle` rad, `base_link` | Controller-Timer 20 Hz, aber nur im Modus `AUTONOMOUS`; neutral bei deaktivierter Logik, stale Scan/Odometrie, fehlender Freigabe, Fahrzeugfehler oder Hindernis |
| `/control/autonomous_cmd` | `rc_car_interfaces/msg/DriveRequest` | `ackermann_to_drive_request` | `drive_commander`, `safety_watchdog` | normalisiert `-100..100`, kein Frame | ereignisgetrieben; nach 0,3 s Ackermann-Timeout einmal neutral |
| `/drive_commands` | `rc_car_interfaces/msg/DriveCommand` | `drive_commander`, beobachtet genau 1 | `drive_command_to_twist`; `usb_bridge` nur in nicht für AP-B01 gestarteten Profilen | normalisiert `-100..100`, kein Frame | standardmäßig 50 Hz; stale/ungültige/inaktive Quelle oder fehlende Freigabe ergibt neutral/deaktiviert |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | vorhandener `drive_command_to_twist` | Gazebo-Ackermann-Backend | m/s und rad/s, kein Header | reine bestehende Simulationsumsetzung hinter `/drive_commands`; kein zulässiger Ausgang neuer Algorithmen |

Beobachteter isolierter Graph:

```yaml
drive_commands:
  type: rc_car_interfaces/msg/DriveCommand
  publisher_count: 1
  publishers: [/drive_commander]
autonomous_ackermann_cmd:
  type: ackermann_msgs/msg/AckermannDriveStamped
  publisher_count: 1
  publishers: [/control_center]
```

Der `control_center` abonniert außerdem `/scan`, `/odometry/filtered`, `/map`
und `/planning/racing_line`. Die Rennlinie wird derzeit nur auf Empfang und
Punktzahl beobachtet; sie geht nicht in die LIDAR-Gap-Fahrlogik ein. Damit ist
der vorhandene Knoten kein Bahnfolger.

Quellseitige Eigentümersuche bestätigt: Im aktiven eigenen Quellbaum erzeugt
nur `workspace/src/avaj_car_control/scripts/drive_commander` einen Publisher
für `/drive_commands`. `rc_car_usb_bridge` und `drive_command_to_twist`
abonnieren dieses Topic nur.

## Testregistrierung und Ergebnisse

| Paket | Registrierte Tests | Isoliertes Ergebnis |
|---|---:|---|
| `avaj_car_control` | 2 CTest/Pytest-Suites, 24 Pytest-Fälle | 18/18 `drive_commander`, 6/6 Ackermann-Adapter bestanden; `colcon test-result`: 26 Ergebnisdatensätze, 0 Fehler/Fehlschläge/Skips |
| `rc_car_usb_bridge` | Pytest über `ament_python`, 36 Fälle | 36/36 bestanden unter eigener Domain; nur PTY/synthetisch, kein reales USB-Gerät |
| `avaj_sensor_processing` | Pytest über `ament_python`, 2 Lintfälle | 2/2 bestanden |
| `rc_car_interfaces` | keine CTest-Tests registriert | `ctest -N`: 0 |
| `control_center` | keine CTest-Tests registriert | `ctest -N`: 0 |
| `avaj_slam` | keine CTest-Tests registriert | `ctest -N`: 0 |

Reproduzierbare Befehle:

```bash
docker compose run --rm -e ROS_DOMAIN_ID=201 jazzy bash -lc \
  'cd /workspace; source /opt/ros/jazzy/setup.bash; source install/setup.bash; \
   colcon test --packages-select avaj_car_control --event-handlers console_direct+; \
   colcon test-result --test-result-base build/avaj_car_control --verbose'

docker compose run --rm -e ROS_DOMAIN_ID=202 jazzy bash -lc \
  'cd /workspace; source /opt/ros/jazzy/setup.bash; source install/setup.bash; \
   colcon test --packages-select rc_car_usb_bridge --event-handlers console_direct+; \
   colcon test-result --test-result-base build/rc_car_usb_bridge --verbose'

docker compose run --rm -e ROS_DOMAIN_ID=204 jazzy bash -lc \
  'cd /workspace; source /opt/ros/jazzy/setup.bash; source install/setup.bash; \
   colcon test --packages-select avaj_sensor_processing --event-handlers console_direct+'
```

Die ROS-Domain muss in dieser Umgebung im gültigen DDS-Bereich liegen. Ein
Diagnoseversuch mit IDs 301–303 brach nur die ROS-Laufzeitfälle ohne XML ab;
die Wiederholung mit 201–204 bestand. Das ist kein Produktcodefehler, zeigt
aber, dass AP-T01 eine gültige, zentral vergebene Domain-ID erzwingen muss.

## Aktuelle Abweichungen

1. Der Arbeitsbaum ist nicht sauber; Folgepakete dürfen die bestehenden
   Änderungen nicht resetten, bereinigen oder überschreiben.
2. `DEVELOPMENT_PLAN.md — AVAJ RC-Car.md` fehlt.
3. Die Paket-Gesamttests erzwingen derzeit keine je Testlauf eindeutige,
   gültige `ROS_DOMAIN_ID`; die Isolation bleibt Aufruferverantwortung.
4. `rc_car_interfaces`, `control_center` und `avaj_slam` haben keine
   registrierten Tests.
5. `control_center` liest `/planning/racing_line`, folgt dem Pfad aber nicht.
6. Der vorhandene `autonomous_drive.launch.py` startet im sicheren Default zwar
   die USB-Bridge mit `dry_run=true`; AP-B01 hat diesen Launch bewusst nicht
   verwendet. Neue lokale Simulationsprofile dürfen die Bridge nicht starten.
7. Die Sicherheitsgrenze aus `CURRENT_STATE.md` bleibt unverändert: keine
   verifizierte ESP-Endautorität, kein unabhängiger ESP-Watchdog, keine reale
   Encoderodometrie und kein physischer Not-Aus. Nichts in AP-B01 erteilt eine
   Realfahrzeugfreigabe.

## Exklusive Dateigrenzen für Welle 1

Jedes Folgepaket darf zusätzlich genau seinen eigenen Bericht
`docs/work_packages/AP-<ID>.md` anlegen. Außerhalb der folgenden Pfade ist vor
einer Änderung eine neue, explizite Eigentumszuweisung erforderlich.

### AP-T01 – Testharness

Erlaubt:

```text
tools/**
.github/workflows/**
workspace/src/avaj_car_control/test/**
workspace/src/avaj_car_control/CMakeLists.txt       # nur Testregistrierung
workspace/src/avaj_car_control/package.xml          # nur Testabhängigkeiten
workspace/src/rc_car_usb_bridge/test/**
workspace/src/rc_car_usb_bridge/setup.py            # nur Testregistrierung
workspace/src/rc_car_usb_bridge/package.xml         # nur Testabhängigkeiten
workspace/src/avaj_sensor_processing/test/**
workspace/src/avaj_sensor_processing/setup.py       # nur Testregistrierung
workspace/src/avaj_sensor_processing/package.xml    # nur Testabhängigkeiten
docs/work_packages/AP-T01.md
```

Verboten sind Produktionsskripte, Nodes, Launches und alle AP-S01-/AP-D01-/
AP-P01-Flächen. Tests dürfen USB-Bridge und Hardwaredienste nicht starten.

### AP-S01 – Gazebo/TF/SLAM

Erlaubt:

```text
workspace/src/avaj_slam/**
workspace/simulation/bridge.yaml
workspace/simulation/start_gazebo.sh
workspace/simulation/models/avaj_car/**
workspace/simulation/worlds/jetson_test_track.sdf
docs/work_packages/AP-S01.md
```

AP-S01 besitzt diese Fläche in Welle 1 exklusiv. Tests und neue Hilfsdateien
müssen innerhalb dieser Pfade bleiben; Ground Truth darf nur Auswertung sein.

### AP-D01 – Pfaddaten/Importer

Erlaubt:

```text
workspace/src/avaj_racing/**                       # neues Paket, nur Importer/Validator/Beispieldaten/Tests
docs/work_packages/AP-D01.md
```

AP-D01 darf `/planning/reference_path` und kompatibel
`/planning/racing_line` als `nav_msgs/msg/Path` bereitstellen, aber keinen
Controller oder automatische Trackextraktion einführen.

### AP-P01 – separate Pylonenwelten

Erlaubt:

```text
workspace/simulation/worlds/pylon_*.sdf
workspace/simulation/models/pylon*/**
workspace/simulation/models/cone*/**
workspace/simulation/evaluation/pylon*/**
docs/work_packages/AP-P01.md
```

AP-P01 darf weder `jetson_test_track.sdf` noch das bestehende Fahrzeugmodell
`workspace/simulation/models/avaj_car/**` ändern; diese gehören parallel
AP-S01. Neue Modellnamen müssen mit `pylon` oder `cone` beginnen, damit die
Eigentumsgrenze maschinell prüfbar bleibt.

## Für alle Folgepakete gesperrte Flächen

```yaml
forbidden_paths:
  - workspace/src/rc_car_usb_bridge/**
  - docs/esp_feedback_protocol.md
  - workspace/src/rc_car_interfaces/msg/**
  - workspace/src/rc_car_interfaces/CMakeLists.txt
  - workspace/src/rc_car_interfaces/package.xml
  - workspace/src/avaj_car_control/scripts/**
  - workspace/src/avaj_car_control/launch/**
  - workspace/src/controll center/**
  - workspace/src/bno08x_driver/**
  - workspace/src/ldlidar_stl_ros2/**
  - compose.yaml
  - config/**
  - hotplug/**
  - CURRENT_STATE.md
  - docs/ros_graph.md
forbidden_topics_for_new_publishers:
  - /drive_commands
  - /control/autonomous_cmd
  - /cmd_vel
sole_allowed_controller_output:
  topic: /control/autonomous_ackermann_cmd
  type: ackermann_msgs/msg/AckermannDriveStamped
```

Die Testdateien und Testregistrierungszeilen von AP-T01 sind die einzige
Ausnahme von der pauschalen Sperre für `rc_car_usb_bridge/**` und
`avaj_car_control/**`; Produktionscode bleibt gesperrt. `rc_car_interfaces` und
`docs/ros_graph.md` gehören erst den in `Codex_Arbeitspaket.md` festgelegten
späteren Integrations-/Vertragspaketen.

## Reuse-Entscheidung

AP-B01 implementiert keinen Algorithmus und übernimmt keinen Fremdcode. Das
Reuse-Gate endet deshalb mit `NOT_APPLICABLE`. Für die Baselineprüfung wurden
ausschließlich vorhandene Standardwerkzeuge (`git`, `colcon`, `ctest`, ROS-2-
CLI) und der vorhandene Quellstand verwendet. `THIRD_PARTY.md` wurde nicht
angelegt oder geändert.

## Abschlussklassifikation

```yaml
implemented:
  - reproducible repository and package baseline
  - machine-readable ownership and forbidden-path boundary
tested:
  - six own packages build successfully
  - avaj_car_control isolated tests pass
  - rc_car_usb_bridge synthetic and PTY tests pass
  - avaj_sensor_processing lint tests pass
  - sole /drive_commands publisher observed
  - sole control_center Ackermann publisher observed
simulated: []
hardware_validated: []
remaining_follow_up:
  - AP-T01 deterministic valid ROS_DOMAIN_ID allocation and graph harness
  - AP-S01 Gazebo/TF/SLAM stability
  - AP-D01 validated closed reference path importer
  - optional AP-P01 separate pylon scenarios
```
