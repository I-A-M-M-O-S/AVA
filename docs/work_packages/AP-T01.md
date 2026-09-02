# AP-T01 – Deterministisches lokales Testharness

```yaml
work_package: AP-T01
status: complete
completion_date: 2026-09-02
environment: local_ros_jazzy_container
branch: orin
head: 7df2f36f1a8d00ff6080dbec1ae1263aa5948f2b
working_tree_clean_before: false
working_tree_clean_after: false
production_code_changed: false
interfaces_changed: false
launch_files_changed: false
hardware_accessed: false
usb_bridge_process_started: false
real_vehicle_validation: false
```

## Ergebnis und Umfang

AP-T01 stellt einen wiederverwendbaren, lokalen Teststart und registrierte
Graph-Invariantentests bereit. Es wurden keine Fahrlogik, ROS-Interfaces,
Launchdateien, ESP-/USB-Komponenten oder Hardwarekonfigurationen geändert.
Vorhandene und parallel entstandene Arbeitsbaumänderungen blieben erhalten.

AP-T01 hat ausschließlich folgende Änderungen vorgenommen:

- `tools/run_local_tests.sh`
- `workspace/src/avaj_car_control/test/graph_invariants.py`
- `workspace/src/avaj_car_control/test/test_graph_invariants.py`
- Testregistrierung für `test_graph_invariants` in
  `workspace/src/avaj_car_control/CMakeLists.txt`
- Testabhängigkeit `tf2_msgs` in
  `workspace/src/avaj_car_control/package.xml`
- diese Übergabe

Die bereits vorhandenen Tests, insbesondere
`test_ackermann_to_drive_request.py`, `test_drive_commander.py` und alle
Bridge-/Sensor-Tests, sind keine Implementierungsleistung von AP-T01. Sie
werden vom Harness lediglich reproduzierbar mit ausgeführt.

## Testharness

`tools/run_local_tests.sh`:

1. reserviert mit `flock` exklusiv eine gültige DDS-Domain aus `180..232`;
2. setzt `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`;
3. startet mit `docker compose run --rm --no-deps` ausschließlich den
   Entwicklungscontainer, keine Compose-Abhängigkeiten oder Hardwaredienste;
4. baut `rc_car_interfaces`, `rc_car_usb_bridge`,
   `avaj_sensor_processing` und `avaj_car_control`;
5. führt die drei Pakete seriell aus, sodass ROS-Tests derselben Domain nicht
   miteinander konkurrieren;
6. begrenzt `colcon test` auf 180 Sekunden, sendet bei Ablauf zuerst SIGINT
   und erzwingt erst nach weiteren 10 Sekunden das Ende;
7. wertet jedes Paket separat mit `colcon test-result --verbose` aus;
8. gibt den Domain-Lock bei normalem Ende, Fehler, SIGINT oder SIGTERM frei.

Reproduzierbarer Aufruf aus dem Repository-Root:

```bash
./tools/run_local_tests.sh
```

Alle ROS-Graph-Tests verwenden `use_sim_time=true`. Die Beobachtungsdauer und
Prozessbegrenzung verwenden absichtlich monotone Wall-Time, damit ein Test auch
ohne `/clock` deterministisch beendet wird.

## Graph-Invarianten

`graph_invariants.py` ist ein begrenzter ROS-Graphmonitor und zugleich direkt
aufrufbares Prüfwerkzeug. Der registrierte Test erzeugt ausschließlich
synthetische In-Process-Publisher; es wird kein Produktions-Launch und keine
USB-Bridge gestartet.

| Vertrag | Typ | Erwarteter Publisher | Beobachtung | Fehlerverhalten |
|---|---|---|---|---|
| `/drive_commands` | `rc_car_interfaces/msg/DriveCommand` | exakt `/drive_commander` | DDS-Endpunkte während eines begrenzten Fensters | fehlender, falsch benannter oder zweiter Publisher erzeugt Fehlerbericht und Exit 1 |
| `/control/autonomous_ackermann_cmd` | `ackermann_msgs/msg/AckermannDriveStamped` | höchstens einer; mit CLI-Option exakt einer | DDS-Endpunkte | zweiter Publisher erzeugt Fehlerbericht und Exit 1 |
| `map -> odom` auf `/tf` oder `/tf_static` | `tf2_msgs/msg/TFMessage` | höchstens ein konfigurierter globaler TF-Owner | Transform plus Endpunkte der bekannten Owner | gleichzeitige Owner oder unbekannter Owner bei beobachtetem Transform erzeugen Fehlerbericht und Exit 1 |

Die Nachrichten tragen ihre bestehenden Einheiten und Frames; das Harness
erzeugt keine Fahrwerte. Der synthetische TF verwendet die Frames `map` und
`odom`. Das Prüfwerkzeug publiziert nichts und hat daher keine eigene Rate.
Standard-Beobachtungszeit sind zwei Sekunden. SIGINT führt ohne Traceback zu
Exit 130 und zerstört Node, Executor und ROS-Kontext.

