# 🚁 Complete Lab Demonstration Guide
## VIT Chennai — Autonomous Wall Painting Drone System

---

## 📋 Overview

This guide walks you through the complete demonstration process:
1. **Phase 1:** Show SITL simulation demo to evaluator
2. **Phase 2:** Upload codes to real hardware (ESP32-CAM + Pixhawk)
3. **Phase 3:** Demonstrate real hardware operation

---

# PHASE 1: SIMULATION DEMO (Show First)

> **Purpose:** Demonstrate the system working in simulation before touching real hardware.

## Step 1.1: Start Mission Planner SITL

```
1. Open Mission Planner
2. Click "Simulation" tab (top menu)
3. Select "Multirotor → ArduCopter"
4. Click "Start Simulation"
5. Wait 30 seconds → Green "Connected" status in top-right
```

## Step 1.2: Run Demo Script

```powershell
cd C:\mdp
.\drone_env\Scripts\activate
cd backend
python demo_simulation.py
```

### Expected Output:
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
  Altitude: 3.5m
  Altitude: 9.6m
  ✓ Reached altitude!

[5/6] Starting paint mission...
  📍 Waypoint 1/4: Cell (0,0) — Top-Left
  💦 SPRAYING (simulated)
  ✓ Cell (0,0) — spray complete
  ...

[6/6] Mission complete! Returning to launch...
  ✓ DEMO COMPLETE
```

### ✅ What to Show:
- Mission Planner: Virtual drone moving on satellite map
- Terminal: Progress logs showing autonomous navigation

### 💬 What to Say:
> "This is our autonomous drone painting system running in simulation. The drone navigates to GPS waypoints calculated from a grid overlay on the wall. Watch how it flies to each cell and simulates spray activation."

---

# PHASE 2: UPLOAD CODES TO REAL HARDWARE

> **Purpose:** Prepare all hardware components for real demonstration.

## Step 2.1: Flash ESP32-S3 (Programmer Board)

```
┌─────────────────────────────────────────────────────┐
│  In Arduino IDE:                                   │
│  1. Go to Tools → Board → ESP32 Arduino →          │
│     "ESP32S3 Dev Module"                           │
│  2. Connect ESP32-S3 via USB                       │
│  3. Select correct COM port (Tools → Port)         │
│  4. Open: C:\mdp\esp32s3\esp32s3.ino               │
│  5. Click Upload ▶                                 │
│  6. Open Serial Monitor (115200 baud)              │
└─────────────────────────────────────────────────────┘
```

### ✅ Success Check:
```
[Bridge] ESP32-S3 USB-to-Serial bridge ready
[Bridge] GPIO17 (TX) → ESP32-CAM U0R
[Bridge] GPIO18 (RX) → ESP32-CAM U0T
```

---

## Step 2.2: Wire ESP32-S3 to ESP32-CAM

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

**⚠️ IMPORTANT:** Connect ESP32-CAM IO0 to GND for boot/flash mode!

---

## Step 2.3: Flash ESP32-CAM

```
┌─────────────────────────────────────────────────────┐
│  In Arduino IDE (keep ESP32-S3 connected via USB): │
│                                                    │
│  1. Tools → Board → "AI Thinker ESP32-CAM"         │
│  2. Tools → Partition Scheme →                     │
│     "Huge APP (3MB No OTA/1MB SPIFFS)"             │
│  3. Tools → Flash Frequency → 80 MHz               │
│  4. Open: C:\mdp\esp32cam\esp32cam.ino             │
│  5. Click Upload ▶                                 │
│  6. Wait for "Hard resetting via RTS pin..."       │
│                                                    │
│  ⚠️ AFTER FLASHING:                                │
│  7. REMOVE IO0-GND jumper from ESP32-CAM           │
│  8. Press RESET button on ESP32-CAM                │
│  9. Disconnect ESP32-S3 (not needed anymore)       │
└─────────────────────────────────────────────────────┘
```

### ✅ Success Check:
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

**Check:** On phone/laptop WiFi list → See **"PaintDrone"** network

---

## Step 2.4: Wire Relay + Pump System

### Wiring Diagram:
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

### Connections Summary:
| From | To |
|------|-----|
| ESP32-CAM GPIO 13 | Relay IN |
| ESP32-CAM 5V | Relay VCC (⚠️ MUST be 5V, not 3.3V!) |
| ESP32-CAM GND | Relay GND |
| Relay COM | 12V Power + |
| Relay NO (Normally Open) | Pump + |
| Pump - | 12V Power - |

---

## Step 2.5: Connect Pixhawk Flight Controller

```
┌─────────────────────────────────────────────────────┐
│  1. Connect Pixhawk to laptop via USB cable        │
│  2. Open Device Manager → Ports (COM & LPT)        │
│  3. Note the COM port number (e.g., COM3)          │
│                                                    │
│  4. Edit: C:\mdp\backend\drone_controller.py       │
│     Change line ~52:                               │
│                                                    │
│     # FROM (simulation):                           │
│     CONNECTION_STRING = 'tcp:127.0.0.1:5762'       │
│                                                    │
│     # TO (real hardware):                          │
│     CONNECTION_STRING = 'COM3'  # Your COM port    │
└─────────────────────────────────────────────────────┘
```

### Connection Options:
| Setup | Connection String |
|-------|-------------------|
| USB (Windows) | `'COM3'` or `'COM4'` |
| USB (Linux) | `'/dev/ttyACM0'` |
| Telemetry Radio (Windows) | `'COM5'` |
| Telemetry Radio (Linux) | `'/dev/ttyUSB0'` |
| Ethernet/UDP | `'udp:192.168.1.1:14550'` |

---

# PHASE 3: REAL HARDWARE DEMONSTRATION

> **Purpose:** Show the complete system working with actual hardware.

## Step 3.1: Test ESP32-CAM

```powershell
# Connect laptop WiFi to "PaintDrone" (password: paintdrone123)

