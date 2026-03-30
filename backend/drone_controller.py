"""
============================================================
 DroneController — Autonomous Drone Control via DroneKit
 VIT Chennai Multi-Disciplinary Project — Drone #3
============================================================

Connects to Pixhawk 2.4.8 (NOT V6X) and provides:
  - Arm and takeoff
  - GPS waypoint navigation
  - Safety monitoring (battery, altitude, geofence)
  - Grid cell to GPS coordinate conversion

HARDWARE SPECS (Drone #3):
  Flight Controller: Pixhawk 2.4.8
  Frame:            F450 Quadcopter X-config
  ESCs:             4x 30A Brushless
  RC Receiver:      FlySky FS-IA6B (6-channel)
  Battery:          Orange 3S 3300mAh 35C LiPo (11.1V)

Connection modes for Pixhawk 2.4.8:
  SITL:    'tcp:127.0.0.1:5762'
  USB:     'COM3' (Windows) or '/dev/ttyACM0' (Linux)
  TELEM:   'COM5' (Windows) or '/dev/ttyUSB0' (Linux)
  
NOTE: Pixhawk 2.4.8 has NO Ethernet port (unlike V6X)
============================================================
"""

# Monkey-patch for Python 3.10+ compatibility with DroneKit
import collections
import collections.abc
for attr in ("MutableMapping", "MutableSequence", "MutableSet",
             "Mapping", "Sequence", "Set", "Iterable", "Iterator",
             "Callable", "Hashable", "Sized"):
    if not hasattr(collections, attr):
        setattr(collections, attr, getattr(collections.abc, attr))

import time
import math
import threading
import requests
from dronekit import connect, VehicleMode, LocationGlobalRelative

# ══════════════════════════════════════════════════════════════
#  Configuration — TUNED FOR PIXHAWK 2.4.8 + INDOOR LAB TESTING
# ══════════════════════════════════════════════════════════════

# ESP32-CAM address for spray commands
ESP32_CONTROL = "http://192.168.4.1"

# ────────────────────────────────────────────────────────────────
#  INDOOR LAB SAFETY SETTINGS (Drone #3)
#  ⚠️ CRITICAL: These are set for INDOOR TESTING at 1m altitude
# ────────────────────────────────────────────────────────────────
PAINTING_ALTITUDE  = 1.0     # meters — INDOOR LAB SAFE HEIGHT
WALL_DISTANCE      = 0.5     # meters from wall to hover
CELL_WIDTH_M       = 0.3     # real-world width of one grid cell
CELL_HEIGHT_M      = 0.3     # real-world height of one grid cell
SPRAY_DURATION_MS  = 800     # milliseconds per cell
CONTINUOUS_SPEED   = 0.2     # m/s — SLOWER FOR INDOOR (was 0.3)
GRID_COLS          = 12
GRID_ROWS          = 8

# ────────────────────────────────────────────────────────────────
#  INDOOR LAB SAFETY LIMITS
#  ⚠️ STRICT LIMITS FOR LAB ENVIRONMENT
# ────────────────────────────────────────────────────────────────
MAX_ALTITUDE       = 1.5     # meters — INDOOR LAB CEILING LIMIT (triggers RTL)
MIN_BATTERY        = 20      # percent — RTL if below (increased for safety)
MAX_DISTANCE       = 3.0     # meters from home — INDOOR GEOFENCE

# ────────────────────────────────────────────────────────────────
#  PIXHAWK 2.4.8 CONNECTION SETTINGS
# ────────────────────────────────────────────────────────────────
# For USB connection (Micro USB cable):
#   Windows: 'COM3' (check Device Manager for actual port)
#   Linux:   '/dev/ttyACM0'
#   Baud:    115200
#
# For TELEM port (telemetry radio):
#   Windows: 'COM5'
#   Linux:   '/dev/ttyUSB0'
#   Baud:    57600
#
# For SITL simulation:
#   'tcp:127.0.0.1:5762'
# ────────────────────────────────────────────────────────────────
CONNECTION_STRING = 'COM9'   # USB connection for Pixhawk 2.4.8
BAUD_RATE = 115200           # USB baud rate (use 57600 for TELEM)


# ══════════════════════════════════════════════════════════════
#  DroneController Class
# ══════════════════════════════════════════════════════════════

