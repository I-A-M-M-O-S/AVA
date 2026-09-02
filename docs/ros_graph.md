# ROS-2-Graph und Schnittstellen

Diese Datei ist der verbindliche Namensvertrag für dauerhafte ROS-Topics und
Nodes. Simulation und reale Hardware werden über Launchprofile ausgewählt und
dürfen nicht gleichzeitig dieselben Raw-Topics publizieren.

## Sensorpfad

```text
Simulation oder Hardware
        │
        ├── /scan_raw ───────> /sensors/lidar_preprocessor ──> /scan
        ├── /imu/data_raw ───> /sensors/imu_preprocessor ────> /imu/data
        └── /camera/image_raw (bereits gemeinsames Treiberformat)
```

High-Level-Nodes dürfen keine `/sim/...`-Topics abonnieren. Unterschiede
zwischen Gazebo und Hardware enden an der Treibergrenze. `scan_preprocessor`
filtert ungültige und außerhalb der konfigurierten Grenzen liegende Messwerte.
`imu_preprocessor` verwirft nicht-endliche Werte. Der BNO085 liefert bereits
einen fusionierten Rotationsvektor; ein zusätzlicher Madgwick-Filter ist daher
in der aktuellen Baseline nicht aktiv.

## Node-Namen

| Node | Paket | Aufgabe |
|---|---|---|
| `/sensors/lidar_driver` | `ldlidar_stl_ros2` | Reale LiDAR-Rohdaten |
| `/sensors/lidar_preprocessor` | `avaj_sensor_processing` | LiDAR-Validierung und Filterung |
| `/sensors/imu_driver` | `bno08x_driver` | Reale IMU-Rohdaten |
| `/sensors/imu_preprocessor` | `avaj_sensor_processing` | IMU-Validierung |
| `/sensors/camera_driver` | `usb_cam` | Reale Kameradaten |
| `/ekf_filter_node` | `robot_localization` | Lokale Zustandsschätzung |
| `/slam_toolbox` | `slam_toolbox` | Exklusiver Publisher von `map -> odom` im Mappingprofil |
| `/mode_manager` | `avaj_car_control` | Gewählter Jetson-Modus |
| `/safety_watchdog` | `avaj_car_control` | Software-Fahrfreigabe |
| `/drive_commander` | `avaj_car_control` | Einziger Publisher des finalen Fahrbefehls |
| `/usb_bridge` | `rc_car_usb_bridge` | Transport zum ESP32, keine Fahrentscheidung |

Treiber liegen im Namespace `/sensors`. Bestehende sicherheitsrelevante
Steuerungsnamen bleiben absichtlich stabil, insbesondere `/drive_commander`.

## Dauerhafte Topic-Schnittstellen

