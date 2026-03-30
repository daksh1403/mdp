# 🚁 Drone Default Parameters — Pixhawk 2.4.8 (Drone #3)

This document lists all configurable parameters for the PaintDrone system.

**Hardware:** Pixhawk 2.4.8 | F450 Quadcopter | FlySky FS-IA6B | 3S 3300mAh LiPo

---

## ⚠️ CURRENT MODE: INDOOR LAB TESTING

> **WARNING:** Safety limits are configured for INDOOR operation.
> Maximum altitude is 1.5m. Adjust before outdoor flights!

---

## 📍 Painting Parameters

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `PAINTING_ALTITUDE` | `1.0 m` | **INDOOR LAB** height for painting (reduced from 3.0m) |
| `WALL_DISTANCE` | `0.5 m` | Distance from the wall to hover while painting |
| `CELL_WIDTH_M` | `0.3 m` | Real-world width of one grid cell |
| `CELL_HEIGHT_M` | `0.3 m` | Real-world height of one grid cell |
| `SPRAY_DURATION_MS` | `800 ms` | Spray duration per cell |
| `CONTINUOUS_SPEED` | `0.2 m/s` | Movement speed (reduced for indoor safety) |
| `GRID_COLS` | `12` | Number of columns in the painting grid |
| `GRID_ROWS` | `8` | Number of rows in the painting grid |

---

## ⚠️ Safety Limits (Indoor Lab)

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `MAX_ALTITUDE` | `1.5 m` | **INDOOR CEILING** — triggers RTL if exceeded |
| `MIN_BATTERY` | `20%` | Minimum battery level — triggers RTL if below |
| `MAX_DISTANCE` | `3.0 m` | **INDOOR GEOFENCE** — maximum distance from home |

---

## 🔌 Connection Settings — Pixhawk 2.4.8

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `CONNECTION_STRING` | `COM3` | USB connection (check Device Manager) |
| `BAUD_RATE` | `115200` | USB baud rate |
| `ESP32_CONTROL` | `http://192.168.4.1` | ESP32-CAM address for spray commands |

### Connection Options for Pixhawk 2.4.8

| Mode | Connection String | Baud Rate |
|------|-------------------|-----------|
| **USB (Windows)** | `COM3` | 115200 |
| **USB (Linux)** | `/dev/ttyACM0` | 115200 |
| **TELEM Radio (Windows)** | `COM5` | 57600 |
| **TELEM Radio (Linux)** | `/dev/ttyUSB0` | 57600 |
| **SITL (Simulator)** | `tcp:127.0.0.1:5762` | N/A |

> ⚠️ **NOTE:** Pixhawk 2.4.8 has NO Ethernet port (unlike V6X). Use USB or TELEM radio only.

---

## 📐 Coordinate System

- **Column** → East offset from origin
- **Row** → Controls altitude (Row 0 = top = highest altitude)
- Grid cells are converted to GPS waypoints using the origin coordinates

---

## 🔧 Modifying Parameters

All parameters are defined at the top of `backend/drone_controller.py`. To modify:

```python
# Example: Switch to outdoor mode (ONLY AFTER INDOOR TESTING)
MAX_ALTITUDE       = 8.0     # meters
PAINTING_ALTITUDE  = 3.0     # meters
MAX_DISTANCE       = 10.0    # meters

# Example: Change USB port
CONNECTION_STRING = 'COM4'   # Your actual COM port

# Example: Switch to TELEM radio
CONNECTION_STRING = 'COM5'
BAUD_RATE = 57600
```

---

## 🔋 Battery Information (Orange 3S 3300mAh)

| Spec | Value |
|------|-------|
| Chemistry | LiPo |
| Cells | 3S |
| Nominal Voltage | 11.1V |
| Full Charge | 12.6V |
| Low Cutoff | 10.5V (3.5V/cell) |
| Capacity | 3300 mAh |
| Discharge Rate | 35C |
| Connector | XT60 |

---

## 📝 Notes

- **INDOOR TESTING:** Always test with props OFF first!
- Safety limits will automatically trigger RTL mode if exceeded
- Battery monitoring runs in a background thread (checks every 1 second)
- Always have a safety pilot with RC transmitter in STABILIZE mode override
