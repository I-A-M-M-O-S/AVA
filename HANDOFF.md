# Übergabe: Jetson, ROS 2 Jazzy, Sensoren und Gazebo-Fahrzeug

Stand: 22. August 2026, Zeitzone Europe/Berlin

> **Aktueller Stand:** Diese historische Übergabe wird durch
> [`CURRENT_STATE.md`](CURRENT_STATE.md) ergänzt. Neue Agenten müssen zuerst
> `AGENTS.md` und `CURRENT_STATE.md` lesen; der dort datierte Live-, Test- und
> Sicherheitsstand hat bei Abweichungen Vorrang.

Diese Datei ist der zentrale Einstiegspunkt für eine neue Codex-/ChatGPT-Instanz.
Vor Änderungen zuerst diese Datei und anschließend `README.md`, `compose.yaml`
und die betroffenen Konfigurationen lesen. Das System ist produktiv benutzt;
laufende Container nicht pauschal beenden oder löschen.

## 1. Ziel und aktueller Aufbau

Auf einem NVIDIA Jetson Orin NX 16 GB entsteht ein autonomes Allrad-RC-Fahrzeug.
ROS 2 Jazzy läuft absichtlich in einem Ubuntu-24.04-ARM64-Docker-Container, weil
das Jetson-Hostsystem Ubuntu 22.04 / JetPack 6 verwendet. So bleiben L4T,
CUDA und die NVIDIA-Treiber des Hosts unangetastet, während ROS Jazzy offiziell
auf Noble verwendet wird.

Bereits vorhanden:

- ROS 2 Jazzy Desktop einschließlich RViz und rqt
- reale Arducam UC-852 als ROS-Kamera
- realer STL27L-LiDAR als `LaserScan` (momentan nicht eingesteckt)
- realer BNO085 über I²C als IMU und Magnetometer
- USB-Hotplug für Kamera und LiDAR
- Gazebo Harmonic mit einem fahrbaren Allrad-Ackermann-Modell
- simulierte Kamera, LiDAR und IMU auf getrennten `/sim/...`-Topics

Nicht vorhanden bzw. noch offen:

- Motorcontroller, Servo-/Lenkcontroller und reale Fahrzeug-Odometrie
- endgültige Fahrzeugmasse, Karosseriemaße und Trägheitswerte
- exakte x-Positionen der real montierten Frontsensoren (derzeit Frontkante angenommen)
- Kamerakalibrierung
- vollständiger ROS-TF-Baum für Simulation und reales Fahrzeug
- SLAM-/Lokalisierungs-Stack noch nicht konfiguriert und gestartet
- F1TENTH-Stack; er wurde besprochen, aber nicht installiert

## 2. Jetson-Host

- Benutzer: `avaj`, UID/GID 1000
- Hostname: `avaj-desktop`
- Plattform: NVIDIA Jetson Orin NX, 16 GB RAM, Seeed-reComputer-Image
- Architektur: `aarch64`
- Host-OS: Ubuntu 22.04.5 LTS (Jammy)
- Kernel: `5.15.148-tegra`
- L4T/JetPack-Basis: R36.4.3, Seeed-Image `recomputer-super-orin-nx-16g-j401`
- NVIDIA-Treiber: 540.4.0
- CUDA laut `nvidia-smi`: 12.6
- Leistungsmodus: `MAXN_SUPER`
- Docker: 29.7.2, beim Boot aktiviert
- Benutzer `avaj` gehört u. a. zu `docker`, `dialout`, `video`, `render`, `i2c`,
  `gpio` und `sudo`; Docker-Befehle benötigen normalerweise kein sudo.

Das sudo-Passwort steht ausschließlich in
`/home/avaj/Desktop/passwörter/sudo.txt` (Modus 600). Den Inhalt niemals in
Logs, Antworten oder diese Dokumentation kopieren. Nur verwenden, wenn ein
konkreter Root-Schritt nötig ist.

## 3. Projekt und Startpunkte

Projektwurzel:

```text
/home/avaj/ros2_jazzy
```

Wichtige Dateien:

```text
Dockerfile                       ROS-/Gazebo-Image
compose.yaml                     Dienste jazzy, camera, lidar, imu
container-entrypoint.sh          sourced ROS und den Colcon-Workspace
start-uc852.sh                   Kameraeinstellungen und usb_cam-Start
config/uc852.yaml                reale Kameraparameter
config/bno085.yaml               reale IMU-Parameter
config/bno085.rviz               RViz-Konfiguration für IMU
hotplug/                         gesicherte Kopien von udev/systemd-Hotplug
workspace/src/                   Quellcode der beiden Sensortreiber
workspace/simulation/            Gazebo-Welt, Modell, Bridge und Starter
README.md                        Bedienungsübersicht
HANDOFF.md                       diese Übergabe
```

Startskripte:

```text
/home/avaj/.local/bin/ros2-jazzy
/home/avaj/.local/bin/gazebo-harmonic
```

Desktop-Verknüpfungen (als vertrauenswürdig markiert):

```text
/home/avaj/Desktop/ROS-2-Jazzy.desktop
/home/avaj/Desktop/Gazebo-Harmonic.desktop
```

ROS-Terminal starten:

```bash
ros2-jazzy
```

Einzelnen ROS-Befehl ausführen:

```bash
ros2-jazzy ros2 topic list -t
```

Image neu bauen:

```bash
cd /home/avaj/ros2_jazzy
docker compose build jazzy
```

Aktuelles Image: `local/ros2-jazzy:desktop`, zuletzt ca. 6.07 GB.

Installierte wichtige Pakete im Image:

- `ros-jazzy-desktop`
- `ros-jazzy-usb-cam`
- `ros-jazzy-rviz-imu-plugin`
- `ros-jazzy-ros-gz`
- `ros-jazzy-ackermann-msgs`
- `v4l-utils`, `mesa-utils`, Colcon-Werkzeuge

