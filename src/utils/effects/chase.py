#
# file: src/utils/effects/chase.py (Improved)
#
import time
from typing import Optional, Unpack

import numpy as np

from .color_source import ColorSource
from .effect import Effect, EffectOptionsKwargs


class Chase(Effect):
    """
    A "comet" or "chase" effect with a bright head and a tapering tail that
    moves smoothly across the LED strip using sub-pixel rendering.
    """

    def __init__(
        self,
        rgb_container,
        color_source: ColorSource,
        width: int = 10,
        delay: float = 0.0,
        duration: Optional[float] = None,
        loop_interval: float = 0.0,
        resolution_multiplier: int = 8,  # <-- NEW: Controls smoothness
        **kwargs: Unpack[EffectOptionsKwargs],
    ):
        """
        Initializes the Chase effect.

        Args:
            width: The total integer width of the comet in LEDs.
            delay: An initial delay before the first run starts.
            duration: If set, the effect will stop looping and finish.
            loop_interval: The time to wait between the end of one run
                           and the start of the next.
            resolution_multiplier: Higher values create a smoother, anti-aliased
                                   comet at the cost of more memory/CPU. 8 is
                                   a good default for a smooth look.
            **kwargs: Standard effect options.
        """
        super().__init__(rgb_container, color_source, **kwargs)

        self.width = max(1, width)
        self.delay = delay
        self.duration = duration
        self.loop_interval = max(0.0, loop_interval)
        self.resolution_multiplier = max(1, resolution_multiplier)
        self._loop_start_time: Optional[float] = None

        # --- NEW: Create a high-resolution pattern for smooth stamping ---
        high_res_width = self.width * self.resolution_multiplier
        self.high_res_pattern = np.linspace(
            1.0, 0.0, num=high_res_width, dtype=np.float32
        )

    def _update_brightness(self):
        """
        Calculates the sub-pixel position of the chase and renders it to a
        high-resolution canvas before downsampling for a smooth result.
        """
        now = time.monotonic()

        # 1. Looping and timing logic (unchanged)
        if self.duration is not None and (now - self.start_time) >= self.duration:
            self._is_finished = True
            self.brightness_array.fill(0.0)
            return

        if self._loop_start_time is None:
            self._loop_start_time = self.start_time + self.delay

        if now < self._loop_start_time:
            self.brightness_array.fill(0.0)
            return

        # 2. Calculate floating-point position (unchanged)
        time_in_loop = now - self._loop_start_time
        head_position = time_in_loop * self.options.speed

        # 3. Check for run completion (unchanged)
        comet_start_position = head_position - self.width
        if comet_start_position >= self.num_leds:
            self._loop_start_time = now + self.loop_interval
            self.brightness_array.fill(0.0)
            return

        # --- NEW: High-Resolution Rendering Logic ---

        # 4. Create a high-resolution canvas to draw on.
        high_res_led_count = self.num_leds * self.resolution_multiplier
        high_res_canvas = np.zeros(high_res_led_count, dtype=np.float32)

        # 5. Calculate the comet's head position in the high-res space.
        high_res_head_pos = head_position * self.resolution_multiplier
        int_head_pos = int(high_res_head_pos)

        # 6. "Stamp" the high-res pattern onto the high-res canvas.
        #    This is the same slicing logic as before, but with high-res variables.
        target_start = int_head_pos - len(self.high_res_pattern)
        target_end = int_head_pos

        write_start = max(0, target_start)
        write_end = min(high_res_led_count, target_end)

        if write_start < write_end:
            read_start = write_start - target_start
            read_end = write_end - target_start
            high_res_canvas[write_start:write_end] = self.high_res_pattern[
                read_start:read_end
            ]

        # 7. Downsample the high-res canvas to the final brightness array.
        #    We do this by reshaping the canvas and averaging each block of
        #    high-res pixels that corresponds to a single real LED.
        reshaped_canvas = high_res_canvas.reshape(
            self.num_leds, self.resolution_multiplier
        )
        np.mean(reshaped_canvas, axis=1, out=self.brightness_array)
