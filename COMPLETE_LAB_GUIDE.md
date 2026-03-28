# 🚁 PaintDrone - Complete Lab Guide
## Everything You Need to Know for Lab Implementation

---

# 📋 TABLE OF CONTENTS

1. [System Overview](#1-system-overview)
2. [Hardware Components](#2-hardware-components)
3. [Software Files Explained](#3-software-files-explained)
4. [Hardware Connections](#4-hardware-connections)
5. [Software Setup](#5-software-setup)
6. [Complete Workflow](#6-complete-workflow)
7. [Step-by-Step Lab Instructions](#7-step-by-step-lab-instructions)
8. [Troubleshooting](#8-troubleshooting)

---

# 1. SYSTEM OVERVIEW

## What Does This Project Do?

PaintDrone is an **autonomous wall painting drone** that:
1. **SEES** the wall using a camera (ESP32-CAM)
2. **DETECTS** unpainted (white) areas using AI
3. **FLIES** to each unpainted area (Pixhawk drone)
4. **SPRAYS** paint automatically (relay-controlled pump)

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PAINTDRONE SYSTEM                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐        │
│  │  ESP32-CAM   │◀───────▶│   LAPTOP     │◀───────▶│  PIXHAWK     │        │
│  │              │  WiFi   │              │ MAVLink │  DRONE       │        │
│  │ • Camera     │         │ • Flask      │         │              │        │
│  │ • WiFi AP    │         │ • Detection  │         │ • Flight     │        │
│  │ • Relay      │         │ • Web UI     │         │ • GPS        │        │
│  │ • Spray Ctrl │         │ • Path Plan  │         │ • Sensors    │        │
│  └──────────────┘         └──────────────┘         └──────────────┘        │
│         │                                                   │               │
│         │                                                   │               │
│         ▼                                                   ▼               │
│  ┌──────────────┐                                   ┌──────────────┐        │
│  │  PAINT PUMP  │                                   │  MOTORS x4   │        │
│  │  (12V DC)    │                                   │  (BLDC)      │        │
│  └──────────────┘                                   └──────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 2. HARDWARE COMPONENTS

## 2.1 Drone Hardware

| Component | Model | Purpose |
|-----------|-------|---------|
| **Flight Controller** | Pixhawk V6X | Brain of drone - controls flight, reads sensors |
| **GPS Module** | Holybro M9N/M10 | Provides position data for autonomous flight |
| **Motors** | 2212 920KV (or similar) | BLDC motors that spin propellers |
| **ESCs** | 30A BLHeli | Electronic Speed Controllers - power motors |
| **Battery** | 4S LiPo 5000mAh | Power source (14.8V nominal) |
| **Frame** | F450 or similar | Drone body |
| **Propellers** | 10x4.5 or 9x4.5 | Generate lift |
| **Telemetry** | SiK Radio 915MHz | Wireless link to Mission Planner |
| **RC Receiver** | FrSky/FlySky | For manual override (safety pilot) |

## 2.2 Spray System Hardware

| Component | Model | Purpose |
|-----------|-------|---------|
| **ESP32-CAM** | AI-Thinker | Camera + WiFi + GPIO for relay |
| **5V Relay Module** | 1-channel | Switches pump power ON/OFF |
| **DC Pump** | 12V diaphragm | Sprays paint |
| **Tubing** | 6mm silicone | Carries paint from tank to nozzle |
| **Paint Tank** | 500ml bottle | Holds paint (mounted on drone) |
| **Nozzle** | Adjustable spray | Controls spray pattern |
| **12V Power** | BEC or separate battery | Powers pump (from drone battery via BEC) |

## 2.3 Programming Hardware

| Component | Purpose |
|-----------|---------|
| **ESP32-S3 DevKit** | Used as USB-to-Serial programmer for ESP32-CAM |
| **Jumper Wires** | Connect ESP32-S3 to ESP32-CAM for programming |
| **USB-C Cable** | Connect ESP32-S3 to laptop |

---

# 3. SOFTWARE FILES EXPLAINED

## 3.1 File Structure

```
C:\mdp\
├── esp32cam/
│   └── esp32cam.ino      ← ESP32-CAM firmware
├── esp32s3/
│   └── esp32s3.ino       ← USB programmer firmware
├── backend/
│   ├── app.py            ← Main Flask server
│   ├── drone_controller.py ← Pixhawk interface
│   ├── demo_simulation.py  ← SITL demo
│   └── static/
│       └── index.html    ← Web UI
├── requirements.txt      ← Python packages
├── LAB_IMPLEMENTATION_GUIDE.md
└── COMPLETE_LAB_GUIDE.md (this file)
```

## 3.2 What Each File Does

### 📁 esp32cam/esp32cam.ino
**Purpose:** Firmware for ESP32-CAM board

**What it does:**
- Creates WiFi Access Point "PaintDrone" (password: paintdrone123)
- Runs 2 HTTP servers:
  - Port 80: Control commands (spray, status)
  - Port 81: MJPEG camera stream
- Controls relay on GPIO 13
- Has 30-second watchdog for safety (auto-stops continuous spray)

**Key endpoints:**
```
GET  /ping           → Check if alive
GET  /status         → Relay state, uptime
POST /spray          → Precision spray (800ms default)
POST /spray_start    → Start continuous spray
POST /spray_stop     → Stop spray
GET  /capture_frame  → Single JPEG image
GET  :81/stream      → Live video stream
```

---

### 📁 esp32s3/esp32s3.ino
**Purpose:** Makes ESP32-S3 act as USB-to-Serial programmer

**What it does:**
- Bridges USB (computer) to UART (ESP32-CAM)
- Allows uploading code to ESP32-CAM which has no USB port
- Pass-through serial communication

**When to use:**
- Only during programming ESP32-CAM
- Not needed during normal operation

---

### 📁 backend/app.py
**Purpose:** Main brain of the system - Flask web server

**What it does:**
1. **Serves Web UI** - The beautiful control panel
2. **Proxies camera stream** - Solves CORS issues
3. **Paint detection** - 6-method AI algorithm
4. **Spray control** - Sends commands to ESP32-CAM
5. **Drone control** - Sends commands to Pixhawk
6. **Smart path planning** - Decides continuous vs precision spray

**Key routes:**
```python
/                    → Web UI
/capture             → Capture + analyze wall
/esp_ping            → Check ESP32 connection
/spray               → Precision spray
/spray_start         → Continuous spray ON
/spray_stop          → Spray OFF
/smart_spray_sequence → SSE for smart mission
/drone/connect       → Connect to Pixhawk
/drone/arm_takeoff   → Arm + takeoff
/drone/land          → Land
/drone/rtl           → Return to launch
```

**Paint Detection Algorithm (6 methods):**
```
1. Adaptive Threshold (30% weight) - Local contrast
2. Brightness Check (20%) - Overall lightness
3. Saturation Analysis (25%) - Color intensity
4. Otsu Binary (10%) - Auto-threshold
5. LAB Color Space (10%) - Perceptual lightness
6. Blur Detection (5%) - Edge-less = white

Combined Vote → Morphological cleanup → 8×12 Grid
```

---

### 📁 backend/drone_controller.py
**Purpose:** DroneKit wrapper for Pixhawk communication

**What it does:**
- Connects to Pixhawk via MAVLink protocol
- Arms drone, controls takeoff/landing
- Sends GPS waypoints
- Monitors battery, altitude, distance
- Implements safety limits

**Key functions:**
```python
connect()           → Connect to Pixhawk
arm_and_takeoff()   → Arm motors, takeoff to altitude
goto_global()       → Fly to GPS coordinate
land()              → Land at current position
return_to_launch()  → Fly back to takeoff point
cells_to_waypoints() → Convert grid cells to GPS
```

**Connection strings:**
```
SITL:     tcp:127.0.0.1:5762
USB:      COM3 (or /dev/ttyACM0 on Linux)
Telemetry: udp:192.168.1.1:14550
```

---

### 📁 backend/demo_simulation.py
**Purpose:** Standalone demo for lab incharge (no real drone needed)

**What it does:**
- Runs with Mission Planner SITL (simulator)
- Arms virtual drone
- Flies to 4 waypoints
- Simulates spray at each point
- Lands safely

**When to use:**
- First demo to lab incharge
- Testing without real drone

---

### 📁 backend/static/index.html
**Purpose:** Professional web UI

**Features:**
- Dark theme with animations
- Real-time status badges (ESP32, Pixhawk, Spray)
- Live camera feed
- 8×12 grid overlay
- Click cells to select
- Smart spray path planning
- Progress tracking
- Activity log
- Keyboard shortcuts (SPACE=spray, ESC=emergency)

---

# 4. HARDWARE CONNECTIONS

## 4.1 ESP32-CAM Wiring

```
┌─────────────────────────────────────────────────────────────┐
│                     ESP32-CAM CONNECTIONS                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ESP32-CAM          5V Relay Module        12V Pump        │
│   ┌───────┐          ┌───────────┐          ┌───────┐       │
│   │       │          │           │          │       │       │
│   │ GPIO13├─────────▶│ IN        │          │       │       │
│   │       │          │           │          │       │       │
│   │   5V  ├─────────▶│ VCC       │          │       │       │
│   │       │          │           │   COM ──▶│  +    │       │
│   │  GND  ├─────────▶│ GND       │          │       │       │
│   │       │          │        NO ├─────────▶│  -    │       │
│   └───────┘          └───────────┘          └───────┘       │
│                            │                     │          │
│                            │                     │          │
│                      ┌─────┴─────┐         ┌─────┴─────┐    │
│                      │  12V PSU  │         │   PUMP    │    │
│                      │  or BEC   │         │  GROUND   │    │
│                      └───────────┘         └───────────┘    │
│                                                             │
│  ⚠️ CRITICAL: Relay VCC MUST be 5V (not 3.3V)              │
│  ⚠️ Relay won't click at 3.3V - coil needs 5V!             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 4.2 ESP32-CAM Programming Setup

```
┌─────────────────────────────────────────────────────────────┐
│              PROGRAMMING ESP32-CAM via ESP32-S3             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   COMPUTER                                                  │
│      │                                                      │
│      │ USB-C                                                │
│      ▼                                                      │
│   ┌──────────────┐         ┌──────────────┐                 │
│   │  ESP32-S3    │         │  ESP32-CAM   │                 │
│   │              │         │              │                 │
│   │  TX (GPIO43)├─────────▶│ U0R (RX)     │                 │
│   │              │         │              │                 │
│   │  RX (GPIO44)│◀─────────│ U0T (TX)     │                 │
│   │              │         │              │                 │
│   │  5V         ├─────────▶│ 5V           │                 │
│   │              │         │              │                 │
│   │  GND        ├─────────▶│ GND          │                 │
│   │              │         │              │                 │
│   └──────────────┘         │ IO0 ─────┐   │                 │
│                            │          │   │                 │
│                            │ GND ◀────┘   │ ← JUMPER!       │
│                            │              │   (upload only) │
│                            └──────────────┘                 │
│                                                             │
│  STEPS:                                                     │
│  1. Wire as shown above                                     │
│  2. Connect IO0 to GND (enter bootloader mode)              │
│  3. Upload esp32cam.ino                                     │
│  4. REMOVE IO0-GND jumper                                   │
│  5. Press RESET button                                      │
│  6. "PaintDrone" WiFi appears!                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 4.3 Pixhawk Connections

```
┌─────────────────────────────────────────────────────────────┐
│                    PIXHAWK V6X CONNECTIONS                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                     PIXHAWK V6X                        │ │
│  ├───────────────────────────────────────────────────────┤  │
│  │                                                       │  │
│  │  POWER1 ◀──── Power Module ◀──── 4S LiPo Battery     │  │
│  │                                                       │  │
│  │  GPS ◀─────── GPS/Compass Module (M9N)               │  │
│  │                                                       │  │
│  │  TELEM1 ◀──── SiK Radio (915MHz) ◀──── Laptop        │  │
│  │                                                       │  │
│  │  RC IN ◀───── RC Receiver ◀──── RC Transmitter       │  │
│  │                                                       │  │
│  │  MAIN OUT 1-4 ─────▶ ESC 1-4 ─────▶ Motors 1-4      │  │
│  │                                                       │  │
│  │  USB ◀───── (Optional) Direct laptop connection      │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  MOTOR ORDER (X-configuration):                             │
│                                                             │
│        FRONT                                                │
│          ▲                                                  │
│    1 ┌───┴───┐ 2          1 = Front Right (CW)             │
│      │       │            2 = Front Left (CCW)              │
│      │   ●   │            3 = Back Left (CW)                │
│      │       │            4 = Back Right (CCW)              │
│    4 └───────┘ 3                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# 5. SOFTWARE SETUP

## 5.1 Arduino IDE Setup (for ESP32)

### Step 1: Install Arduino IDE
Download from: https://www.arduino.cc/en/software

### Step 2: Add ESP32 Board Manager
1. Open Arduino IDE
2. File → Preferences
3. Add to "Additional Board Manager URLs":
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Tools → Board → Boards Manager
5. Search "ESP32" → Install "esp32 by Espressif Systems"

### Step 3: Install Libraries
Tools → Manage Libraries → Install:
- `ArduinoJson` by Benoit Blanchon

### Step 4: Board Settings for ESP32-CAM
```
Board:           AI Thinker ESP32-CAM
CPU Frequency:   240 MHz
Flash Mode:      QIO
Flash Size:      4MB (32Mb)
Partition:       Huge APP (3MB No OTA/1MB SPIFFS)
Upload Speed:    115200
```

### Step 5: Board Settings for ESP32-S3
```
Board:           ESP32S3 Dev Module
USB CDC On Boot: Enabled
Upload Speed:    921600
```

## 5.2 Python Environment Setup

### Step 1: Install Python 3.9+
Download from: https://www.python.org/downloads/
(Recommend Python 3.9 or 3.10 for DroneKit compatibility)

### Step 2: Create Virtual Environment
```bash
cd C:\mdp
python -m venv drone_env
drone_env\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install flask flask-cors opencv-python numpy requests dronekit dronekit-sitl future
```

### Step 4: Verify Installation
```bash
python -c "import flask, cv2, dronekit; print('All OK!')"
```

## 5.3 Mission Planner Setup

### Step 1: Download Mission Planner
From: https://firmware.ardupilot.org/Tools/MissionPlanner/

### Step 2: Connect to Pixhawk
1. Connect Pixhawk via USB or telemetry
2. Select COM port (top right)
3. Select baud rate: 115200
4. Click CONNECT

### Step 3: Calibrate Sensors
1. Initial Setup → Mandatory Hardware
2. Calibrate: Accel, Compass, Radio, ESC

### Step 4: Set Up SITL (Simulator)
1. Simulation → Multirotor
2. Wait for "APM: ArduPilot Ready"
3. Connect Mission Planner to localhost:14550

---

# 6. COMPLETE WORKFLOW

## 6.1 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            COMPLETE DATA FLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   CAMERA    │    │   LAPTOP    │    │    DRONE    │    │    SPRAY    │  │
│  │  ESP32-CAM  │    │   FLASK     │    │   PIXHAWK   │    │    PUMP     │  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │
│         │                  │                  │                  │         │
│         │  1. CAPTURE      │                  │                  │         │
│         │◀─────────────────│                  │                  │         │
│         │  GET /capture    │                  │                  │         │
│         │                  │                  │                  │         │
│         │  2. JPEG IMAGE   │                  │                  │         │
│         │─────────────────▶│                  │                  │         │
│         │                  │                  │                  │         │
│         │                  │ 3. DETECT        │                  │         │
│         │                  │ white areas      │                  │         │
│         │                  │ (6 algorithms)   │                  │         │
│         │                  │                  │                  │         │
│         │                  │ 4. PLAN PATH     │                  │         │
│         │                  │ (smart grouping) │                  │         │
│         │                  │                  │                  │         │
│         │                  │ 5. GOTO          │                  │         │
│         │                  │─────────────────▶│                  │         │
│         │                  │ MAVLink command  │                  │         │
│         │                  │                  │                  │         │
│         │                  │                  │ 6. FLY           │         │
│         │                  │                  │ to GPS coord     │         │
│         │                  │                  │                  │         │
│         │                  │ 7. ARRIVED       │                  │         │
│         │                  │◀─────────────────│                  │         │
│         │                  │                  │                  │         │
│         │  8. SPRAY CMD    │                  │                  │         │
│         │◀─────────────────│                  │                  │         │
│         │  POST /spray     │                  │                  │         │
│         │                  │                  │                  │         │
│         │  9. RELAY ON     │                  │                  │         │
│         │────────────────────────────────────────────────────────▶         │
│         │  GPIO 13 HIGH    │                  │                  │ 10.PUMP │
│         │                  │                  │                  │  SPRAYS │
│         │                  │                  │                  │         │
│         │  11. RELAY OFF   │                  │                  │         │
│         │  (after 800ms)   │                  │                  │         │
│         │────────────────────────────────────────────────────────▶ STOP   │
│         │                  │                  │                  │         │
│         │                  │ 12. NEXT CELL    │                  │         │
│         │                  │ or MISSION DONE  │                  │         │
│         │                  │                  │                  │         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 6.2 Protocol Details

### WiFi Communication (Laptop ↔ ESP32-CAM)
```
Protocol: HTTP over WiFi
Network:  "PaintDrone" AP created by ESP32-CAM
IP:       192.168.4.1 (ESP32-CAM)
          192.168.4.100+ (connected devices)
```

### MAVLink Communication (Laptop ↔ Pixhawk)
```
Protocol: MAVLink v2
Options:
  - USB:       Direct serial (COM3 or /dev/ttyACM0)
  - Telemetry: UDP over SiK radio (udp:192.168.1.1:14550)
  - SITL:      TCP to simulator (tcp:127.0.0.1:5762)
```

### Relay Control (ESP32-CAM → Pump)
```
Pin:      GPIO 13
Logic:    Active HIGH (GPIO 13 HIGH = relay ON = pump ON)
Safety:   30-second watchdog (auto-shutoff)
```

---

# 7. STEP-BY-STEP LAB INSTRUCTIONS

## Stage 1: Flash ESP32-S3 Programmer

1. Connect ESP32-S3 to laptop via USB-C
2. Open Arduino IDE
3. Open `esp32s3/esp32s3.ino`
4. Select board: ESP32S3 Dev Module
5. Select port (COMx)
6. Click Upload
7. ✅ Verify: Serial monitor shows "ESP32-S3 USB-to-Serial Bridge Ready"

## Stage 2: Flash ESP32-CAM

1. Wire ESP32-S3 to ESP32-CAM (see Section 4.2)
2. Connect IO0 to GND on ESP32-CAM
3. Open `esp32cam/esp32cam.ino`
4. Select board: AI Thinker ESP32-CAM
5. Select same COM port as ESP32-S3
6. Click Upload
7. Remove IO0-GND jumper
8. Press RESET on ESP32-CAM
9. ✅ Verify: Phone can see "PaintDrone" WiFi

## Stage 3: Test ESP32-CAM

1. Connect phone/laptop to "PaintDrone" WiFi (password: paintdrone123)
2. Open browser: http://192.168.4.1/ping
3. ✅ Verify: See `{"status":"ok"}`
4. Open: http://192.168.4.1:81/stream
5. ✅ Verify: See live camera feed

## Stage 4: Wire Relay and Pump

1. Connect ESP32-CAM GPIO 13 → Relay IN
2. Connect ESP32-CAM 5V → Relay VCC
3. Connect ESP32-CAM GND → Relay GND
4. Connect 12V power → Relay COM
5. Connect pump positive → Relay NO
6. Connect pump negative → 12V ground

## Stage 5: Test Spray System

1. Connect to "PaintDrone" WiFi
2. Open browser console (F12)
3. Run: `fetch('http://192.168.4.1/spray', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{"duration_ms":500}'}).then(r=>r.json()).then(console.log)`
4. ✅ Verify: Hear relay click, see pump spray for 0.5 seconds

## Stage 6: Run Flask Server

1. Open terminal in `C:\mdp\backend`
2. Activate venv: `drone_env\Scripts\activate`
3. Run: `python app.py`
4. ✅ Verify: See "Running on http://localhost:5000"

## Stage 7: Test Web UI

1. Open browser: http://localhost:5000
2. ✅ Verify: See professional dark UI
3. Check ESP32 badge turns green
4. Click "Capture & Analyze"
5. ✅ Verify: See captured image with grid overlay

## Stage 8: SITL Demo (for lab incharge)

1. Open Mission Planner
2. Click Simulation → Multirotor → Start SITL
3. Wait for "APM Ready"
4. In new terminal: `python demo_simulation.py`
5. ✅ Verify: Virtual drone arms, flies to waypoints, lands

## Stage 9: Connect Real Pixhawk

1. Connect Pixhawk via USB or telemetry
2. In web UI, go to Drone section
3. Enter connection string (e.g., "COM3" or "udp:...")
4. Click Connect
5. ✅ Verify: Drone status badge turns green

## Stage 10: First Flight (TETHERED!)

1. **SAFETY**: Attach tether to drone
2. **SAFETY**: Clear area of people
3. **SAFETY**: Have RC transmitter ready for override
4. In web UI, click "Arm & Takeoff"
5. ✅ Verify: Drone hovers at 2 meters
6. Click "Land"
7. ✅ Verify: Drone lands safely

---

# 8. TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| Can't see "PaintDrone" WiFi | Remove IO0-GND jumper, press RESET |
| Relay doesn't click | Check VCC is 5V not 3.3V |
| Camera feed black | Check camera ribbon cable |
| DroneKit import error | Install `future` package |
| SITL won't connect | Check port 5762, disable firewall |
| Drone won't arm | Calibrate compass in Mission Planner |
| Spray too short | Increase duration_ms in settings |
| Detection misses white | Lower sensitivity setting |

---

## 🎯 SUCCESS CRITERIA

Your project is working when:

1. ✅ ESP32-CAM creates WiFi and streams video
2. ✅ Relay clicks when spray command sent
3. ✅ Pump sprays paint
4. ✅ Web UI shows camera feed
5. ✅ Detection finds unpainted areas
6. ✅ Smart path planning groups adjacent cells
7. ✅ SITL demo flies virtual drone
8. ✅ Real drone arms, takes off, hovers, lands
9. ✅ Full mission: detect → fly → spray → complete

---

*Good luck in the lab! 🚁🎨*

*VIT Chennai Multi-Disciplinary Project*
*GitHub: https://github.com/daksh1403/auto-drone*