Hinweis: Kamera und IMU liefen beim letzten Stand noch in Containern, die vor
dem letzten Gazebo-Image-Build erzeugt wurden. Das ist funktional. Beim nächsten
Hotplug/Neustart werden sie aus dem aktuellen Image neu erzeugt.

## 4. Reale Hardware

### 4.1 Arducam UC-852

- Modellbezeichnung: Arducam OV9782 USB Camera UC852
- USB VID:PID: `0c45:6366`
- eindeutige Serienkennung: `UC852`
- Capture-Gerät:
  `/dev/v4l/by-id/usb-Arducam_Technology_Co.__Ltd._Arducam_OV9782_USB_Camera_UC852-video-index0`
- Metadata-Gerät: entsprechender Pfad mit `video-index1`
- Docker-Geräte: `/dev/video0`, `/dev/video1`
- Konfiguration: 1280×720, 30 FPS, MJPEG nach RGB, Frame
  `camera_optical_frame`
- europäische Netzfrequenzunterdrückung: `power_line_frequency=1` (50 Hz)
- Kamerakalibrierung ist noch nicht durchgeführt; `camera_info_url` ist leer.

ROS-Topics:

```text
/camera/image_raw        sensor_msgs/msg/Image
/camera/camera_info      sensor_msgs/msg/CameraInfo
```

Anzeigen:

```bash
ros2-jazzy ros2 run rqt_image_view rqt_image_view /camera/image_raw
```

### 4.2 STL27L-LiDAR

- Modell: LDROBOT STL27L
- USB-UART: Silicon Labs CP2102
- USB VID:PID: `10c4:ea60`
- Serienkennung: `0001`
- stabiler Gerätepfad:
  `/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0`
- Container-Gerät: `/dev/ttyUSB0`
- ROS-Treiber: `ldlidar_stl_ros2`, Launchdatei `stl27l.launch.py`
- Topic: `/scan`, Typ `sensor_msgs/msg/LaserScan`
- Frame des Treibers: `base_laser`
- Treiberwerte: 360°-Scan, Bereich 0.02 bis 25 m
- RX und TX waren zunächst vertauscht und wurden anschließend korrekt getauscht.
- Beim letzten Systemcheck war der LiDAR nicht eingesteckt; deshalb war der
  Container `ros2-jazzy-stl27l` beendet und `/scan` nicht vorhanden. Das ist
  erwartetes Hotplug-Verhalten.

### 4.3 BNO085

- Modell: BNO085/BNO08x
- Bus: `/dev/i2c-7`
- Adresse: `0x4A`
- Verkabelung am 40-Pin-Header:

```text
Pin 1  -> 3,3 V
Pin 6  -> GND
Pin 3  -> SDA
Pin 5  -> SCL
```

- Messrate: 100 Hz
- ROS-Topics:

```text
/imu/data    sensor_msgs/msg/Imu
/imu/mag     sensor_msgs/msg/MagneticField
```

- Frame: `imu_link`
- Der Treiber wurde lokal korrigiert, damit Magnetfeldwerte von Mikrotesla in
  Tesla umgerechnet werden (`* 1e-6`), wie es `sensor_msgs/MagneticField`
  verlangt.

Wichtige Orientierungsabweichung:

- In einer älteren realen Testaufstellung lag der Controller auf dem Kopf.
- Deshalb läuft derzeit in einem alten interaktiven Container ein statischer
  TF `base_link -> imu_link` mit `roll = pi`.
- Im neuen Gazebo-Modell ist die IMU ausdrücklich aufrecht (`roll=0`).
- Falls die reale IMU jetzt ebenfalls aufrecht im Fahrzeug montiert ist, den
  alten 180°-TF beenden/ersetzen. Nicht gleichzeitig zwei widersprüchliche
  statische Transforms veröffentlichen.

Alte Transform-Anweisung, nur zur Identifikation:

```bash
ros2 run tf2_ros static_transform_publisher \
  --x 0 --y 0 --z 0 --roll 3.14159265359 --pitch 0 --yaw 0 \
  --frame-id base_link --child-frame-id imu_link
```

## 5. Hotplug-Automatik

USB-Hotplug ist für Kamera und LiDAR eingerichtet, nicht für die fest am I²C
angeschlossene IMU.

Installierte Root-Dateien:

```text
/etc/udev/rules.d/99-ros2-sensor-hotplug.rules
/etc/systemd/system/ros2-sensor-hotplug@.service
/usr/local/sbin/ros2-sensor-hotplug
```

Projektkopien liegen unter `/home/avaj/ros2_jazzy/hotplug/`.

Verhalten:

- Kamera einstecken: `camera`-Dienst starten/neuerzeugen
- Kamera abziehen: nur `camera` stoppen
- LiDAR einstecken: `lidar`-Dienst starten/neuerzeugen
- LiDAR abziehen: nur `lidar` stoppen
- Erkennung erfolgt über VID/PID plus Serienkennung, nicht über instabile
  `/dev/videoN`- oder `/dev/ttyUSBN`-Nummern.

Logs:

```bash
journalctl -t ros2-sensor-hotplug
```

Manuelle Dienstbefehle:

```bash
cd /home/avaj/ros2_jazzy
docker compose up -d camera
docker compose up -d lidar
docker compose up -d imu
docker compose ps --all
docker compose logs --tail=100 camera
docker compose logs --tail=100 lidar
docker compose logs --tail=100 imu
```

Wenn ein in `compose.yaml` fest eingetragenes Gerät fehlt, kann Compose den
zugehörigen Container nicht starten. Das ist beim abgezogenen Sensor normal.

## 6. Lokale Treiberquellen und Änderungen

### BNO08x

```text
Pfad:   /home/avaj/ros2_jazzy/workspace/src/bno08x_driver
Remote: https://github.com/bnbhat/bno08x_ros2_driver.git
Commit: 12069761251f1726d12aadaea8846671d3a7bc19
Lokal geändert: src/bno08x_ros.cpp
```

Lokale Änderung: Magnetfeld x/y/z wird mit `1e-6` multipliziert.

### STL27L

