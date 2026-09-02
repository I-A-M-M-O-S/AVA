# AP-R01 — Reuse- und Lizenzentscheidung

**Stand:** 2. September 2026  
**Repositorybasis:** Branch `orin`,
`7df2f36f1a8d00ff6080dbec1ae1263aa5948f2b`, einschließlich vorhandener
uncommitteter Änderungen  
**Validierungsniveau:** lokale Bestandsaufnahme, Source-/Lizenzprüfung und
isolierte Syntax-/Import-Probes; keine Produktionsintegration, keine
Simulation und keine Hardwarevalidierung

## 1. Ergebnis

AP-R01 ist abgeschlossen. Alle ausgewählten Upstreams sind auf einen Commit
gepinnt und lizenzseitig nachvollziehbar. Die verbindlichen Entscheidungen für
Folgepakete sind:

| Bedarf | Primärentscheidung | Vergleich/Fallback | Nicht verwenden |
|---|---|---|---|
| Bahnfolger | **USE** Nav2 RPP 1.3.12 hinter AVAJ Twist/Ackermann-Adapter | **ADAPT** nur den Pure-Pursuit-Kern aus `tum-phoenix/f1tenth_ros`, falls der AP-C01-Benchmark dies rechtfertigt | **REJECT** `f1tenth-dev/pure_pursuit` |
| Lokalisierung | **USE** installierten `slam_toolbox`-Lokalisierungsmodus | **REFERENCE ONLY** Nav2 `map_server` + AMCL; nur nach messbarem Vergleich hochstufen | eigener Lokalisierer oder parallele `map -> odom`-Publisher |
| Centerline/Rennlinie | **ADAPT offline** ausgewählte `trajectory_planning_helpers` 0.80 | **REFERENCE ONLY** TUMFTM-Gesamtoptimierer und dessen Dateiformate | vollständigen Minimum-Time-Stack jetzt importieren |
| Pylonbildpfad | **USE** ROS `camera_calibration`, `image_proc`, `cv_bridge` und OpenCV | austauschbarer HSV-/Geometrie-Adapter nur als Gazebo-Baseline | Realübertragbarkeit oder Reichweite ohne Kalibrier-/Messquelle behaupten |
| Gate/Slalom | kleiner AVAJ-Planer gegen AP-M01-Vertrag; kein Upstream-Code gewählt | OpenCV nur für Wahrnehmungsprimitive | fremden Fahrzeug-, Command- oder Safety-Gesamtstack importieren |

Die vollständigen Pins, Lizenzen, Attributionen, APIs und Adaptergrenzen stehen
in [`THIRD_PARTY.md`](../../THIRD_PARTY.md).

Der Plan führt AP-B01 als harte Abhängigkeit aller Folgearbeiten. Eine
AP-B01-Übergabe war unter `docs/work_packages/` nicht vorhanden. Die
Rechercheentscheidung von AP-R01 ist damit vollständig, sie autorisiert aber
noch keinen Start von AP-C01, AP-G01, AP-P02 oder AP-P03, bevor AP-B01 und die
jeweiligen weiteren Planabhängigkeiten erfüllt sind.

## 2. Scope und Sicherheitsgrenze

Geändert wurden ausschließlich:

- `THIRD_PARTY.md`
- `docs/work_packages/AP-R01.md`

Es wurden keine Probes in den Quellbaum übernommen. Prüfklone lagen nur unter
`/tmp/ap-r01.VAtbkQ`, also außerhalb von `workspace/src`. Es wurden keine ROS-
Nodes gestartet, keine Topics publiziert, keine Geräte geöffnet und weder
ESP/USB/I²C noch Kamera, LiDAR, Aktoren oder reales Fahrzeug verwendet.

Die vorhandene Downstream-Kette, `drive_commander`, der Ackermann-Adapter,
`rc_car_usb_bridge`, `rc_car_interfaces`, `docs/ros_graph.md` und
`CURRENT_STATE.md` blieben unverändert. AP-R01 fügt keinen Publisher hinzu.

## 3. Gelesene Vorgaben und Ausgangszustand