class DroneController:
    """Manages autonomous drone movement for painting."""

    def __init__(self, connection_string=CONNECTION_STRING):
        self.connection_string = connection_string
        self.vehicle = None
        self.home_location = None
        self.connected = False
        self._safety_thread = None
        self._safety_running = False

    def connect(self):
        """Connect to Pixhawk 2.4.8 via DroneKit."""
        print(f"[Drone] Connecting to Pixhawk 2.4.8 at {self.connection_string}...")
        print(f"[Drone] Baud rate: {BAUD_RATE}")
        try:
            self.vehicle = connect(
                self.connection_string,
                baud=BAUD_RATE,
                wait_ready=True,
                timeout=30
            )
            self.connected = True
            print(f"[Drone] Connected!")
            print(f"[Drone] Firmware: {self.vehicle.version}")
            print(f"[Drone] GPS: {self.vehicle.gps_0}")
            print(f"[Drone] Battery: {self.vehicle.battery}")
            print(f"[Drone] Mode: {self.vehicle.mode.name}")
            print(f"[Drone] Armed: {self.vehicle.armed}")
            
            # Start safety monitor
            self.start_safety_monitor()
            
            return True
        except Exception as e:
            print(f"[Drone] Connection FAILED: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Safely disconnect from drone."""
        self.stop_safety_monitor()
        if self.vehicle:
            self.vehicle.close()
            self.connected = False
            print("[Drone] Disconnected")

    def get_status(self):
        """Return current drone status as dict."""
        if not self.connected or not self.vehicle:
            return {"connected": False}
        try:
            return {
                "connected":   True,
                "mode":        self.vehicle.mode.name,
                "armed":       self.vehicle.armed,
                "altitude":    self.vehicle.location.global_relative_frame.alt,
                "lat":         self.vehicle.location.global_frame.lat,
                "lon":         self.vehicle.location.global_frame.lon,
                "battery":     self.vehicle.battery.level if self.vehicle.battery else 0,
                "gps_fix":     self.vehicle.gps_0.fix_type if self.vehicle.gps_0 else 0,
                "groundspeed": self.vehicle.groundspeed,
                "heading":     self.vehicle.heading,
                "is_armable":  self.vehicle.is_armable,
            }
        except Exception as e:
            return {"connected": True, "error": str(e)}

    def is_ready_to_fly(self):
        """Check all pre-flight conditions."""
        if not self.connected:
            return False, "Not connected to drone"
        if self.vehicle.gps_0.fix_type < 3:
            return False, "GPS fix not ready (need fix_type >= 3)"
        if self.vehicle.battery and self.vehicle.battery.level < MIN_BATTERY:
            return False, f"Battery too low: {self.vehicle.battery.level}%"
        if not self.vehicle.is_armable:
            return False, "Vehicle is not armable (check pre-arm conditions)"
        return True, "Ready"

    def arm_and_takeoff(self, target_altitude):
        """Arm the drone and take off to target_altitude (meters).
        
        ⚠️ INDOOR LAB SAFETY: Max altitude is capped at MAX_ALTITUDE (1.5m)
        """
        # Cap altitude for indoor safety
        if target_altitude > MAX_ALTITUDE:
            print(f"[SAFETY] Requested altitude {target_altitude}m exceeds indoor limit!")
            print(f"[SAFETY] Capping to MAX_ALTITUDE = {MAX_ALTITUDE}m")
            target_altitude = MAX_ALTITUDE
        
        print(f"[Drone] Arming and taking off to {target_altitude}m...")
        print(f"[SAFETY] Indoor lab mode: MAX_ALT={MAX_ALTITUDE}m, GEOFENCE={MAX_DISTANCE}m")

        # Switch to GUIDED mode
        self.vehicle.mode = VehicleMode("GUIDED")
        time.sleep(2)

        # Arm
        self.vehicle.armed = True
        timeout = 10
        while not self.vehicle.armed and timeout > 0:
            print("[Drone] Waiting for arm...")
            time.sleep(1)
            timeout -= 1

        if not self.vehicle.armed:
            raise Exception("Drone failed to arm — check pre-arm conditions")

        print("[Drone] Armed! Taking off...")

        # Takeoff
        self.vehicle.simple_takeoff(target_altitude)

        # Store home location
        self.home_location = self.vehicle.location.global_frame

        # Wait for altitude
        while True:
            alt = self.vehicle.location.global_relative_frame.alt
            print(f"[Drone] Altitude: {alt:.1f}m / {target_altitude}m")
            if alt >= target_altitude * 0.95:
                print("[Drone] Target altitude reached!")
                break
            time.sleep(1)

    def goto_global(self, lat, lon, alt):
        """Fly to a specific GPS coordinate."""
        target = LocationGlobalRelative(lat, lon, alt)
        self.vehicle.simple_goto(target, groundspeed=1.0)
        print(f"[Drone] Flying to lat={lat:.6f} lon={lon:.6f} alt={alt}m")

    def wait_until_reached(self, target_lat, target_lon,
                            tolerance_m=0.5, timeout=30):
        """Wait until drone reaches target GPS position."""
        start = time.time()
        while time.time() - start < timeout:
            current = self.vehicle.location.global_frame
            dist = self._distance_m(
                current.lat, current.lon,
                target_lat, target_lon
            )
            if dist <= tolerance_m:
                print(f"[Drone] Reached target (dist={dist:.2f}m)")
                return True
            time.sleep(0.5)
        print(f"[Drone] Timeout reaching target")
        return False

    def hover(self, duration_s):
        """Hold current position for duration_s seconds."""
        print(f"[Drone] Hovering for {duration_s}s...")
        time.sleep(duration_s)

    def return_to_launch(self):
        """Switch to RTL mode."""
        print("[Drone] Returning to launch...")
        self.vehicle.mode = VehicleMode("RTL")

    def land(self):
        """Land at current position."""
        print("[Drone] Landing...")
        self.vehicle.mode = VehicleMode("LAND")

    def _distance_m(self, lat1, lon1, lat2, lon2):
        """Calculate distance in meters between two GPS coordinates."""
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = (math.sin(dphi/2)**2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(dlam/2)**2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    def offset_to_gps(self, origin_lat, origin_lon, north_m, east_m):
        """Convert meter offset from origin GPS to new GPS coordinate."""
        R = 6371000
        new_lat = origin_lat + (north_m / R) * (180 / math.pi)
        new_lon = origin_lon + (east_m / R) * (180 / math.pi) / math.cos(
                                 math.radians(origin_lat))
        return new_lat, new_lon

    def is_safe_to_approach(self, target_lat, target_lon):
        """Check if target is within safe distance from home."""
        if not self.home_location:
            return True
        dist = self._distance_m(
            self.home_location.lat, self.home_location.lon,
            target_lat, target_lon
        )
        return dist <= MAX_DISTANCE

    # ══════════════════════════════════════════════════════════
    #  Safety Monitor
    # ══════════════════════════════════════════════════════════

    def start_safety_monitor(self):
        """Start background safety monitoring thread."""
        if self._safety_thread and self._safety_thread.is_alive():
            return
        self._safety_running = True
        self._safety_thread = threading.Thread(target=self._safety_loop, daemon=True)
        self._safety_thread.start()
        print("[Safety] Monitor started")

    def stop_safety_monitor(self):
        """Stop safety monitoring thread."""
        self._safety_running = False
        if self._safety_thread:
            self._safety_thread.join(timeout=2)
        print("[Safety] Monitor stopped")

    def _safety_loop(self):
        """Background safety check loop."""
        while self._safety_running and self.connected:
            try:
                # Check battery
                if self.vehicle.battery and self.vehicle.battery.level:
                    if self.vehicle.battery.level < MIN_BATTERY:
                        print(f"[SAFETY] Battery low ({self.vehicle.battery.level}%)! RTL!")
                        self.vehicle.mode = VehicleMode("RTL")

                # Check altitude
                alt = self.vehicle.location.global_relative_frame.alt
                if alt > MAX_ALTITUDE:
                    print(f"[SAFETY] Altitude too high ({alt:.1f}m)! RTL!")
                    self.vehicle.mode = VehicleMode("RTL")

            except Exception as e:
                print(f"[Safety] Check error: {e}")

            time.sleep(1)


# ══════════════════════════════════════════════════════════════
#  Helper Functions
# ══════════════════════════════════════════════════════════════

def cells_to_waypoints(cells, origin_lat, origin_lon,
                        cell_w=CELL_WIDTH_M, cell_h=CELL_HEIGHT_M):
    """
    Convert grid cell (row, col) list to GPS waypoints.
    Wall is assumed NORTH of drone. Column → East, Row → Altitude.
    """
    controller = DroneController()
    waypoints = []

    for row, col in cells:
        # Column → East offset
        east_m = col * cell_w

        # Row → Altitude (row 0 = top = highest)
        alt = PAINTING_ALTITUDE + ((GRID_ROWS - 1 - row) * cell_h)

        # Convert to GPS
        lat, lon = controller.offset_to_gps(
            origin_lat, origin_lon, 0, east_m
        )

        waypoints.append({
            "row": row, "col": col,
            "lat": lat, "lon": lon,
            "alt": alt
        })

    return waypoints


def group_cells_by_row(cells):
    """
    Group cells by row for continuous painting.
    Returns dict: {row_number: [col1, col2, ...]} sorted.
    """
    rows = {}
    for row, col in cells:
        if row not in rows:
            rows[row] = []
        rows[row].append(col)
    # Sort columns within each row
    for r in rows:
        rows[r].sort()
    return dict(sorted(rows.items()))


# ══════════════════════════════════════════════════════════════
#  Singleton Instance
# ══════════════════════════════════════════════════════════════

drone = DroneController()