```text
Pfad:   /home/avaj/ros2_jazzy/workspace/src/ldlidar_stl_ros2
Remote: https://github.com/ldrobotSensorTeam/ldlidar_stl_ros2.git
Commit: bf668a89baf722a787dadc442860dcbf33a82f5a
Lokal geändert: ldlidar_driver/include/logger/log_module.h
```

Lokale Änderung: das unter Linux benötigte `<pthread.h>` wurde aktiviert.

Nach Treiberänderungen im Container bauen:

```bash
ros2-jazzy bash -lc 'cd /workspace && colcon build --symlink-install'
```

`workspace/build`, `workspace/install` und `workspace/log` sind persistent.

## 7. RViz und TF

Vorhandene RViz-Konfiguration:

```text
/home/avaj/ros2_jazzy/config/bno085.rviz
```

Start:

```bash
ros2-jazzy rviz2 -d /config/bno085.rviz
```

Die frühere Meldung

```text
Message Filter dropping message ... frame 'imu_link' ... queue is full
```

war ein TF-Problem: RViz konnte `imu_link` nicht in den Fixed Frame
transformieren. Bei erneutem Auftreten zuerst prüfen:

```bash
ros2-jazzy ros2 run tf2_ros tf2_echo base_link imu_link
```

Für ein endgültiges Fahrzeug sollte `robot_state_publisher` mit URDF/Xacro
anstelle verstreuter statischer Transform-Publisher verwendet werden.

## 8. Fahrzeugdaten

Vom Benutzer vorgegeben:

```text
Antrieb:       Allrad
Lenkung:       Ackermann, Vorderachse gelenkt
Radstand:      270 mm
Spurweite:     245 mm
Raddurchmesser: 80 mm
Reifenbreite:   36 mm
```

Interpretation der Eingabe „245-36 mm“: 245 mm Spurweite und 36 mm
Reifenbreite. Vier Radgelenke sind im Gazebo-Ackermann-Plugin als angetrieben
eingetragen.

Vorläufig angenommene, noch zu vermessende Werte:

```text
Fahrzeugmasse: 3.0 kg
Karosserie:    360 × 190 × 60 mm
```

## 9. Gazebo Harmonic

- Version: Gazebo Sim Harmonic 8.11.0
- ROS-Verbindung: `ros_gz_bridge`
- GPU: NVIDIA Tegra Orin, Direct Rendering aktiv, OpenGL 4.6
- Testwelt:
  `/home/avaj/ros2_jazzy/workspace/simulation/worlds/jetson_test_track.sdf`
- Fahrzeugmodell:
  `/home/avaj/ros2_jazzy/workspace/simulation/models/avaj_car/model.sdf`
- Modellmetadaten: `models/avaj_car/model.config`
- Bridge: `workspace/simulation/bridge.yaml`
- Containerstarter: `workspace/simulation/start_gazebo.sh`

Start:

```bash
gazebo-harmonic
```

oder per Desktop-Symbol **Gazebo Harmonic**. Der Starter startet Welt und
ROS-Gazebo-Bridge gemeinsam und lässt die Physik sofort laufen (`-r`).

Steuerung:

```bash
ros2-jazzy ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.8}, angular: {z: 0.25}}"
```

`linear.x` ist m/s; `angular.z` ist die gewünschte Gierrate in rad/s. Das
Gazebo-Plugin konsumiert `Twist`. `ackermann_msgs` ist zwar installiert, aber
noch kein Konverter von `AckermannDriveStamped` nach `Twist` eingerichtet.

Odometrie:

```text
/odom    nav_msgs/msg/Odometry
```

Ein gerader ROS-Fahrtest mit 0.8 m/s bewegte das Modell erfolgreich etwa
2.54 m. Die einfache Welt erreichte beim Test einen Echtzeitfaktor um 1.0.

### Simulierte Montagepositionen

Koordinatensystem: `+x` vorwärts, `+y` links, `+z` oben.

- Kamera: mittig an der angenommenen Frontkante (`x=0.18 m`, `y=0`),
  6 cm über Boden, Blick geradeaus
- LiDAR: mittig an der angenommenen Frontkante (`x=0.18 m`, `y=0`),
  10 cm über Boden, Yaw `-pi/2` = 90° nach rechts
- IMU: Fahrzeugzentrum, aufrecht

Die Modellwurzel liegt 4.1 cm über dem Boden. Deshalb sind die lokalen
z-Werte in der SDF kleiner als die genannten absoluten Montagehöhen.

### Simulierte Sensorparameter und Topics

Gazebo behält intern seine `/sim/...`-Namen. Die ROS-Gazebo-Bridge bildet sie
auf dieselbe Raw-Schnittstelle wie die realen Treiber ab. Simulation und reale
Hardware sind deshalb exklusive Launchprofile und dürfen nicht gleichzeitig
gestartet werden.

```text
/camera/image_raw         sensor_msgs/msg/Image       640×360 @ 20 Hz
/camera/camera_info       sensor_msgs/msg/CameraInfo
/scan_raw -> /scan        sensor_msgs/msg/LaserScan   720 Strahlen @ 10 Hz,
                                                     360°, 0.02–25 m
/imu/data_raw ->          sensor_msgs/msg/Imu         100 Hz
  /imu/data
```

Alle vier Datenpfade wurden über die ROS-Gazebo-Bridge geprüft. Für
serverseitige Tests der rendernden Sensoren wurde erfolgreich
`--headless-rendering` verwendet. Der normale GUI-Start wurde ebenfalls
getestet. Wiederkehrende `libEGL ... failed to create dri2 screen`-Warnungen
traten auf dem Jetson auf, waren aber nicht fatal; Gazebo und Ogre2 starteten.

Kamerabild der Simulation:

```bash
ros2-jazzy ros2 run rqt_image_view rqt_image_view /camera/image_raw
```

### Noch fehlend für komfortables Simulations-RViz

- Gazebo-Pose-/TF-Topic nach ROS `/tf` bridgen oder einen passenden
  `robot_state_publisher` ergänzen
