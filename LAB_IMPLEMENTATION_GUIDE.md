# 🚁 DRONE LAB IMPLEMENTATION GUIDE
## VIT Chennai — Autonomous Wall Painting System

---

# 📋 TABLE OF CONTENTS

1. [Pre-Lab Checklist](#1-pre-lab-checklist)
2. [Stage 1: Flash ESP32-CAM](#2-stage-1-flash-esp32-cam)
3. [Stage 2: Test Spray System](#3-stage-2-test-spray-system)
4. [Stage 3: SITL Demo for Lab Incharge](#4-stage-3-sitl-demo-for-lab-incharge)
5. [Stage 4: Ground Telemetry Test](#5-stage-4-ground-telemetry-test)
6. [Stage 5: Tethered Hover Test](#6-stage-5-tethered-hover-test)
7. [Stage 6: Free Flight Test](#7-stage-6-free-flight-test)
8. [Troubleshooting](#8-troubleshooting)
9. [Success Checkpoints](#9-success-checkpoints)

---

# 1. PRE-LAB CHECKLIST

## What to Bring to Lab

- [ ] Laptop with all files at `C:\mdp\`
- [ ] ESP32-CAM module (AI Thinker)
- [ ] ESP32-S3 DevKit (for flashing)
- [ ] Relay module (Active HIGH, 5V)
- [ ] 12V water pump + nozzle + tubing
- [ ] Buck converter (12V → 5V, 3A+)
- [ ] Jumper wires (M-F, M-M)
- [ ] USB cables (Micro-USB, USB-C)
- [ ] Multimeter (for checking voltages)
- [ ] Small water container (for pump testing)

## Software Prerequisites

```bash
# Open PowerShell/CMD and run:
cd C:\mdp
python -m venv drone_env
drone_env\Scripts\activate
pip install -r requirements.txt

# Test DroneKit:
python -c "from dronekit import connect; print('DroneKit OK')"
```

## Files Structure
```
C:\mdp\
├── requirements.txt
├── esp32cam\
│   └── esp32cam.ino        ← Flash to ESP32-CAM
├── esp32s3\
│   └── esp32s3.ino         ← Flash to ESP32-S3 (programmer)
└── backend\
    ├── app.py              ← Flask server
    ├── drone_controller.py ← DroneKit wrapper
    ├── demo_simulation.py  ← SITL demo script
    └── static\
        └── index.html      ← Web UI
```

---

# 2. STAGE 1: FLASH ESP32-CAM

## Step 1.1: Flash ESP32-S3 (Programmer)

1. Open Arduino IDE
2. Go to **Tools → Board → ESP32 Arduino → ESP32S3 Dev Module**
3. Connect ESP32-S3 via USB
4. Select correct COM port in **Tools → Port**
5. Open `C:\mdp\esp32s3\esp32s3.ino`
6. Click **Upload** ▶️
7. Wait for "Done uploading"

### ✅ SUCCESS CHECK:
Open Serial Monitor (115200 baud) → See: `[Bridge] ESP32-S3 USB-to-Serial bridge ready`

---

## Step 1.2: Wire ESP32-S3 to ESP32-CAM

```
ESP32-S3          ESP32-CAM
─────────         ─────────
GPIO17 (TX)  →    U0R (RX)
GPIO18 (RX)  ←    U0T (TX)
GND          ─    GND
5V           ─    5V

IMPORTANT: Also connect ESP32-CAM IO0 → GND (boot mode)
```

### Wiring Diagram:
```
    ESP32-S3                      ESP32-CAM
   ┌────────┐                    ┌────────┐
   │    5V  ├────────────────────┤ 5V     │
   │   GND  ├────────────────────┤ GND    │
   │ GPIO17 ├────────────────────┤ U0R    │
   │ GPIO18 ├────────────────────┤ U0T    │
   └────────┘                    │ IO0 ───┼──► GND (BOOT MODE)
                                 └────────┘
```

---

## Step 1.3: Flash ESP32-CAM

1. Keep ESP32-S3 connected to laptop USB
2. In Arduino IDE: **Tools → Board → ESP32 Arduino → AI Thinker ESP32-CAM**
3. **Tools → Partition Scheme → Huge APP (3MB No OTA/1MB SPIFFS)**
4. **Tools → Flash Frequency → 80 MHz**
5. Open `C:\mdp\esp32cam\esp32cam.ino`
6. Click **Upload** ▶️
7. Wait for "Hard resetting via RTS pin..."
8. **REMOVE IO0-GND JUMPER** from ESP32-CAM
9. Press **RESET** button on ESP32-CAM

### ✅ SUCCESS CHECK:
1. Open Serial Monitor (115200 baud)
2. See output:
```
╔══════════════════════════════════════════╗
║   ESP32-CAM Paint Drone Controller       ║
║   VIT Chennai MDP Project                ║
╚══════════════════════════════════════════╝
[INIT] Relay pin configured (GPIO 13)
[CAM] Camera initialized successfully
[WIFI] AP Started: PaintDrone
[WIFI] AP IP: 192.168.4.1
[WIFI] Password: paintdrone123
[HTTP] Control server started on port 80
[HTTP] Stream server started on port 81

[READY] ESP32-CAM is ready!
```

3. On phone/laptop, check WiFi → See **"PaintDrone"** network

---

# 3. STAGE 2: TEST SPRAY SYSTEM

## Step 2.1: Wire Relay and Pump

### Wiring (ESP32-CAM + Relay + Pump):
```
ESP32-CAM GPIO 13  ──►  Relay IN
ESP32-CAM 5V       ──►  Relay VCC    ⚠️ MUST BE 5V!
ESP32-CAM GND      ──►  Relay GND

Relay COM          ──►  12V Power+ (or battery+)
Relay NO           ──►  Pump+
Pump-              ──►  12V Power- (or battery-)
```

### Circuit Diagram:
```
                    RELAY MODULE
                   ┌───────────┐
ESP32-CAM GPIO13 ──┤ IN        │
ESP32-CAM 5V     ──┤ VCC   COM ├──► 12V+ (battery/power supply)
ESP32-CAM GND    ──┤ GND    NO ├──► PUMP +
                   └───────────┘     │
                                     │
                    PUMP             │
                   ┌────┐            │
                   │  + ├────────────┘
                   │  - ├──► 12V- (battery/power supply)
                   └────┘
```

---

## Step 2.2: Test on Bench (Before Mounting)

1. Connect laptop to **PaintDrone** WiFi
2. Open browser: `http://192.168.4.1/ping`
   - ✅ Should see: `{"status":"ok","device":"ESP32-CAM"}`

3. Test relay manually (open CMD/PowerShell):
```bash
# Test spray for 500ms:
curl -X POST http://192.168.4.1/spray -H "Content-Type: application/json" -d "{\"duration_ms\":500}"
```
   - ✅ Relay should CLICK
   - ✅ Pump should spray for 0.5 seconds

4. Test continuous spray:
```bash
# Start spray:
curl -X POST http://192.168.4.1/spray_start

# Pump should run continuously...
# After 3 seconds, stop:
curl -X POST http://192.168.4.1/spray_stop
```

5. Test camera stream:
   - Open browser: `http://192.168.4.1:81/stream`
   - ✅ Should see live video from ESP32-CAM

### ✅ SUCCESS CHECK:
| Test | Expected Result |
|------|-----------------|
| `/ping` | Returns `{"status":"ok"}` |
| `/spray` | Relay clicks, pump fires briefly |
| `/spray_start` | Pump runs continuously |
| `/spray_stop` | Pump stops immediately |
| `/stream` (port 81) | Live video in browser |

---

# 4. STAGE 3: SITL DEMO FOR LAB INCHARGE

> **PURPOSE:** Show the system working in simulation before requesting real drone access.

## Step 3.1: Setup Mission Planner SITL

1. Open **Mission Planner**
2. Click **Simulation** tab (top menu)
3. Select: **Multirotor → ArduCopter**
4. Click **Start Simulation**
5. Wait **30 seconds** for initialization
6. Verify: Green "Connected" status in top-right

---

## Step 3.2: Run Flask Backend

Open new terminal:
```bash
cd C:\mdp
drone_env\Scripts\activate
cd backend
python app.py
```

✅ See:
```
============================================================
  Paint-Drone Flask Backend
  VIT Chennai Multi-Disciplinary Project
============================================================
  ESP32 Control : http://192.168.4.1
  ESP32 Stream  : http://192.168.4.1:81
  Web UI        : http://localhost:5000
============================================================
```

---

## Step 3.3: Run SITL Demo Script

Open another terminal:
```bash
cd C:\mdp
drone_env\Scripts\activate
cd backend
python demo_simulation.py
```

### What Happens:
```
============================================================
  🚁 AUTONOMOUS DRONE PAINTING — SITL DEMO
  VIT Chennai Multi-Disciplinary Project
============================================================

[1/6] Connecting to SITL on tcp:127.0.0.1:5762...
  ✓ Connected! Mode: GUIDED

[2/6] Waiting for GPS position...
  ✓ Home: -35.363261, 149.165237

[3/6] Pre-arm checks...
  ✓ Pre-arm checks passed

[4/6] Arming and taking off...
  ✓ Armed! Taking off to 10.0m...
  Altitude: 1.2m
  Altitude: 3.5m
  Altitude: 7.8m
  Altitude: 9.6m
  ✓ Reached altitude!

[5/6] Starting paint mission...
  📍 Waypoint 1/4: Cell (0,0) — Top-Left
  → Cell (0,0) — Top-Left: dist=45.2m  alt=10.1m
  → Cell (0,0) — Top-Left: dist=12.3m  alt=10.0m
  → Cell (0,0) — Top-Left: dist=1.5m   alt=10.0m
  💦 Cell (0,0) — Top-Left — SPRAYING (simulated)
  ✓ Cell (0,0) — Top-Left — spray complete

  [... repeats for 4 waypoints ...]

[6/6] Mission complete! Returning to launch...

============================================================
  ✓ DEMO COMPLETE — Ready for real drone integration!
============================================================
```

### What Sir Sees:
| Mission Planner (Left Screen) | Web UI (Right Screen) |
|-------------------------------|----------------------|
| Virtual drone on satellite map | Live camera feed (if ESP32 connected) |
| Drone moving between waypoints | Grid overlay |
| Flight path drawn | Countdown timer |
| Telemetry (altitude, battery, GPS) | Progress bar |

---

## Step 3.4: Explain to Lab Incharge

**Script to say:**

> "Sir, this is our autonomous wall-painting drone system. Let me show you how it works:
>
> 1. **The ESP32-CAM** (shows physical board) creates a WiFi hotspot and streams live video. It also controls the spray pump via GPIO 13.
>
> 2. **The Flask backend** runs on the laptop. It captures images, runs computer vision to detect unpainted areas, divides the wall into an 8×12 grid, and sends commands to both the drone and ESP32.
>
> 3. **DroneKit** (shows VS Code with code) connects to the Pixhawk via MAVLink and sends GPS waypoints. The drone flies autonomously to each grid cell.
>
> 4. **Safety features** include: geofence, battery monitor, altitude limit, hardware watchdog on ESP32 (auto-shutoff after 30 seconds), and RC override.
>
> Currently running in SITL simulation. The virtual drone is following the same commands that would go to a real Pixhawk.
>
> **Our request:** We'd like to do a ground telemetry test — just USB connection, props OFF — to verify DroneKit can read real Pixhawk telemetry."

---

# 5. STAGE 4: GROUND TELEMETRY TEST

> **PURPOSE:** Verify DroneKit connects to real Pixhawk. Props OFF, zero flight risk.

## Step 4.1: Connect to Pixhawk

1. Connect Pixhawk to laptop via **USB cable**
2. Note the COM port (check Device Manager)
3. Edit `C:\mdp\backend\drone_controller.py`:
```python
# Change line 52:
CONNECTION_STRING = 'COM3'  # Use your actual COM port
```

---

## Step 4.2: Run Connection Test

```bash
cd C:\mdp
drone_env\Scripts\activate
python -c "
from dronekit import connect
print('Connecting...')
v = connect('COM3', wait_ready=True, timeout=30)  # Change COM port
print(f'Connected! Mode: {v.mode.name}')
print(f'GPS: {v.gps_0}')
print(f'Battery: {v.battery}')
print(f'Armed: {v.armed}')
v.close()
print('Done!')
"
```

### ✅ SUCCESS CHECK:
```
Connecting...
Connected! Mode: STABILIZE
GPS: GPSInfo:fix=3,num_sat=8
Battery: Battery:voltage=12.4,current=0.0,level=98
Armed: False
Done!
```

---

## Step 4.3: Run Flask with Real Pixhawk

1. Edit `drone_controller.py`:
```python
CONNECTION_STRING = 'COM3'  # Your actual port
```

2. Start Flask:
```bash
cd backend
python app.py
```

3. Open browser: `http://localhost:5000`

4. Watch drone telemetry update in real-time

### ✅ SUCCESS CHECK:
| Check | Pass Criteria |
|-------|---------------|
| ESP32 status dot | Green (if WiFi connected) |
| Drone status dot | Green |
| Telemetry updates | Battery %, altitude, GPS visible |

---

# 6. STAGE 5: TETHERED HOVER TEST

> **PURPOSE:** First flight test with safety tether. ⚠️ REQUIRES RC SAFETY PILOT

## Step 5.1: Pre-Flight Setup

1. **Attach tether:** Tie 1-meter rope from drone frame to heavy ground anchor
2. **Props ON:** Install propellers (check CW/CCW direction!)
3. **Battery:** Fully charged 3S LiPo (12.4-12.6V)
4. **Clear area:** Remove people, objects from 5m radius
5. **RC ready:** Safety pilot has transmitter, knows mode switch

---

## Step 5.2: Tethered Takeoff Test

1. Start Flask backend with real Pixhawk connection
2. Open web UI: `http://localhost:5000`
3. Arm drone (via Mission Planner or code)
4. Command takeoff to 1m altitude:
```python
# In Python console:
from drone_controller import drone
drone.connect()
drone.arm_and_takeoff(1.0)  # 1 meter only!
```

5. Drone should:
   - Arm (hear motors spin up)
   - Rise to ~1m (limited by tether)
   - Hover stable

6. Land:
```python
drone.land()
```

### ✅ SUCCESS CHECK:
| Check | Pass Criteria |
|-------|---------------|
| Motors arm | All 6 motors spin |
| Takeoff | Drone lifts off ground |
| Hover | Stable at ~1m (tether taut) |
| Land | Safe descent, disarms |

---

## Step 5.3: Tethered Spray Test

1. Mount ESP32-CAM and spray system on drone
2. Connect to PaintDrone WiFi from laptop
3. Start Flask backend
4. Arm and hover at 1m (tethered)
5. Trigger spray via web UI or curl:
```bash
curl -X POST http://192.168.4.1/spray -H "Content-Type: application/json" -d "{\"duration_ms\":800}"
```
6. ✅ Pump should fire while drone hovers
7. Land

---

# 7. STAGE 6: FREE FLIGHT TEST

> **PURPOSE:** First autonomous mission. ⚠️ MAXIMUM CAUTION

## Pre-Flight Checklist

- [ ] Battery: >80%
- [ ] GPS: 3D fix, >8 satellites
- [ ] RC transmitter: Bound, tested mode switch
- [ ] Geofence: Set in Mission Planner (5m radius, 5m altitude)
- [ ] Safety pilot: Finger on mode switch
- [ ] Clear area: 10m radius, no people
- [ ] Video recording: For documentation

## Flight Procedure

1. Place drone 2m from target wall
2. Start Flask with drone connected
3. Capture & Detect wall in web UI
4. Select ONE CELL only (minimize risk)
5. Click "Start Auto Spray" with use_drone=True
6. Drone should:
   - Arm and takeoff
   - Fly to cell GPS position
   - Hover and spray
   - Return to launch

### ⚠️ ABORT PROCEDURE
If anything goes wrong:
1. **RC PILOT:** Switch to STABILIZE or LOITER
2. **Flask:** Click ABORT button
3. **Mission Planner:** Set RTL mode
4. **Last resort:** Motor kill switch

---

# 8. TROUBLESHOOTING

## ESP32-CAM Issues

| Problem | Solution |
|---------|----------|
| No "PaintDrone" WiFi | Remove IO0-GND jumper, press RESET |
| Camera init failed | Re-seat camera ribbon cable |
| Relay doesn't click | Wire relay VCC to 5V, not 3.3V |
| Pump runs forever | Check `/spray_stop` works, check watchdog |

## DroneKit Issues

| Problem | Solution |
|---------|----------|
| "No module named 'past'" | `pip install future` |
| Connection timeout | Check COM port, try `--wait-ready False` |
| "Vehicle not armable" | Check GPS fix, calibrate in Mission Planner |

## Flight Issues

| Problem | Solution |
|---------|----------|
| Drone won't arm | Check pre-arm conditions in Mission Planner |
| Altitude wrong | Calibrate barometer, check home position |
| Waypoints ignored | Verify AUTO mode, check mission upload |

---

# 9. SUCCESS CHECKPOINTS

## Stage 1 ✅
- [ ] ESP32-CAM flashed
- [ ] "PaintDrone" WiFi visible
- [ ] `/ping` returns OK

## Stage 2 ✅
- [ ] Relay clicks on spray command
- [ ] Pump fires for specified duration
- [ ] Watchdog auto-shutoff works (30s)

## Stage 3 ✅
- [ ] SITL demo runs end-to-end
- [ ] Virtual drone moves on Mission Planner
- [ ] Lab incharge approves next stage

## Stage 4 ✅
- [ ] DroneKit connects to real Pixhawk
- [ ] Telemetry reads correctly
- [ ] Flask shows live drone status

## Stage 5 ✅
- [ ] Tethered takeoff successful
- [ ] Spray fires while hovering
- [ ] Safe landing

## Stage 6 ✅
- [ ] Free flight to single cell
- [ ] Autonomous spray at position
- [ ] Safe RTL

---

# 🎉 CONGRATULATIONS!

You have successfully implemented the Autonomous Drone Wall-Painting System!

**Next Steps:**
- Test multi-cell missions
- Try continuous spray mode
- Measure painting accuracy
- Document results for final report

---

*VIT Chennai | Multi-Disciplinary Project | 2026*
