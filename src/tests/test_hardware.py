# In your main.py, replace the main logic with this test:

# ... (imports and hardware setup)
from ..utils.effects.manual_ramp import ManualBrightnessRamp
from ..utils.effects.color_source import StaticColor

#
# file: src/main.py (Minimal Test Version)
#
import time

# --- Minimal Imports ---
from openrgb import OpenRGBClient
from openrgb.utils import DeviceType

# Framework components needed for this single test
from ..stage_manager import StageManager
from ..utils.effects.color_source import StaticColor
from ..utils.effects import LiquidFill

# Your hardware-specific setup helper
from ..utils.openrgb_helper import resize_argb_zones, ZoneConfig

# ==============================================================================
#  Configuration
# ==============================================================================

# --- Hardware Config (Unchanged) ---
ZONE_CONFIGS = [
    ZoneConfig(index=0, role="strimmer", name="D_LED1 Bottom", led_count=27),
    ZoneConfig(index=1, role="fan", name="D_LED2 Top", led_count=24),
]

# --- Animation Config ---
FPS = 60
FRAME_TIME = 1.0 / FPS

# We only need one color source for this test
LIQUID_FILL_HSV = (0.08, 1.0)  # A vibrant, saturated blue/purple

# ==============================================================================
#  Main Test Logic
# ==============================================================================


def main():
    """Initializes hardware and runs a single LiquidFill effect."""
    client = OpenRGBClient()

    # --- 1. Hardware Initialization ---
    print("Initializing hardware...")
    try:
        motherboard = client.get_devices_by_type(DeviceType.MOTHERBOARD)[0]
        motherboard.set_mode("direct")
        resize_argb_zones(motherboard, ZONE_CONFIGS)
        print(f"Successfully configured motherboard: {motherboard.name}")
    except IndexError:
        print("FATAL: No motherboard device found. Exiting.")
        return
    except Exception as e:
        print(f"FATAL: An error occurred during hardware setup: {e}")
        return

    # We will only apply the effect to the strimmer zone for this test
    strimmer_zone = motherboard.zones[ZONE_CONFIGS[0].index]
    fan_zone = motherboard.zones[ZONE_CONFIGS[1].index]
    # --- 2. Framework Setup ---
    # The manager needs to know about all devices, even if we don't use them all.
    manager = StageManager([strimmer_zone, fan_zone])
    liquid_color_source = StaticColor(hsv=LIQUID_FILL_HSV)

    print("\n--- RUNNING HARDWARE DIAGNOSTIC ---")
    print("Watch the strimmer closely. Does it fade smoothly or in visible steps?")

    white_source = StaticColor(hsv=(0.0, 0.0))  # Use white for pure brightness test

    # Run the test
    test_effect = ManualBrightnessRamp(
        strimmer_zone, color_source=white_source, dither_strength=0.005
    )
    manager.add_effect(test_effect, strimmer_zone)

    try:
        while not test_effect.is_finished():
            manager.update()
            time.sleep(1 / 60)  # Run at 60fps
        print("--- DIAGNOSTIC COMPLETE ---")
        time.sleep(2)
    finally:
        strimmer_zone.clear()
        strimmer_zone.show()


if __name__ == "__main__":
    main()
