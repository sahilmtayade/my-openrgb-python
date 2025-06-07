#
# file: main.py
#
import time
from enum import Enum, auto

from openrgb import OpenRGBClient
from openrgb.utils import DeviceType, RGBColor

# Import the framework and your custom effect classes
from .stage_manager import StageManager
from .utils.effects import (
    Chase,
    # Fade,
    LiquidFill,
    # SignFlicker,
    StaticBrightness,
)  # NOTE: You must create these!
from .utils.effects.color_source import Gradient, StaticColor
from .utils.openrgb_helper import (
    ZoneConfig,
    configure_motherboard_zones,
    configure_standalone_devices,
)


# --- Define states for the application's lifecycle ---
class AppState(Enum):
    STATE_1_LIQUID = auto()
    STATE_2_MAIN_SHOW = auto()
    STATE_3_FADE_OUT = auto()
    STATE_4_IDLE = auto()
    EXITING = auto()


# --- Define constant colors and settings ---
ZONE_CONFIGS = [
    ZoneConfig(index=0, role="strimmer", name="D_LED1 Bottom", led_count=27),
    ZoneConfig(index=1, role="fans", name="D_LED2 Top", led_count=24),
]

# Color palettes in HSV (Hue 0-1, Saturation 0-1)
STRIMMER_HSV = (18 / 360, 1.0)  # A vibrant, saturated blue/purple
RAM_FAN_START_HSV = (0.0, 0)  # White
RAM_FAN_END_HSV = (18 / 360, 1.0)  # Fiery orange

FPS = 60
FRAME_TIME = 1.0 / FPS
STANDALONE_DEVICES = [DeviceType.DRAM]


def run():
    """Main function to run the lighting controller."""
    client = OpenRGBClient()

    # --- Device Setup ---
    try:
        # --- 1. Hardware Initialization ---
        motherboard_zones = configure_motherboard_zones(client, ZONE_CONFIGS)
        standalone_devices = configure_standalone_devices(client, STANDALONE_DEVICES)

        # --- 2. Get Specific Devices and Create Master List ---
        strimmer = motherboard_zones.get("strimmer")
        fans = motherboard_zones.get("fans")
        dram_sticks = [dev for dev in standalone_devices if dev.type == DeviceType.DRAM]

        if not strimmer or not fans or not dram_sticks:
            print("FATAL: One or more essential devices not found. Exiting.")
            return

        all_managed_devices = list(motherboard_zones.values()) + standalone_devices

        # --- 3. Framework and State Machine Setup ---
        manager = StageManager(all_managed_devices)
    except Exception as e:
        print(f"FATAL: Could not initialize hardware: {e}")
        return

    current_state = AppState.STATE_1_LIQUID
    blocking_effects = []

    # --- Define Color Sources ---
    strimmer_source = StaticColor(hsv=STRIMMER_HSV)
    ram_fan_gradient = Gradient(
        start_hsv=RAM_FAN_START_HSV, end_hsv=RAM_FAN_END_HSV, weight=0.8
    )

    # --- Kick off the sequence ---
    print(f"[{current_state.name}] Starting...")
    effect = LiquidFill(strimmer, color_source=strimmer_source, speed=5.0)
    manager.add_effect(effect, strimmer)
    blocking_effects.append(effect)

    # --- Main Application Loop ---
    try:
        while current_state != AppState.EXITING:
            loop_start_time = time.monotonic()

            # This single call runs all animations and updates hardware
            manager.update()

            # --- State Transition Logic ---
            is_state_finished = all(effect.is_finished() for effect in blocking_effects)

            if is_state_finished:
                if current_state == AppState.STATE_1_LIQUID:
                    current_state = AppState.STATE_2_MAIN_SHOW
                    print(f"[{current_state.name}] Starting...")
                    blocking_effects.clear()
                    manager.clear_effects(strimmer)
                    manager.add_effect(
                        StaticBrightness(strimmer, color_source=strimmer_source),
                        strimmer,
                    )
                    chase1 = Chase(
                        dram_sticks[0],
                        color_source=ram_fan_gradient,
                        speed=20,
                        delay=0.0,
                        width=3,
                        reverse=True,
                    )
                    chase2 = Chase(
                        dram_sticks[1],
                        color_source=ram_fan_gradient,
                        speed=20,
                        delay=0.3,
                        width=3,
                        reverse=True,
                    )
                    # flicker = SignFlicker(fans)
                    manager.add_effect(chase1, dram_sticks[0])
                    manager.add_effect(chase2, dram_sticks[1])
                    # manager.add_effect(flicker, fans)
                    blocking_effects = [
                        chase1,
                        chase2,
                        # flicker
                    ]

                elif current_state == AppState.STATE_2_MAIN_SHOW:
                    current_state = AppState.STATE_3_FADE_OUT
                    print(f"[{current_state.name}] Starting...")
                    blocking_effects.clear()
                    for dev in all_managed_devices:
                        manager.clear_effects(dev)

                    # fade_strimmer = Fade(strimmer, from_color=LIQUID_COLOR)
                    # fade_fans = Fade(fans, from_color=RAM_CHASE_COLOR_MAP[0])
                    # fade_dram1 = Fade(dram_sticks[0], from_color=RGBColor(255, 200, 0))
                    # fade_dram2 = Fade(dram_sticks[1], from_color=RGBColor(255, 200, 0))
                    # manager.add_effect(fade_strimmer, strimmer)
                    # manager.add_effect(fade_fans, fans)
                    # manager.add_effect(fade_dram1, dram_sticks[0])
                    # manager.add_effect(fade_dram2, dram_sticks[1])
                    # blocking_effects = [
                    #     fade_strimmer,
                    #     fade_fans,
                    #     fade_dram1,
                    #     fade_dram2,
                    # ]

                elif current_state == AppState.STATE_3_FADE_OUT:
                    current_state = AppState.STATE_4_IDLE
                    print(
                        f"[{current_state.name}] Startup complete. Running idle effects."
                    )
                    blocking_effects.clear()
                    for dev in all_managed_devices:
                        manager.clear_effects(dev)

                    # for dev in all_devices:
                    #     manager.add_effect(IdleRainbow(dev, speed=0.1), dev)

            # --- Frame Rate Limiter ---
            elapsed = time.monotonic() - loop_start_time
            if (sleep_time := FRAME_TIME - elapsed) > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nInterrupted by user. Shutting down.")
    finally:
        # --- Cleanup ---
        print("Clearing all devices to black.")
        for device in all_managed_devices:
            device.clear()
            # A final show call may be needed on some devices to apply the clear
            device.show()


if __name__ == "__main__":
    run()