Vor der Änderung wurden `AGENTS.md`, `CURRENT_STATE.md`, `AGENTS (1).md`,
`Codex_Arbeitspaket.md`, `HANDOFF.md` und `README.md` geprüft. Die in
`AGENTS.md` genannte Datei `DEVELOPMENT_PLAN.md — AVAJ RC-Car.md` existiert
nicht; `Codex_Arbeitspaket.md` benennt diesen Zustand ausdrücklich und hebt
die Datei für dieses Paket als Voraussetzung auf.

Vorheriger Worktree-Auszug:

```text
 M AGENTS (1).md
 M HANDOFF.md
 M README.md
 M docs/ros_graph.md
 M workspace/src/avaj_car_control/...
 M workspace/src/controll center/...
 m workspace/src/bno08x_driver
 m workspace/src/ldlidar_stl_ros2
 ?? AGENTS.md
 ?? CURRENT_STATE.md
 ?? Codex_Arbeitspaket.md
 ?? workspace/src/avaj_car_control/scripts/ackermann_to_drive_request
 ?? workspace/src/avaj_car_control/test/test_ackermann_to_drive_request.py
 ?? workspace/src/controll center/src/
```

Diese fremden Änderungen wurden nicht verworfen, zurückgesetzt oder
überschrieben.

## 4. Installierter Jazzy-/ARM64-Stand

Die Prüfung erfolgte read-only im bereits laufenden ROS-Container. Es wurde
kein Gerätepfad geöffnet.

| Komponente | Beobachteter Stand | ARM64-Status |
|---|---|---|
| OS/ROS/Python | `arm64`, ROS 2 Jazzy, Python 3.12.3 | nativ |
| Nav2 RPP | `1.3.12-1noble.20260614.095312` | installiert |
| Nav2 AMCL | `1.3.12-1noble.20260614.075224` | installiert |
| Nav2 map_server | `1.3.12-1noble.20260614.103023` | installiert |
| slam_toolbox | `2.8.5-1noble.20260614.104642` | installiert |
| cv_bridge | `4.1.0-1noble.20260612.114100` | installiert |
| OpenCV | `4.6.0+dfsg-13.1ubuntu1`, Python `cv2 4.6.0` | installiert |
| NumPy/SciPy | 1.26.4 / 1.11.4 | installiert |
| image_proc | — | nicht installiert |
| camera_calibration | — | nicht installiert |
| quadprog/CasADi/scikit-learn | — | nicht installiert |

Die Paketdateien und Ament-Indexmarker bestätigen RPP, AMCL, map_server,
slam_toolbox, cv_bridge und image_geometry. `image_proc` und
`camera_calibration` müssen von AP-P02 als gepinnte Jazzy-Binärabhängigkeiten
ergänzt werden; AP-R01 installiert sie nicht.

Reproduzierbare Kernprüfung:

```bash
docker exec ros2-jazzy-sensor-processing bash -lc '
  dpkg --print-architecture
  python3 --version
  for p in \
    ros-jazzy-nav2-regulated-pure-pursuit-controller \
    ros-jazzy-nav2-amcl ros-jazzy-nav2-map-server \
    ros-jazzy-slam-toolbox ros-jazzy-image-proc \
    ros-jazzy-camera-calibration ros-jazzy-cv-bridge; do
    dpkg-query -W "$p" 2>/dev/null || echo "$p NOT_INSTALLED"
  done
'
```

## 5. Reuse-Gate im Detail

### 5.1 Bahnfolger

Nav2 RPP ist ein installierter, gepflegter Jazzy-C++-Plugin mit standardisiertem
`nav2_core::Controller`-API. Er akzeptiert `nav_msgs/Path`, Pose und aktuelle
Geschwindigkeit und liefert `TwistStamped`. Sein Nachteil für AVAJ ist der
Nav2-Controller-/Costmap-Kontext und die notwendige korrekte Ackermann-
Umsetzung. Dies ist trotzdem weniger riskant als ein eigener Bahnfolger und
deshalb der primäre AP-C01-Kandidat.