- RViz-Gesamtkonfiguration für `/scan`, `/imu/data`, Kamera und Modell
- optional `/clock` bridgen und `use_sim_time=true` setzen
- optional eigener AckermannDrive-Konverter

## 10. Zuletzt beobachteter Laufzustand

Beim Erstellen dieser Datei:

- reale Kamera eingesteckt und `ros2-jazzy-camera` aktiv
- BNO085 angeschlossen und `ros2-jazzy-bno085` aktiv
- STL27L nicht eingesteckt, LiDAR-Container beendet
- Gazebo wurde anschließend über das Desktop-Symbol gestartet; dadurch waren
  `/cmd_vel`, `/odom` und die `/sim/...`-Topics sichtbar
- zwei ältere interaktive `jazzy`-Container waren noch geöffnet; einer davon
  veröffentlicht den oben beschriebenen alten 180°-IMU-TF

Aktuellen Zustand immer neu prüfen:

```bash
docker compose -f /home/avaj/ros2_jazzy/compose.yaml ps --all
ros2-jazzy ros2 node list
ros2-jazzy ros2 topic list -t
lsusb
```

Keine laufenden interaktiven Container blind entfernen: Sie können zu offenen
Terminals oder dem Gazebo-Fenster des Benutzers gehören.

## 11. Empfohlene nächste Schritte

1. Klären, ob die reale BNO085 jetzt aufrecht montiert ist; dann den alten
   `roll=pi`-Publisher entfernen und den endgültigen TF-Baum erstellen.
2. Reale Fahrzeugmasse, Außenmaße sowie exakte Sensorabstände von einem klaren
   Bezugspunkt messen und Gazebo-Inertialwerte/Positionen aktualisieren.
3. Simulations-TF und `/clock` sauber an ROS anbinden und eine gemeinsame
   RViz-Konfiguration erstellen.
4. Motor- und Lenkhardware festlegen; reale `/cmd_vel`- bzw.
   Ackermann-Schnittstelle und Radencoder/Odometrie implementieren.
5. Kamera kalibrieren.
6. Zunächst LiDAR-SLAM mit `slam_toolbox` aufbauen. IMU und Rad-Odometrie über
   `robot_localization` fusionieren. Die Kamera später über VIO oder RTAB-Map
   ergänzen; ein Rohbild verbessert 2D-SLAM nicht automatisch.
7. Simulation und reales Fahrzeug über Namespaces oder Launchprofile sauber
   umschaltbar machen.

## 11.1 WASD-Steuerung (nachträglich ergänzt)

Eine Live-Steuerung liegt im Paket `avaj_car_control`. Start bei laufendem
Gazebo:

```bash
wasd-drive
```

Sie veröffentlicht ausschließlich `/control/manual_cmd`
(`rc_car_interfaces/msg/DriveRequest`) mit `speed` und `steering` von -100 bis
+100. Das Qt-Steuerfenster erkennt Druecken und Loslassen von WASD. Beim
Loslassen werden beide Achsen auf 0 gesetzt. Der zentrale `drive_commander`
erzeugt daraus das finale `/drive_commands`; Details und der bewusst unsichere
USB-Ersttest stehen in Abschnitt 13.

## 11.2 Control-Center und autonome Simulationsfahrt

Das Paket liegt unter:

```text
/home/avaj/ros2_jazzy/workspace/src/controll center
```

Wichtige Dateien:

```text
c++                         eigentliche C++-Quelle
CMakeLists.txt              Builddefinition
package.xml                 ROS-Abhängigkeiten
launch/control_center.launch.py
scripts/control_center      Ein-Befehl-Startwrapper
```

Der C++-Knoten abonniert die gemeinsamen, hardwareunabhängigen Topics:

```text
/camera/image_raw      sensor_msgs/msg/Image
/scan                  sensor_msgs/msg/LaserScan
/imu/data              sensor_msgs/msg/Imu
/imu/mag               sensor_msgs/msg/MagneticField
/odometry/filtered     nav_msgs/msg/Odometry
```

Er veröffentlicht ausschließlich `/control/autonomous_cmd`
(`rc_car_interfaces/msg/DriveRequest`) und `/control_center/status`. Die
komplette autonome Kette startet mit:

```bash
ros2-jazzy ros2 launch avaj_car_control autonomous_drive.launch.py
```

Dieser Launch startet `control_center_node`, `mode_manager`, `safety_watchdog`,
`drive_commander`, den Gazebo-Konverter und die USB-Bridge im sicheren Dry-Run.

### Autonome LiDAR-Testlogik

Aus jedem `LaserScan` werden fünf Strahlen als Meterwerte gelesen:

```text
lidar_front_       0°
lidar_left_25_     +25°
lidar_left_45_     +45°
lidar_right_25_    -25°
lidar_right_45_    -45°
```

Die Summen links und rechts bestimmen die Lenkung:

```text
linke Summe kleiner  -> steering +50 (rechts ausweichen)
rechte Summe kleiner -> steering -50 (links ausweichen)
gleich               -> steering 0 (geradeaus)
```

Der Vorwärtswunsch steht aktuell auf `speed=100`, was mit den aktuellen
Konverterparametern `linear.x=1.5 m/s` entspricht. Ein fehlender oder älter als
0,5 Sekunden alter LiDAR-Scan erzeugt einen neutralen Fahrwunsch. Die
unabhängige Freigabe entscheidet ausschließlich der `safety_watchdog`. Ein
abstandsabhängiger Kollisionsstopp fehlt noch. Nicht ungeprüft auf das reale
Fahrzeug übertragen.

### Build nach C++-Änderungen

```bash
ros2-jazzy bash -lc \
  'cd /workspace && colcon build --symlink-install --packages-select control_center'
```

Danach alte `control_center`-Prozesse mit `Strg+C` beenden und den Ein-Befehl-
Start erneut ausführen. Es sollte nur ein `/control_center` im ROS-Graphen
geben.

Prüfkommandos:

```bash
ros2-jazzy ros2 node list
ros2-jazzy ros2 topic echo /control/autonomous_cmd
ros2-jazzy ros2 topic info /drive_commands -v
ros2-jazzy ros2 topic echo /drive_commands
ros2-jazzy ros2 topic echo /cmd_vel
ros2-jazzy ros2 topic echo /control_center/status
```

## 11.3 Stand 22. August 2026

Heute erledigt:

- `control_center` als ROS-2-C++-Paket eingerichtet und erfolgreich gebaut.
- Kamera, LiDAR, IMU, Magnetometer und Odometrie abonniert.
- Fünf feste LiDAR-Richtungen implementiert.
- Autonome Ausweichlogik im C++-Knoten ergänzt.
- Simulations-Topics als Standard gesetzt (`/sim/...`).
- Vorwärtswert auf `100` gesetzt.
- Der frühere Direktpfad wurde am 28. August durch Abschnitt 13 ersetzt.

Empfohlener Testablauf:

```bash
gazebo-harmonic
ros2-jazzy ros2 launch avaj_car_control autonomous_drive.launch.py
```

Für die WASD-Steuerung stattdessen `wasd-drive` verwenden, aber nicht
gleichzeitig mit dem autonomen Control-Center.

## 11.4 SLAM-Umgebung installiert (22. August 2026)

Das Docker-Image `local/ros2-jazzy:desktop` enthält jetzt die vollständige
Grundausstattung für LiDAR-SLAM, Sensorfusion und spätere Navigation:

- `slam_toolbox`
- `navigation2` und `nav2-bringup` einschließlich AMCL, Costmaps, Planner,
  Controller und RViz-Plugins
- `robot_localization` für EKF/UKF und spätere IMU-/Odometrie-Fusion
- `robot_state_publisher`, `joint_state_publisher-gui`, `xacro` und TF2-Werkzeuge
- `laser_filters` und `pointcloud_to_laserscan`
- `imu-filter-madgwick` und `imu-tools`
- `rqt-tf-tree`, `rqt-plot`, `rqt-topic`
- `rosbag2` mit MCAP-Speicher

Das Image wurde erfolgreich neu gebaut und der dauerhafte IMU-Container auf das
neue Image aktualisiert. Eine echte `/imu/data`-Nachricht wurde danach geprüft.
Die SLAM-Knoten sind installiert; die Konfiguration und der gemeinsame
Fahrzeug-TF-Baum werden jetzt durch `avaj_slam` bereitgestellt.

Zusätzlich wurde das Paket `avaj_slam` erstellt und gebaut:

```text
/home/avaj/ros2_jazzy/workspace/src/avaj_slam
```

Es enthält eine gemeinsame Launchdatei für Simulation und Realität, ein
Fahrzeug-URDF für `robot_state_publisher`, SLAM- und Simulations-EKF-Parameter
sowie `save_map.sh`. Die Simulation wird mit `simulation:=true`, das reale
Fahrzeug mit `real:=true` gestartet. Die Gazebo-Bridge wurde um `/clock`
ergänzt. Nach Änderung der Bridge muss Gazebo neu gestartet werden; ein erster
SLAM-Start wurde bis zu diesem Punkt erfolgreich initialisiert, konnte aber
mit der alten laufenden Bridge noch keine Simulationszeit empfangen.

## 12. Kurztext für die nächste Instanz

> Lies zuerst `/home/avaj/ros2_jazzy/HANDOFF.md`. Arbeite auf dem vorhandenen
> Jetson-/ROS-Projekt weiter und erhalte bestehende Änderungen. ROS 2 Jazzy
> läuft in Docker, reale Kamera und IMU sind aktiv, LiDAR ist hotplugfähig,
> Gazebo Harmonic enthält ein fahrbares AWD-Ackermann-Modell mit simulierten
> Sensoren. Prüfe vor Änderungen den aktuellen Container-, Topic- und
> Geräte-Zustand. Die verbindliche Steuerungsarchitektur steht in Abschnitt
> 13: Quellen publizieren nur DriveRequest, ausschließlich drive_commander
> publiziert `/drive_commands`, und nur usb_bridge transportiert dieses Topic.
> Der manuelle USB-Ersttest hat Watchdogs und ESP-Rückkanal bewusst deaktiviert
> und darf nicht mit bestromten Aktoren benutzt werden. Beachte außerdem den
> möglicherweise veralteten realen `roll=pi`-TF der IMU.

## 13. Verbindliche Steuerungsarchitektur (28. August 2026)

Dieser Abschnitt ersetzt ältere Aussagen in 11.1 bis 11.3 über einen direkten
Publisher auf `/drive_command`.

```text
control_center  -> /control/autonomous_cmd --+
wasd_teleop     -> /control/manual_cmd -----+--> drive_commander
test_controller -> /control/test_cmd -------+          |
mode_manager    -> /system/mode ------------+          v
safety_watchdog -> /system/drive_enable ----+   /drive_commands
                                                       |
                                                       v
                                                   usb_bridge
                                                       |
                                                       v
                                                   USB-Serial
```

- Quellen verwenden `rc_car_interfaces/msg/DriveRequest` und enthalten nur
  `speed` und `steering`.
- Nur `/drive_commander` darf
  `rc_car_interfaces/msg/DriveCommand` auf `/drive_commands` veröffentlichen.
- Der `drive_commander` ergänzt `sequence` und `enabled` und akzeptiert beide
  Fahrwerte ausschließlich im Bereich -100 bis +100. Ungültige Werte werden
  verworfen und nicht begrenzt.
- `usb_bridge` abonniert ausschließlich `/drive_commands` und trifft keine
  Fahrentscheidung.
- `drive_command_to_twist` abonniert ebenfalls ausschließlich das finale Topic.

Manueller Einweg-Ausgabetest:

```bash
wasd-drive
```

