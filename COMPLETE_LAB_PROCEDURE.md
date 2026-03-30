# 🚁 Complete Lab Procedure — Drone #3 Indoor Testing

## VIT Chennai Multi-Disciplinary Project

> **Hardware:** Pixhawk 2.4.8 | F450 Quadcopter | FlySky FS-IA6B | Orange 3S 3300mAh

---

# 📋 Quick Reference

| Setting | Value |
|---------|-------|
| Max Altitude | **1.0m** (painting) / **1.5m** (ceiling) |
| Geofence | **3.0m** radius |
| USB Port | **COM3** (check Device Manager) |
| Baud Rate | **115200** |
| WiFi SSID | **PaintDrone** |
| WiFi Password | **paintdrone123** |
| ESP32-CAM IP | **192.168.4.1** |

---

# PHASE 1: Software Setup (Before Lab)

## Step 1.1 — Clone/Update Repository

```bash
# Navigate to your project folder
cd D:\OneDrive\Desktop\DSA\mdp_repo

# Pull latest code from GitHub
git pull origin main
```

**Expected output:**
```
Already up to date.
```
or
```
Updating abc123..def456
Fast-forward
 ...
```

✅ **CHECKPOINT:** Repository is up to date

---

## Step 1.2 — Create Python Virtual Environment (First Time Only)

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# You should see (venv) in your terminal
```

**Expected output:**
```
(venv) D:\OneDrive\Desktop\DSA\mdp_repo>
```

✅ **CHECKPOINT:** Virtual environment activated

---

## Step 1.3 — Install Dependencies

```bash
# Navigate to backend folder
cd backend

# Install all required packages
pip install -r requirements.txt
```

**Expected output:**
```
Installing collected packages: ...
Successfully installed dronekit-2.x.x flask-x.x.x opencv-python-x.x.x ...
```

✅ **CHECKPOINT:** All packages installed without errors

---

## Step 1.4 — Verify Installation

Run these commands one by one:

```bash
# Test DroneKit
python -c "from dronekit import connect; print('DroneKit OK')"
```
Expected: `DroneKit OK`

```bash
# Test OpenCV
python -c "import cv2; print('OpenCV OK')"
```
Expected: `OpenCV OK`

```bash
# Test Flask
python -c "from flask import Flask; print('Flask OK')"
```
Expected: `Flask OK`

✅ **CHECKPOINT:** All three tests show "OK"

---

# PHASE 2: Hardware Setup (In the Lab)

## Step 2.1 — Gather Equipment

Collect these items:
- [ ] Drone #3 (F450 with Pixhawk 2.4.8)
- [ ] Orange 3S 3300mAh LiPo battery (charged >80%)
- [ ] FlySky FS-i6 RC transmitter (with batteries)
- [ ] Micro USB cable (for Pixhawk connection)
- [ ] Laptop with project installed
- [ ] ESP32-CAM module (if testing spray system)
- [ ] Buck converter (set to 5V output)

---

## Step 2.2 — Physical Inspection

**Check the frame:**
- [ ] No cracks or damage
- [ ] All arms securely attached
- [ ] Landing gear intact

**Check the wiring:**
- [ ] ESC wires connected to Pixhawk MAIN OUT 1-4
- [ ] Power wires secure (no exposed copper)
- [ ] RC receiver antenna extended

**Check the motors:**
- [ ] All 4 motors spin freely by hand
- [ ] No grinding or resistance
- [ ] Motor nuts tight

**Check the battery connector:**
- [ ] XT60 connector clean (no burn marks)
- [ ] Balance connector intact

---

## ⚠️ Step 2.3 — REMOVE ALL PROPELLERS

**CRITICAL SAFETY STEP!**

1. Remove all 4 propellers
2. Store them separately
3. Do NOT install until Phase 6

```
┌─────────────────────────────────────────┐
│  ⚠️  PROPELLERS MUST BE OFF FOR:        │
│       - Phase 2 (Hardware Setup)        │
│       - Phase 3 (USB Connection Test)   │
│       - Phase 4 (Arm Test)              │
│       - Phase 5 (ESP32-CAM Setup)       │
└─────────────────────────────────────────┘
```

✅ **CHECKPOINT:** All 4 propellers removed and stored safely

---

## Step 2.4 — Connect Pixhawk to Laptop

1. **Find the USB port** on Pixhawk 2.4.8 (Micro USB)
2. **Connect Micro USB cable** to Pixhawk
3. **Connect other end** to laptop USB port
4. **Wait** for Windows to detect the device

**Finding the COM port:**
1. Open **Device Manager** (Win+X → Device Manager)
2. Expand **Ports (COM & LPT)**
3. Look for **"Pixhawk"** or **"Arduino Mega 2560"**
4. Note the COM number (e.g., COM3, COM4, COM5)

```
Example Device Manager view:
├─ Ports (COM & LPT)
│   ├─ Arduino Mega 2560 (COM3)  ← This is your Pixhawk
│   └─ USB Serial Device (COM5)
```

**If COM port is different from COM3:**
Update `backend/test_connection.py` line 19:
```python
CONNECTION = 'COM4'  # Change to your actual port
```

Also update `backend/drone_controller.py` line ~87:
```python
CONNECTION_STRING = 'COM4'  # Change to your actual port
```

✅ **CHECKPOINT:** COM port identified and noted

---

## Step 2.5 — Power the Drone

1. **Double-check:** Propellers are removed!
2. **Connect battery:** Plug XT60 connector into drone
3. **Listen for tones:** Pixhawk plays a musical scale
4. **Watch LEDs:** Should blink then stabilize

**Pixhawk LED meanings:**
| LED Color | Meaning |
|-----------|---------|
| Blue flashing | Disarmed, no GPS lock |
| Green flashing | Disarmed, GPS locked |
| Solid colors | Armed (motors will spin!) |
| Red flashing | Error - check Mission Planner |

✅ **CHECKPOINT:** Pixhawk powered and LEDs active

---

# PHASE 3: USB Connection Test

## Step 3.1 — Run Connection Test Script

Open a terminal in the `backend` folder:

```bash
cd D:\OneDrive\Desktop\DSA\mdp_repo\backend

