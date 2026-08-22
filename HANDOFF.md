# Übergabe: Jetson, ROS 2 Jazzy, Sensoren und Gazebo-Fahrzeug

Stand: 22. August 2026, Zeitzone Europe/Berlin

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

Die Simulation verwendet absichtlich `/sim/...`, damit reale und simulierte
Publisher gleichzeitig laufen können, ohne Messungen zu vermischen.

```text
/sim/camera/image_raw     sensor_msgs/msg/Image       640×360 @ 20 Hz
/sim/camera/camera_info   sensor_msgs/msg/CameraInfo
/sim/scan                 sensor_msgs/msg/LaserScan   720 Strahlen @ 10 Hz,
                                                     360°, 0.02–25 m
/sim/imu/data             sensor_msgs/msg/Imu         100 Hz
```

Alle vier Datenpfade wurden über die ROS-Gazebo-Bridge geprüft. Für
serverseitige Tests der rendernden Sensoren wurde erfolgreich
`--headless-rendering` verwendet. Der normale GUI-Start wurde ebenfalls
getestet. Wiederkehrende `libEGL ... failed to create dri2 screen`-Warnungen
traten auf dem Jetson auf, waren aber nicht fatal; Gazebo und Ogre2 starteten.

Kamerabild der Simulation:

```bash
ros2-jazzy ros2 run rqt_image_view rqt_image_view /sim/camera/image_raw
```

### Noch fehlend für komfortables Simulations-RViz

- Gazebo-Pose-/TF-Topic nach ROS `/tf` bridgen oder einen passenden
  `robot_state_publisher` ergänzen
- RViz-Gesamtkonfiguration für `/sim/scan`, `/sim/imu/data`, Kamera und Modell
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

Sie veröffentlicht `/drive_command` (`avaj_car_control/msg/DriveCommand`) mit
den Feldern `steering` und `acceleration`, jeweils 0 bis 100 und Neutralstellung
50. Das Qt-Steuerfenster erkennt Druecken und Loslassen von WASD: gehaltene
Tasten setzen die Achse direkt auf 0 oder 100, beim Loslassen springt sie auf
50 zurueck. Der Konverter erzeugt daraus `/cmd_vel`.

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

Der C++-Knoten abonniert standardmäßig die Simulationstopics:

```text
/sim/camera/image_raw  sensor_msgs/msg/Image
/sim/scan              sensor_msgs/msg/LaserScan
/sim/imu/data          sensor_msgs/msg/Imu
/imu/mag               sensor_msgs/msg/MagneticField
/odom                  nav_msgs/msg/Odometry
/drive_command         avaj_car_control/msg/DriveCommand
```

Er veröffentlicht `/drive_command` und `/control_center/status`. Der
Ein-Befehl-Start lautet:

```bash
ros2-jazzy ros2 run control_center control_center
```

Der Wrapper startet automatisch `control_center_node` und
`drive_command_to_twist`. Der Konverter veröffentlicht anschließend auf
`/cmd_vel` (`linear.x` in m/s, `angular.z` in rad/s).

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
linke Summe kleiner  -> steering 75 (rechts ausweichen)
rechte Summe kleiner -> steering 25 (links ausweichen)
gleich               -> steering 50 (geradeaus)
```

Der Vorwärtswert steht aktuell auf `acceleration=100`, was mit den aktuellen
Konverterparametern `linear.x=1.5 m/s` entspricht. Für diesen reinen Gazebo-
Test wurden Sicherheitsstopps entfernt; fehlende LiDARwerte werden als weit
entfernt behandelt. Nicht ungeprüft auf das reale Fahrzeug übertragen.

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
ros2-jazzy ros2 topic info /drive_command -v
ros2-jazzy ros2 topic echo /drive_command
ros2-jazzy ros2 topic echo /cmd_vel
ros2-jazzy ros2 topic echo /control_center/status
```

## 11.3 Stand 22. August 2026

Heute erledigt:

- `control_center` als ROS-2-C++-Paket eingerichtet und erfolgreich gebaut.
- Kamera, LiDAR, IMU, Magnetometer, Odometrie und Fahrbefehle abonniert.
- Fünf feste LiDAR-Richtungen implementiert.
- Autonome Ausweichlogik im C++-Knoten ergänzt.
- Simulations-Topics als Standard gesetzt (`/sim/...`).
- Sicherheitsstopps für den reinen Gazebo-Test entfernt.
- Vorwärtswert auf `100` gesetzt.
- ROS-Launch integriert, der Control-Center und Converter gemeinsam startet.
- Ein-Befehl-Start erfolgreich getestet.

Empfohlener Testablauf:

```bash
gazebo-harmonic
ros2-jazzy ros2 run control_center control_center
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
> Geräte-Zustand. Der aktuelle Test-Control-Center startet mit einem Befehl
> automatisch auch den DriveCommand-Konverter, nutzt standardmäßig `/sim/...`
> und fährt mit `acceleration=100` ohne Sicherheitsstopp. Beachte besonders
> den möglicherweise veralteten realen `roll=pi`-TF der IMU und übertrage die
> autonome Testlogik nicht ungeprüft auf das reale Fahrzeug.
