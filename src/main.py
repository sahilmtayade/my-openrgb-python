#
# file: main.py (Updated)
#
import time
from enum import Enum, auto

from openrgb import OpenRGBClient
from openrgb.utils import DeviceType, RGBColor

from .gradients import (
    flame_gradient,
    ocean_bands_gradient,
    ocean_shimmer_gradient,
    tropical_waters_gradient,
)

# Import the framework and your custom effect classes
from .stage_manager import StageManager
from .utils.effects import (
    Chase,
    Effect,
    FadeIn,
    FadeToBlack,
    FlickerRamp,  # Using the staged version as it seems to be what you're using
    LiquidFill,
    StaticBrightness,
)
from .utils.effects.color_source import (
    Gradient,
    MultiGradient,
    ScrollingColorSource,
    ScrollingPauseColorSource,
    StaticColor,
)
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

# --- Color palettes in HSV (Hue 0-1, Saturation 0-1, Value 0-1) --- # <-- CHANGED
STRIMMER_HSV = (18 / 360, 1.0, 1.0)  # Fiery orange at full brightness # <-- CHANGED
RAM_FAN_START_HSV = (
    0.0,
    0.0,
    1.0,
)  # White (Hue and Sat don't matter, Value is 1) # <-- CHANGED
RAM_FAN_END_HSV = (18 / 360, 1.0, 1.0)  # Fiery orange at full brightness # <-- CHANGED
# --- NEW: Define colors for the idle RAM state ---
RAM_IDLE_START_HSV = (0.5, 1.0, 1.0)  # Vibrant Cyan
RAM_IDLE_END_HSV = (0.33, 1.0, 1.0)  # Vibrant Green

FPS = 60
FRAME_TIME = 1.0 / FPS
STANDALONE_DEVICES = [DeviceType.DRAM]
RAM_OFFSET = 0.3


