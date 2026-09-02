# AP-S01 – Gazebo-, TF- und SLAM-Basis stabilisieren

```yaml
work_package: AP-S01
status: complete
baseline_date: 2026-09-02
environment: local_ros_jazzy_container
validation_mode:
  - Gazebo Harmonic simulation
  - manual WASD driving
  - live ROS 2 graph inspection
  - TF inspection
  - SLAM mapping
hardware_validated: false
real_vehicle_validation: false
```

## 1. Ergebnis

AP-S01 ist für den aktuellen lokalen Simulationsstand abgeschlossen.

Die vorhandene Gazebo-/ROS-2-/SLAM-Kette wurde nicht unnötig umgebaut, sondern
gegen die Anforderungen des Arbeitspakets praktisch validiert. Der bekannte
Mapping-Stack funktioniert reproduzierbar mit:

```text
Gazebo
  -> /clock
  -> simulierte Sensoren
  -> /scan
  -> EKF
  -> /odometry/filtered
  -> TF: odom -> base_link
  -> slam_toolbox
  -> TF: map -> odom
  -> /map
```

Die resultierende TF-Kette ist damit:

```text
map
  -> odom
  -> base_link
  -> avaj_car/lidar_link/stl27_sim
```

Während manueller Fahrt mit WASD wurde eine brauchbare SLAM-Karte aufgebaut.
Der Benutzer hatte mit diesem Simulationsstand bereits zuvor eine gute Karte
erstellt und auf einer gespeicherten Karte mit Nav2 eine Fahrtenplanung
durchgeführt. Die Umsetzung eines Nav2-/Bahnfolger-Ausgangs auf den
AVAJ-Ackermann-Fahrbefehl gehört ausdrücklich nicht zu AP-S01.

## 2. Verwendeter Launch

Der bestehende Launch

```text
workspace/src/avaj_slam/launch/slam.launch.py
```

wurde im Simulationsprofil mit aktivierter Simulationszeit verwendet:

```bash
ros2 launch avaj_slam slam.launch.py \
  simulation:=true \
  use_sim_time:=true
```

Optional kann RViz mit:

```bash
rviz:=true
```

zugeschaltet werden.

Der Launch trennt Simulation und Realprofil gegenseitig und startet für die
Simulation insbesondere:

- `robot_state_publisher`
- `sim_odom_frame_bridge`
- `sim_base_frame_bridge`
- `sim_lidar_frame_bridge`
- `ekf_filter_node`
- `slam_toolbox`
- optional `rviz2`

`slam_toolbox` wird als Lifecycle-Node konfiguriert und anschließend aktiviert.

## 3. Verifizierte Kern-Topics

Im vollständigen Simulations-/SLAM-Zustand waren unter anderem vorhanden:

```text
/clock
/scan
/scan_raw
/odom
/odometry/filtered
/map
/map_metadata
/map_updates
/tf
/tf_static
```

Zusätzlich waren die bereits vorhandenen Steuerungs-, Kamera-, IMU- und
Fahrzeugtopics sichtbar. Diese gehören nicht zum Implementierungsumfang von
AP-S01.

## 4. SLAM-Lifecycle

Live geprüft:

```text
ros2 lifecycle get /slam_toolbox
```

Ergebnis:

```text
active [3]
```

Damit war `slam_toolbox` während der Validierung aktiv.

## 5. Odometrie

Live geprüft:

```text
ros2 topic info /odometry/filtered -v
```

Ergebnis:

```text
Type: nav_msgs/msg/Odometry
Publisher count: 1
Publisher: /ekf_filter_node
```

Gemessene Rate während des Laufs:

```text
ca. 32–35 Hz
```

Beobachtete Beispielwerte:

```text
average rate: 33.867 Hz
average rate: 32.223 Hz
average rate: 33.459 Hz
average rate: 34.579 Hz
```

Es wurde kein zweiter Publisher für `/odometry/filtered` beobachtet.

## 6. Map

Live geprüft:

```text
ros2 topic info /map -v
```

Ergebnis:

```text
Type: nav_msgs/msg/OccupancyGrid
Publisher count: 1
Publisher: /slam_toolbox
Durability: TRANSIENT_LOCAL
```

Die Karte wurde in RViz sichtbar aufgebaut und während manueller Fahrt
fortgeschrieben.

## 7. TF-Verträge und Ownership

### EKF

Die laufenden Parameter wurden direkt am Node geprüft:

