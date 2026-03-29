# 🚁 Drone Default Parameters

This document lists all configurable parameters for the PaintDrone system.

---

## 📍 Painting Parameters

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `PAINTING_ALTITUDE` | `3.0 m` | Default height above ground for painting operations |
| `WALL_DISTANCE` | `0.5 m` | Distance from the wall to hover while painting |
| `CELL_WIDTH_M` | `0.3 m` | Real-world width of one grid cell |
| `CELL_HEIGHT_M` | `0.3 m` | Real-world height of one grid cell |
| `SPRAY_DURATION_MS` | `800 ms` | Spray duration per cell |
| `CONTINUOUS_SPEED` | `0.3 m/s` | Movement speed during continuous painting |
| `GRID_COLS` | `12` | Number of columns in the painting grid |
| `GRID_ROWS` | `8` | Number of rows in the painting grid |

---

## ⚠️ Safety Limits

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `MAX_ALTITUDE` | `8.0 m` | Maximum allowed altitude — triggers RTL (Return To Launch) if exceeded |
| `MIN_BATTERY` | `15%` | Minimum battery level — triggers RTL if below this threshold |
| `MAX_DISTANCE` | `10.0 m` | Maximum allowed distance from home position — safety geofence limit |

---

## 🔌 Connection Settings

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| `CONNECTION_STRING` | `tcp:127.0.0.1:5762` | Default connection (SITL simulator) |
| `ESP32_CONTROL` | `http://192.168.4.1` | ESP32-CAM address for spray commands |

### Connection Options

| Mode | Connection String |
|------|-------------------|
| **SITL (Simulator)** | `tcp:127.0.0.1:5762` |
| **USB (Windows)** | `COM3` |
| **USB (Linux)** | `/dev/ttyACM0` |
| **Ethernet** | `udp:192.168.1.1:14550` |
| **Radio (Windows)** | `COM5` |
| **Radio (Linux)** | `/dev/ttyUSB0` |

---

## 📐 Coordinate System

- **Column** → East offset from origin
- **Row** → Controls altitude (Row 0 = top = highest altitude)
- Grid cells are converted to GPS waypoints using the origin coordinates

---

## 🔧 Modifying Parameters

All parameters are defined at the top of `backend/drone_controller.py`. To modify:

```python
# Example: Change painting altitude to 4 meters
PAINTING_ALTITUDE = 4.0

# Example: Increase grid size
GRID_COLS = 16
GRID_ROWS = 10

# Example: Change connection for real hardware
CONNECTION_STRING = 'COM3'  # Windows USB
```

---

## 📝 Notes

- Always test parameter changes in SITL simulation before flying with real hardware
- Safety limits (MAX_ALTITUDE, MIN_BATTERY, MAX_DISTANCE) will automatically trigger RTL mode
- Battery monitoring runs in a background thread and checks every 1 second