| Topic | Typ | Publisher | Abonnenten | Einheit / Frame | Rate | Timeout / Fehlerverhalten |
|---|---|---|---|---|---|---|
| `/scan_raw` | `sensor_msgs/msg/LaserScan` | aktiver LiDAR-Treiber oder Gazebo-Bridge | `lidar_preprocessor` | m, Sensorframe | 10 Hz | Kein Fallback; fehlende Daten sperren autonomes Fahren |
| `/scan` | `sensor_msgs/msg/LaserScan` | `lidar_preprocessor` | SLAM, Steuerung, Watchdog | m, unveränderter Sensorframe | Eingangsrate | Watchdog aktuell 0,5 s |
| `/imu/data_raw` | `sensor_msgs/msg/Imu` | BNO085 oder Gazebo-Bridge | `imu_preprocessor` | SI, `imu_link` bzw. Simulationsframe | 100 Hz | NaN/Inf wird verworfen |
| `/imu/data` | `sensor_msgs/msg/Imu` | `imu_preprocessor` | EKF, Steuerung, Watchdog | SI, unveränderter Sensorframe | Eingangsrate | Watchdog aktuell 0,5 s |
| `/imu/mag` | `sensor_msgs/msg/MagneticField` | BNO085 | Diagnose / spätere Fusion | T, `imu_link` | 100 Hz | Derzeit nicht sicherheitskritisch ausgewertet |
| `/camera/image_raw` | `sensor_msgs/msg/Image` | Kamera oder Gazebo-Bridge | Wahrnehmung, optional Watchdog | Pixel, `camera_optical_frame` | 20/30 Hz | Im PYLON-Modus später zwingend erforderlich |
| `/camera/camera_info` | `sensor_msgs/msg/CameraInfo` | Kamera oder Gazebo-Bridge | Bildverarbeitung | Kamerakalibrierung | Bildrate | Unkalibrierte Hardwaredaten sind nicht produktionsreif |
| `/odom` | `nav_msgs/msg/Odometry` | Gazebo oder spätere Radodometrie | EKF | m, m/s, `odom -> base_link` | 50 Hz | Rohquelle; nicht direkt von High-Level-Steuerung verwenden |
| `/odometry/filtered` | `nav_msgs/msg/Odometry` | EKF | Steuerung, SLAM | SI, `odom -> base_link` | EKF-Rate | Bei Verlust autonomes Fahren sperren (noch umzusetzen) |
| `/planning/racing_line` | `nav_msgs/msg/Path` | späterer Racing-Line-Planer | `control_center` | m, üblicherweise `map` | bei neuer Planung | Noch optional; die LIDAR_GAP-Basislogik nutzt es noch nicht |
| `/control/autonomous_ackermann_cmd` | `ackermann_msgs/msg/AckermannDriveStamped` | `control_center` | `ackermann_to_drive_request` | m/s und Lenkwinkel rad, `base_link` | 20 Hz | Frische LiDAR-/Odometrie- und Fahrfreigabeprüfung vor Bewegung |
| `/control/autonomous_cmd` | `rc_car_interfaces/msg/DriveRequest` | `ackermann_to_drive_request` | `drive_commander`, Watchdog | normiert, späte Aktuatoranpassung | Eingangsrate | Adapter-Timeout 0,3 s; danach einmal neutral und keine künstliche Heartbeat-Verlängerung |
| `/control/manual_cmd` | `rc_car_interfaces/msg/DriveRequest` | `wasd_teleop` | `drive_commander` | normiert, Testpfad | 50 Hz | Nicht die spätere ESP-direkte MANUAL-Architektur |
| `/system/mode` | `std_msgs/msg/String` | `mode_manager` | Watchdog, `drive_commander` | Enum als Übergangslösung | 1 Hz + Änderung | Ungültige Werte werden abgelehnt |
| `/system/drive_enable` | `std_msgs/msg/Bool` | `safety_watchdog` | `drive_commander` | bool | 20 Hz | Fehlende Pflichtinputs ergeben `false` |
| `/drive_commands` | `rc_car_interfaces/msg/DriveCommand` | ausschließlich `drive_commander` | USB-Bridge, Simulatoradapter | normiert, `base_link` | 50 Hz | Stale/fehlende Quelle ergibt neutral und disabled |
| `/vehicle/status` | `rc_car_interfaces/msg/VehicleStatus` | `usb_bridge` | Diagnose; später Watchdog | Owner/Lock/Arming/Faults, Jetson-Empfangszeit | gültige `V1,STA`-Frames | Ungültige Frames publizieren nichts; derzeit keine Fahrfreigabe |
| `/vehicle/actuator_status` | `rc_car_interfaces/msg/ActuatorStatus` | `usb_bridge` | Diagnose/Logging | tatsächlich angewandt, normiert; Jetson-Empfangszeit | gültige `V1,ACT`-Frames | Nicht mit angefordertem `DriveCommand` gleichsetzen |
| `/vehicle/encoders` | `rc_car_interfaces/msg/WheelEncoderState` | `usb_bridge` | spätere Odometrie/Watchdog | vier signed Counts; Jetson-Empfangszeit | gültige `V1,ENC`-Frames | int32-Wrap; derzeit keine Safety-Gate-Wirkung |
| `/drive_usb/rx` | `std_msgs/msg/String` | `usb_bridge` | ausschließlich Diagnose | untrusted Raw-RX | abgeschlossene/verworfene Zeile | Nie als Fahrzeugzustand oder Fahrfreigabe verwenden |
| `/drive_usb/status` | `std_msgs/msg/String` | `usb_bridge` | Diagnose; bestehender optionaler Arrival-Watchdog | JSON-Übergangsschnittstelle | Zustandsänderung | connected/disconnected, valid feedback sowie konkrete Reject-Gründe; setzt selbst kein Drive-Enable |

`control_center` konsumiert zusätzlich Kamera/Kamerakalibrierung, IMU,
Magnetometer, Karte, Fahrzeugstatus, Aktuatorstatus, Encoder, Systemmodus,
Fahrfreigabe sowie die Status-Heartbeats von `drive_commander` und USB-Bridge.
Sein Fahralgorithmus bleibt dadurch von der normierten ESP-Schnittstelle
getrennt. Die aktuelle `LIDAR_GAP`-Logik ist nur der erste austauschbare
Algorithmus; ein Racing-Line-Follower publiziert später über denselben
Ackermann-Ausgang.

Der vollständige Frame-, CRC-, Sequenz-, Zeit-, Bereichs- und Wrap-Vertrag
steht in `docs/esp_feedback_protocol.md`. Die neuen Feedbacktopics entstehen
ausschließlich nach vollständiger Validierung. Der `safety_watchdog` wurde in
diesem Paket bewusst nicht auf ESP-Feedback umgestellt.

Die String-Schnittstellen für Modus und Status sind ausdrücklich
Übergangslösungen. Sie werden später durch typisierte Messages ersetzt, ohne
die hier definierte Sensororganisation erneut zu ändern.

## Reproduzierbare Profile

- Hardware: `docker compose up -d sensor_processing lidar imu camera`
- Simulation: `gazebo-harmonic`; der Start startet Bridge und Processing.
- SLAM Simulation: `ros2 launch avaj_slam slam.launch.py simulation:=true use_sim_time:=true`
- SLAM Hardware: `ros2 launch avaj_slam slam.launch.py real:=true`

`simulation:=true` und `real:=true` sind im SLAM-Launch gegenseitig
ausgeschlossen. Dadurch können nicht versehentlich zwei gleichnamige
SLAM-Lifecycle-Nodes `map -> odom` beanspruchen.