# Test 1: Ping ESP32
curl http://192.168.4.1/ping
# ✅ Expected: {"status":"ok","device":"ESP32-CAM"}

# Test 2: Spray relay (500ms)
curl -X POST http://192.168.4.1/spray -H "Content-Type: application/json" -d "{\"duration_ms\":500}"
# ✅ Expected: Relay CLICKS, pump sprays for 0.5 seconds

# Test 3: Camera stream
# Open browser: http://192.168.4.1:81/stream
# ✅ Expected: Live video from ESP32-CAM
```

---

## Step 3.2: Test Pixhawk Connection (Props OFF!)

```powershell
cd C:\mdp
.\drone_env\Scripts\activate

# Quick connection test
python -c "
from dronekit import connect
print('Connecting to Pixhawk...')
v = connect('COM3', wait_ready=True, timeout=30)
print(f'✓ Connected!')
print(f'  Mode: {v.mode.name}')
print(f'  Battery: {v.battery}')
print(f'  GPS: {v.gps_0}')
print(f'  Armed: {v.armed}')
v.close()
print('✓ Disconnected')
"
```

### ✅ Expected Output:
```
Connecting to Pixhawk...
✓ Connected!
  Mode: STABILIZE
  Battery: Battery:voltage=12.4,current=0.0,level=98
  GPS: GPSInfo:fix=3,num_sat=8
  Armed: False
✓ Disconnected
```

---

## Step 3.3: Start Flask Server

```powershell
cd C:\mdp
.\drone_env\Scripts\activate
cd backend
python app.py
```

### ✅ Expected Output:
```
============================================================
  Paint-Drone Flask Backend
  VIT Chennai Multi-Disciplinary Project
============================================================
  ESP32 Control : http://192.168.4.1
  ESP32 Stream  : http://192.168.4.1:81
  Web UI        : http://localhost:5000
============================================================
 * Running on http://0.0.0.0:5000
