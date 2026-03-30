"""
Indoor Hover Test (1 meter altitude)
VIT Chennai MDP — Drone #3

⚠️ SAFETY: This test REQUIRES propellers and will fly the drone!
   - Clear 4m x 4m area
   - Safety pilot with RC in STABILIZE
   - All people at safe distance

Run: python test_hover.py
"""
import collections
import collections.abc
for attr in ("MutableMapping", "MutableSequence", "MutableSet",
             "Mapping", "Sequence", "Set", "Iterable", "Iterator",
             "Callable", "Hashable", "Sized"):
    if not hasattr(collections, attr):
        setattr(collections, attr, getattr(collections.abc, attr))

from dronekit import connect, VehicleMode
import time
import sys

# ════════════════════════════════════════════════════════
#  INDOOR LAB SAFETY CONFIGURATION
# ════════════════════════════════════════════════════════
TARGET_ALTITUDE = 1.0   # meters — INDOOR LAB HEIGHT
MAX_ALTITUDE = 1.5      # meters — absolute ceiling
HOVER_TIME = 10         # seconds
CONNECTION = 'COM3'
BAUD = 115200

print("="*60)
print("🚁 INDOOR HOVER TEST — 1 METER ALTITUDE")
print("="*60)
print(f"  Target altitude: {TARGET_ALTITUDE}m")
print(f"  Max altitude:    {MAX_ALTITUDE}m (ceiling limit)")
print(f"  Hover duration:  {HOVER_TIME}s")
print(f"  Connection:      {CONNECTION}")
print("="*60)

print("\n⚠️  SAFETY CHECKLIST:")
print("  ├─ [ ] Propellers installed correctly (CW/CCW)")
print("  ├─ [ ] Area cleared (4m x 4m minimum)")
print("  ├─ [ ] Safety pilot holding RC in STABILIZE mode")
print("  ├─ [ ] All people warned and at safe distance")
print("  └─ [ ] Battery charged >80%")

print("\n⚠️  EMERGENCY PROCEDURES:")
print("  1. Safety pilot: Flip to STABILIZE immediately")
print("  2. Lower throttle to descend")
print("  3. DO NOT try to catch the drone!")

confirm = input("\nType 'FLY' to proceed: ")
if confirm != 'FLY':
    print("Aborted.")
    sys.exit(0)

print(f"\n🔌 Connecting to {CONNECTION}...")
try:
    vehicle = connect(CONNECTION, baud=BAUD, wait_ready=True, timeout=30)
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

print(f"\n📊 Pre-flight Status:")
print(f"  GPS Fix:    {vehicle.gps_0.fix_type} (need >= 3)")
print(f"  Satellites: {vehicle.gps_0.satellites_visible}")
print(f"  Battery:    {vehicle.battery.level}%")
print(f"  Voltage:    {vehicle.battery.voltage}V")
print(f"  Is Armable: {vehicle.is_armable}")
print(f"  Mode:       {vehicle.mode.name}")

# Safety checks
if vehicle.gps_0.fix_type < 3:
    print("\n⚠️  WARNING: No GPS fix!")
    print("   Indoor testing without GPS requires:")
    print("   - ARMING_CHECK = 0 in Mission Planner")
    print("   - Or optical flow / mocap system")
    cont = input("   Continue anyway? (yes/no): ")
    if cont.lower() != 'yes':
        vehicle.close()
        sys.exit(0)

if not vehicle.is_armable:
    print("\n❌ Vehicle NOT armable!")
    print("   Check pre-arm conditions in Mission Planner")
    vehicle.close()
    sys.exit(1)

if vehicle.battery.level and vehicle.battery.level < 20:
    print(f"\n❌ Battery too low ({vehicle.battery.level}%)!")
    print("   Charge battery before flight")
    vehicle.close()
    sys.exit(1)

print("\n📡 Switching to GUIDED mode...")
vehicle.mode = VehicleMode("GUIDED")
time.sleep(2)

if vehicle.mode.name != "GUIDED":
    print(f"❌ Failed to switch to GUIDED (current: {vehicle.mode.name})")
    vehicle.close()
    sys.exit(1)

print(f"   Mode: {vehicle.mode.name} ✓")

print("\n🔓 ARMING...")
vehicle.armed = True

timeout = 10
while not vehicle.armed and timeout > 0:
    print(f"   Waiting for arm... ({timeout}s)")
    time.sleep(1)
    timeout -= 1

if not vehicle.armed:
    print("❌ Failed to arm!")
    vehicle.close()
    sys.exit(1)

print("✅ ARMED!")

print(f"\n🚀 TAKING OFF to {TARGET_ALTITUDE}m...")
vehicle.simple_takeoff(TARGET_ALTITUDE)

# Monitor altitude during ascent
while True:
    alt = vehicle.location.global_relative_frame.alt
    print(f"   Altitude: {alt:.2f}m / {TARGET_ALTITUDE}m")
    
    if alt >= TARGET_ALTITUDE * 0.95:
        print(f"\n✅ REACHED {TARGET_ALTITUDE}m!")
        break
    
    # Safety ceiling check
    if alt > MAX_ALTITUDE:
        print(f"\n⚠️  CEILING BREACH ({alt:.2f}m > {MAX_ALTITUDE}m)!")
        print("   Emergency landing...")
        vehicle.mode = VehicleMode("LAND")
        break
    
    time.sleep(1)

# Hover
if vehicle.mode.name == "GUIDED":
    print(f"\n⏱️  HOVERING for {HOVER_TIME} seconds...")
    print("   Safety pilot: Be ready to take over!\n")
    
    for i in range(HOVER_TIME, 0, -1):
        alt = vehicle.location.global_relative_frame.alt
        bat = vehicle.battery.level if vehicle.battery.level else "N/A"
        print(f"   [{i:2d}s] Alt: {alt:.2f}m | Batt: {bat}%")
        time.sleep(1)

# Land
print("\n🛬 LANDING...")
vehicle.mode = VehicleMode("LAND")

# Monitor descent
while vehicle.armed:
    alt = vehicle.location.global_relative_frame.alt
    print(f"   Descending... Alt: {alt:.2f}m")
    if alt < 0.1:
        break
    time.sleep(1)

# Wait for disarm
time.sleep(3)

print("\n✅ LANDED!")

if vehicle.armed:
    print("⚠️  Still armed — disarming...")
    vehicle.armed = False
    time.sleep(2)

vehicle.close()

print("\n" + "="*60)
print("🎉 HOVER TEST COMPLETE!")
print("="*60)
print("\nNext steps:")
print("  1. Check drone for any issues")
print("  2. Note any drift or instability")
print("  3. Proceed to Checkpoint 6 if successful")
