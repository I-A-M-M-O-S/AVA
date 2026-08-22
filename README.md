# ROS 2 Jazzy auf dem Jetson

Eine vollständige technische Übergabe für die Fortsetzung mit einer anderen
Instanz steht in [`HANDOFF.md`](HANDOFF.md).

Diese Umgebung installiert ROS 2 Jazzy Desktop in einem Ubuntu-24.04-ARM64-
Container. Das Jetson-Hostsystem und seine L4T-Pakete bleiben unverändert.

Start:

```bash
ros2-jazzy
```

Ein einzelner Befehl kann ebenfalls direkt ausgeführt werden:

```bash
ros2-jazzy ros2 pkg list
```

Der dauerhafte Colcon-Arbeitsbereich liegt unter `workspace/`.

## Gazebo Harmonic

Gazebo Harmonic 8 und die ROS-2-Anbindung `ros_gz` sind im Container
installiert. Über das Desktop-Symbol **Gazebo Harmonic** startet die lokale
Teststrecke. Dasselbe geht im Terminal mit:

```bash
gazebo-harmonic
```

Die Strecke liegt unter
`workspace/simulation/worlds/jetson_test_track.sdf`. Für das spätere
Fahrzeugmodell sind außerdem die ROS-Nachrichten `ackermann_msgs` installiert.

Die Teststrecke enthält das Modell `avaj_car` mit den bisher bekannten Maßen:

- Allradantrieb, Ackermann-Lenkung an der Vorderachse
- Radstand: 270 mm
- Spurweite: 245 mm
- Reifen: 80 mm Durchmesser, 36 mm Breite

Der Desktop-Starter aktiviert automatisch die ROS-Gazebo-Brücke. Steuerung und
Odometrie stehen dadurch als `/cmd_vel` und `/odom` zur Verfügung. Beispiel:

```bash
ros2-jazzy ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.8}, angular: {z: 0.25}}"
```

`linear.x` ist die Geschwindigkeit in m/s, `angular.z` die gewünschte
Gierrate in rad/s. Das vorläufige Modell nimmt 3 kg Fahrzeugmasse und eine
Karosserie von 360 x 190 x 60 mm an; diese Werte sollten später mit den echten
Abmessungen ersetzt werden.

### Live-Steuerung mit WASD

Gazebo starten und danach in einem zweiten Terminal die Tastatursteuerung
oeffnen:

```bash
wasd-drive
```

Der Client veroeffentlicht mit 20 Hz auf `/drive_command` den Typ
`avaj_car_control/msg/DriveCommand`. Beide Felder liegen zwischen 0 und 100:

- `steering`: 0 = ganz links, 50 = gerade, 100 = ganz rechts
- `acceleration`: 0 = voll rueckwaerts, 50 = neutral, 100 = voll vorwaerts

Im Steuerfenster werden die Tasten gehalten: `W` setzt vorwaerts auf 100, `S`
rueckwaerts auf 0, `A` links auf 0 und `D` rechts auf 100. Beim Loslassen
springt die jeweilige Achse sofort auf 50 zurueck. Dadurch funktionieren auch
Kombinationen wie `W+A`. `Q` oder Escape beendet die Steuerung. Wenn das
Steuerfenster den Tastaturfokus verliert, wird aus Sicherheitsgruenden sofort
neutralisiert. Ein gleichzeitig gestarteter Konverter bildet den Befehl auf
`/cmd_vel` ab.

Für die autonome C++-Steuerung reicht jetzt ein einziger Startbefehl:

```bash
ros2-jazzy ros2 run control_center control_center
```

Dieser startet den `control_center_node` und automatisch den
`drive_command_to_twist`-Konverter. Der autonome Test fährt mit
`acceleration=100` und entscheidet die Lenkung aus fünf LiDAR-Richtungen.
`wasd-drive` und der autonome `control_center` sollten nicht gleichzeitig
laufen, da beide auf `/drive_command` veröffentlichen.

Der autonome Simulationsmodus enthält derzeit absichtlich keine
Sicherheitsstopps und ist nur für Gazebo-Tests vorgesehen.

### Simulierte Sensoren

Das Modell besitzt Sensoren an den angegebenen Montagepositionen:

- Kamera mittig vorne, 6 cm über Boden, Blick geradeaus
- STL27-LiDAR mittig vorne, 10 cm über Boden, Orientierung 90 Grad rechts
- BNO085 aufrecht in der Fahrzeugmitte

Damit echte und simulierte Messwerte gleichzeitig betrieben werden können,
verwenden die simulierten Sensoren eigene Topics:

- `/sim/camera/image_raw` und `/sim/camera/camera_info`
- `/sim/scan`
- `/sim/imu/data`

Die Kamera simuliert zunächst 640 x 360 Pixel mit 20 Hz, der LiDAR 720 Strahlen
mit 10 Hz und die IMU 100 Hz. Diese moderaten Werte halten die Simulation auf
dem Jetson flüssig.

