# 🛡️ Indoor Lab Drone Testing — Safety Checklist

## VIT Chennai MDP — Drone #3 (Pixhawk 2.4.8)

> ⚠️ **SAFETY FIRST:** Follow ALL checkpoints in order. Never skip steps!

---

## 📋 Pre-Flight Information

| Item | Value |
|------|-------|
| Drone ID | #3 |
| Flight Controller | Pixhawk 2.4.8 |
| Max Altitude (Lab) | **1.0m** (ceiling limit: 1.5m) |
| Geofence Radius | **3.0m** |
| Battery | Orange 3S 3300mAh 35C |
| RC Transmitter | FlySky FS-i6 |

---

# ✅ CHECKPOINT 1: Software Setup Verification

## 1.1 Python Environment
```bash
# Create virtual environment (if not exists)
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Verify Installation:
```bash
python -c "from dronekit import connect; print('DroneKit OK')"
python -c "import cv2; print('OpenCV OK')"
python -c "from flask import Flask; print('Flask OK')"
```

**✅ PASS:** All imports work without errors

---

## 1.2 Check USB Port
```bash
# Windows: Open Device Manager
# Look for: "Ports (COM & LPT)" → "Pixhawk" or "Arduino Mega"
# Note the COM port number (e.g., COM3, COM4)
```

### Update connection if needed:
```python
# In backend/drone_controller.py, line ~62
CONNECTION_STRING = 'COM3'  # Change to your actual port
```

**✅ PASS:** COM port identified and configured

---

## 1.3 Verify Safety Parameters
```bash
# Open drone_controller.py and confirm these values:
```

| Parameter | Required Value | Your Value |
|-----------|----------------|------------|
| `MAX_ALTITUDE` | 1.5 | _____ |
| `PAINTING_ALTITUDE` | 1.0 | _____ |
| `MAX_DISTANCE` | 3.0 | _____ |
| `MIN_BATTERY` | 20 | _____ |
| `CONNECTION_STRING` | 'COM3' | _____ |
| `BAUD_RATE` | 115200 | _____ |

**✅ PASS:** All safety parameters confirmed

---

# ✅ CHECKPOINT 2: USB Connection Test

## 2.1 Physical Connection
1. [ ] Pixhawk powered OFF
2. [ ] Connect Micro USB cable to Pixhawk 2.4.8
3. [ ] Connect other end to laptop
4. [ ] Power ON Pixhawk (via battery or USB power)
5. [ ] Wait for Pixhawk startup tones (musical scale)

## 2.2 Test Connection Script
Create test file `test_connection.py`:
```python
"""Test Pixhawk 2.4.8 connection"""
import collections
import collections.abc
for attr in ("MutableMapping", "MutableSequence", "MutableSet",
             "Mapping", "Sequence", "Set", "Iterable", "Iterator",
             "Callable", "Hashable", "Sized"):
    if not hasattr(collections, attr):
        setattr(collections, attr, getattr(collections.abc, attr))

from dronekit import connect
import sys

CONNECTION = 'COM3'  # Change to your port
BAUD = 115200

print(f"Connecting to Pixhawk 2.4.8 at {CONNECTION}...")
try:
    vehicle = connect(CONNECTION, baud=BAUD, wait_ready=True, timeout=30)
    
    print("\n" + "="*50)
    print("✅ CONNECTION SUCCESSFUL!")
    print("="*50)
    print(f"Firmware:    {vehicle.version}")
    print(f"Vehicle:     {vehicle.vehicle_type}")
    print(f"Mode:        {vehicle.mode.name}")
    print(f"Armed:       {vehicle.armed}")
    print(f"GPS Fix:     {vehicle.gps_0.fix_type}")
    print(f"GPS Sats:    {vehicle.gps_0.satellites_visible}")
    print(f"Battery:     {vehicle.battery.level}%")
    print(f"Voltage:     {vehicle.battery.voltage}V")
    print(f"Is Armable:  {vehicle.is_armable}")
    print("="*50)
    
    vehicle.close()
    print("\nConnection closed cleanly.")
    
