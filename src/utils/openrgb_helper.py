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
        print(f"✓ Motherboard '{motherboard.name}' configured.")
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
            print(f"✓ {len(devices)} device(s) of type '{dev_type.name}' configured.")
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