```

---

## Step 3.4: Open Web UI

```
Open browser: http://localhost:5000
```

### ✅ Verify These:
| Element | Status |
|---------|--------|
| Drone status indicator | 🟢 GREEN |
| ESP32 status indicator | 🟢 GREEN |
| Battery percentage | Shows actual % |
| GPS coordinates | Shows lat/lon |
| Camera feed | Live video (if enabled) |

---

## Step 3.5: Demo Flight Sequence

```
┌───────────────────────────────────────────────────────────┐
│  IN WEB UI — STEP BY STEP:                                │
│                                                           │
│  1. Click "Connect"                                       │
│     → Wait for green drone status                         │
│                                                           │
│  2. Click "Arm & Takeoff"                                 │
│     → Drone arms (motors spin)                            │
│     → Drone rises to 3m altitude                          │
│                                                           │
│  3. Select cells on the painting grid                     │
│     → Click squares to select areas to paint              │
│                                                           │
│  4. Click "Start Auto Spray"                              │
│     → Drone flies to first cell                           │
│     → Hovers and triggers spray                           │
│     → Moves to next cell, repeats                         │
│                                                           │
│  5. Click "RTL" (Return To Launch)                        │
│     → Drone returns to starting position                  │
│     → Lands and disarms                                   │
└───────────────────────────────────────────────────────────┘
```

---

## 💬 What to Say During Demo

### During Simulation:
> "This is our autonomous drone painting system. The drone navigates using GPS waypoints calculated from a grid overlay on the wall. Each cell is 30cm × 30cm. Watch how it flies to each position and triggers the spray."

### After Uploading Codes:
> "Now I'll show the same system on real hardware. The ESP32-CAM creates a WiFi hotspot called 'PaintDrone' and controls the spray pump via GPIO 13. The Pixhawk handles all flight control through DroneKit."

### During Real Demo:
> "The web interface captures the wall image, divides it into an 8×12 grid, and sends autonomous navigation commands. Safety features include battery monitoring (RTL below 15%), altitude geofence (max 8m), distance geofence (max 10m from home), and manual RC override."

---

# 🔧 TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| "PaintDrone" WiFi not visible | Remove IO0-GND jumper, press RESET on ESP32-CAM |
| Camera init failed | Re-seat camera ribbon cable firmly |
| Relay doesn't click | Check relay VCC is connected to 5V (not 3.3V) |
| Pump runs forever | Test `/spray_stop` endpoint, check watchdog (auto-stop after 30s) |
| Pixhawk connection timeout | Verify COM port in Device Manager, try different USB port |
| "Vehicle not armable" | Need GPS fix (3D) — take drone outside for GPS lock |
| Flask shows ESP32 error | Connect laptop to "PaintDrone" WiFi first |
| Drone won't arm | Check pre-arm conditions in Mission Planner |

---

# 📝 EVALUATOR QUESTIONS & ANSWERS

### Q: How does the drone know it's 0.5m from the wall?
**A:** The system uses GPS-based waypoint navigation, not active distance sensing. The drone is pre-positioned at a known distance from the wall, and waypoints are calculated based on that origin. The 0.5m is a configuration parameter, not real-time sensing.

### Q: What if GPS fails mid-flight?
**A:** The Pixhawk has multiple failsafes — it will switch to LAND mode if GPS is lost. Additionally, RC override is always available for manual control.

### Q: How is spray duration controlled?
**A:** Spray duration is configured in `drone_controller.py` (default 800ms per cell). The ESP32-CAM also has a hardware watchdog that auto-stops spray after 30 seconds as a safety measure.

### Q: What's the grid resolution?
**A:** Default is 12 columns × 8 rows, with each cell being 30cm × 30cm. Total coverage area: 3.6m × 2.4m.

### Q: Can it detect unpainted areas?
**A:** Yes, the system uses OpenCV in the Flask backend to analyze captured images and detect areas needing paint based on color segmentation.

---

# ✅ SUCCESS CHECKLIST

## Phase 1 (Simulation)
- [ ] Mission Planner SITL running
- [ ] `demo_simulation.py` completes successfully
- [ ] Virtual drone visible moving on map

## Phase 2 (Hardware Upload)
- [ ] ESP32-S3 flashed (bridge ready message)
- [ ] ESP32-CAM flashed ("PaintDrone" WiFi visible)
- [ ] Relay wired and tested (clicks on command)
- [ ] Pump fires on spray command
- [ ] Pixhawk connected (telemetry reads correctly)

## Phase 3 (Real Demo)
- [ ] Flask server running
- [ ] Web UI shows green status indicators
- [ ] Drone arms and takes off
- [ ] Spray triggers at waypoints
- [ ] Safe RTL and landing

---

*VIT Chennai | Multi-Disciplinary Project | 2026*
