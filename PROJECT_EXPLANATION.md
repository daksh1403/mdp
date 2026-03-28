# 🎨 PaintDrone — Complete Project Explanation

## VIT Chennai Multi-Disciplinary Project
**Autonomous Wall Painting Drone System**

---

## 🎯 What This Project Does

PaintDrone is an **autonomous drone system that paints walls**. Here's the complete workflow:

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PAINTDRONE SYSTEM                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   📷 CAMERA          →   🧠 BRAIN         →   🚁 DRONE                  │
│   (ESP32-CAM)            (Laptop)              (Pixhawk V6X)            │
│                                                                         │
│   - Takes photo          - Detects white      - Flies to each           │
│   - Live stream            areas (unpainted)    unpainted cell          │
│   - Controls spray       - Plans path         - Hovers while spraying   │
│     pump relay           - Shows web UI       - Returns home safely     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure Explained

```
C:\mdp\
├── esp32cam/
│   └── esp32cam.ino          ← ESP32-CAM firmware (camera + spray control)
├── esp32s3/
│   └── esp32s3.ino           ← USB-to-Serial bridge for programming
├── backend/
│   ├── app.py                ← Flask web server (main brain)
│   ├── drone_controller.py   ← DroneKit wrapper for Pixhawk
│   ├── demo_simulation.py    ← SITL demo for lab incharge
│   └── static/
│       └── index.html        ← Web UI (professional design)
├── requirements.txt          ← Python dependencies
└── LAB_IMPLEMENTATION_GUIDE.md ← Step-by-step guide
```

---

## 🔄 Step-by-Step Workflow

### STEP 1: System Setup

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│   ESP32-CAM    │     │    LAPTOP      │     │   PIXHAWK      │
│                │     │                │     │                │
│ Creates WiFi   │     │ Connects to    │     │ Connected via  │
│ "PaintDrone"   │────▶│ PaintDrone     │────▶│ telemetry or   │
│ Password:      │     │ WiFi           │     │ USB            │
│ paintdrone123  │     │                │     │                │
└────────────────┘     └────────────────┘     └────────────────┘
         │                     │                      │
    192.168.4.1          192.168.4.100         /dev/ttyACM0
```

### STEP 2: Open Web Interface

1. Run the server: `python app.py`
2. Open browser: `http://localhost:5000`
3. You see the **professional web UI**

### STEP 3: Live Camera Feed

```
┌─────────────────────────────────────────────────────────────┐
│  📷 CAMERA VIEW                         [Live] [Analysis]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                                                     │   │
│   │      🔴 LIVE                                        │   │
│   │                                                     │   │
│   │            [Real-time wall image from               │   │
│   │             ESP32-CAM camera]                       │   │
│   │                                                     │   │
│   │                                                     │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
│   [ 📸 Capture & Analyze ]  [ ☑️ Select All ]  [ 🗑️ Clear ]  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### STEP 4: Capture & Analyze Wall

When you click **"Capture & Analyze"**:

```
ESP32-CAM                     Laptop Backend                    Browser UI
    │                              │                                │
    │  GET /capture_frame          │                                │
    │◀─────────────────────────────│                                │
    │                              │                                │
    │──────────────────────────────▶                                │
    │  Returns JPEG image          │                                │
    │                              │                                │
    │                    ┌─────────▼─────────┐                      │
    │                    │ PAINT DETECTION   │                      │
    │                    │ ALGORITHM:        │                      │
    │                    │                   │                      │
    │                    │ 1. Adaptive       │                      │
    │                    │    Threshold (30%)│                      │
    │                    │                   │                      │
    │                    │ 2. Brightness     │                      │
    │                    │    Check (20%)    │                      │
    │                    │                   │                      │
    │                    │ 3. Saturation     │                      │
    │                    │    Analysis (25%) │                      │
    │                    │                   │                      │
    │                    │ 4. Otsu Binary    │                      │
    │                    │    (10%)          │                      │
    │                    │                   │                      │
    │                    │ 5. LAB Color      │                      │
    │                    │    Space (10%)    │                      │
    │                    │                   │                      │
    │                    │ 6. Blur Detection │                      │
    │                    │    (5%)           │                      │
    │                    │                   │                      │
    │                    │ = COMBINED VOTE   │                      │
    │                    └─────────┬─────────┘                      │
    │                              │                                │
    │                              │ { image, unpainted_cells }     │
    │                              │────────────────────────────────▶
    │                              │                                │
