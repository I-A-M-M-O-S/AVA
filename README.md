# ROS 2 Jazzy auf dem Jetson

Der kanonische, zuletzt verifizierte Projektstand steht in
[`CURRENT_STATE.md`](CURRENT_STATE.md). Neue Entwickler und Agenten müssen diese
Datei vor Änderungen lesen.

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

`wasd-drive` startet die komplette manuelle Testkette:

```text
wasd_teleop -> /control/manual_cmd -> drive_commander
             -> /drive_commands -> usb_bridge -> USB-Serial
```

Der WASD-Node veröffentlicht mit 50 Hz ausschließlich
`/control/manual_cmd` (`rc_car_interfaces/msg/DriveRequest`). Die Fahrwerte
liegen zwischen -100 und +100:

- `steering`: -100 = ganz links, 0 = gerade, +100 = ganz rechts
- `speed`: -100 = voll rueckwaerts, 0 = Stopp, +100 = voll vorwaerts

Im Steuerfenster werden die Tasten gehalten: `W` setzt vorwaerts auf +100, `S`
rueckwaerts auf -100, `A` links auf -100 und `D` rechts auf +100. Beim Loslassen
springt die jeweilige Achse sofort auf 0 zurueck. Dadurch funktionieren auch
Kombinationen wie `W+A`. `Q` oder Escape beendet die Steuerung. Wenn das
Steuerfenster den Tastaturfokus verliert, wird aus Sicherheitsgruenden sofort
neutralisiert. Der `drive_commander` ergänzt Zeitstempel, Sequenz und die
separate Sicherheitsfreigabe. Er ist der einzige Publisher von
`/drive_commands` (`rc_car_interfaces/msg/DriveCommand`). Der Gazebo-Konverter
abonniert ebenfalls nur dieses finale Topic.

Der aktuelle `manual_usb_test.launch.py` ist absichtlich ein reiner
Ausgabetest: ROS-Quellenwatchdog, USB-Nachrichtenwatchdog und ESP-Rückkanal sind
deaktiviert. Solange dieser Testmodus verwendet wird, dürfen Motorcontroller
und Lenkservo nicht angeschlossen beziehungsweise nicht mit Leistung versorgt
werden.

Die autonome Kette startet sicher (USB zunächst Dry-Run) mit:

```bash
ros2-jazzy ros2 launch avaj_car_control autonomous_drive.launch.py
```

Der `control_center` veröffentlicht ausschließlich
`/control/autonomous_cmd`. `mode_manager`, `safety_watchdog` und
`drive_commander` entscheiden getrennt über Auswahl und Freigabe. Manuelle und
autonome Launches nicht gleichzeitig starten.

Die Testlogik besitzt noch keinen abstandsabhängigen Kollisionsstopp und ist
nur für Gazebo-Tests vorgesehen.

### ESP32-USB-Bridge

Die Bridge abonniert ausschließlich `/drive_commands` und erzeugt ein lesbares,
CRC-gesichertes Protokoll:

```bash
ros2-jazzy ros2 run rc_car_usb_bridge usb_bridge
ros2-jazzy ros2 topic echo /drive_usb/tx
ros2-jazzy ros2 topic echo /drive_usb/status
```

Ein Frame sieht beispielsweise so aus:

```text
CMD,42,30,-20,1*887F
```

Der Entwicklungscontainer erhält dynamischen Zugriff auf USB-CDC-Geräte
(`/dev/ttyACM*`) und USB-Serial-Adapter (`/dev/ttyUSB*`). Es gibt absichtlich
keine feste Gerätebindung. Der manuelle Ersttest filtert nach der physischen
USB-Topologie `1-2.2`. Das ist die freie Buchse im selben physischen
Doppel-USB-A-Block wie die Apple-Tastatur (`1-2.1`).
Die Bridge wartet, bis dort genau ein serielles Gerät erscheint.

Topologie eines eingesteckten Adapters kontrollieren:

```bash
for tty in /sys/class/tty/ttyACM* /sys/class/tty/ttyUSB*; do
  test -e "$tty" && readlink -f "$tty/device"
done
```

Falls der tatsächlich verwendete Anschluss nicht `1-2.2` enthält:

```bash
wasd-drive usb_physical_port:=GEFUNDENER_USB_PFAD
```

Ein USB-A-Port ist ein USB-Host und erzeugt ohne eingestecktes
USB-Serial-Gerät keinen seriellen Datenstrom. Für PuTTY auf einem Laptop ist
deshalb ein USB-Serial-Endpunkt erforderlich; eine direkte USB-A-zu-USB-A-
Verbindung zwischen Jetson und Laptop ist nicht zulässig.

Debugging:

```bash
ros2-jazzy ros2 topic echo /control/manual_cmd --no-daemon --spin-time 8
ros2-jazzy ros2 topic info /drive_commands --verbose
ros2-jazzy ros2 topic echo /drive_commands --no-daemon --spin-time 8
ros2-jazzy ros2 topic echo /drive_usb/tx --no-daemon --spin-time 8
ros2-jazzy ros2 topic echo /drive_usb/status --no-daemon --spin-time 8
```

