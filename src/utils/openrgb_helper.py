import time
import traceback
from dataclasses import dataclass

from openrgb import OpenRGBClient
from openrgb.orgb import Device, Zone
from openrgb.utils import DeviceType

from src.stage_manager import StageManager

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
        print(
            f"! ERROR: Could not configure motherboard zones: {e} {traceback.format_exc()}"
        )
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
            print(
                f"! ERROR: Could not configure device type '{dev_type.name}': {e} {traceback.format_exc()}"
            )

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
    num_devices: int,
    num_zones: int,
    timeout: float = SERVER_POLL_TIMEOUT,
    interval: float = SERVER_POLL_INTERVAL,
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
                if len(devices) >= num_devices:
                    motherboard = client.get_devices_by_type(DeviceType.MOTHERBOARD)[0]
                    if len(motherboard.zones) >= num_zones:
                        print(
                            f"  - Success! Detected {len(devices)} devices with {len(motherboard.zones)} zones."
                        )
                        return client
                    else:
                        print(
                            f"  - Connected, but found {len(motherboard.zones)} zones (expected at least {num_zones})."
                        )
                else:
                    print(
                        f"  - Connected, but found {len(devices)} devices (expected {num_devices}). {devices=}"
                    )
            else:
                # Connected, but no devices yet. Server is still initializing.
                print("  - Connected, but no devices found yet. Waiting...")
        except Exception:
            # Server is not ready yet, wait for the interval and try again.
            print("waiting for OpenRGB server to start...")
            time.sleep(interval)

    # If the loop finishes without returning, we have timed out.
    raise TimeoutError(f"Could not connect to OpenRGB server within {timeout} seconds.")


def setup_hardware_with_retry(
    client: OpenRGBClient,
    timeout: float,
    interval: float,
    zone_configs: list[ZoneConfig],
    device_types: list[DeviceType],
) -> tuple[StageManager, dict[str, Device], list[Device], list[Device]]:
    """
    Configures all required hardware, retrying until success or timeout.
    """
    start_time = time.monotonic()
    print("\n--- Starting Hardware Configuration ---")

    while time.monotonic() - start_time < timeout:
        try:
            # 1. Attempt to configure all devices.
            motherboard_zones = configure_motherboard_zones(client, zone_configs)
            standalone_devices = configure_standalone_devices(client, device_types)

            # 2. Verify that all essential devices were found and configured.
            strimmer = motherboard_zones.get("strimmer")
            fans = motherboard_zones.get("fans")
            dram_sticks = [
                dev for dev in standalone_devices if dev.type == DeviceType.DRAM
            ]

            if strimmer and fans and dram_sticks:
                # 3. If everything succeeded, we are done.
                print("--- Hardware Configuration Successful ---")
                all_managed_devices = (
                    list(motherboard_zones.values()) + standalone_devices
                )
                manager = StageManager(all_managed_devices)
                return (
                    manager,
                    motherboard_zones,
                    standalone_devices,
                    all_managed_devices,
                )  # type: ignore
            else:
                # Some devices were missing after configuration. Log and retry.
                print(
                    "! Post-configuration check failed: Not all essential devices were found."
                )

        except Exception as e:
            # Catch any exception during setup, including OpenRGBDisconnected.
            print(f"! HARDWARE SETUP FAILED during attempt: {e}")

        # Wait before the next full attempt.
        print(f"  Will retry in {interval} seconds...")
        time.sleep(interval)

    # If the loop finishes, we have timed out.
    raise TimeoutError(
        f"Could not successfully configure all hardware within {timeout} seconds."
    )