except Exception as e:
    print(f"\n❌ CONNECTION FAILED: {e}")
    print("\nTroubleshooting:")
    print("1. Check COM port in Device Manager")
    print("2. Ensure Pixhawk is powered")
    print("3. Try different USB cable")
    print("4. Check BAUD rate (115200 for USB, 57600 for TELEM)")
    sys.exit(1)
```

Run:
```bash
python test_connection.py
```

**✅ PASS:** See "CONNECTION SUCCESSFUL!" message

---

# ✅ CHECKPOINT 3: Pre-flight Checks (PROPS OFF!)

## ⚠️ WARNING: DO NOT INSTALL PROPELLERS YET!

## 3.1 Physical Inspection
- [ ] Frame is intact, no cracks
- [ ] All 4 motors spin freely by hand
- [ ] All wires securely connected
- [ ] Battery connector (XT60) not damaged
- [ ] RC receiver antenna extended
- [ ] Pixhawk mounted securely
- [ ] **PROPELLERS REMOVED** ⚠️

## 3.2 Battery Check
- [ ] Battery voltage: _____ V (should be 11.1V - 12.6V)
- [ ] Battery charged above 80%
- [ ] XT60 connector clean, no burn marks
- [ ] Balance connector intact

## 3.3 RC Transmitter Setup
1. [ ] Transmitter powered ON
2. [ ] Throttle stick at MINIMUM (down)
3. [ ] Flight mode switch to STABILIZE (Position 1 / UP)
4. [ ] Check binding (LED on receiver solid)

**✅ PASS:** All physical checks complete, PROPS OFF

---

# ✅ CHECKPOINT 4: Arm Test (PROPS OFF!)

## ⚠️ CRITICAL: PROPELLERS MUST BE OFF!

## 4.1 Manual Arm Test via RC
1. [ ] Pixhawk powered, connected to laptop
2. [ ] RC transmitter ON, throttle at minimum
3. [ ] Mode switch on STABILIZE
4. [ ] Hold throttle down-right for 3 seconds
5. [ ] Listen for arming tone (long beep)
6. [ ] Check: Motors should NOT spin (no props = no danger)
7. [ ] Immediately DISARM: throttle down-left for 3 seconds

**✅ PASS:** Arm/disarm works via RC

## 4.2 Arm Test via Script
Create `test_arm.py`:
```python
"""Test arming (PROPS MUST BE OFF!)"""
import collections
import collections.abc
for attr in ("MutableMapping", "MutableSequence", "MutableSet",
             "Mapping", "Sequence", "Set", "Iterable", "Iterator",
             "Callable", "Hashable", "Sized"):
    if not hasattr(collections, attr):
        setattr(collections, attr, getattr(collections.abc, attr))

from dronekit import connect, VehicleMode
import time

CONNECTION = 'COM3'
BAUD = 115200

print("⚠️  WARNING: PROPELLERS MUST BE REMOVED!")
input("Press ENTER to confirm props are OFF...")

print(f"\nConnecting to {CONNECTION}...")
vehicle = connect(CONNECTION, baud=BAUD, wait_ready=True, timeout=30)

print(f"Mode: {vehicle.mode.name}")
print(f"Armed: {vehicle.armed}")
print(f"Is Armable: {vehicle.is_armable}")

if not vehicle.is_armable:
    print("\n❌ Vehicle not armable!")
    print("Check: GPS fix, pre-arm checks in Mission Planner")
    vehicle.close()
    exit(1)

print("\nSwitching to GUIDED mode...")
vehicle.mode = VehicleMode("GUIDED")
time.sleep(2)

print("Attempting to ARM...")
vehicle.armed = True

timeout = 10
while not vehicle.armed and timeout > 0:
    print(f"  Waiting for arm... ({timeout}s)")
    time.sleep(1)
    timeout -= 1

if vehicle.armed:
    print("\n✅ ARMED SUCCESSFULLY!")
    print("Motors would spin now (but props are off)")
    time.sleep(3)
    
    print("\nDISARMING...")
    vehicle.armed = False
    time.sleep(2)
    print(f"Armed: {vehicle.armed}")
else:
    print("\n❌ FAILED TO ARM")
    print("Check pre-arm conditions in Mission Planner")