```text
use_sim_time    = true
frequency       = 50.0
sensor_timeout  = 0.2
world_frame     = odom
odom_frame      = odom
base_link_frame = base_link
publish_tf      = true
```

Damit besitzt der EKF den dynamischen Transform:

```text
odom -> base_link
```

### slam_toolbox

Die laufenden Parameter wurden direkt am Node geprüft:

```text
use_sim_time          = true
map_frame             = map
odom_frame            = odom
base_frame            = base_link
scan_topic            = /scan
scan_queue_size       = 1
transform_timeout     = 0.3
tf_buffer_duration    = 30.0
minimum_time_interval = 0.2
throttle_scans        = 1
```

Damit besitzt `slam_toolbox` den globalen Transform:

```text
map -> odom
```

### Live-TF-Prüfung

Folgende Transformationen wurden mit `tf2_echo` erfolgreich beobachtet:

```text
map -> odom
odom -> base_link
```

Nach dem anfänglichen Aufbau des TF-Buffers wurden kontinuierlich gültige
Transformationen ausgegeben.

Beispiel `map -> odom`:

```text
Translation: [-1.330, -0.408, 0.000]
Yaw:         ca. -0.157 rad
```

Beispiel `odom -> base_link`:

```text
Translation: [-2.941, 0.401, 0.000]
Yaw:         ca. 1.230 rad
```

Die Anfangsmeldung von `tf2_echo`, dass Frames noch nicht bekannt seien,
verschwand nach dem Aufbau des lokalen TF-Buffers und wurde nicht als
persistenter Fehler beobachtet.

## 8. LiDAR-/Scan-Pfad

Ein Live-Scan auf `/scan` zeigte:

```yaml
header:
  stamp:
    sec: 465
    nanosec: 300000000
  frame_id: avaj_car/lidar_link/stl27_sim
```

Der Scan enthielt plausible Distanzwerte und wurde von `slam_toolbox`
verwendet.

Gemessene Ankunftsrate in einem Lauf:

```text
ca. 14.3 Hz
```

Beispiel:

```text
average rate: 14.275 Hz
average rate: 14.285 Hz
average rate: 14.311 Hz
average rate: 14.350 Hz
average rate: 14.362 Hz
```

Die Messung zeigte Wall-Time-Bursts mit `min: 0.000 s` und Maximalabständen bis
ungefähr `0.17 s`. Da Mapping und Kartenqualität praktisch funktionierten,
wurde hier keine invasive Änderung an einer bereits funktionierenden
Simulationskette vorgenommen.

## 9. Reproduzierte slam_toolbox-Queue-Drops

Der bereits bekannte Fehler wurde reproduziert:

```text
Message Filter dropping message:
frame 'avaj_car/lidar_link/stl27_sim'
reason 'discarding message because the queue is full'
```

In einem längeren beobachteten Lauf traten beispielhaft Drops zu folgenden
Simulationszeiten auf:

```text
120.7
150.2
206.7
240.2
264.2
342.8
348.6
366.9
373.6
471.9
490.0
521.6
524.6
```

Das entspricht 13 beobachteten Drops über ungefähr 404 Sekunden
Simulationszeit.

Bei einer beobachteten Scanrate von ungefähr 14 Hz ergibt sich nur als grobe
Abschätzung:

```text
404 s * 14 Scans/s ~= 5656 Scans
13 / 5656 ~= 0.23 %
```

Die Größenordnung der beobachteten Verluste liegt damit ungefähr bei
`0.2–0.3 %`.

Diese Zahl ist eine Schätzung aus Laufzeit, gemessener mittlerer Scanrate und
gezählten Logmeldungen; sie ist kein exakt instrumentierter Paketverlustwert.

Die Drops führten im beobachteten Simulationslauf zu keiner erkennbaren
Beeinträchtigung der praktisch erzeugten Karte. Die Karte wurde weiterhin
korrekt aufgebaut.

`scan_queue_size` ist bereits `1`; die Queue wurde bewusst nicht nur zur
Unterdrückung der Meldung vergrößert.

Für AP-S01 wird der Zustand deshalb als reproduzierter, quantitativ kleiner und
aktuell nicht blockierender Timing-/MessageFilter-Effekt klassifiziert.

## 10. tf2_monitor-Hinweis

Ein erster `tf2_monitor`-Lauf lieferte Werte in der Größenordnung von
`1.78836e+09 s`.