```

### STEP 5: Grid Display

After analysis, the wall is divided into **8×12 = 96 cells**:

```
┌────────────────────────────────────────────────────────────────┐
│  📸 CAPTURED IMAGE                                             │
├────────────────────────────────────────────────────────────────┤
│  ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐            │
│  │   │   │ 🔴│ 🔴│ 🔴│   │   │   │   │   │   │   │  Row 0     │
│  ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤            │
│  │   │ 🔴│ 🔴│ 🔴│ 🔴│ 🔴│   │   │   │   │   │   │  Row 1     │
│  ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤            │
│  │   │ 🔴│ 🔴│   │   │ 🔴│   │   │   │ 🔴│ 🔴│   │  Row 2     │
│  ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤            │
│  │   │   │   │   │   │   │   │   │   │   │   │   │  Row 3     │
│  ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤            │
│  │   │   │   │   │   │   │   │   │   │   │   │   │  Row 4     │
│  ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤            │
│  │   │   │   │ 🔴│ 🔴│   │   │   │   │   │   │   │  Row 5     │
│  ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤            │
│  │   │   │   │   │   │   │   │   │   │   │   │   │  Row 6     │
│  ├───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┤            │
│  │   │   │   │   │   │   │   │   │   │   │   │   │  Row 7     │
│  └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘            │
│                                                                │
│  🔴 = Unpainted area (white/needs paint)                       │
│  🟢 = Already painted (colored)                                │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### STEP 6: User Selects Cells

Click on red cells to select them for painting:

```
🔴 Unpainted (detected)  →  Click  →  🔵 Selected (to paint)
🔵 Selected              →  Click  →  🔴 Deselected

Or use "Select All" button to select all unpainted cells at once.
```

### STEP 7: Start Autonomous Mission

When you click **"🚀 Start Autonomous Mission"**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                         MISSION EXECUTION                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   FOR EACH SELECTED CELL:                                              │
│                                                                        │
│   1. MOVE TO CELL                                                      │
│      ┌──────────┐          ┌──────────┐                                │
│      │  Drone   │ ──────▶  │  Cell    │   GPS coordinates              │
│      │ Position │          │ Position │   calculated from              │
│      └──────────┘          └──────────┘   grid position                │
│                                                                        │
│   2. HOVER IN POSITION                                                 │
│      ┌──────────┐                                                      │
│      │  Drone   │  Stabilizes at painting altitude (2m)                │
│      │ Hovers   │  Waits 0.5 seconds                                   │
│      └──────────┘                                                      │
│                                                                        │
│   3. SPRAY PAINT                                                       │
│      ┌──────────┐          ┌──────────┐                                │
│      │  Laptop  │ ──────▶  │ ESP32-CAM│   HTTP POST /spray             │
│      │  Server  │          │  Relay   │   duration_ms: 800             │
│      └──────────┘          └──────────┘                                │
│                               │                                        │
│                               ▼                                        │
│                         ┌──────────┐                                   │
│                         │   PUMP   │   Paint sprays for 0.8 seconds    │
│                         │   ON!    │                                   │
│                         └──────────┘                                   │
│                                                                        │
│   4. MARK AS COMPLETE                                                  │
│      Cell status: 🔵 Selected → 🟢 Sprayed (green checkmark)           │
│                                                                        │
│   5. REPEAT for next cell...                                           │
│                                                                        │
│   6. RETURN HOME when all cells done                                   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🎮 Two Spray Modes

### Mode 1: Precision Mode (Default)

```
Cell-by-cell spraying:
   Cell 1     Cell 2     Cell 3
     │          │          │
     ▼          ▼          ▼
   [SPRAY]   [SPRAY]   [SPRAY]
   800ms     800ms     800ms
     │          │          │
   STOP      STOP      STOP
```

- Drone flies to each cell, hovers, sprays for 800ms, stops
- Best for: Touch-up work, small areas

### Mode 2: Continuous Mode

```
Row-by-row spraying:
   START ─────────────────────────▶ END
     │                               │
     ▼                               ▼
   [SPRAY ON]───────────────────[SPRAY OFF]
         Drone flies along row
```