# Run the connection test
python test_connection.py
```

**Expected successful output:**
```
============================================================
🔌 PIXHAWK 2.4.8 CONNECTION TEST
============================================================
Connection: COM3
Baud rate:  115200
============================================================

Connecting to Pixhawk 2.4.8...

============================================================
✅ CONNECTION SUCCESSFUL!
============================================================
Firmware:    APM:Copter V4.x.x (abc123)
Vehicle:     2
Mode:        STABILIZE
Armed:       False
GPS Fix:     0
GPS Sats:    0
Battery:     85%
Voltage:     11.5V
Is Armable:  False
============================================================

✅ Connection closed cleanly.
```

**If connection fails:**
```
❌ CONNECTION FAILED: [error message]

🔧 Troubleshooting:
1. Check COM port in Device Manager
2. Ensure Pixhawk is powered
3. Try different USB cable
4. Verify BAUD rate (115200 for USB)
5. Close Mission Planner if it's connected
```

**Common issues:**
| Problem | Solution |
|---------|----------|
| "COM port not found" | Check Device Manager for correct port |
| "Permission denied" | Close Mission Planner or other programs |
| "Timeout" | Check USB cable, try different port |
| "Baud rate error" | Use 115200 for USB, 57600 for TELEM |

✅ **CHECKPOINT:** See "CONNECTION SUCCESSFUL!" message

---

# PHASE 4: Arm Test (Props OFF!)

## Step 4.1 — Prepare RC Transmitter

1. **Power ON** the FlySky FS-i6 transmitter
2. **Check throttle** — must be at MINIMUM (down position)
3. **Check mode switch** — set to STABILIZE (position 1 / up)
4. **Verify binding** — receiver LED should be solid (not blinking)

```
FlySky FS-i6 Switch Setup:
┌─────────────────────────────────────────┐
│   SWA  SWB  SWC  SWD                    │
│    ↑    ↑    ↑    ↑   ← All UP for      │
│                         STABILIZE       │
│                                         │
│        [LCD Screen]                     │
│                                         │
│    ┌─────┐    ┌─────┐                   │
│    │  ↑  │    │  ↑  │  ← Both sticks    │
│    │  │  │    │  │  │    centered       │
│    │  ↓  │    │  ↓  │                   │
│    └─────┘    └─────┘                   │
│   THROTTLE  PITCH/ROLL                  │
│   (keep low)                            │
└─────────────────────────────────────────┘
```

✅ **CHECKPOINT:** RC transmitter ON, throttle LOW, mode STABILIZE

---

## Step 4.2 — Run Arm Test Script

```bash
cd D:\OneDrive\Desktop\DSA\mdp_repo\backend

