"""
Test Arming (PROPELLERS MUST BE REMOVED!)
VIT Chennai MDP — Drone #3

⚠️ SAFETY: Only run this with propellers OFF!

Run: python test_arm.py
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
#  CONFIGURATION
# ════════════════════════════════════════════════════════
CONNECTION = 'COM9'
BAUD = 115200

print("="*60)
print("🔓 PIXHAWK 2.4.8 ARM TEST")
print("="*60)
print("\n⚠️  WARNING: PROPELLERS MUST BE REMOVED!")
print("    This test will attempt to arm the motors.\n")

confirm = input("Type 'CONFIRM' to proceed (props are OFF): ")
if confirm != 'CONFIRM':
    print("Aborted.")
    sys.exit(0)

print(f"\nConnecting to {CONNECTION}...")
try:
    vehicle = connect(CONNECTION, baud=BAUD, wait_ready=True, timeout=30)
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

print(f"\nCurrent State:")
print(f"  Mode:       {vehicle.mode.name}")
print(f"  Armed:      {vehicle.armed}")
print(f"  Is Armable: {vehicle.is_armable}")
print(f"  GPS Fix:    {vehicle.gps_0.fix_type}")
print(f"  Battery:    {vehicle.battery.level}%")

if not vehicle.is_armable:
    print("\n❌ Vehicle NOT armable!")
    print("   Possible issues:")
    print("   - No GPS fix (normal indoors)")
    print("   - Pre-arm checks failing")
    print("   - RC transmitter not connected")
    print("\n💡 For indoor testing without GPS:")
    print("   Set ARMING_CHECK=0 in Mission Planner")
    vehicle.close()
    sys.exit(1)

print("\n📡 Switching to GUIDED mode...")
vehicle.mode = VehicleMode("GUIDED")
time.sleep(2)
print(f"   Mode: {vehicle.mode.name}")

print("\n🔓 Attempting to ARM...")
vehicle.armed = True

timeout = 10
while not vehicle.armed and timeout > 0:
    print(f"   Waiting for arm... ({timeout}s)")
    time.sleep(1)
    timeout -= 1

if vehicle.armed:
    print("\n" + "="*60)
    print("✅ ARMED SUCCESSFULLY!")
    print("="*60)
    print("   Motors would spin now (but props are OFF)")
    
    print("\n⏱️  Holding for 3 seconds...")
    time.sleep(3)
    
    print("\n🔒 DISARMING...")
    vehicle.armed = False
    time.sleep(2)
    
    if not vehicle.armed:
        print("✅ Disarmed successfully!")
    else:
        print("⚠️  Still armed — use RC to disarm!")
else:
    print("\n" + "="*60)
    print("❌ FAILED TO ARM")
    print("="*60)
    print("   Check pre-arm conditions in Mission Planner")

vehicle.close()
print("\n✅ Test complete.")
