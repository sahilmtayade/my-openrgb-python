#
# file: src/main.py (Minimal Test Version)
#
import time
from enum import Enum, auto

# --- Minimal Imports ---
from openrgb import OpenRGBClient
from openrgb.utils import DeviceType

# Framework components needed for this single test
from ..stage_manager import StageManager

# --- Framework Components ---
from ..utils.effects import (
    Chase,
    Gradient,
    LiquidFill,
    ScrollingColorMap,
    StaticBrightness,  # Assuming you create this for a simple idle
)
from ..utils.effects.color_source import StaticColor

# Your hardware-specific setup helper
from ..utils.openrgb_helper import (
    ZoneConfig,
    configure_motherboard_zones,
    configure_standalone_devices,
)

# ==============================================================================
#  Configuration
# ==============================================================================


# Define the states of our application
class AppState(Enum):
    STARTUP = auto()
    IDLE = auto()
    EXITING = auto()


# --- Hardware Config ---
# Note: I changed "strimmers" to "strimmer" (singular) for clarity
ZONE_CONFIGS = [
    ZoneConfig(index=0, role="strimmer", name="D_LED1 Bottom", led_count=27),
    ZoneConfig(index=1, role="fans", name="D_LED2 Top", led_count=24),
]
STANDALONE_DEVICES = [DeviceType.DRAM]

# --- Animation Config ---
FPS = 60
FRAME_TIME = 1.0 / FPS

# Color palettes in HSV (Hue 0-1, Saturation 0-1)
STRIMMER_HSV = (0.75, 1.0)  # A vibrant, saturated blue/purple
RAM_FAN_START_HSV = (0.05, 1.0)  # Fiery orange
RAM_FAN_END_HSV = (0.12, 1.0)  # Fiery yellow

# ==============================================================================
#  Main Application Logic
# ==============================================================================


def main():
    """Initializes hardware and runs a full startup-to-idle sequence."""
    client = OpenRGBClient()

    # --- 1. Hardware Initialization ---
    motherboard_zones = configure_motherboard_zones(client, ZONE_CONFIGS)
    standalone_devices = configure_standalone_devices(client, STANDALONE_DEVICES)

    # --- 2. Get Specific Devices and Create Master List ---
    strimmer = motherboard_zones.get("strimmer")
    fans = motherboard_zones.get("fans")
    dram_sticks = [dev for dev in standalone_devices if dev.type == DeviceType.DRAM]

    if not all([strimmer, fans, dram_sticks]):
        print("FATAL: One or more essential devices not found. Exiting.")
        return

    all_managed_devices = list(motherboard_zones.values()) + standalone_devices

    # --- 3. Framework and State Machine Setup ---
    manager = StageManager(all_managed_devices)
    current_state = AppState.STARTUP
    blocking_effects = []

    # --- 4. Define Color Sources ---
    strimmer_source = StaticColor(hsv=STRIMMER_HSV)
    chase_source = Gradient(start_hsv=RAM_FAN_START_HSV, end_hsv=RAM_FAN_END_HSV)

    # --- 5. Create and Add the STARTUP Effects ---
    print(f"[{current_state.name}] Starting startup sequence...")

    # Strimmer gets a LiquidFill
    fx1 = LiquidFill(
        strimmer, color_source=strimmer_source, speed=25.0, wavefront_width=8
    )
    manager.add_effect(fx1, strimmer)
    blocking_effects.append(fx1)

    # Fans get a chase (as a placeholder for your NeonSignFlicker)
    fx2 = Chase(fans, color_source=chase_source, width=10, speed=30.0)
    manager.add_effect(fx2, fans)
    blocking_effects.append(fx2)

    # Each RAM stick gets a staggered chase
    for i, stick in enumerate(dram_sticks):
        fx_ram = Chase(
            stick, color_source=chase_source, width=8, speed=20.0, delay=i * 0.4
        )
        manager.add_effect(fx_ram, stick)
        blocking_effects.append(fx_ram)

    # --- 6. Main Loop ---
    print("Running effects... Press Ctrl+C to exit.")
    try:
        while current_state != AppState.EXITING:
            loop_start = time.monotonic()
            manager.update()

            # --- State Transition Logic ---
            if current_state == AppState.STARTUP:
                if all(effect.is_finished() for effect in blocking_effects):
                    print(f"\n[{current_state.name}] Startup sequence finished.")

                    # Transition to the IDLE state
                    current_state = AppState.IDLE
                    print(f"[{current_state.name}] Starting idle effects...")

                    # Clean up the old state
                    blocking_effects.clear()
                    # No need to call manager.clear_effects() since the manager does this automatically

                    # Add your new, indefinite idle effects here
                    # For example, a static gradient on the strimmer and scrolling colors on fans
                    idle_strimmer_source = Gradient(
                        (0.7, 1.0), (0.9, 1.0)
                    )  # Purple to Pink
                    idle_fan_source = ScrollingColorMap(
                        [(0.1, 1.0), (0.1, 0.0)], speed=10
                    )  # Orange/White

                    manager.add_effect(
                        StaticBrightness(strimmer, color_source=idle_strimmer_source),
                        strimmer,
                    )
                    manager.add_effect(
                        StaticBrightness(fans, color_source=idle_fan_source), fans
                    )
                    # You could add something to RAM too, or leave it black

            # Frame Rate Limiter
            elapsed = time.monotonic() - loop_start
            if (sleep_time := FRAME_TIME - elapsed) > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nCtrl+C detected. Shutting down.")
        current_state = AppState.EXITING
    finally:
        # --- Cleanup ---
        print("Setting all devices to black.")
        for device in all_managed_devices:
            if device:  # Check if device object is not None
                device.clear()
                device.show()


if __name__ == "__main__":
    main()
