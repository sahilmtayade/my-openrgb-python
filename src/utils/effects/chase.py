#
# file: src/utils/effects/chase.py
#
import time
from typing import Unpack

import numpy as np

from .color_source import ColorSource

# Corrected imports as per your structure
from .effect import Effect, EffectOptionsKwargs


class Chase(Effect):
    """
    A "comet" or "chase" effect with a bright head and a tapering tail that
    moves across the LED strip.
    """

    def __init__(
        self,
        rgb_container,
        color_source: ColorSource,
        width: int = 10,
        delay: float = 0.0,
        **kwargs: Unpack[EffectOptionsKwargs],
    ):
        """
        Initializes the Chase effect.

        Args:
            rgb_container: The OpenRGB device to target.
            color_source: The ColorSource that defines the comet's color.
            width: The total integer width of the comet in number of LEDs,
                   including the head and tail.
            **kwargs: Standard effect options like speed, reverse, gamma, etc.
        """
        super().__init__(rgb_container, color_source, **kwargs)

        # Ensure width is a positive integer.
        self.width = max(1, width)
        self.delay = delay
        # --- Pre-calculate the brightness pattern for efficiency ---
        # Create a linear gradient from 1.0 (bright head) down to 0.0 (end of tail).
        # This pattern is our "stamp" that we will apply each frame.
        self.pattern = np.linspace(1.0, 0.0, num=self.width, dtype=np.float32)

    def _update_brightness(self):
        """
        Calculates the position of the chase and "stamps" the brightness
        pattern onto the main brightness array.
        """
        # 1. Calculate the current position of the comet's HEAD based on time and speed.
        elapsed_time = time.monotonic() - self.start_time

        # --- NEW: Check the delay before running any logic ---
        if elapsed_time < self.delay:
            return  # Do nothing until the delay has passed

        # Calculate position based on time *since the delay ended*
        head_position = (elapsed_time - self.delay) * self.options.speed

        # 2. Check for completion.
        #    The effect is finished when the start of the comet (the tip of the tail)
        #    has moved completely past the end of the LED strip.
        comet_start_position = head_position - self.width
        if comet_start_position >= self.num_leds:
            self._is_finished = True
            self.brightness_array.fill(0.0)  # Ensure it's left black
            return

        # 3. Clear the brightness array from the previous frame.
        self.brightness_array.fill(0.0)

        # 4. Calculate the precise slice to stamp the pattern.
        #    This handles cases where the comet is partially on or off the strip.

        # The head is now an integer position.
        int_head_pos = int(head_position)

        # Determine the target start/end indices on the main brightness array
        target_start = int_head_pos - self.width
        target_end = int_head_pos

        # Determine the actual indices to write to, clamped to the array bounds
        write_start = max(0, target_start)
        write_end = min(self.num_leds, target_end)

        # If the write indices are invalid (comet is fully off-screen), do nothing.
        if write_start >= write_end:
            return

        # Determine which part of the source `self.pattern` to read from,
        # corresponding to the visible part of the comet.
        read_start = write_start - target_start
        read_end = write_end - target_start

        # 5. "Stamp" the visible part of the pattern onto the brightness array.
        self.brightness_array[write_start:write_end] = self.pattern[read_start:read_end]