Der C++-Pure-Pursuit aus `tum-phoenix/f1tenth_ros` ist ROS 2 und publiziert
bereits SI-Ackermann-Befehle. Er wird als begrenzter Vergleichskern ausgewählt,
nicht als Gesamtstack: Pfadbesitz per CSV, F1TENTH-Topics/Frames, fehlende
Stale-/Fehlergrenzen und keine Tests erfordern einen AVAJ-Adapter oder eine
kleine isolierte Extraktion. AP-C01 muss direkte RPP-Nutzung bevorzugen, wenn
der Benchmark die Abnahmebedingungen erfüllt.

`f1tenth-dev/pure_pursuit` ist ROS 1, seit 2020 unverändert und scheitert im
Prüfstand bereits an Python-3.12-Syntax. Die Quelle wird verworfen.

### 5.2 Lokalisierung

`slam_toolbox` 2.8.5 enthält im installierten Jazzy-Paket ein
`localization_slam_toolbox_node`, eine Localization-Launchdatei und
Lokalisierungsparameter. AP-L01 verwendet dies zuerst und erzwingt exklusive
Ownership von `map -> odom`. Wichtig: der Modus lädt einen serialisierten
Posegraph; die bisher dokumentierten PGM/YAML-Karten allein erfüllen diese API
nicht. AP-L01 muss deshalb Save -> Shutdown -> Load für beide erforderlichen
Artefakte reproduzierbar machen.

Nav2 map_server/AMCL bleibt ein installierter, lizenzierter Fallback für
PGM/YAML. Er darf nur nach einem messbaren Vergleich aktiviert werden und nie
parallel zu slam_toolbox laufen.

### 5.3 Rennlinie und Geschwindigkeitsprofil

`trajectory_planning_helpers` bietet die kleinste brauchbare Bibliotheksgrenze:
NumPy-Eingaben, geschlossene Track-Geometrie, Splines, Normalen, Krümmung,
Minimum-Curvature und Geschwindigkeitsprofile. Die Verwendung bleibt offline
und wird auf ausgewählte Funktionen begrenzt. LGPL-3.0 und lokale Änderungen
müssen erhalten und ausgeliefert werden.

Der Gesamtoptimierer dokumentiert ein geeignetes sieben-spaltiges SI-Format,
ist aber für Python 3.7 mit alten, exakt gepinnten wissenschaftlichen Paketen
und optional CasADi 3.5.1 ausgelegt. Er wird daher nur als Format- und
Algorithmusreferenz verwendet. Minimum-Time-Optimierung ist nicht Teil des
MVP.

### 5.4 Pylonwahrnehmung und lokaler Pfad

Die offiziellen ROS-Komponenten decken Kalibrierung, Entzerrung und den
Image/OpenCV-Übergang ab. OpenCV deckt die für eine deterministische Gazebo-
Baseline nötigen HSV-, Morphologie-, Kontur- und Projektionsprimitive ab. Kein
geprüfter offizieller Baustein liefert jedoch einen domänenspezifischen
Pylondetektor oder eine Gate-/Slalomzustandsmaschine.

Daher bleibt AP-P02 hinter einem austauschbaren Detector-Vertrag und darf für
die definierte Simulationswelt eine explizit nicht realvalidierte HSV-Baseline
verwenden. AP-P03 implementiert später nur die kleine AVAJ-Semantik und gibt
`/planning/local_path` aus. Ein fremder Fahrzeug-, VESC-, Command- oder
Safety-Stack wird nicht importiert.

## 6. Probes und Ergebnisse

Die Probes waren read-only beziehungsweise erzeugten ausschließlich
Python-Cachedateien im temporären Prüfverzeichnis.