Diese Werte werden nicht als reale TF-Latenz interpretiert, da die laufende
Simulation ROS-Simulationszeit verwendete, während dieser Monitorlauf nicht
explizit mit `use_sim_time=true` gestartet wurde. Die Werte spiegeln damit die
Differenz zwischen Wall-Time und Simulationszeit wider und sind für eine
TF-Latenzbewertung nicht verwendbar.

Die funktionale TF-Verfügbarkeit wurde stattdessen durch erfolgreiche
`tf2_echo`-Abfragen sowie die laufende SLAM-Kartierung bestätigt.

## 11. TF-Publisher

Auf `/tf` wurden Publisher von folgenden bestehenden Nodes beobachtet:

```text
robot_state_publisher
ekf_filter_node
slam_toolbox
```

`slam_toolbox` erschien mit mehreren Endpoints desselben Node-Namens; dies wurde
nicht als zweiter fachlicher Besitzer von `map -> odom` interpretiert.

Auf `/tf_static` wurden beobachtet:

```text
robot_state_publisher
sim_odom_frame_bridge
sim_base_frame_bridge
sim_lidar_frame_bridge
```

Die aktive Frame-Konfiguration und die Live-TF-Abfragen ergaben die gewünschte
funktionale Kette.

## 12. Kontrollierter Shutdown

Der SLAM-/TF-/EKF-Stack wurde mit `Ctrl-C` beendet.

Der Launch meldete unter anderem:

```text
user interrupted with ctrl-c (SIGINT)
```

Danach beendeten sich die relevanten Prozesse sauber:

```text
static_transform_publisher ... process has finished cleanly
robot_state_publisher ... process has finished cleanly
ekf_node ... process has finished cleanly
async_slam_toolbox_node ... process has finished cleanly
rviz2 ... process has finished cleanly
```

`slam_toolbox` meldete zusätzlich:

```text
Unregistering sensor: Custom Described Lidar
```

Nach dem Shutdown waren `slam_toolbox`, EKF, die drei Sim-TF-Bridges,
`robot_state_publisher` und RViz nicht mehr in `ros2 node list` vorhanden.

Der kontrollierte Shutdown von AP-S01 wird daher als bestanden bewertet.

## 13. Vorhandene USB-Bridge

Im beobachteten Gesamtsystem war ein bestehender Node:

```text
/usb_bridge
```

vorhanden.

Dieser Zustand ist ausdrücklich gewollter Bestand und nach Benutzerentscheidung
kein Fehler von AP-S01. Die USB-Bridge war bereits zuvor konfiguriert und soll
bestehen bleiben.

AP-S01 hat:

- die USB-Bridge nicht implementiert,
- das ESP-/USB-Protokoll nicht geändert,
- keine USB-Transportlogik geändert,
- keine Hardwarefunktion als durch AP-S01 validiert eingestuft.

Die Bridge wird in diesem Bericht ausschließlich als bereits vorhandener
Systembestand dokumentiert.

Für `/drive_commands` wurde weiterhin genau ein Publisher beobachtet:

```text
Publisher count: 1
Publisher: /drive_commander
```

Die bestehenden Subscriber waren:

```text
/drive_command_to_twist
/usb_bridge
```

Die globale Publisher-Invariante blieb damit erhalten.

## 14. Bekannte Auffälligkeit: doppelte Sensor-Node-Namen

`ros2 node list` zeigte:

```text
/sensors/imu_preprocessor
/sensors/imu_preprocessor
/sensors/lidar_preprocessor
/sensors/lidar_preprocessor
```

ROS warnte entsprechend vor identischen Node-Namen.

Gleichzeitig war für `/scan` zuvor nur ein Publisher sichtbar. Es wurde daher
in AP-S01 keine fremde Sensorimplementierung geändert.

Diese Auffälligkeit bleibt als Follow-up für eine spätere Graph-/Integrations-
oder Testharness-Prüfung dokumentiert und blockiert den nachgewiesenen
SLAM-Betrieb nicht.

## 15. Praktisch validierter Simulationsstand

Der Benutzer bestätigte im vollständigen Simulationsstand:

- Gazebo läuft;
- das Fahrzeug kann manuell mit WASD gefahren werden;
- LiDAR-/Scan-Daten sind sichtbar;
- SLAM baut eine brauchbare Karte auf;
- die Karte ist in RViz sichtbar;
- eine gute Karte wurde bereits zuvor auf diese Weise erstellt;
- auf einer gespeicherten Karte konnte bereits mit Nav2 eine Fahrtenplanung
  durchgeführt werden.