- Drone flies along entire row with spray continuously ON
- Spray auto-stops after 30 seconds (safety watchdog)
- Best for: Large unpainted areas, faster coverage

---

## 🛠️ Hardware Connections

### ESP32-CAM Wiring

```
┌─────────────────────────────────────────────────────────────────┐
│                        ESP32-CAM                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   GPIO 13  ──────────────▶  Relay IN                           │
│   5V       ──────────────▶  Relay VCC  (MUST be 5V, not 3.3V!) │
│   GND      ──────────────▶  Relay GND                          │
│                                                                 │
│   Relay OUT ─────────────▶  12V Pump Power (via external PSU)  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

⚠️ CRITICAL: Relay VCC MUST be 5V!
   - 3.3V will NOT click the relay coil
   - Use the 5V pin on ESP32-CAM, NOT 3.3V
```

### Programming ESP32-CAM (Using ESP32-S3)

```
┌────────────────────────┐         ┌────────────────────────┐
│      ESP32-S3          │         │      ESP32-CAM         │
│  (USB-to-Serial)       │         │   (Target Board)       │
├────────────────────────┤         ├────────────────────────┤
│                        │         │                        │
│  USB to Computer       │         │  IO0  ───▶  GND        │
│                        │         │  (During upload only)  │
│  TX (GPIO 43) ─────────┼────────▶│  U0R (RX)              │
│  RX (GPIO 44) ─────────┼◀────────│  U0T (TX)              │
│  GND ──────────────────┼─────────│  GND                   │
│  5V ───────────────────┼─────────│  5V                    │
│                        │         │                        │
└────────────────────────┘         └────────────────────────┘

Steps:
1. Connect wires as shown
2. Connect IO0 to GND on ESP32-CAM
3. Upload sketch
4. Remove IO0-GND jumper
5. Press RESET
6. "PaintDrone" WiFi appears!
```

---

## 🌐 Network Architecture

```
                    ┌─────────────────────────────────────────┐
                    │           WiFi Network                  │
                    │         "PaintDrone"                    │
                    │       Password: paintdrone123           │
                    └─────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│  ESP32-CAM    │          │    Laptop     │          │   Phone       │
│  192.168.4.1  │          │ 192.168.4.100 │          │ 192.168.4.xxx │
│               │          │               │          │               │
│ Port 80:      │◀────────│ Flask Server  │─────────▶│ (Can view     │
│  Commands     │          │ localhost:5000│          │  web UI too!) │
│               │          │               │          │               │
│ Port 81:      │◀────────│ Proxies       │          │               │
│  MJPEG Stream │          │ camera stream │          │               │
│               │          │               │          │               │
└───────────────┘          └───────┬───────┘          └───────────────┘
                                   │
                                   │ MAVLink Protocol
                                   │ (USB, Serial, or UDP)
                                   ▼
                          ┌───────────────┐
                          │  Pixhawk V6X  │
                          │               │
                          │ Flight        │
                          │ Controller    │
                          │               │
                          └───────────────┘
```

---

## 🔒 Safety Features (6 Layers)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: GEOFENCE (Mission Planner)                                     │
│   - If drone exits defined boundary → AUTO RTL (Return To Launch)       │
│   - Configure in Mission Planner before flight                          │
├─────────────────────────────────────────────────────────────────────────┤
│ LAYER 2: BATTERY MONITOR                                                │
│   - If battery < 15% → AUTO RTL                                         │
│   - Drone will land before battery dies                                 │
├─────────────────────────────────────────────────────────────────────────┤
│ LAYER 3: ALTITUDE LIMIT                                                 │
│   - If altitude > 8 meters → AUTO RTL                                   │
│   - Prevents flying too high                                            │
├─────────────────────────────────────────────────────────────────────────┤
│ LAYER 4: DISTANCE LIMIT                                                 │
│   - If distance from home > 10 meters → WAYPOINT BLOCKED                │
│   - Won't fly too far from starting point                               │
├─────────────────────────────────────────────────────────────────────────┤
│ LAYER 5: ESP32 WATCHDOG                                                 │
│   - Continuous spray auto-stops after 30 seconds                        │
│   - Prevents pump running forever                                       │
├─────────────────────────────────────────────────────────────────────────┤
│ LAYER 6: RC OVERRIDE (Safety Pilot)                                     │
│   - Flip mode switch on RC controller                                   │
│   - Instantly takes manual control                                      │
│   - Always have a safety pilot ready!                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🖥️ API Endpoints Reference

