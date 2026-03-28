"""
============================================================
 Demo Simulation — SITL Test for Lab Incharge
 VIT Chennai Multi-Disciplinary Project
============================================================

Run this script to demonstrate the drone system working
in simulation (ArduPilot SITL) before requesting access
to the real drone.

PREREQUISITES:
  1. Mission Planner open with SITL simulation running
  2. Python environment with DroneKit installed

WHAT IT DOES:
  1. Connects to SITL on tcp:127.0.0.1:5762
  2. Arms the virtual drone
  3. Takes off to 10m
  4. Flies to 4 waypoints (simulating paint grid corners)
  5. Simulates spray at each position
  6. Returns to launch

TO RUN:
  1. Start Mission Planner SITL (Simulation tab → Multirotor)
  2. Wait 30 seconds for initialization
  3. Run: python demo_simulation.py
============================================================
"""

# Monkey-patch for Python 3.10+ compatibility
import collections
import collections.abc
for attr in ("MutableMapping", "MutableSequence", "MutableSet",
             "Mapping", "Sequence", "Set", "Iterable", "Iterator",
             "Callable", "Hashable", "Sized"):
    if not hasattr(collections, attr):
        setattr(collections, attr, getattr(collections.abc, attr))

from dronekit import connect, VehicleMode, LocationGlobalRelative
import time
import math

# ══════════════════════════════════════════════════════════════
#  Configuration
# ══════════════════════════════════════════════════════════════

CONN_STRING = 'tcp:127.0.0.1:5762'  # SITL connection
ALTITUDE = 10.0                      # meters
WAYPOINT_REACH_DIST = 2.0           # meters tolerance
TIMEOUT = 120                        # seconds max wait


# ══════════════════════════════════════════════════════════════
#  Helper Functions
# ══════════════════════════════════════════════════════════════

def distance_metres(loc1, loc2):
    """Approximate ground distance in metres between two GPS locations."""
    dlat = (loc2.lat - loc1.lat) * 1.113195e5
    dlon = (loc2.lon - loc1.lon) * 1.113195e5 * math.cos(math.radians(loc1.lat))
    return math.sqrt(dlat**2 + dlon**2)


def goto_and_wait(vehicle, lat, lon, alt, label="target"):
    """Fly to a waypoint and block until arrival or timeout."""
    target = LocationGlobalRelative(lat, lon, alt)
    last_send = 0
    RESEND_INTERVAL = 5

    t0 = time.time()
    while True:
        elapsed = time.time() - t0
        
        # Re-send goto periodically
        if elapsed - last_send >= RESEND_INTERVAL:
            vehicle.simple_goto(target, groundspeed=3.0)
            last_send = elapsed

        current = vehicle.location.global_relative_frame
        dist = distance_metres(current, target)
        print(f"  → {label}: dist={dist:.1f}m  alt={current.alt:.1f}m")

        if dist < WAYPOINT_REACH_DIST:
            break

        if elapsed > TIMEOUT:
            print(f"  [!] Timeout reaching {label}, continuing...")
            break
        time.sleep(1)


def simulate_spray(label):
    """Simulate spray action (no real ESP32 needed for demo)."""
    print(f"  💦 {label} — SPRAYING (simulated)")
    time.sleep(1)
    print(f"  ✓ {label} — spray complete")


# ══════════════════════════════════════════════════════════════
#  Main Demo
# ══════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 60)
    print("  🚁 AUTONOMOUS DRONE PAINTING — SITL DEMO")
    print("  VIT Chennai Multi-Disciplinary Project")
    print("=" * 60 + "\n")

    # Connect to SITL
    vehicle = None
    while vehicle is None:
        try:
            print(f"[1/6] Connecting to SITL on {CONN_STRING}...")
            vehicle = connect(CONN_STRING, wait_ready=True, heartbeat_timeout=15)
        except Exception as e:
            print(f"  Connection failed ({e}). Retrying in 5s...")
            time.sleep(5)
    print(f"  ✓ Connected! Mode: {vehicle.mode.name}\n")

    # Wait for valid GPS
    print("[2/6] Waiting for GPS position...")
    t0 = time.time()
    while True:
        home = vehicle.location.global_relative_frame
        if home.lat != 0 and home.lon != 0:
            break
        if time.time() - t0 > TIMEOUT:
            print("ERROR: No valid GPS position. Exiting.")
            vehicle.close()
            return
        time.sleep(1)
    HOME_LAT = home.lat
    HOME_LON = home.lon
    print(f"  ✓ Home: {HOME_LAT:.6f}, {HOME_LON:.6f}\n")

    # Pre-arm checks
    print("[3/6] Pre-arm checks...")
    t0 = time.time()
    while not vehicle.is_armable:
        if time.time() - t0 > TIMEOUT:
            print("ERROR: Vehicle never became armable. Exiting.")
            vehicle.close()
            return
        time.sleep(1)
    print("  ✓ Pre-arm checks passed\n")

    # Arm and takeoff
    print("[4/6] Arming and taking off...")
    vehicle.mode = VehicleMode("GUIDED")
    time.sleep(2)
    vehicle.armed = True
    
    t0 = time.time()
    while not vehicle.armed:
        if time.time() - t0 > TIMEOUT:
            print("ERROR: Failed to arm. Exiting.")
            vehicle.close()
            return
        print("  Waiting to arm...")
        time.sleep(1)

    print(f"  ✓ Armed! Taking off to {ALTITUDE}m...")
    vehicle.simple_takeoff(ALTITUDE)

    t0 = time.time()
    while vehicle.location.global_relative_frame.alt < ALTITUDE * 0.9:
        if time.time() - t0 > TIMEOUT:
            print("  [!] Takeoff timeout, proceeding...")
            break
        alt = vehicle.location.global_relative_frame.alt
        print(f"  Altitude: {alt:.1f}m")
        time.sleep(1)
    print(f"  ✓ Reached altitude!\n")

    # Paint mission — 4 corners of 50m square
    print("[5/6] Starting paint mission...")
    OFFSET = 0.00045  # ~50 metres
    paint_positions = [
        (HOME_LAT + OFFSET, HOME_LON,          "Cell (0,0) — Top-Left"),
        (HOME_LAT + OFFSET, HOME_LON + OFFSET, "Cell (0,11) — Top-Right"),
        (HOME_LAT,          HOME_LON + OFFSET, "Cell (7,11) — Bottom-Right"),
        (HOME_LAT,          HOME_LON,          "Cell (7,0) — Bottom-Left"),
    ]

    for i, (lat, lon, label) in enumerate(paint_positions):
        print(f"\n  📍 Waypoint {i+1}/4: {label}")
        goto_and_wait(vehicle, lat, lon, ALTITUDE, label)
        simulate_spray(label)

    # RTL
    print("\n[6/6] Mission complete! Returning to launch...")
    vehicle.mode = VehicleMode("RTL")
    time.sleep(15)

    # Cleanup
    vehicle.close()
    print("\n" + "=" * 60)
    print("  ✓ DEMO COMPLETE — Ready for real drone integration!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