python test_arm.py
```

**When prompted, type `CONFIRM`:**
```
============================================================
🔓 PIXHAWK 2.4.8 ARM TEST
============================================================

⚠️  WARNING: PROPELLERS MUST BE REMOVED!
    This test will attempt to arm the motors.

Type 'CONFIRM' to proceed (props are OFF): CONFIRM
```

**Expected successful output:**
```
Connecting to COM3...

Current State:
  Mode:       STABILIZE
  Armed:      False
  Is Armable: True
  GPS Fix:    3
  Battery:    85%

📡 Switching to GUIDED mode...
   Mode: GUIDED

🔓 Attempting to ARM...
   Waiting for arm... (10s)
   Waiting for arm... (9s)

============================================================
✅ ARMED SUCCESSFULLY!
============================================================
   Motors would spin now (but props are OFF)

⏱️  Holding for 3 seconds...

🔒 DISARMING...
✅ Disarmed successfully!

✅ Test complete.
```

**If "Not armable" error:**
```
❌ Vehicle NOT armable!
   Possible issues:
   - No GPS fix (normal indoors)
   - Pre-arm checks failing
   - RC transmitter not connected

💡 For indoor testing without GPS:
   Set ARMING_CHECK=0 in Mission Planner
```

**Disabling pre-arm checks (for indoor testing):**
1. Open Mission Planner
2. Connect to Pixhawk
3. Go to **CONFIG** → **Full Parameter List**
4. Find **ARMING_CHECK**
5. Set to **0** (disable all checks)
6. Click **Write Params**

⚠️ **WARNING:** Re-enable ARMING_CHECK before outdoor flights!

✅ **CHECKPOINT:** See "ARMED SUCCESSFULLY!" message

---

# PHASE 5: ESP32-CAM Setup

## Step 5.1 — Flash ESP32-CAM (First Time Only)

**Required hardware:**
- ESP32-S3 as programmer (or FTDI adapter)
- Jumper wires

**Wiring (ESP32-S3 → ESP32-CAM):**
```
ESP32-S3 GPIO17 (TX)  →  ESP32-CAM U0R (RX)
ESP32-S3 GPIO18 (RX)  →  ESP32-CAM U0T (TX)
ESP32-S3 GND          →  ESP32-CAM GND
ESP32-S3 5V           →  ESP32-CAM 5V
ESP32-CAM IO0         →  GND (for flashing mode)
```

**Flash procedure:**
1. Upload `esp32s3/esp32s3.ino` to ESP32-S3 first
2. Connect ESP32-CAM as shown above
3. In Arduino IDE:
   - Board: "AI Thinker ESP32-CAM"
   - Partition: "Huge APP (3MB No OTA/1MB SPIFFS)"
4. Upload `esp32cam/esp32cam.ino`
5. Remove IO0-GND jumper
6. Press RESET on ESP32-CAM

✅ **CHECKPOINT:** ESP32-CAM flashed successfully

---

## Step 5.2 — Power ESP32-CAM on Drone

**Power source:** Drone battery via buck converter

1. **Set buck converter to 5V** (CRITICAL!)
2. Connect buck converter input to battery XT60 (via Y-splitter)
3. Connect buck converter output to ESP32-CAM 5V and GND

```
Battery XT60 ─┬─► Drone PDB
              │
              └─► Buck Converter ─► ESP32-CAM 5V
                  (IN: 11.1V)        (OUT: 5V)
                  (OUT: 5V)
