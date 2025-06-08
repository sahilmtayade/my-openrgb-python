import time
from dataclasses import dataclass

from openrgb import OpenRGBClient
from openrgb.orgb import Device, Zone
from openrgb.utils import DeviceType

from .debug_utils import debug_print


def resize_argb_zones(motherboard: Device, zone_configs):
    for zone_cfg in zone_configs:
        idx = zone_cfg.index
        name = zone_cfg.name
        led_count = zone_cfg.led_count
        motherboard.zones[idx].resize(led_count)
        debug_print(
            f"Zone: {name}, LEDs: {len(motherboard.zones[idx].leds)} (expected {led_count})"
        )


@dataclass
class ZoneConfig:
    index: int
    role: str
    name: str
    led_count: int


def configure_motherboard_zones(
    client: OpenRGBClient, zone_configs: list[ZoneConfig]
) -> dict[str, Zone]:
    """
    Finds the motherboard, configures its ARGB zones, and returns them in a dictionary.

    Returns: A dictionary mapping the 'role' from each ZoneConfig to its zone object.
             Returns an empty dictionary if the motherboard is not found.
    """
    print("--- Configuring Motherboard ARGB Zones ---")
    try:
        motherboard = client.get_devices_by_type(DeviceType.MOTHERBOARD)[0]
        motherboard.set_mode("direct")
        resize_argb_zones(motherboard, zone_configs)
        print(f"Motherboard '{motherboard.name}' configured.")
        # Use a dictionary comprehension for a concise return.
        return {zc.role: motherboard.zones[zc.index] for zc in zone_configs}
    except Exception as e:
        print(f"! ERROR: Could not configure motherboard zones: {e}")
        return {}


def configure_standalone_devices(
    client: OpenRGBClient, device_types: list[DeviceType]
) -> list[Device]:
    """
    Finds all devices of the given types and sets their mode to 'direct'.

    Returns: A flat list of all found and configured device objects.
    """
    print("--- Configuring Standalone Devices ---")
    configured_devices = []
    for dev_type in device_types:
        try:
            devices = client.get_devices_by_type(dev_type)
            if not devices:
                continue  # Silently skip if no devices of this type are found

            for dev in devices:
                dev.set_mode("direct")
            configured_devices.extend(devices)
            print(f"{len(devices)} device(s) of type '{dev_type.name}' configured.")
        except Exception as e:
            print(f"! ERROR: Could not configure device type '{dev_type.name}': {e}")

    return configured_devices


def get_motherboard_and_dram_devices(client: OpenRGBClient) -> list[Device]:
    """
    Returns all devices of type MOTHERBOARD and DRAM.
    """
    devices = []
    try:
        devices.extend(client.get_devices_by_type(DeviceType.MOTHERBOARD))
    except Exception as e:
        print(f"! ERROR: Could not get MOTHERBOARD devices: {e}")
    try:
        devices.extend(client.get_devices_by_type(DeviceType.DRAM))
    except Exception as e:
        print(f"! ERROR: Could not get DRAM devices: {e}")
    return devices


if __name__ == "__main__":
    # Test
    client = OpenRGBClient()
    devices = get_motherboard_and_dram_devices(client)
    print(f"Found {len(devices)} MOTHERBOARD/DRAM devices:")
    for dev in devices:
        print(f"- {dev.name} ({dev.type.name})")


# ... (all your other imports) ...

# --- Configuration Constants (Can be in a separate file) ---
# ... (all your configs like FPS, ZONE_CONFIGS, etc.) ...
SERVER_POLL_TIMEOUT = 15  # Max seconds to wait for the server to start
SERVER_POLL_INTERVAL = 0.2  # Seconds between connection attempts


# --- NEW: Connection Polling Function ---
def connect_with_retry(
    timeout: float = SERVER_POLL_TIMEOUT, interval: float = SERVER_POLL_INTERVAL
) -> OpenRGBClient:
    """
    Attempts to connect to the OpenRGB server, retrying until the timeout.

    Args:
        timeout: The maximum number of seconds to keep trying.
        interval: The time in seconds to wait between connection attempts.

    Returns:
        An initialized and connected OpenRGBClient instance.

    Raises:
        TimeoutError: If a connection cannot be established within the timeout.
    """
    start_time = time.monotonic()
    print("Attempting to connect to OpenRGB server...")
    while time.monotonic() - start_time < timeout:
        try:
            client = OpenRGBClient()
            # If the above line doesn't raise an exception, we are connected.
            print("Successfully connected to OpenRGB server.")
            # Step 2: Check if devices have been detected
            devices = client.devices
            if devices:
                print(f"  - Success! Detected {len(devices)} devices.")
                return client
            else:
                # Connected, but no devices yet. Server is still initializing.
                print("  - Connected, but no devices found yet. Waiting...")
        except Exception:
            # Server is not ready yet, wait for the interval and try again.
            time.sleep(interval)

    # If the loop finishes without returning, we have timed out.
    raise TimeoutError(f"Could not connect to OpenRGB server within {timeout} seconds.")
