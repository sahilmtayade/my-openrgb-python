#
# file: src/utils/effects/chase.py (Corrected)
#
import time
from typing import Optional, Unpack

import numpy as np

from .color_source import ColorSource
from .effect import Effect, EffectOptionsKwargs


class Chase(Effect):
    """
    A "comet" or "chase" effect with a bright head and a tapering tail that
    moves across the LED strip. Supports looping and a finite duration.
    """

    def __init__(
        self,
        rgb_container,
        color_source: ColorSource,
        width: int = 10,
        delay: float = 0.0,
        duration: Optional[float] = None,
        loop_interval: float = 0.0,
        **kwargs: Unpack[EffectOptionsKwargs],
    ):
        """
        Initializes the Chase effect.

        Args:
            width: The total integer width of the comet in LEDs.
            delay: An initial delay before the first run starts.
            duration: If set, the effect will stop looping and finish after this
                      many seconds have passed since its creation.
            loop_interval: The time in seconds to wait between the end of one
                           run and the start of the next.
            **kwargs: Standard effect options like speed, reverse, gamma, etc.
        """
        super().__init__(rgb_container, color_source, **kwargs)

        self.width = max(1, width)
        self.delay = delay
        self.duration = duration
        self.loop_interval = max(0.0, loop_interval)

        # --- NEW: Simplified state management ---
        # This will hold the time.monotonic() value when the current run
        # is scheduled to start. It's the key to resetting the animation.
        self._loop_start_time: Optional[float] = None

        # Pre-calculate the brightness pattern for efficiency
        self.pattern = np.linspace(1.0, 0.0, num=self.width, dtype=np.float32)

    def _update_brightness(self):
        """
        Calculates the position of the chase, handles the looping state,
        and stamps the brightness pattern onto the main brightness array.
        """
        now = time.monotonic()

        # 1. Check for permanent completion based on total duration
        if self.duration is not None and (now - self.start_time) >= self.duration:
            self._is_finished = True
            self.brightness_array.fill(0.0)
            return

        # 2. Initialize the start time for the very first loop, including the delay
        if self._loop_start_time is None:
            self._loop_start_time = self.start_time + self.delay

        # 3. Check if we are currently in a delay or loop_interval period
        if now < self._loop_start_time:
            # We are waiting for the next run to start. Keep the strip black.
            self.brightness_array.fill(0.0)
            return

        # --- If we get here, the comet is actively running ---

        # 4. Calculate position based on time *since the current loop started*
        time_in_loop = now - self._loop_start_time
        head_position = time_in_loop * self.options.speed

        # 5. Check if the current run has finished
        comet_start_position = head_position - self.width
        if comet_start_position >= self.num_leds:
            # The comet has moved off-screen. Schedule the next loop.
            self._loop_start_time = now + self.loop_interval
            self.brightness_array.fill(0.0)
            return

        # 6. If the comet is on-screen, draw it.
        self.brightness_array.fill(0.0)

        int_head_pos = int(head_position)
        target_start = int_head_pos - self.width
        target_end = int_head_pos

        write_start = max(0, target_start)
        write_end = min(self.num_leds, target_end)

        if write_start >= write_end:
            return  # Comet is not yet on screen

        read_start = write_start - target_start
        read_end = write_end - target_start

        self.brightness_array[write_start:write_end] = self.pattern[read_start:read_end]
