#
# file: main.py (Updated)
#
import time
from enum import Enum, auto

from openrgb import OpenRGBClient
from openrgb.utils import DeviceType, RGBColor

from src.gradients import LIQUID_HSV, RAM_CHASE_BOTTOM_HSV, RAM_CHASE_TOP_HSV
from src.utils.effects.breathing import Breathing

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
    ChaseRamp,
    Effect,
    FadeIn,
    FadeToBlack,
    FlickerRamp,  # Using the staged version as it seems to be what you're using
    LiquidFill,
    StaticBrightness,
)
from .utils.effects.color_source import (
    ColorShift,
    Gradient,
    MultiGradient,
    ScrollingColorSource,
    StaticColor,
)
from .utils.openrgb_helper import (
    ZoneConfig,
    configure_motherboard_zones,
    configure_standalone_devices,
    connect_with_retry,
    setup_hardware_with_retry,
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


FPS = 30
FRAME_TIME = 1.0 / FPS
STANDALONE_DEVICES = [DeviceType.DRAM]
RAM_OFFSET = 0.3
IDLE_CHASE_INTERVAL = 15  # Time in seconds between idle chases
IDLE_CHASE_SPEED = 30.0  # Speed of the idle chase effect
IDLE_CHASE_DELAY = 5  # Delay before the idle chase starts
HARDWARE_SETUP_TIMEOUT = 60
HARDWARE_SETUP_INTERVAL = 1.0  # Seconds between hardware setup attempts


def run():
    """Main function to run the lighting controller."""
    try:
        # Part 1: Connect to the Server
        client = connect_with_retry(
            num_devices=3,
            num_zones=2,
        )

        # Part 2: Configure Hardware (with its own timeout)
        manager, motherboard_zones, standalone_devices, all_managed_devices = (
            setup_hardware_with_retry(
                client=client,
                timeout=HARDWARE_SETUP_TIMEOUT,
                interval=HARDWARE_SETUP_INTERVAL,
                zone_configs=ZONE_CONFIGS,
                device_types=STANDALONE_DEVICES,
            )
        )
        strimmer = motherboard_zones.get("strimmer")
        fans = motherboard_zones.get("fans")
        dram_sticks = [dev for dev in standalone_devices if dev.type == DeviceType.DRAM]

        if not strimmer or not fans or not dram_sticks:
            print("FATAL: One or more essential devices not found. Exiting.")
            return

    except TimeoutError as e:
        print(f"FATAL: A startup step timed out: {e}")
        return
    except Exception as e:
        print(f"FATAL: An unexpected error occurred during startup: {e}")
        return

    current_state = AppState.STATE_1_LIQUID
    blocking_effects: list[Effect] = []

    # --- Define Color Sources using the new HSV format ---
    strimmer_source = StaticColor(hsv=LIQUID_HSV)  # <-- NOW USES (H,S,V)
    # ram_gradient = Gradient(
    #     start_hsv=RAM_CHASE_TOP_HSV,
    #     end_hsv=RAM_CHASE_BOTTOM_HSV,
    #     start_pos=0.0,
    #     end_pos=0.4,
    # )  # <-- NOW USES (H,S,V)

    # This gradient now defines its own dark and light parts using the 'V' channel.

    fan_scrolling_color = ColorShift(
        gradient_source=flame_gradient,
        cycle_duration=20.0,
    )
    # --- NEW: Create the idle RAM gradient source ---
    ram_idle_gradient = tropical_waters_gradient

    ram_idle_scrolling_color_1 = ScrollingColorSource(
        source=ram_idle_gradient, pause=20, scroll_fraction=1.6, speed=10.0
    )
    ram_idle_scrolling_color_2 = ScrollingColorSource(
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
    manager.add_effect(effect)
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
                        )
                    )
                    chase1 = Chase(
                        dram_sticks[0],
                        color_source=fan_scrolling_color,
                        speed=20,
                        delay=0.0,
                        width=3,
                        duration=None,
                        loop_interval=1,
                        reverse=True,
                    )
                    chase2 = Chase(
                        dram_sticks[1],
                        color_source=fan_scrolling_color,
                        speed=20,
                        delay=RAM_OFFSET,
                        width=3,
                        duration=None,
                        loop_interval=1,
                        reverse=True,
                    )

                    fan_chase = ChaseRamp(
                        fans,
                        color_source=fan_scrolling_color,
                        initial_speed=5,
                        acceleration=10,
                        max_speed=120,
                        max_width=100,
                        dither_strength=0.14,
                        reverse=True,
                    )
                    manager.add_effect(chase1)
                    manager.add_effect(chase2)
                    manager.add_effect(fan_chase)
                    blocking_effects = [fan_chase]
                    fan_scrolling_color.reset()

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
                    manager.add_effect(fade_strimmer)
                    manager.add_effect(fade_fans)
                    manager.add_effect(fade_dram1)
                    manager.add_effect(fade_dram2)
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
                    manager.add_effect(idle_ram1)
                    manager.add_effect(idle_ram2)

                    # --- NEW: Add chase effects for fans and strimmer in idle state ---
                    idle_fan_color = ScrollingColorSource(
                        source=ram_idle_gradient,
                        speed=10.0,
                        pause=20,
                        scroll_fraction=1.6,
                        initial_roll_ratio=0.0,
                    )
                    idle_strimmer_color = ScrollingColorSource(
                        source=ram_idle_gradient,
                        speed=10.0,
                        pause=20,
                        scroll_fraction=1.6,
                        initial_roll_ratio=RAM_OFFSET,
                    )
                    idle_fan_chase = Chase(
                        fans,
                        color_source=idle_fan_color,
                        speed=IDLE_CHASE_SPEED,
                        delay=IDLE_CHASE_DELAY,
                        width=3,
                        duration=None,
                        loop_interval=IDLE_CHASE_INTERVAL,  # long loop interval
                        reverse=False,
                    )
                    idle_strimmer_chase = Chase(
                        strimmer,
                        color_source=idle_strimmer_color,
                        speed=IDLE_CHASE_SPEED,
                        delay=IDLE_CHASE_DELAY,
                        width=3,
                        duration=None,
                        loop_interval=IDLE_CHASE_INTERVAL,  # long loop interval
                        reverse=False,
                    )
                    idle_breathing_colors = ScrollingColorSource(
                        source=ram_idle_gradient,
                        speed=10.0,
                        resolution_multiplier=32,
                        initial_roll_ratio=RAM_OFFSET,
                    )
                    idle_breathing_fans = Breathing(
                        fans,
                        color_source=idle_breathing_colors,
                        min_brightness=0,
                        on_duration=30,
                        off_duration=90,
                        transition_duration=5,
                        speed=5.0,
                        duration=None,  # Infinite breathing
                    )
                    manager.add_effect(idle_fan_chase)
                    manager.add_effect(idle_strimmer_chase)
                    manager.add_effect(idle_breathing_fans)

                    blocking_effects.extend(
                        [idle_ram1, idle_ram2, idle_fan_chase, idle_strimmer_chase]
                    )

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