def run():
    """Main function to run the lighting controller."""
    client = OpenRGBClient()

    # --- Device Setup ---
    try:
        motherboard_zones = configure_motherboard_zones(client, ZONE_CONFIGS)
        standalone_devices = configure_standalone_devices(client, STANDALONE_DEVICES)
        strimmer = motherboard_zones.get("strimmer")
        fans = motherboard_zones.get("fans")
        dram_sticks = [dev for dev in standalone_devices if dev.type == DeviceType.DRAM]

        if not strimmer or not fans or not dram_sticks:
            print("FATAL: One or more essential devices not found. Exiting.")
            return

        all_managed_devices = list(motherboard_zones.values()) + standalone_devices
        manager = StageManager(all_managed_devices)
    except Exception as e:
        print(f"FATAL: Could not initialize hardware: {e}")
        return

    current_state = AppState.STATE_1_LIQUID
    blocking_effects: list[Effect] = []

    # --- Define Color Sources using the new HSV format ---
    strimmer_source = StaticColor(hsv=STRIMMER_HSV)  # <-- NOW USES (H,S,V)
    ram_gradient = Gradient(
        start_hsv=RAM_FAN_START_HSV,
        end_hsv=RAM_FAN_END_HSV,
        start_pos=0.0,
        end_pos=0.4,
    )  # <-- NOW USES (H,S,V)

    # This gradient now defines its own dark and light parts using the 'V' channel.

    fan_scrolling_color = ScrollingColorSource(
        source=flame_gradient,
        speed=5.0,
    )
    # --- NEW: Create the idle RAM gradient source ---
    ram_idle_gradient = tropical_waters_gradient

    ram_idle_scrolling_color_1 = ScrollingPauseColorSource(
        source=ram_idle_gradient, pause=20, scroll_fraction=1.6, speed=10.0
    )
    ram_idle_scrolling_color_2 = ScrollingPauseColorSource(
        source=ram_idle_gradient,
        speed=10.0,
        pause=20,
        scroll_fraction=1.6,
        delay=RAM_OFFSET,
        initial_roll_ratio=RAM_OFFSET,
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
            manager.update()

            is_state_finished = all(effect.is_finished() for effect in blocking_effects)

            if is_state_finished:
                if current_state == AppState.STATE_1_LIQUID:
                    current_state = AppState.STATE_2_MAIN_SHOW
                    print(f"[{current_state.name}] Starting...")
                    blocking_effects.clear()
                    manager.clear_effects(strimmer)
                    # Use StaticBrightness to show the scrolling flame at its full, self-defined brightness
                    manager.add_effect(
                        StaticBrightness(
                            strimmer, color_source=fan_scrolling_color, brightness=1.0
                        ),
                        strimmer,
                    )
                    chase1 = Chase(
                        dram_sticks[0],
                        color_source=ram_gradient,
                        speed=20,
                        delay=0.0,
                        width=3,
                        duration=5,
                        loop_interval=1,
                        reverse=True,
                    )
                    chase2 = Chase(
                        dram_sticks[1],
                        color_source=ram_gradient,
                        speed=20,
                        delay=RAM_OFFSET,
                        width=3,
                        duration=5,
                        loop_interval=1,
                        reverse=True,
                    )
                    # NOTE: Cleaned up the FlickerRamp/StaticBrightness overwrite.
                    # Using StagedFlickerRamp as it seems to be the intended effect.
                    # flicker = StagedFlickerRamp(
                    #     fans,
                    #     color_source=fan_scrolling_color,
                    #     total_duration=5,
                    #     comet_width=3,
                    # )
                    manager.add_effect(chase1, dram_sticks[0])
                    manager.add_effect(chase2, dram_sticks[1])
                    manager.add_effect(
                        StaticBrightness(
                            fans, color_source=fan_scrolling_color, brightness=1.0
                        ),
                        fans,
                    )
                    blocking_effects = [chase1, chase2]

                elif current_state == AppState.STATE_2_MAIN_SHOW:
                    current_state = AppState.STATE_3_FADE_OUT
                    print(f"[{current_state.name}] Starting...")
                    blocking_effects.clear()
                    manager.clear_all_effects()

                    FADE_OUT_DURATION = 3.0
                    fade_strimmer = FadeToBlack(
                        strimmer,
                        color_source=fan_scrolling_color,
                        duration=FADE_OUT_DURATION,
                    )
                    fade_fans = FadeToBlack(
                        fans,
                        color_source=fan_scrolling_color,
                        duration=FADE_OUT_DURATION,
                    )
                    # The FadeIn effect now reveals the gradient's own brightness,
                    # rather than fading from black to a fully bright version of the gradient.
                    fade_dram1 = FadeIn(
                        dram_sticks[0],
                        color_source=ram_idle_scrolling_color_1,
                        duration=FADE_OUT_DURATION,
                    )
                    fade_dram2 = FadeIn(
                        dram_sticks[1],
                        color_source=ram_idle_scrolling_color_2,
                        duration=FADE_OUT_DURATION,
                    )
                    manager.add_effect(fade_strimmer, strimmer)
                    manager.add_effect(fade_fans, fans)
                    manager.add_effect(fade_dram1, dram_sticks[0])
                    manager.add_effect(fade_dram2, dram_sticks[1])
                    blocking_effects = [
                        fade_strimmer,
                        fade_fans,
                        fade_dram1,
                        fade_dram2,
                    ]

                elif current_state == AppState.STATE_3_FADE_OUT:
                    current_state = AppState.STATE_4_IDLE
                    print(
                        f"[{current_state.name}] Startup complete. Running idle effects."
                    )
                    blocking_effects.clear()
                    manager.clear_all_effects()
                    # --- NEW: Set up the infinite idle effects for the RAM ---
                    idle_ram1 = StaticBrightness(
                        dram_sticks[0],
                        color_source=ram_idle_scrolling_color_1,
                        brightness=1.0,  # duration=None is default for infinite
                    )
                    idle_ram2 = StaticBrightness(
                        dram_sticks[1],
                        color_source=ram_idle_scrolling_color_2,
                        brightness=1.0,  # duration=None is default for infinite
                    )
                    manager.add_effect(idle_ram1, dram_sticks[0])
                    manager.add_effect(idle_ram2, dram_sticks[1])

                    blocking_effects.extend([idle_ram1, idle_ram2])

            elapsed = time.monotonic() - loop_start_time
            if (sleep_time := FRAME_TIME - elapsed) > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nInterrupted by user. Shutting down.")
    finally:
        print("Clearing all devices to black.")
        for device in all_managed_devices:
            device.clear()
            device.show()


if __name__ == "__main__":
    run()