Nicht Teil von AP-S01 ist die Umsetzung des von Nav2 beziehungsweise einem
Bahnfolger erzeugten Bewegungsbefehls auf den festgelegten
`AckermannDriveStamped`-Ausgang. Das bleibt einem Folgepaket für
Lokalisierung/Bahnfolger/Integration vorbehalten.

## 16. Abnahme gegen AP-S01

| Anforderung | Ergebnis |
|---|---|
| Gazebo-Simulation funktioniert | **erfüllt** |
| `/clock` vorhanden | **erfüllt** |
| `/scan` vorhanden und praktisch nutzbar | **erfüllt** |
| `/odometry/filtered` vorhanden | **erfüllt** |
| genau ein Odometrie-Publisher | **erfüllt** |
| `/map` vorhanden | **erfüllt** |
| genau ein Map-Publisher | **erfüllt** |
| `slam_toolbox` aktiv | **erfüllt** |
| `map -> odom` verfügbar | **erfüllt** |
| `odom -> base_link` verfügbar | **erfüllt** |
| funktionale TF-Kette bis LiDAR | **erfüllt** |
| brauchbare Karte bei manueller Fahrt | **erfüllt** |
| Queue-Drops reproduziert und klassifiziert | **erfüllt** |
| Queue-Drops praktisch nicht blockierend | **erfüllt** |
| kontrollierter Shutdown | **erfüllt** |
| reale Hardwarevalidierung | **nicht durchgeführt / nicht behauptet** |

## 17. Grenzen

AP-S01 weist ausdrücklich nicht nach:

- reale Fahrzeugfunktion;
- reale LiDAR-/Kamera-/IMU-Funktion;
- reale Encoderodometrie;
- ESP-Endautorität;
- physische Aktorik;
- Hardware-Safety;
- gespeicherte Kartenlokalisierung nach Neustart;
- autonomes Folgen eines Referenzpfades;
- Ackermann-Bahnfolger;
- Rundenerkennung;
- End-to-End-Racing.

Diese Punkte gehören zu späteren Arbeitspaketen.

## 18. Empfohlene Folgearbeiten

Der Simulations-/SLAM-Unterbau ist für die nächsten Arbeitspakete ausreichend.

Priorisierte Folgearbeiten:

1. gespeicherte Kartenlokalisierung als eigenes Lokalisierungspaket;
2. Referenzpfad/Importer;
3. Ackermann-Bahnfolger-Benchmark;
4. spätere Integration der Komponenten;
5. optional die doppelten Sensor-Node-Namen im zentralen Test-/Integrationsgraph
   untersuchen.

Die sporadischen `slam_toolbox`-Queue-Drops sollen nicht ohne messbaren
praktischen Nutzen durch invasive Änderungen an der funktionierenden
Simulationskette optimiert werden.

## 19. Abschlussklassifikation

```yaml
implemented:
  - existing Gazebo/TF/EKF/SLAM simulation stack retained
  - simulation and real launch profiles remain separated
  - lifecycle activation of slam_toolbox confirmed
  - canonical map -> odom -> base_link -> lidar TF chain confirmed

tested:
  - slam_toolbox lifecycle active
  - single /odometry/filtered publisher
  - single /map publisher
  - map -> odom transform
  - odom -> base_link transform
  - live LaserScan frame and payload
  - scan and odometry update rates
  - controlled shutdown
  - single /drive_commands publisher remains drive_commander

simulated:
  - manual WASD driving in Gazebo
  - live SLAM mapping
  - usable map visible in RViz
  - sporadic slam_toolbox MessageFilter drops reproduced
  - estimated scan-drop magnitude approximately 0.2-0.3 percent in one observed run

known_follow_up:
  - duplicate imu_preprocessor and lidar_preprocessor node names in ROS graph
  - optional exact instrumentation of MessageFilter drop rate if ever required

hardware_validated: []
real_vehicle_validated: []
```

## 20. Abschlussentscheidung

```yaml
status: complete
decision: accept
reason:
  - required Gazebo, scan, odometry, TF and map chain is functional
  - SLAM mapping is practically usable
  - TF ownership is consistent with slam_toolbox map->odom and EKF odom->base_link
  - observed scan drops are rare, reproducible and non-blocking
  - controlled shutdown succeeds
  - remaining findings do not justify destabilizing the working simulation stack
```