Für `map -> odom` ist eine Jazzy-Einschränkung berücksichtigt: Die öffentliche
Python-Callback-API liefert in dieser Installation Sequenz und Zeitstempel,
aber keine Publisher-GID pro TF-Nachricht. Deshalb korreliert der Monitor den
beobachteten Transform konservativ mit den DDS-Endpunkten der bekannten
globalen TF-Owner `/slam_toolbox` und `/amcl`. Weitere erlaubte Owner werden
explizit und wiederholbar mit `--global-tf-node /voller/node_name` angegeben.
Damit schlägt ein gleichzeitiger Mapping-/Lokalisierungsbetrieb fehl, ohne alle
anderen legitimen `/tf`-Publisher fälschlich zu verbieten.

Registrierte Fälle:

- ein `/drive_commander`, ein autonomer Ackermann-Controller und ein
  `slam_toolbox`-Owner bestehen;
- ein absichtlich zweiter `/drive_commands`-Publisher wird erkannt;
- ein absichtlich zweiter Ackermann-Publisher wird erkannt;
- gleichzeitige `slam_toolbox`- und `amcl`-TF-Owner werden erkannt.

Der Positivfall prüft die exakten Publishernamen für beide Fahrbefehlstopics.
Die Negativfälle bestehen nur dann, wenn der Monitor den injizierten Konflikt
als Fehler klassifiziert.

## Verifikation

Finaler vollständiger Lauf:

```bash
./tools/run_local_tests.sh
```

Ergebnis mit exklusiv reservierter `ROS_DOMAIN_ID=180`:

- Build: vier ausgewählte Pakete erfolgreich;
- `avaj_sensor_processing`: 2/2 Tests bestanden;
- `rc_car_usb_bridge`: 36/36 vorhandene synthetische/PTy-Tests bestanden;
- `avaj_car_control`: drei CTest-Suites bestanden;
  - `test_drive_commander`: 18/18 vorhandene Fälle;
  - `test_ackermann_to_drive_request`: 6/6 vorhandene Fälle;
  - `test_graph_invariants`: 4/4 neue AP-T01-Fälle;
- `colcon test-result`:
  - Bridge: 36 Datensätze, 0 Fehler/Fehlschläge/Skips;
  - Sensorverarbeitung: 2 Datensätze, 0 Fehler/Fehlschläge/Skips;
  - Fahrzeugsteuerung: 31 Ergebnisdatensätze, 0
    Fehler/Fehlschläge/Skips (einschließlich CTest-Suiteeinträgen).

Zusätzlicher Stilnachweis:

```bash
python3 -m flake8 \
  src/avaj_car_control/test/graph_invariants.py \
  src/avaj_car_control/test/test_graph_invariants.py
```

Ergebnis: keine Befunde.

Kontrollierter Interrupt-Nachweis unter isolierter `ROS_DOMAIN_ID=182`:

```bash
timeout --preserve-status --signal=INT --kill-after=5s 1s \
  python3 src/avaj_car_control/test/graph_invariants.py \
    --observe-seconds 30 --allow-no-drive-commander
```

Ergebnis: Exit 130, Ausgabe
`{"ok": false, "interrupted": true}`, kein Traceback und kein
`invalid context`-Fehler.

Während aller Läufe wurden weder `/dev/ttyUSB*` noch `/dev/ttyACM*`, I²C,
Kamera oder LiDAR geöffnet. Die vorhandenen PTY-Tests verwenden ausschließlich
vom Betriebssystem erzeugte Pseudoterminals. Weder `usb_bridge` noch Gazebo,
Sensor-Hardwaredienste oder Aktoren wurden gestartet.

## Reuse-Entscheidung

AP-T01 enthält keinen Fahr- oder Wahrnehmungsalgorithmus. Das Reuse-Gate ist
daher `NOT_APPLICABLE`. Wiederverwendet wurden ausschließlich vorhandene
Standardwerkzeuge und APIs: `colcon`, CTest/Pytest, `timeout`, `flock`, ROS-2-
Graphendpunkte, Standardnachrichten und der vorhandene Jazzy-Container. Es
wurde kein externer Code kopiert und `THIRD_PARTY.md` nicht geändert.

## Einschränkungen und Folgearbeit

- Der Monitor kann nur Teilnehmer seiner isolierten DDS-Domain beobachten;
  genau das ist für reproduzierbare Tests beabsichtigt.
- Ein neuer globaler TF-Provider muss im Prüfaufruf explizit als
  `--global-tf-node` benannt werden. Das ist eine fail-closed Konfiguration,
  keine automatische Heuristik.
- AP-T01 ergänzt keine Tests in `control_center`, `avaj_slam` oder
  `rc_car_interfaces`, weil deren Dateien laut AP-B01 anderen Paketen gehören.
- Das Ergebnis ist ausschließlich lokal/softwarevalidiert. Es enthält keine
  Gazebo-, Hardware-, ESP-, USB-Geräte-, Aktor- oder Realfahrzeugvalidierung.

```yaml
implemented:
  - exclusive valid ROS_DOMAIN_ID allocation
  - local-only sequential build/test runner with timeout and cleanup
  - bounded reusable ROS graph monitor
  - positive and duplicate-owner graph regression tests
tested:
  - selected package build
  - 2 sensor-processing tests
  - 36 existing bridge synthetic/PTy tests
  - 28 avaj_car_control pytest cases, including 4 new graph cases
  - flake8
  - clean SIGINT handling
simulated: []
hardware_validated: []
```
