def detect_devices(client):
    devices = client.devices
    return devices

def configure_led_zone(device, zone_index, color, effect):
    if zone_index < len(device.leds):
        led_zone = device.leds[zone_index]
        led_zone.set_color(color)
        led_zone.set_effect(effect)
        return True
    return False

def apply_lighting_effects(client, device_configs):
    for device_name, config in device_configs.items():
        device = next((d for d in client.devices if d.name == device_name), None)
        if device:
            for zone_index, zone_config in enumerate(config['zones']):
                color = zone_config['color']
                effect = zone_config['effect']
                configure_led_zone(device, zone_index, color, effect)