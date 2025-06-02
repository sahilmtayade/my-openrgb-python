from openrgb.orgb import Device

from utils.debug_utils import debug_print


def resize_argb_zones(motherboard: Device, zone_configs):
    for zone_cfg in zone_configs:
        idx = zone_cfg.index
        name = zone_cfg.name
        led_count = zone_cfg.led_count
        motherboard.zones[idx].resize(led_count)
        debug_print(
            f"Zone: {name}, LEDs: {len(motherboard.zones[idx].leds)} (expected {led_count})"
        )
