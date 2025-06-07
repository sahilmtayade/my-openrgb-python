#
# file: main.py
#
import time
from enum import Enum, auto
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor

# Import the framework and your custom effect classes
from stage_manager import StageManager
from utils import (
    LiquidFill,
    Chase,
    SignFlicker,
    Static,
    Fade,
)  # NOTE: You must create these!


# --- Define states for the application's lifecycle ---
class AppState(Enum):
    STATE_1_LIQUID = auto()
    STATE_2_MAIN_SHOW = auto()
    STATE_3_FADE_OUT = auto()
    STATE_4_IDLE = auto()
    EXITING = auto()


# --- Define constant colors and settings ---
LIQUID_COLOR = RGBColor(70, 0, 255)
RAM_CHASE_COLOR_MAP = [RGBColor(255, 0, 0), RGBColor(255, 80, 0), RGBColor(255, 150, 0)]
FPS = 60
FRAME_TIME = 1.0 / FPS


def run():
    """Main function to run the lighting controller."""
    client = OpenRGBClient()

    # --- Device Setup ---
    try:
        print("Detecting devices...")
        cables = client.get_devices_by_name("My Cable Combs")[0]
        fans = client.get_devices_by_name("My Case Fans")[0]
        ram1 = client.get_devices_by_name("My RAM Stick 1")[0]
        ram2 = client.get_devices_by_name("My RAM Stick 2")[0]
        all_devices = [cables, fans, ram1, ram2]
        print("All devices found.")
    except IndexError:
        print(
            "FATAL: Could not find all required RGB devices. Please check names in OpenRGB."
        )
        return

    # --- Initialization ---
    manager = StageManager(all_devices)
    current_state = AppState.STATE_1_LIQUID
    blocking_effects = []

    # --- Kick off the sequence ---
    print(f"[{current_state.name}] Starting...")
    effect = LiquidFill(cables, speed=5.0, color=LIQUID_COLOR)
    manager.add_effect(effect, cables)
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
                    manager.clear_effects(cables)

                    manager.add_effect(Static(cables, color=LIQUID_COLOR), cables)
                    chase1 = Chase(
                        ram1, color_map=RAM_CHASE_COLOR_MAP, speed=20, delay=0.0
                    )
                    chase2 = Chase(
                        ram2, color_map=RAM_CHASE_COLOR_MAP, speed=20, delay=0.5
                    )
                    flicker = SignFlicker(fans)
                    manager.add_effect(chase1, ram1)
                    manager.add_effect(chase2, ram2)
                    manager.add_effect(flicker, fans)
                    blocking_effects = [chase1, chase2, flicker]

                elif current_state == AppState.STATE_2_MAIN_SHOW:
                    current_state = AppState.STATE_3_FADE_OUT
                    print(f"[{current_state.name}] Starting...")
                    blocking_effects.clear()
                    for dev in all_devices:
                        manager.clear_effects(dev)

                    fade_cables = Fade(cables, from_color=LIQUID_COLOR)
                    fade_fans = Fade(fans, from_color=RAM_CHASE_COLOR_MAP[0])
                    fade_ram1 = Fade(ram1, from_color=RGBColor(255, 200, 0))
                    fade_ram2 = Fade(ram2, from_color=RGBColor(255, 200, 0))
                    manager.add_effect(fade_cables, cables)
                    manager.add_effect(fade_fans, fans)
                    manager.add_effect(fade_ram1, ram1)
                    manager.add_effect(fade_ram2, ram2)
                    blocking_effects = [fade_cables, fade_fans, fade_ram1, fade_ram2]

                elif current_state == AppState.STATE_3_FADE_OUT:
                    current_state = AppState.STATE_4_IDLE
                    print(
                        f"[{current_state.name}] Startup complete. Running idle effects."
                    )
                    blocking_effects.clear()
                    for dev in all_devices:
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
        for device in all_devices:
            device.clear()
            # A final show call may be needed on some devices to apply the clear
            device.show()


if __name__ == "__main__":
    run()