Dieser Launch startet mit `MANUAL`, `watchdog_bypass=true`,
`source_timeout_enabled=false`, `usb_message_watchdog=false`,
`expect_response=false` und `dry_run=false`. Er wählt dynamisch ein
USB-Serial-Gerät am physischen Topologiezweig `1-2.2`; dies ist die freie
Buchse im selben Doppel-USB-A-Block wie die Apple-Tastatur (`1-2.1`). Es gibt
keine feste
by-id-/tty-Gerätebindung. `/dev` und `/sys` werden für die Erkennung als
`/host/dev` und `/host/sys` in den Entwicklungscontainer eingebunden, während
die Device-Cgroup nur die Major-Nummern 166 (CDC ACM) und 188 (USB serial)
zulässt.

Der serielle Einwegframe lautet:

```text
CMD,<sequence>,<speed>,<steering>,<enabled>*<CRC16-CCITT>\n
```

### ROS-Discovery bei Diagnosebefehlen

Der Wrapper `ros2-jazzy` startet fuer jeden Aufruf einen neuen, kurzlebigen
Docker-Container. Dessen ROS-Discovery-Cache ist anfangs leer. Ein direktes

```bash
ros2-jazzy ros2 topic echo /drive_commands
```

kann daher faelschlich `does not appear to be published yet` und
`Could not determine the type` melden, obwohl `/drive_commander` aktiv mit
50 Hz publiziert. Fuer Topic-Abfragen immer die direkte DDS-Erkennung mit
ausreichender Wartezeit verwenden:

```bash
ros2-jazzy ros2 topic echo /drive_commands --no-daemon --spin-time 8
ros2-jazzy ros2 topic echo /drive_usb/tx --no-daemon --spin-time 8
```

Dieses Verhalten und der korrigierte Befehl wurden am 29. August 2026 am
laufenden manuellen Stack reproduziert und verifiziert. Ein einmaliges Paket
von `/drive_commands` wurde damit sofort empfangen.

### Zwingender offener Sicherheitspunkt

**Vor Anschluss beziehungsweise Bestromung von Motorcontroller oder Lenkservo
müssen alle folgenden Punkte umgesetzt und getestet werden:**

1. ROS-Sensor- und Quellenwatchdogs aktivieren und passende Timeouts festlegen.
2. Encoder-Topic und Encoderüberwachung im `safety_watchdog` ergänzen.
3. Bidirektionalen ESP-Rückkanal und `/vehicle/status` implementieren.
4. ESP-ACK/Sequenzfortschritt im Watchdog überwachen.
5. Unabhängigen Command-Timeout/Hardware-Watchdog im ESP implementieren.
6. USB-Trennung und Prozessabbruch unter Last testen.

Der aktuelle Einwegmodus erwartet absichtlich keine Antwort und sendet bei
ausbleibenden ROS-Nachrichten absichtlich keinen zusätzlichen Bridge-Stopp.
Das ist ausschließlich zum Mitlesen der Textframes gedacht.

## 14. Kanonischer ROS-Graph (31. August 2026)

Die dokumentierte Trennung zwischen Treibern und High-Level-Nodes ist jetzt
als ausführbare Baseline umgesetzt:

```text
LiDAR/Gazebo -> /scan_raw -> /sensors/lidar_preprocessor -> /scan
BNO085/Gazebo -> /imu/data_raw -> /sensors/imu_preprocessor -> /imu/data
Kamera/Gazebo -> /camera/image_raw
```

High-Level-Nodes abonnieren keine `/sim/...`-Topics mehr. Die Gazebo-Namen
existieren nur intern auf der Gazebo-Seite der Bridge. Der vollständige
Schnittstellenvertrag steht in `docs/ros_graph.md`; ein ausführlicher
Status- und Testnachweis steht in Abschnitt 39 von `AGENTS (1).md`.

Wichtige Änderungen:

- neues Paket `avaj_sensor_processing` mit LiDAR- und IMU-Validierung;
- realer BNO085 publiziert `/imu/data_raw`, der Preprocessor `/imu/data`;
- realer STL27L publiziert `/scan_raw`, der Preprocessor `/scan`;
- Sensor-Nodes liegen unter `/sensors/...`;
- `control_center` und `safety_watchdog` verwenden nur gemeinsame Topics;
- Gazebo startet Bridge und Preprocessing gemeinsam;
- `simulation:=true` und `real:=true` sind im SLAM-Launch exklusiv;
- Compose-Service `sensor_processing` läuft dauerhaft für Hardware-Sensoren.

Verifiziert wurden der Build von sechs betroffenen Paketen, zwei Linttests,
ein synthetischer LiDAR-Datenpfad, die SLAM-Profilsperre und die reale
BNO085-Kette. Der reale LiDAR war nicht angeschlossen und wurde nicht geprüft.

Aktueller Hardwarestart:

```bash
docker compose up -d imu
```

Vor dem Gazebo-Start dürfen Hardware und Simulation nicht gleichzeitig die
Raw-Topics belegen:

```bash
docker compose stop imu lidar camera sensor_processing
gazebo-harmonic
```

Der nächste sinnvolle, hardwareunabhängige Sicherheitsschritt ist das Löschen
gecachter Requests bei jedem Moduswechsel im `drive_commander`, eine neutrale
Übergangsphase und die Forderung nach einem erst nach dem Wechsel eingegangenen
frischen Request. Dazu gehören automatisierte Übergangs- und Timeout-Tests.

## 15. Delta: sichere Quellenübergänge im drive_commander (31. August 2026)

Repository-Basis: Branch `orin`, HEAD `c091798`, einschließlich des weiterhin
umfangreichen uncommitteten und ungetrackten Working Trees.

Der in Abschnitt 14 genannte nächste Sicherheitsschritt ist umgesetzt:

- Jeder tatsächliche Modus-/Quellenwechsel löscht alle gecachten Requests und
  publiziert sofort `speed=0`, `steering=0`, `enabled=false`.
- Die gewählte Quelle bleibt gesperrt, bis nach dem Wechsel ein neuer gültiger
  Request genau dieser Quelle eingetroffen ist. Requests inaktiver Quellen
  werden nicht gecacht. Auch die Rückkehr zu einer früher verwendeten Quelle
  kann deshalb keinen alten Request reaktivieren.