```

⚠️ **WARNING:** Verify 5V output BEFORE connecting to ESP32-CAM!

✅ **CHECKPOINT:** ESP32-CAM powered, LED on

---

## Step 5.3 — Connect Laptop to PaintDrone WiFi

1. Open WiFi settings on laptop
2. Find network: **PaintDrone**
3. Connect with password: **paintdrone123**
4. Wait for connection (may show "No Internet" - this is normal)

```
Your laptop IP will be: 192.168.4.x (assigned by ESP32-CAM)
ESP32-CAM IP is: 192.168.4.1
```

✅ **CHECKPOINT:** Connected to PaintDrone WiFi

---

## Step 5.4 — Test ESP32-CAM Endpoints

**Test 1: Ping endpoint**
Open browser and go to:
```
http://192.168.4.1/ping
```

Expected response:
```json
{"status":"ok","device":"ESP32-CAM"}
```

**Test 2: Status endpoint**
```
http://192.168.4.1/status
```

Expected response:
```json
{"relay":"off","mode":"precision","uptime_ms":12345,"wifi_clients":1}
```

**Test 3: Video stream**
```
http://192.168.4.1:81/stream
```

Expected: Live video feed from camera

**Test 4: Single frame capture**
```
http://192.168.4.1/capture_frame
```

Expected: JPEG image download

✅ **CHECKPOINT:** All 4 ESP32-CAM tests pass

---

# PHASE 6: First Flight Test (1 meter)

## ⚠️ SAFETY BRIEFING — READ BEFORE PROCEEDING

```
┌─────────────────────────────────────────────────────────────┐
│                    ⚠️ SAFETY CRITICAL ⚠️                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. CLEAR THE AREA: Minimum 4m x 4m open space              │
│                                                             │
│  2. SAFETY PILOT: One person holds RC transmitter           │
│     - Mode switch on STABILIZE                              │
│     - Ready to take manual control IMMEDIATELY              │
│                                                             │
│  3. SAFE DISTANCE: All people at least 3m from drone        │
│                                                             │
│  4. EMERGENCY PROCEDURE:                                    │
│     - Safety pilot: Flip to STABILIZE instantly             │
│     - Lower throttle to descend                             │
│     - DO NOT try to catch the drone!                        │
│                                                             │
│  5. FIRE SAFETY: Sand bucket or fire extinguisher nearby    │
│     - DO NOT use water on LiPo fires!                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 6.1 — Install Propellers

**Propeller direction (viewed from above):**
```
        FRONT
    CW ←──┬──→ CCW
         ╱│╲
        ╱ │ ╲
       ╱  │  ╲
      ╱   │   ╲
    CCW ←─┴──→ CW
        REAR

CW  = Clockwise (usually marked)
CCW = Counter-Clockwise
```

