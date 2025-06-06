from dotenv import load_dotenv
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor, DeviceType
import time
from dataclasses import dataclass

from utils.openrgb_helper import resize_argb_zones
from utils.debug_utils import debug_print

load_dotenv()


@dataclass
class ZoneConfig:
    index: int
    role: str
    name: str
    led_count: int


ZONE_CONFIGS = [
    ZoneConfig(index=0, role="strimmer", name="D_LED1 Bottom", led_count=27),
    ZoneConfig(index=1, role="fan", name="D_LED2 Top", led_count=24),
]


def main():
    client = OpenRGBClient()  # Connects to localhost:6742 by default

    # Get all motherboards
    motherboards = client.get_devices_by_type(DeviceType.MOTHERBOARD)
    if not motherboards:
        print("No motherboard device found.")
        return

    motherboard = motherboards[0]
    motherboard.set_mode("direct")
    debug_print(f"Found motherboard: {motherboard.name}")

    # Pass ZONE_CONFIGS directly to resize_argb_zones
    resize_argb_zones(motherboard, ZONE_CONFIGS)

    # Print all zones and their LED counts
    for zone_cfg in ZONE_CONFIGS:
        zone = motherboard.zones[zone_cfg.index]
        debug_print(
            f"Zone {zone_cfg.index} ({zone_cfg.role}): {zone.name}, LEDs: {len(zone.leds)} (expected {zone_cfg.led_count})"
        )

    # Use zones directly by index or role
    strimmer_zone = motherboard.zones[ZONE_CONFIGS[0].index]
    fan_zone = motherboard.zones[ZONE_CONFIGS[1].index]

    # Set strimmer_zone to pastel red (e.g., RGB 255, 128, 128)
    pastel_red = RGBColor(255, 128, 128)
    strimmer_zone.set_color(pastel_red)

    # Set fan_zone to a pastel gradient (e.g., pastel rainbow)
    pastel_gradient = [
        RGBColor(255, 105, 180),  # stronger pink
        RGBColor(255, 165, 80),  # orange-ish
        RGBColor(255, 255, 80),  # warm yellow
        RGBColor(80, 255, 120),  # mint green
        RGBColor(80, 180, 255),  # sky blue
        RGBColor(180, 80, 255),  # purple
    ]

    # Repeat or interpolate the gradient to match the number of LEDs
    fan_led_count = len(fan_zone.leds)
    gradient_colors = [
        pastel_gradient[i % len(pastel_gradient)] for i in range(fan_led_count)
    ]
    fan_zone.set_colors(gradient_colors)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")


if __name__ == "__main__":
    main()