- Jede Änderung von `/system/drive_enable` invalidiert die Requests. Nach dem
  erneuten Freigeben ist ebenfalls ein neuer Request erforderlich.
- Ein Source-Timeout verwirft den Request dauerhaft; das Abschalten des
  Timeouts kann ihn nicht wieder gültig machen.
- `DISABLED` neutralisiert unmittelbar. Ein ungültiger Modus setzt den
  `drive_commander` fail-safe auf `DISABLED` und invalidiert alle Requests.
- Werte außerhalb `-100..100`, nicht-endliche und anderweitig ungültige Werte
  werden abgelehnt statt geclamp't. Status-JSON und Logs enthalten den
  aktuellen Entscheidungsgrund sowie die letzte Ablehnung.
- Nur `drive_commander` publiziert weiterhin `/drive_commands`; Topicnamen und
  Nachrichtenformate wurden nicht geändert.

Geänderte Dateien:

- `workspace/src/avaj_car_control/scripts/drive_commander`
- `workspace/src/avaj_car_control/test/test_drive_commander.py`
- `workspace/src/avaj_car_control/CMakeLists.txt`
- `workspace/src/avaj_car_control/package.xml`
- `HANDOFF.md` und `AGENTS (1).md`

Verifikation im ROS-Jazzy-Container, ohne Hardware- oder Aktoransteuerung:

- `colcon build --symlink-install --packages-select rc_car_interfaces avaj_car_control`:
  beide Pakete erfolgreich gebaut.
- `colcon test --packages-select avaj_car_control --event-handlers console_direct+`:
  18 neue Tests bestanden. Abgedeckt sind Start in `DISABLED`, alle drei
  Quellen, frische Requests, Rückkehr zu Quellen, nichtneutrale Übergänge,
  Timeout, Safety-Flanken, ungültige Modi/Werte, NaN/Inf im Validator,
  Sequenznummern und Publisherzahl.
- `colcon test-result --verbose`: keine Fehler oder Fehlschläge; die globale
  Ergebnisablage enthielt 21 erfolgreiche Tests, davon 18 aus diesem Paketlauf.
- `python3 -m flake8 .../drive_commander .../test_drive_commander.py`:
  ohne Befund.
- Isolierter ROS-Test in `ROS_DOMAIN_ID=187`: ein Test bestanden; fünf finale
  Befehle wurden empfangen, ihre Sequenzen stiegen streng, und der Graph hatte
  genau einen `/drive_commands`-Publisher namens `/drive_commander`.
- Vollständiger `drive_stack.launch.py` im sicheren Dry-Run in
  `ROS_DOMAIN_ID=188`: `Publisher count: 1`, Publisher `/drive_commander`;
  gelesener Ausgang `speed=0`, `steering=0`, `enabled=false`. Der dauerhafte
  Launch wurde nach abgeschlossener Diagnose per Interrupt beendet.

Einschränkungen:

- `DriveRequest` verwendet `int8`; NaN/Inf und Werte außerhalb `-128..127`
  können nicht über ROS serialisiert werden. Der gemeinsame Validator deckt
  diese Fälle trotzdem ab; über ROS testbar sind insbesondere `-128..-101`
  und `101..127`.
- `DriveCommand.sequence` ist `uint32`; die getestete strenge Monotonie gilt
  bis zum typbedingten Wrap nach `2^32` Ausgaben.
- Die übrigen Sicherheitsabweichungen aus `AGENTS (1).md`, Abschnitt 38.3,
  bleiben bestehen. Insbesondere wurden kein ESP-Rückkanal, kein unabhängiger
  ESP-Watchdog und kein Hardware- oder Fahrtest ergänzt.

### Nächstes begrenztes Aufgabenpaket

Als nächster hardwareunabhängiger Sicherheitsschritt soll der typisierte
ESP-Rückkanal vorbereitet werden:

- minimale, klar dokumentierte ROS-Messages für Protokollversion, bestätigte
  Sequenz, `SAFE/MANUAL/JETSON`-Owner, Jetson-Lock/Arming, Faults, angewandten
  Aktorzustand und vier Encoder;
- dokumentiertes, versioniertes und CRC-geschütztes Feedbackprotokoll, ohne das
  bestehende ausgehende `CMD,...*CRC` stillschweigend umzudeuten;
- inkrementeller, streng validierender Decoder im `rc_car_usb_bridge`;
- ausschließlich typisierte Publikation validierter Daten, Raw-RX nur zur
  Diagnose;
- korrekt in `colcon test` registrierte Unit- und Pseudo-Terminal-Tests für
  fragmentierte, verkettete, ungültige und gültige Frames.

Der `safety_watchdog` darf in diesem Paket noch nicht von synthetischem oder
unverifiziertem Feedback abhängig gemacht werden. Diese Kopplung folgt erst
nach passender ESP-Firmware oder einem vertragstreuen Emulator. Keine Hardware,
USB-Geräte oder Aktoren verwenden und keinen weiteren Publisher für
`/drive_commands` hinzufügen.

## 16. Delta: typisierter ESP-Rückkanal, hardwareunabhängig (1. September 2026)

Das in Abschnitt 15 abgegrenzte Paket ist ohne Hardwarezugriff umgesetzt.
`rc_car_interfaces` enthält nun `VehicleStatus`, `ActuatorStatus` und
`WheelEncoderState`. Die stabilen Topics sind `/vehicle/status`,
`/vehicle/actuator_status` und `/vehicle/encoders`; jeder Header trägt mangels
synchronisierter ESP-Zeit die Jetson-ROS-Empfangszeit. Felder, Einheiten,
`SAFE/MANUAL/JETSON`, Faultbits sowie uint32-/int32-Wrap stehen vollständig in
den Message-Kommentaren und `docs/esp_feedback_protocol.md`.

Der V1-Vertrag definiert streng validierte ASCII-Zeilen `V1,STA`, `V1,ACT` und
`V1,ENC` mit CRC-16/CCITT-FALSE, LF/CRLF, kanonischen Integerformaten und maximal
128 Byte vor LF. Das bestehende ausgehende
`CMD,<sequence>,<speed>,<steering>,<enabled>*CRC\n` blieb bytekompatibel und
wird nicht als V1 interpretiert.