| Probe | Ergebnis | Klassifikation |
|---|---|---|
| `python3 -m compileall -q trajectory_planning_helpers/...` | erfolgreich | Python-3.12-Syntax kompatibel |
| Import `trajectory_planning_helpers` | Fehler `ModuleNotFoundError: quadprog` | erwartete, noch unaufgelöste Abhängigkeit |
| `python3 -m compileall -q global_racetrajectory_optimization` | erfolgreich | Syntax allein, kein Laufzeitnachweis |
| `python3 -m compileall -q f1tenth-dev/pure_pursuit/scripts` | Fehler in `find_nearest_goal.py`: Zuweisung vor `global` | REJECT bestätigt |
| Package-/Headerprüfung RPP | `setPlan(Path)` und `computeVelocityCommands(...)->TwistStamped` vorhanden | Adaptergrenze bestätigt |
| Package-/Launchprüfung slam_toolbox | Localization-Node/-Launch vorhanden | Primärkandidat bestätigt |

Es wurde bewusst kein Third-party-Build als AVAJ-Build ausgegeben: AP-R01 hat
nichts in `workspace/src` importiert. Ein Syntaxlauf ist kein Funktions-,
Performance- oder Simulationsnachweis.

## 7. Verbindliche Folgearbeiten

### AP-C01

- RPP 1.3.12 direkt benchmarken und seinen vollständigen Nav2-Kontext messen.
- Gegen den gepinnten tum-phoenix-Kern vergleichen; keine Gesamtstack-
  Übernahme.
- Nur `/control/autonomous_ackermann_cmd` publizieren.
- Twist/Ackermann-Umsetzung nahe Null, Reverse, Vorzeichen, Sättigung,
  Lenkrate, stale Pose/Path und TF-Fehler testen.

### AP-L01

- slam_toolbox-Posegraph plus Kartenartefakte speichern und laden.
- Lifecycle-Zustände `DISABLED/MAPPING/LOCALIZATION` exklusiv machen.
- AMCL nur bei dokumentierter, messbarer Notwendigkeit verwenden.

### AP-G01/AP-V01

- TPH 0.80 in einer separaten gepinnten Offline-Umgebung auf ARM64/Python 3.12
  oder einer dokumentierten kompatiblen Python-Version bauen und testen.
- `quadprog`/BLAS-Lösung und LGPL-Auslieferung vor Codeübernahme festhalten.
- Mit konservativer Centerline/konstantem Tempo beginnen; Gesamtoptimierer
  nicht importieren.

### AP-P02/AP-P03

- image_pipeline 5.0.13 binär ergänzen und Kalibrierstatus erzwingen.
- cv_bridge/OpenCV direkt nutzen, Detector-Backend austauschbar halten.
- Kein ML-Modell ohne separat gepinnte Gewichte, Dataset-/Gewichtslizenz,
  ARM64-Laufzeitmessung und klare API übernehmen.
- Gate/Slalom als kleine, getestete AVAJ-Planungslogik implementieren, nicht
  aus einem fremden Fahrzeugstack kopieren.

## 8. Abnahme gegen AP-R01

- Konkrete unveränderliche Commits: **erfüllt**.
- Lizenz und Attribution pro Kandidat: **erfüllt**.
- Maintenance, ROS/Python, ARM64, API, Adapteraufwand: **erfüllt**.
- Entscheidungen `USE/ADAPT/REFERENCE ONLY/REJECT`: **erfüllt**.
- Installierte Jazzy-Pakete zuerst geprüft: **erfüllt**.
- Kein Gesamtstack importiert, keine Laufzeitdownloads: **erfüllt**.
- Änderungen ausschließlich in der AP-R01-Dateiliste: **erfüllt**.
- Hardware-/USB-/ESP-/Aktortest: **nicht durchgeführt und nicht behauptet**.

## 9. Abschließender Worktree-Check

`git status --short` und `git diff --stat` wurden nach der Arbeit erneut
ausgeführt. Alle vorgefundenen Modifikationen, Löschungen, Submodulzustände und
unverfolgten Dateien sind weiterhin vorhanden. Neu hinzugekommen sind nur:

```text
?? THIRD_PARTY.md
?? docs/work_packages/AP-R01.md
```

Da beide neuen Dateien noch untracked sind, erscheinen sie erwartungsgemäß
nicht in `git diff --stat`; die Statistik der bereits vorhandenen Änderungen
blieb unverändert. `git diff --check` meldete für die beiden AP-R01-Dateien
keine Whitespace-Fehler.
