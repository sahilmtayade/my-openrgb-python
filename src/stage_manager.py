#
# file: stage_manager.py
#
import time
from typing import Sequence

from openrgb.utils import RGBColor, RGBContainer

from .utils.effects.effect import Effect


class StageManager:
    """
    Manages and renders effects for a list of OpenRGB devices.

    This class acts as a central renderer. It iterates through all active
    effects, calculates their frames, blends them onto per-device canvases,
    and then pushes the final results to the hardware in a tight loop.
    This "calculate all, then show all" approach ensures maximum performance
    and visual synchronization across multiple devices.
    """

    def __init__(self, devices: Sequence[RGBContainer]):
        """
        Initializes the StageManager with the devices to control.

        Args:
            devices: A list of OpenRGB aRGBContainer objects to be managed.
        """
        self.devices = devices

        # A dictionary mapping each device to its list of active effects.
        self._effects_map: dict[RGBContainer, list[Effect]] = {
            dev: [] for dev in devices
        }

        # A drawing canvas for each device to avoid creating new color lists every frame.
        self._canvases: dict[RGBContainer, list[RGBColor]] = {
            dev: [RGBColor(0, 0, 0) for _ in dev.leds] for dev in devices
        }

    def add_effect(self, effect: Effect):
        """Adds a new effect to the effect's target device. The new effect will be layered on top."""
        device = effect.rgb_container
        if device in self._effects_map:
            self._effects_map[device].append(effect)
        else:
            print(
                f"Warning: Device '{str(device)}' is not managed by this StageManager."
            )

    def clear_effects(self, device: RGBContainer):
        """Removes all effects from a specific device."""
        if device in self._effects_map:
            self._effects_map[device].clear()

    def get_active_effects(self, device: RGBContainer) -> list[Effect]:
        """Returns the list of currently active (not finished) effects for a device."""
        return self._effects_map.get(device, [])

    def update(self):
        """
        Executes one full update and render cycle. This should be called once per frame.

        The cycle consists of three phases:
        1. Calculate: Compute the color frames for all active effects.
        2. Blend & Cleanup: Layer the effect frames onto their respective device
           canvases and remove any effects that have finished.
        3. Show: Push the final canvases to the hardware.
        """
        # --- Phase 1 & 2: Calculate, Blend, and Cleanup ---
        for device, active_effects in self._effects_map.items():
            # Start with a black canvas for this device
            canvas = self._canvases[device]
            for i in range(len(canvas)):
                canvas[i] = RGBColor(0, 0, 0)

            effects_to_keep = []
            for effect in active_effects:
                # Calculate the frame for this effect
                effect_frame = effect.calculate_frame()

                # Simple "last on top wins" blend.
                for i, color in enumerate(effect_frame):
                    if i < len(canvas):
                        canvas[i] = color

                # Keep the effect for the next frame only if it's not finished
                if not effect.is_finished():
                    effects_to_keep.append(effect)

            # Update the list of effects for the device
            self._effects_map[device] = effects_to_keep

        # --- Phase 3: Show All ---
        # After ALL calculations are done, send the data to hardware in a tight loop.
        for device in self.devices:
            device.set_colors(self._canvases[device])
            device.show(fast=True)

    def clear_all_effects(self):
        """Clears all effects from all devices managed by this StageManager."""
        for device in self.devices:
            self.clear_effects(device)
