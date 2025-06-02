import openrgb
import time

def main():
    # Initialize OpenRGB client
    client = openrgb.OpenRGB()
    
    # Connect to the OpenRGB server
    if not client.connect():
        print("Failed to connect to OpenRGB server.")
        return

    # Detect connected devices
    devices = client.devices
    if not devices:
        print("No RGB devices detected.")
        return

    print(f"Detected {len(devices)} devices.")
    for device in devices:
        print(f"Device: {device.name}, Type: {device.type}, Zones: {len(device.zones)}")
    # Print details of each device and its zones
    for device in devices:
        for zone in device.zones:
            print(f"Device {device}  Zone: {zone.name}, LEDs: {zone.leds_count}")
    # Apply configurations to devices/zones by name
    for device in devices:
        for zone in device.zones:
            if zone.name == "D_LED1_Bottom":
                zone.leds_count = 27  # Ensure correct LED count
                zone.set_color((255, 0, 0))  # Red for PSU cables
                zone.set_effect("static")
                print(f"Set {device.name} {zone.name} to red (27 LEDs) with static effect.")
            elif zone.name == "D_LED2_Top":
                zone.leds_count = 24  # Ensure correct LED count
                zone.set_color((0, 255, 0))  # Green for fans
                zone.set_effect("static")
                print(f"Set {device.name} {zone.name} to green (24 LEDs) with static effect.")

    # Keep the script running to maintain the effects
    try:    
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")

if __name__ == "__main__":
    main()