### ESP32-CAM (192.168.4.1)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ping` | GET | Health check → `{"status":"ok"}` |
| `/status` | GET | Relay state, uptime, WiFi clients |
| `/spray` | POST | Precision spray → `{"duration_ms": 800}` |
| `/spray_start` | POST | Start continuous spray |
| `/spray_stop` | POST | Stop spray immediately |
| `/capture_frame` | GET | Single JPEG image |
| `:81/stream` | GET | MJPEG continuous stream |

### Flask Backend (localhost:5000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI |
| `/esp_ping` | GET | Check ESP32 connection |
| `/capture` | POST | Capture + analyze wall |
| `/spray` | POST | Trigger spray via ESP32 |
| `/spray_start` | POST | Start continuous spray |
| `/spray_stop` | POST | Stop spray |
| `/spray_sequence` | GET/POST | SSE event stream for mission |
| `/drone/connect` | POST | Connect to Pixhawk |
| `/drone/status` | GET | Drone telemetry |
| `/drone/arm_takeoff` | POST | Arm and takeoff |
| `/drone/land` | POST | Land at current position |
| `/drone/rtl` | POST | Return to launch |
| `/drone/loiter` | POST | Hold position (emergency) |

---

## 📱 Web UI Features

### Professional Design Elements
- **Dark theme** with gradient accents
- **Animated background** grid pattern
- **Real-time status badges** (ESP32, Pixhawk, Spray)
- **Progress tracking** with animated progress bar
- **Activity log** with timestamps

### Key Controls

| Control | Action |
|---------|--------|
| `📸 Capture & Analyze` | Take photo, detect unpainted areas |
| `☑️ Select All` | Select all unpainted cells |
| `🗑️ Clear` | Deselect all |
| `💨 Spray Once` | Manual precision spray |
| `▶️ Start Spray` | Start continuous spray |
| `⏹️ Stop Spray` | Stop continuous spray |
| `🚀 Start Mission` | Begin autonomous painting |
| `ESC key` | Emergency stop modal |
| `SPACE key` | Quick spray |

### Status Indicators

```
🔴 Red dot    = Disconnected
🟢 Green dot  = Connected
🟡 Yellow dot = Spraying (animated blink)
```

---

## 🧪 Testing Checklist

### Stage 1: ESP32-CAM Test
- [ ] Flash esp32cam.ino
- [ ] Connect to "PaintDrone" WiFi
- [ ] Open http://192.168.4.1/ping → `{"status":"ok"}`
- [ ] Open http://192.168.4.1:81/stream → See camera feed

### Stage 2: Spray System Test
- [ ] Wire relay to GPIO 13 (VCC to 5V!)
- [ ] POST to /spray → Hear relay click
- [ ] Connect pump → See paint spray

### Stage 3: Web UI Test
- [ ] Run `python app.py`
- [ ] Open localhost:5000
- [ ] See live camera feed
- [ ] Click Capture & Analyze
- [ ] See detected cells

### Stage 4: SITL Demo
- [ ] Start Mission Planner SITL
- [ ] Run `python demo_simulation.py`
- [ ] Watch virtual drone fly
- [ ] Show to lab incharge ✓

### Stage 5: Real Flight
- [ ] Connect Pixhawk
- [ ] Test arm/takeoff/land
- [ ] Test with tether first!
- [ ] Free flight only after approval

---

## 🎓 Summary

**PaintDrone is:**
1. A camera (ESP32-CAM) that sees the wall
2. A brain (Laptop) that detects unpainted areas
3. A drone (Pixhawk) that flies to each area
4. A spray system (Pump + Relay) that paints

**The magic happens when:**
1. Camera takes photo
2. AI detects white (unpainted) areas
3. User approves cells to paint
4. Drone autonomously flies + sprays each cell
5. Wall gets painted! 🎨

---

*Created for VIT Chennai Multi-Disciplinary Project*
*GitHub: https://github.com/daksh1403/auto-drone*
