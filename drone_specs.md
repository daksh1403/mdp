# 🚁 Drone Hardware Specifications — Extracted from Photos

**VIT Chennai | Multi-Disciplinary Project | Drone #3**

---

## What I Can See in Each Photo

### Image 1 — Full Drone (Top View)
- **Frame:** F450/F550 style quadcopter frame (4 arms, X configuration)
- **Brand marking:** "Ready to Sky" on the dome/canopy cover
- **Motors:** 4x brushless motors with red stator caps
- **Props:** Not installed in this photo
- **RC Receiver:** FlySky receiver visible top-right corner
- **Label:** Drone is labeled **"3"** — this is Drone #3 in the lab

### Image 2 — Pixhawk Close-Up (Top View)
- **Flight Controller:** **Pixhawk 2.4.8** (clearly visible on board)
- **Ports visible (left to right, top to bottom):**
  - `POWER` — power input connector
  - `USB` — micro USB port for laptop connection and flashing
  - `TELEM 1` — telemetry port 1 (for radio/companion computer)
  - `TELEM 2` — telemetry port 2
  - `SPKT/DSM` — Spektrum/DSM receiver port
  - `ADC 3.3V` — analog input 3.3V
  - `ADC 6.6V` — analog input 6.6V
  - `I2C` — I2C bus port
  - `CAN` — CAN bus port
  - `GPS` — GPS module connector
  - `SERIAL 4/5` — additional serial ports
  - `BUZZER` — buzzer connector
  - `SWITCH` — safety switch connector
  - `AUX OUT` — auxiliary PWM outputs (1-6)
  - `MAIN OUT` — main PWM outputs (1-8) for ESCs/motors
  - `PWR` LED indicator
  - `ACT` LED indicator
  - `B/E` LED indicator
  - `SBus` — S.Bus output
- **RC Receiver attached:** FlySky **FS-IA6B** (6-channel 2.4GHz receiver)

### Image 3 — Bottom Frame
- **Power Distribution Board:** Edition 2015 PDB visible
- **Battery connector:** XT60 plug (large yellow connector) for LiPo
- **Landing gear:** 4 leg landing gear attached
- **ESC wires:** Blue phase wires going to each motor arm
- **Frame:** Carbon fibre F450 style

### Image 4 — Side View with Pixhawk
- **Pixhawk 2.4.8** confirmed again from this angle
- **FlySky FS-IA6B receiver** clearly mounted and wired
- **30A ESCs** visible on one arm (white label: "30A Brushless")
- **ESC count:** 4 ESCs (one per motor arm) — confirms **quadcopter**
- **Wiring:** Red/black power wires, blue motor phase wires

### Image 5 — Receiver and ESC Close-Up
- **RC Receiver:** **FlySky FS-IA6B** — 2.4GHz 6-channel receiver
  - Voltage: 4.0-8.4V DC
  - Channels: 6
  - Protocol: AFHDS 2A
- **ESC:** **30A Brushless ESC** confirmed
- **Port connections to Pixhawk visible:** PWM signal wires (yellow/orange) going from Pixhawk MAIN OUT to ESCs

### Image 6 — Battery
- **Brand:** Orange
- **Type:** LiPo (Lithium Polymer)
- **Cells:** **3S (3 Cell)**
- **Voltage:** **11.1V nominal** (12.6V fully charged, 9V cutoff)
- **Capacity:** **3300 mAh**
- **Discharge Rate:** **35C**
- **Max continuous current:** 3300 × 35 = **115.5A**
- **Connector:** XT60 (yellow connector)

---

## Complete Hardware Specification Table