**Installation:**
1. Match prop rotation to motor direction
2. Push prop onto motor shaft
3. Tighten prop nut firmly (but don't over-tighten)
4. **Double-check all 4 props are secure**

✅ **CHECKPOINT:** All 4 propellers installed correctly

---

## Step 6.2 — Pre-Flight Checklist

**Hardware checks:**
- [ ] All 4 propellers installed and secure
- [ ] Battery freshly charged (>80%)
- [ ] Battery securely mounted (won't shift)
- [ ] USB cable connected (for laptop control)
- [ ] RC transmitter ON, throttle LOW, STABILIZE mode

**Area checks:**
- [ ] 4m x 4m clear area
- [ ] No overhead obstacles (lights, fans, cables)
- [ ] All people at 3m distance
- [ ] Safety pilot ready

**Software checks:**
- [ ] COM port configured correctly
- [ ] test_connection.py passed
- [ ] test_arm.py passed

**Announcements:**
- [ ] Announce: "DRONE TEST IN PROGRESS"
- [ ] Confirm everyone is aware and at safe distance

---

## Step 6.3 — Run Hover Test

```bash
cd D:\OneDrive\Desktop\DSA\mdp_repo\backend

python test_hover.py
```

**Follow the prompts:**
```
============================================================
🚁 INDOOR HOVER TEST — 1 METER ALTITUDE
============================================================
  Target altitude: 1.0m
  Max altitude:    1.5m (ceiling limit)
  Hover duration:  10s
  Connection:      COM3
============================================================

⚠️  SAFETY CHECKLIST:
  ├─ [ ] Propellers installed correctly (CW/CCW)
  ├─ [ ] Area cleared (4m x 4m minimum)
  ├─ [ ] Safety pilot holding RC in STABILIZE mode
  ├─ [ ] All people warned and at safe distance
  └─ [ ] Battery charged >80%

Type 'FLY' to proceed: FLY
```

**Flight sequence:**
1. Connects to Pixhawk
2. Shows pre-flight status
3. Switches to GUIDED mode
4. ARMS the motors (they will spin!)
5. Takes off to 1.0m
6. Hovers for 10 seconds
7. Lands automatically
8. Disarms

**Expected output during flight:**
```
🔌 Connecting to COM3...

📊 Pre-flight Status:
  GPS Fix:    3
  Satellites: 8
  Battery:    85%
  Is Armable: True

📡 Switching to GUIDED mode...
   Mode: GUIDED ✓

🔓 ARMING...
✅ ARMED!

🚀 TAKING OFF to 1.0m...
   Altitude: 0.25m / 1.0m
   Altitude: 0.50m / 1.0m
   Altitude: 0.75m / 1.0m
   Altitude: 0.95m / 1.0m

✅ REACHED 1.0m!

⏱️  HOVERING for 10 seconds...
   [10s] Alt: 1.02m | Batt: 84%
   [ 9s] Alt: 0.98m | Batt: 84%
   [ 8s] Alt: 1.01m | Batt: 84%
   ...

🛬 LANDING...
   Descending... Alt: 0.80m
   Descending... Alt: 0.50m
   Descending... Alt: 0.20m

✅ LANDED!

============================================================
🎉 HOVER TEST COMPLETE!
============================================================
```

---

## Step 6.4 — Emergency Procedures

**If drone behaves unexpectedly:**
1. **SAFETY PILOT:** Flip mode switch to STABILIZE immediately
2. **SAFETY PILOT:** Lower throttle to descend
3. Keep people away until motors stop

**If drone drifts:**
- Normal indoors without GPS
- Safety pilot can correct with sticks in STABILIZE

**If drone doesn't arm:**
- Check RC transmitter is ON
- Check throttle is at MINIMUM
- Check ARMING_CHECK parameter

**If drone doesn't land:**
- Safety pilot switch to STABILIZE
- Manually lower throttle
- Or script will timeout and attempt land

✅ **CHECKPOINT:** Drone hovers at 1m for 10 seconds and lands safely

---

# PHASE 7: Full System Integration

## Step 7.1 — Start Flask Backend

```bash
cd D:\OneDrive\Desktop\DSA\mdp_repo\backend

python app.py
```

**Expected output:**
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

---

## Step 7.2 — Open Web Interface

Open browser and go to:
```
http://localhost:5000
```

**Expected:** Paint-Drone control interface loads

---

## Step 7.3 — Test Each Feature

**Test 1: Video Feed**
- [ ] Live video stream visible from ESP32-CAM
- [ ] Frame rate smooth (~20 FPS)

**Test 2: Capture Frame**
- [ ] Click "Capture" button
- [ ] Image captured and displayed
- [ ] Paint detection grid overlay visible

**Test 3: Drone Telemetry**
- [ ] Click "Connect Drone" button
- [ ] Status shows: Connected, Battery %, Mode
- [ ] Real-time altitude updates

**Test 4: Spray Test** (without flying)
- [ ] Click "Test Spray" button
- [ ] Hear relay click from ESP32-CAM
- [ ] Status shows spray activated/deactivated

**Test 5: Full Autonomous Sequence** (optional)
- [ ] Safety pilot ready
- [ ] Area cleared
- [ ] Click "Start Painting" with selected cells
- [ ] Drone takes off, moves, sprays, lands

✅ **CHECKPOINT:** All system integration tests pass

---

# 📝 Test Log Template

Copy this table and fill in during testing:

| Phase | Test | Result | Notes | Date/Time |
|-------|------|--------|-------|-----------|
| 1.4 | DroneKit import | | | |
| 1.4 | OpenCV import | | | |
| 1.4 | Flask import | | | |
| 3.1 | USB Connection | | COM port: | |
| 4.2 | Arm test | | | |
| 5.4 | ESP32 ping | | | |
| 5.4 | ESP32 stream | | | |
| 6.3 | 1m hover | | Duration: | |
| 7.3 | Web UI | | | |

---

# 🔧 Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| COM port not found | Check Device Manager, try different USB port |
| Connection timeout | Check baud rate (115200), close Mission Planner |
| "Not armable" | Disable ARMING_CHECK in Mission Planner for indoor testing |
| No GPS indoors | Normal — set ARMING_CHECK=0 or use optical flow |
| Drone drifts | Normal without GPS — safety pilot can correct |
| ESP32-CAM not responding | Check 5V power, reconnect to PaintDrone WiFi |
| Video stream lag | Reduce resolution or check WiFi interference |
| Flask won't start | Activate venv, check dependencies installed |

---

# ⚠️ Important Reminders

1. **NEVER fly with damaged props or low battery**
2. **ALWAYS have safety pilot with RC ready**
3. **Re-enable ARMING_CHECK before outdoor flights**
4. **Indoor limits: 1.5m ceiling, 3m geofence**
5. **LiPo safety: Never puncture, never overcharge, never leave unattended while charging**

---

*VIT Chennai MDP — Drone #3 Indoor Lab Testing Guide v1.0*
*Last updated: March 2026*