Eine andere Welt kann direkt über die ROS-2-Umgebung gestartet werden:

```bash
ros2-jazzy gz sim /workspace/simulation/worlds/eigene_strecke.sdf
```

## STL-27L

Der STL-27L-Treiber läuft als eigener Dienst und veröffentlicht einen
`sensor_msgs/msg/LaserScan` unter `/scan`.

```bash
docker compose -f /home/avaj/ros2_jazzy/compose.yaml up -d lidar
ros2-jazzy ros2 topic echo /scan --once
```

## Arducam UC-852

Die USB-UVC-Kamera läuft als dauerhafter Dienst mit 1280 x 720 Pixeln,
MJPEG-Eingang und 30 FPS. Sie veröffentlicht:

- `/camera/image_raw` (`sensor_msgs/msg/Image`, RGB8)
- `/camera/camera_info` (`sensor_msgs/msg/CameraInfo`)

Start und Prüfung:

```bash
docker compose -f /home/avaj/ros2_jazzy/compose.yaml up -d camera
ros2-jazzy ros2 topic hz /camera/image_raw
ros2-jazzy ros2 topic echo /camera/camera_info --once
```

Bild anzeigen:

```bash
ros2-jazzy ros2 run rqt_image_view rqt_image_view /camera/image_raw
```

Die Kameraparameter stehen in `config/uc852.yaml`. Die geometrische
Kalibrierung ist noch nicht durchgeführt; deshalb sind die Werte in
`/camera/camera_info` zunächst unkalibriert.

## BNO085 IMU

Der BNO085 ist über den 40-Pin-I²C-Anschluss verbunden:

- Pin 1: 3,3 V
- Pin 6: GND
- Pin 3: SDA
- Pin 5: SCL

Auf diesem Jetson ist das `/dev/i2c-7`; der Sensor verwendet Adresse `0x4A`.
Der dauerhafte IMU-Dienst veröffentlicht mit 100 Hz:

- `/imu/data` (`sensor_msgs/msg/Imu`, Frame `imu_link`)
- `/imu/mag` (`sensor_msgs/msg/MagneticField`, Einheit Tesla)

Start und Prüfung:

```bash
docker compose -f /home/avaj/ros2_jazzy/compose.yaml up -d imu
ros2-jazzy ros2 topic echo /imu/data --once
ros2-jazzy ros2 topic hz /imu/data
```

Die Einstellungen stehen in `config/bno085.yaml`.

IMU und Magnetfeld in RViz anzeigen:

```bash
ros2-jazzy rviz2 -d /config/bno085.rviz
```

## USB-Hotplug

Die Arducam UC-852 und der STL27L werden anhand ihrer eindeutigen USB-IDs
automatisch verwaltet:

- Einstecken der Kamera startet den Dienst `camera`.
- Abziehen der Kamera stoppt nur den Dienst `camera`.
- Einstecken des LiDAR startet den Dienst `lidar`.
- Abziehen des LiDAR stoppt nur den Dienst `lidar`.

Die udev-Regeln und die systemd-Vorlage liegen zusätzlich im Projektordner
`hotplug/`. Systemmeldungen lassen sich so anzeigen:

```bash
journalctl -t ros2-sensor-hotplug
```

## LiDAR-SLAM und Kartierung

Das Paket `avaj_slam` verwendet dieselbe SLAM-Anwendung für Gazebo und das
reale Fahrzeug. Es veröffentlicht den gemeinsamen TF-Baum für Fahrzeug und
Sensoren, startet `slam_toolbox` und bindet in der Simulation die Gazebo-
Odometrie über `robot_localization` an.

Zuerst Gazebo neu starten, damit die `/clock`-Bridge aus der aktuellen
Konfiguration geladen wird. Danach die SLAM-Anwendung für die Simulation
starten:

```bash
gazebo-harmonic
ros2-jazzy ros2 launch avaj_slam slam.launch.py simulation:=true use_sim_time:=true
```

Die Strecke anschließend mit `wasd-drive` langsam abfahren. Für die Karte
werden die Simulationsdaten automatisch auf die gemeinsamen SLAM-Topics
abgebildet:

```text
/sim/scan      -> /scan
/sim/imu/data  -> /imu/data
/odom          -> robot_localization -> odom -> base_link
```

Karte speichern:

```bash
ros2-jazzy ros2 run avaj_slam save_map.sh /workspace/maps/teststrecke
```

Das erzeugt `teststrecke.yaml` und `teststrecke.pgm` im persistenten
Workspace. Für das reale Fahrzeug wird derselbe Startpunkt verwendet:

```bash
ros2-jazzy ros2 launch avaj_slam slam.launch.py real:=true
```

Dafür müssen `/scan`, eine Odometrie mit `odom`/`base_link` und der reale
LiDAR-TF vorhanden sein. Die Kamera wird für 2D-LiDAR-SLAM nicht benötigt.