| Component | Specification | Value |
|---|---|---|
| **Frame** | Type | F450/F550 X-config quadcopter |
| **Frame** | Arms | 4 |
| **Frame** | Material | Carbon fibre |
| **Flight Controller** | Model | **Pixhawk 2.4.8** |
| **Flight Controller** | Firmware | ArduCopter (ArduPilot) |
| **Flight Controller** | USB Port | Micro USB |
| **Flight Controller** | Telemetry | TELEM 1 and TELEM 2 ports |
| **Flight Controller** | Main PWM outputs | 8 (MAIN OUT 1-8) |
| **Flight Controller** | Aux PWM outputs | 6 (AUX OUT 1-6) |
| **RC Receiver** | Model | **FlySky FS-IA6B** |
| **RC Receiver** | Channels | 6 |
| **RC Receiver** | Frequency | 2.4GHz |
| **RC Receiver** | Protocol | AFHDS 2A |
| **RC Receiver** | Voltage | 4.0-8.4V DC |
| **ESCs** | Rating | 30A Brushless |
| **ESCs** | Count | 4 (one per motor) |
| **Motors** | Type | Brushless (red cap) |
| **Motors** | Count | 4 |
| **Battery** | Brand | Orange |
| **Battery** | Chemistry | LiPo |
| **Battery** | Cells | 3S |
| **Battery** | Voltage | **11.1V** nominal |
| **Battery** | Capacity | **3300 mAh** |
| **Battery** | Discharge | 35C |
| **Battery** | Connector | XT60 |
| **Drone Number** | Lab ID | **#3** |

---

## Critical Information for Coding

### DroneKit Connection

This is a **Pixhawk 2.4.8** — NOT the V6X from earlier photos. This is a different (older) drone.

```python
# Pixhawk 2.4.8 connection options:

# Option 1 — USB cable (micro USB to laptop)
CONNECTION_STRING = 'COM3'           # Windows — check Device Manager
CONNECTION_STRING = '/dev/ttyACM0'   # Linux

# Option 2 — TELEM 1 port (via telemetry radio)
CONNECTION_STRING = 'COM5'           # Windows (ground radio USB)
CONNECTION_STRING = '/dev/ttyUSB0'   # Linux

# Baud rate for Pixhawk 2.4.8
BAUD_RATE = 57600   # Default for TELEM ports
BAUD_RATE = 115200  # For USB connection

# DroneKit connect call
vehicle = connect(CONNECTION_STRING, baud=57600, wait_ready=True)
```

### Key Difference from Pixhawk V6X

| Feature | Pixhawk 2.4.8 (THIS DRONE) | Pixhawk V6X (Lab drone earlier) |
|---|---|---|
| USB port | Micro USB | USB-C |
| Ethernet | ❌ No ETH port | ✅ Has ETH port |
| TELEM ports | TELEM 1 + TELEM 2 | Multiple |
| Baud rate | 57600 (TELEM) | 115200 |
| Connection string | `COM3` or `COM5` | `udp:192.168.1.1:14550` |

> **Important:** Since this Pixhawk 2.4.8 has NO Ethernet port, you must use **USB cable** or **telemetry radio** to connect.

### Battery Power for Your Payload

```
Battery output: 11.1V via XT60 connector

For your payload:
  Buck Converter IN+  ──► Battery XT60 positive (11.1V)
  Buck Converter IN-  ──► Battery XT60 negative (GND)
  Buck Converter OUT+ ──► ESP32-CAM 5V + Relay VCC
  Buck Converter OUT- ──► Common GND

Set buck converter output to exactly 5V before connecting.
Max safe draw from 3300mAh 35C battery: 115A (more than enough)
Your payload draws: ~500mA total (very safe)
```

### ESC and Motor Output Pins

```
Pixhawk 2.4.8 MAIN OUT pin mapping for quadcopter X frame:

MAIN OUT 1  ──► ESC Motor 1 (Front Right)
MAIN OUT 2  ──► ESC Motor 2 (Rear Left)
MAIN OUT 3  ──► ESC Motor 3 (Front Left)
MAIN OUT 4  ──► ESC Motor 4 (Rear Right)

AUX OUT 1-6 ──► Available for payload control
              ──► Can use AUX OUT 1 for relay trigger
                  instead of ESP32-CAM if needed
```

### FlySky FS-IA6B Receiver Channels

```
Channel 1  ──► Aileron (Roll)
Channel 2  ──► Elevator (Pitch)
Channel 3  ──► Throttle
Channel 4  ──► Rudder (Yaw)
Channel 5  ──► Flight Mode Switch (GUIDED/STABILIZE/LOITER)
Channel 6  ──► Spare (can use for spray trigger override)
```

---

## Updated drone_controller.py Settings for This Drone

