"""
Test Pixhawk 2.4.8 USB Connection
VIT Chennai MDP — Drone #3

Run: python test_connection.py
"""
import collections
import collections.abc
for attr in ("MutableMapping", "MutableSequence", "MutableSet",
             "Mapping", "Sequence", "Set", "Iterable", "Iterator",
             "Callable", "Hashable", "Sized"):
    if not hasattr(collections, attr):
        setattr(collections, attr, getattr(collections.abc, attr))

from dronekit import connect
import sys

# ════════════════════════════════════════════════════════
#  CONFIGURATION — Update these for your setup
# ════════════════════════════════════════════════════════
CONNECTION = 'COM3'  # Check Device Manager for actual port
BAUD = 115200        # USB baud rate (use 57600 for TELEM)

print("="*60)
print("🔌 PIXHAWK 2.4.8 CONNECTION TEST")
print("="*60)
print(f"Connection: {CONNECTION}")
print(f"Baud rate:  {BAUD}")
print("="*60)

print(f"\nConnecting to Pixhawk 2.4.8...")
try:
    vehicle = connect(CONNECTION, baud=BAUD, wait_ready=True, timeout=30)
    
    print("\n" + "="*60)
    print("✅ CONNECTION SUCCESSFUL!")
    print("="*60)
    print(f"Firmware:    {vehicle.version}")
    print(f"Vehicle:     {vehicle.vehicle_type}")
    print(f"Mode:        {vehicle.mode.name}")
    print(f"Armed:       {vehicle.armed}")
    print(f"GPS Fix:     {vehicle.gps_0.fix_type}")
    print(f"GPS Sats:    {vehicle.gps_0.satellites_visible}")
    print(f"Battery:     {vehicle.battery.level}%" if vehicle.battery.level else "N/A")
    print(f"Voltage:     {vehicle.battery.voltage}V" if vehicle.battery.voltage else "N/A")
    print(f"Is Armable:  {vehicle.is_armable}")
    print("="*60)
    
    vehicle.close()
    print("\n✅ Connection closed cleanly.")
    
except Exception as e:
    print(f"\n❌ CONNECTION FAILED: {e}")
    print("\n🔧 Troubleshooting:")
    print("1. Check COM port in Device Manager")
    print("2. Ensure Pixhawk is powered (via battery or USB)")
    print("3. Try different USB cable")
    print("4. Verify BAUD rate (115200 for USB, 57600 for TELEM)")
    print("5. Close Mission Planner if it's connected")
    sys.exit(1)