vehicle.close()
print("\nTest complete.")
```

Run:
```bash
python test_arm.py
```

**✅ PASS:** "ARMED SUCCESSFULLY!" message seen

---

# ✅ CHECKPOINT 5: First Hover Test (1m)

## ⚠️ NOW YOU MAY INSTALL PROPELLERS

## 5.1 Safety Setup
- [ ] Clear area of 4m x 4m minimum
- [ ] All people at least 3m away
- [ ] Safety pilot holding RC in STABILIZE
- [ ] Fire extinguisher nearby
- [ ] First aid kit accessible
- [ ] Laptop operator ready at safe distance

## 5.2 Propeller Installation
- [ ] Match prop direction to motor (CW/CCW markings)
- [ ] Tighten prop nuts securely
- [ ] Double-check all 4 props

## 5.3 Pre-Takeoff Checklist
- [ ] Battery freshly charged (>80%)
- [ ] GPS lock (>6 satellites, fix_type >= 3)
- [ ] All pre-arm checks pass
- [ ] RC throttle at MINIMUM
- [ ] RC mode switch on STABILIZE
- [ ] Everyone warned: "DRONE TEST IN PROGRESS"

## 5.4 Hover Test Script
Create `test_hover.py`:
```python
"""First hover test at 1m (REQUIRES PROPELLERS)"""
import collections
import collections.abc
for attr in ("MutableMapping", "MutableSequence", "MutableSet",
             "Mapping", "Sequence", "Set", "Iterable", "Iterator",
             "Callable", "Hashable", "Sized"):
    if not hasattr(collections, attr):
        setattr(collections, attr, getattr(collections.abc, attr))

from dronekit import connect, VehicleMode
import time

# ════════════════════════════════════════════════════════
#  SAFETY CONFIGURATION
# ════════════════════════════════════════════════════════
TARGET_ALTITUDE = 1.0  # meters - INDOOR LAB HEIGHT
MAX_ALTITUDE = 1.5     # meters - absolute ceiling
HOVER_TIME = 10        # seconds
CONNECTION = 'COM3'
BAUD = 115200

print("="*60)
print("🚁 INDOOR HOVER TEST — 1 METER ALTITUDE")
print("="*60)
print(f"  Target altitude: {TARGET_ALTITUDE}m")
print(f"  Max altitude:    {MAX_ALTITUDE}m")
print(f"  Hover duration:  {HOVER_TIME}s")
print("="*60)

print("\n⚠️  SAFETY CHECKLIST:")
print("  [ ] Propellers installed correctly")
print("  [ ] Area cleared (4m radius)")
print("  [ ] Safety pilot ready with RC in STABILIZE")
print("  [ ] Everyone warned")

confirm = input("\nType 'FLY' to proceed: ")
if confirm != 'FLY':
    print("Aborted.")
    exit(0)

print(f"\nConnecting to {CONNECTION}...")
vehicle = connect(CONNECTION, baud=BAUD, wait_ready=True, timeout=30)

print(f"GPS Fix: {vehicle.gps_0.fix_type}")
print(f"Satellites: {vehicle.gps_0.satellites_visible}")
print(f"Battery: {vehicle.battery.level}%")
print(f"Is Armable: {vehicle.is_armable}")

if vehicle.gps_0.fix_type < 3:
    print("❌ No GPS fix! Wait for GPS lock.")
    vehicle.close()
    exit(1)

if not vehicle.is_armable:
    print("❌ Not armable! Check pre-arm conditions.")
    vehicle.close()
    exit(1)

print("\n📍 Switching to GUIDED mode...")
vehicle.mode = VehicleMode("GUIDED")
time.sleep(2)

print("🔓 ARMING...")
vehicle.armed = True

timeout = 10
while not vehicle.armed and timeout > 0:
    print(f"  Waiting... ({timeout}s)")
    time.sleep(1)
    timeout -= 1

if not vehicle.armed:
    print("❌ Failed to arm!")
    vehicle.close()
    exit(1)

print("✅ ARMED!")
print(f"\n🚀 TAKING OFF to {TARGET_ALTITUDE}m...")
vehicle.simple_takeoff(TARGET_ALTITUDE)