```python
# ── UPDATE THESE in drone_controller.py ────────────────────

# Connection — Pixhawk 2.4.8 uses USB or radio (no ETH)
CONNECTION_STRING = 'COM3'    # USB cable — check Device Manager for exact port
# OR for telemetry radio:
# CONNECTION_STRING = 'COM5'  # Ground radio USB port

# Baud rate — important for 2.4.8
BAUD_RATE = 57600   # Use this for TELEM port
# BAUD_RATE = 115200  # Use this for USB direct

# Battery safety threshold — 3S LiPo 3300mAh
# Never discharge below 3.5V per cell = 10.5V total
# DroneKit safety monitor threshold:
BATTERY_MIN_PERCENT = 20   # RTL when battery hits 20%

# Frame type — quadcopter (4 motors)
# In Mission Planner: Frame Type = X (not plus)
# FRAME_CLASS = 1 (Quad)
# FRAME_TYPE = 1 (X configuration)
```

---

## Mission Planner Setup for Pixhawk 2.4.8

When connecting this specific drone to Mission Planner:

```
1. Connect micro USB cable → laptop
2. Open Mission Planner
3. Top right: Select COM port (check Device Manager)
4. Baud rate: 115200 (for USB)
5. Click Connect

Key parameters to verify/set:
  FRAME_CLASS  = 1   (Quad)
  FRAME_TYPE   = 1   (X config)
  ARMING_CHECK = 0   (disable for testing, RE-ENABLE for flight)
  FS_THR_ENABLE = 1  (throttle failsafe ON)
  FS_THR_VALUE  = 975 (failsafe throttle PWM)
  RTL_ALT       = 500 (RTL altitude 5m in cm)
  FENCE_ENABLE  = 1   (enable geofence)
  FENCE_RADIUS  = 500 (5m radius in cm)
  FENCE_ALT_MAX = 500 (5m max altitude in cm)
```

---

## Payload Mounting Notes

Based on the frame photos:

```
Available mounting space:
  Top plate:    Pixhawk + receiver already mounted
  Bottom plate: PDB mounted, XT60 connector hanging below
  
Best location for ESP32-CAM + relay:
  Option A: Velcro on top plate SIDE (next to Pixhawk)
  Option B: Mount below bottom plate using standoffs
  
Weight distribution:
  Pump + water: mount centered under bottom plate
  ESP32-CAM: mount at front for clear wall view
  Relay: mount anywhere near ESP32-CAM
  
Cable routing:
  Buck converter input ── tap from XT60 via Y-splitter
  Keep ESP32-CAM wires away from ESC phase wires (interference)
```

---

## RC Transmitter — FlySky FS-i6 (matching the FS-IA6B receiver)

The receiver is **FlySky FS-IA6B** which pairs with **FlySky FS-i6** transmitter (visible top-right in Image 1).

```
Safety pilot setup:
  Switch SWC or SWD ──► Flight mode channel (Ch5)
  
  3-position switch positions:
    Position 1 (up)    ──► STABILIZE  (full manual override)
    Position 2 (mid)   ──► LOITER     (hold position, manual input)
    Position 3 (down)  ──► GUIDED     (autonomous — DroneKit control)

  ALWAYS start in STABILIZE
  Switch to GUIDED only when ready for autonomous flight
  Switch back to STABILIZE instantly if anything wrong
```

---

## Summary — What Changed vs Earlier Plan

| Item | Earlier Assumption | Actual (from photos) |
|---|---|---|
| Flight Controller | Pixhawk V6X | **Pixhawk 2.4.8** |
| Connection | ETH or USB-C | **Micro USB only** |
| Connection string | `udp:192.168.1.1:14550` | **`COM3` (USB)** |
| Baud rate | 115200 | **57600 (TELEM) / 115200 (USB)** |
| Frame type | Hexacopter | **Quadcopter (4 motors)** |
| RC Receiver | Not identified | **FlySky FS-IA6B 6ch** |
| Battery | 3S 11.1V (confirmed) | **Orange 3S 3300mAh 35C XT60** ✅ |

---

*All specifications extracted directly from drone photos — Drone #3, VIT Chennai Drone Lab*