`ros2-jazzy` erzeugt fuer jeden Aufruf einen neuen, kurzlebigen Docker-
Container. Dessen ROS-Discovery-Cache ist beim Start leer. Ein normales
`ros2 topic echo` kann deshalb faelschlich melden, dass ein nachweislich
laufendes Topic nicht publiziert werde oder dass sein Typ unbekannt sei. Fuer
Topic-Abfragen in diesem Projekt deshalb `--no-daemon --spin-time 8`
verwenden. Damit wartet das CLI ohne veralteten Daemon-Cache bis zu acht
Sekunden auf die DDS-Erkennung. Dieses Kommando wurde fuer `/drive_commands`
im laufenden manuellen Stack erfolgreich geprueft.

Für `/drive_commands` muss im normalen Betrieb `Publisher count: 1` gelten;
der Publisher muss `/drive_commander` sein.

**Noch zwingend umzusetzen, bevor Motoren angeschlossen werden:** Watchdogs
wieder aktivieren, ESP-ACK/Status auf `/vehicle/status` implementieren,
Encoderüberwachung ergänzen und einen unabhängigen Command-Timeout im ESP
testen. Der aktuelle Einwegmodus erwartet bewusst keine Antwort.

### Simulierte Sensoren

Das Modell besitzt Sensoren an den angegebenen Montagepositionen:

- Kamera mittig vorne, 6 cm über Boden, Blick geradeaus
- STL27-LiDAR mittig vorne, 10 cm über Boden, Orientierung 90 Grad rechts
- BNO085 aufrecht in der Fahrzeugmitte

Simulation und reale Hardware verwenden dieselbe Treibergrenze. Es darf immer
nur ein Profil die gemeinsamen Rohdaten-Topics publizieren:

- `/camera/image_raw` und `/camera/camera_info`
- `/scan_raw`, aufbereitet als `/scan`
- `/imu/data_raw`, validiert als `/imu/data`

Die Kamera simuliert zunächst 640 x 360 Pixel mit 20 Hz, der LiDAR 720 Strahlen
mit 10 Hz und die IMU 100 Hz. Diese moderaten Werte halten die Simulation auf
dem Jetson flüssig.

Eine andere Welt kann direkt über die ROS-2-Umgebung gestartet werden:

```bash
ros2-jazzy gz sim /workspace/simulation/worlds/eigene_strecke.sdf
```

## STL-27L

Der STL-27L-Treiber veröffentlicht `sensor_msgs/msg/LaserScan` unter
`/scan_raw`. Der gemeinsame Preprocessor stellt anschließend `/scan` bereit.

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
Der dauerhafte IMU-Dienst veröffentlicht mit 100 Hz Rohdaten; der gemeinsame
Preprocessor validiert sie für die kanonische Schnittstelle:

- `/imu/data_raw` -> `/imu/data` (`sensor_msgs/msg/Imu`, Frame `imu_link`)
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
/scan_raw      -> /scan
/imu/data_raw  -> /imu/data
/odom          -> robot_localization -> odom -> base_link
```

Der vollständige Node- und Topic-Vertrag steht in
[`docs/ros_graph.md`](docs/ros_graph.md).

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

### Experimenteller Nav2-Test während Online-SLAM

Wenn Gazebo und der obige AVAJ-SLAM-Launch laufen und `/map` publiziert wird,
können die installierten Nav2-Standardserver und die Nav2-RViz-Oberfläche in
zwei weiteren Terminals gestartet werden:

```bash
ros2-jazzy ros2 launch nav2_bringup navigation_launch.py use_sim_time:=true
ros2-jazzy ros2 launch nav2_bringup rviz_launch.py use_sim_time:=true
```

In RViz `map` als Fixed Frame wählen und mit `Nav2 Goal` ein Ziel setzen.
Nicht zusätzlich `nav2_bringup bringup_launch.py slam:=true` starten, weil
bereits `avaj_slam` den einzigen SLAM-Publisher für `map -> odom` stellt.
WASD und der manuelle Drive-Stack dürfen ebenfalls nicht parallel laufen:
Nav2 publiziert in diesem vorläufigen Profil direkt `/cmd_vel`.

Dieser Ablauf verwendet noch Nav2-Stockparameter. Fahrzeugkontur,
Ackermann-Controller, Geschwindigkeits-/Beschleunigungsgrenzen, Costmaps und
Zielnavigation sind nicht AVAJ-spezifisch validiert. Ein Profil für
gespeicherte Karten und AMCL ist noch nicht implementiert.

Der physische BNO085 bleibt fest an `/dev/i2c-7` angeschlossen und muss für
Gazebo nicht entfernt werden. Die Simulation nutzt ihn derzeit nicht im EKF;
dieser fusioniert ausschließlich Gazebos `/odom`.