# Monitor altitude
while True:
    alt = vehicle.location.global_relative_frame.alt
    print(f"  Altitude: {alt:.2f}m / {TARGET_ALTITUDE}m")
    
    if alt >= TARGET_ALTITUDE * 0.95:
        print(f"\n✅ REACHED {TARGET_ALTITUDE}m!")
        break
    
    # Safety check
    if alt > MAX_ALTITUDE:
        print("⚠️  CEILING BREACH! Landing...")
        vehicle.mode = VehicleMode("LAND")
        break
    
    time.sleep(1)

print(f"\n⏱️  HOVERING for {HOVER_TIME} seconds...")
for i in range(HOVER_TIME, 0, -1):
    alt = vehicle.location.global_relative_frame.alt
    print(f"  [{i}s] Altitude: {alt:.2f}m")
    time.sleep(1)

print("\n🛬 LANDING...")
vehicle.mode = VehicleMode("LAND")

while vehicle.armed:
    alt = vehicle.location.global_relative_frame.alt
    print(f"  Landing... Altitude: {alt:.2f}m")
    if alt < 0.1:
        break
    time.sleep(1)

print("\n✅ LANDED!")
vehicle.armed = False
vehicle.close()

print("\n" + "="*60)
print("🎉 HOVER TEST COMPLETE!")
print("="*60)
```

## 5.5 Emergency Procedures
If anything goes wrong:
1. **SAFETY PILOT:** Flip RC switch to STABILIZE immediately
2. **SAFETY PILOT:** Lower throttle to descend
3. **DO NOT** try to catch the drone
4. If RC fails: Drone should auto-land (failsafe)
5. If fire: Do NOT use water on LiPo — use sand/extinguisher

**✅ PASS:** Drone hovers at 1m for 10 seconds, lands safely

---

# ✅ CHECKPOINT 6: Full System Integration

## 6.1 ESP32-CAM Connection
1. [ ] Power ESP32-CAM (via drone battery + buck converter at 5V)
2. [ ] Connect laptop WiFi to "PaintDrone" (password: paintdrone123)
3. [ ] Test: `ping 192.168.4.1`
4. [ ] Test: Open `http://192.168.4.1/ping` in browser
5. [ ] Test: Open `http://192.168.4.1:81/stream` for video

## 6.2 Flask Backend Test
```bash
cd backend
python app.py
```

Open browser: `http://localhost:5000`

- [ ] Web UI loads
- [ ] Video stream visible
- [ ] "Capture" button works
- [ ] Paint detection shows grid

## 6.3 Full System Test
1. [ ] Drone connected via USB
2. [ ] ESP32-CAM streaming
3. [ ] Web UI showing telemetry
4. [ ] Spray trigger test (relay click heard)
5. [ ] Full autonomous sequence (with safety pilot ready)

**✅ PASS:** All systems working together

---

# 📝 Test Log

| Date | Checkpoint | Result | Notes |
|------|------------|--------|-------|
| _____ | 1 | PASS/FAIL | |
| _____ | 2 | PASS/FAIL | |
| _____ | 3 | PASS/FAIL | |
| _____ | 4 | PASS/FAIL | |
| _____ | 5 | PASS/FAIL | |
| _____ | 6 | PASS/FAIL | |

---

# 🆘 Troubleshooting

## Connection Issues
| Problem | Solution |
|---------|----------|
| COM port not found | Check Device Manager, try different USB port |
| Connection timeout | Check baud rate (115200 for USB) |
| "not armable" | Disable ARMING_CHECK in Mission Planner for testing |

## GPS Issues (Indoor)
| Problem | Solution |
|---------|----------|
| No GPS fix indoors | Normal — GPS won't work indoors |
| Need to test without GPS | Set `ARMING_CHECK = 0` in Mission Planner |
| Better: Use EKF2 | Enable optical flow or use mocap system |

## Arming Issues
| Problem | Solution |
|---------|----------|
| Pre-arm: GPS | Set `GPS_TYPE = 0` to disable GPS check |
| Pre-arm: Compass | Calibrate compass or disable check |
| Pre-arm: RC | Ensure RC transmitter is on and bound |

---

*VIT Chennai MDP — Drone #3 Indoor Lab Testing Checklist v1.0*