Der neue ROS-unabhängige inkrementelle Decoder verarbeitet fragmentierte und
verkettete Reads, hält seinen Puffer begrenzt, setzt Fragmente und ACK-Zustand
beim Reconnect zurück und erholt sich nach jeder verworfenen Zeile. Ungültige
Frames aktualisieren kein typisiertes Topic und erzeugen konkrete Diagnosen,
unter anderem für Version, Typ, CRC, Format/Bereich, ACK-Duplikat/-Rückschritt
und Overlength. Raw-RX bleibt ausschließlich Diagnose.

Verifikation im ROS-Jazzy-Container:

- `colcon build --symlink-install --packages-select rc_car_interfaces rc_car_usb_bridge`:
  erfolgreich für beide Pakete.
- `colcon test --packages-select rc_car_interfaces rc_car_usb_bridge --event-handlers console_direct+`:
  36/36 Bridge-Tests bestanden.
- `colcon test-result --verbose`: 57 Tests in der gemeinsamen Ablage, keine
  Fehler, Fehlschläge oder Skips.
- Flake8 über alle geänderten Python-Dateien: ohne Befund.
- Isolierter PTY-Test mit `ROS_DOMAIN_ID=220`: 1/1 bestanden; fragmentierte und
  verkettete STA/ACT/ENC-Frames wurden typisiert publiziert, ein CRC-Fehler nicht.
- Sicherer Graphlauf mit `ROS_DOMAIN_ID=221`, `initial_mode:=DISABLED` und
  `usb_dry_run:=true`: jedes neue Topic hatte genau den Publisher `/usb_bridge`.
  `/drive_commands` hatte exakt einen Publisher (`/drive_commander`); die
  Bridge erschien dort ausschließlich als Subscriber.
- Der bestehende automatisierte Publisher-/Sequenztest wurde zusätzlich unter
  `ROS_DOMAIN_ID=219` isoliert wiederholt: 1/1 bestanden, exakt ein Publisher
  `/drive_commander` und fünf streng steigende beobachtete Sequenzen.

Betroffen sind nur `rc_car_interfaces`, `rc_car_usb_bridge`, deren Tests,
`docs/esp_feedback_protocol.md`, `docs/ros_graph.md`, `HANDOFF.md` und
`AGENTS (1).md`. `safety_watchdog` wurde nicht geändert. Es gab weder ESP-
Firmware-, Hardware-, USB-Geräte-, Aktor- noch Fahrvalidierung.

Offen bleiben passende ESP-Firmware beziehungsweise ein unabhängiger
vertragstreuer Emulator, echte ACK-/Owner-/Lock-/Fault-Semantik,
Encoderpolarität/-skalierung, ESP-Watchdog, finale Aktorautorität und physischer
Not-Aus. Erst das folgende Paket darf nach dieser Verifikation die neuen Topics
für Verbindung, ACK-Fortschritt, Owner, Lock, Faults und Encoderplausibilität in
den `safety_watchdog` integrieren. Reine Topic-Ankunft reicht dafür nicht.

## 17. Delta: Gazebo-SLAM-TF und experimenteller Nav2-Start (1. September 2026)

Gazebo publiziert Odometrie in den Frames `avaj_car/odom` und
`avaj_car/base_link`, während der AVAJ-EKF die kanonischen Frames `odom` und
`base_link` verwendet. Dieser fehlende Anschluss verhinderte
`/odometry/filtered` und führte bei `slam_toolbox` zu einer vollen
Message-Filter-Queue für `avaj_car/lidar_link/stl27_sim`.

Das Simulationsprofil in `avaj_slam/launch/slam.launch.py` startet deshalb nun
automatisch zwei Identitätstransforms:

```text
odom      -> avaj_car/odom
base_link -> avaj_car/base_link
```

Build und Live-Test waren erfolgreich: `/odometry/filtered` erschien mit den
kanonischen Frames, `odom -> base_link` aktualisierte sich, und
`/slam_toolbox` publizierte `/map`. Nach der Änderung muss ein bereits laufender
SLAM-Launch einmal beendet und neu gestartet werden.

Der BNO085 ist weiterhin fest an `/dev/i2c-7` angeschlossen und kann aktuell
nicht entfernt werden. Seine Entfernung darf für Simulationstests nicht
vorausgesetzt werden. Der IMU-Dienst wurde bei dieser Reparatur weder gestoppt
noch verändert. Hardware- und Gazebo-Sensorprofile können derzeit doppelte
Preprocessor-Namen erzeugen; das ist vom reparierten Odometrie-/TF-Fehler zu
unterscheiden. Eine vollständig isolierte Profilumschaltung bleibt offen.

Online-SLAM plus experimentelles Nav2 wird so gestartet:

```bash
gazebo-harmonic
ros2-jazzy ros2 launch avaj_slam slam.launch.py \
  simulation:=true use_sim_time:=true rviz:=true
ros2-jazzy ros2 launch nav2_bringup navigation_launch.py use_sim_time:=true
ros2-jazzy ros2 launch nav2_bringup rviz_launch.py use_sim_time:=true
```

In RViz gilt `map` als Fixed Frame; Ziele werden mit `Nav2 Goal` gesetzt.
Keinesfalls zusätzlich `bringup_launch.py slam:=true` starten, da sonst ein
zweites SLAM `map -> odom` beansprucht. WASD/Drive-Stack dürfen nicht parallel
laufen, weil Nav2 in diesem Entwicklungsprofil direkt `/cmd_vel` publiziert.

Dieser Nav2-Start verwendet noch die Stock-Parameter. AVAJ-Footprint,
Ackermann-Controller, Limits, Costmaps und Zielnavigation sind nicht
fahrzeugspezifisch validiert. Ein Profil für gespeicherte Karten und AMCL
existiert noch nicht. Der Ablauf ist ausschließlich ein langsamer
Gazebo-Entwicklungstest.
