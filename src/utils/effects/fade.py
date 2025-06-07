import time
from typing import Unpack

import numpy as np

from .color_source import ColorSource
from .effect import Effect, EffectOptionsKwargs


class FadeToBlack(Effect):
    """
    An effect that smoothly fades all LEDs from their current brightness to black (off)
    over a specified duration.
    """

    def __init__(
        self,
        rgb_container,
        color_source: ColorSource,
        duration: float = 2.0,  # Duration in seconds for the fade
        delay: float = 0.0,  # Delay before starting the fade
        **kwargs: Unpack[EffectOptionsKwargs],
    ):
        """
        Initializes the FadeToBlack effect.

        Args:
            rgb_container: The OpenRGB device to target.
            color_source: The ColorSource that defines the colors to display.
            duration: The time in seconds over which to fade to black.
            delay: The time in seconds to wait before starting the fade.
            **kwargs: Standard effect options.
        """
        super().__init__(rgb_container, color_source, **kwargs)
        self.duration = max(0.01, duration)
        self.delay = max(0.0, delay)

    def _update_brightness(self):
        """
        Gradually reduces the brightness of all LEDs to zero over the duration, after an optional delay.
        """
        elapsed_time = time.monotonic() - self.start_time
        if elapsed_time < self.delay:
            # Before delay, keep LEDs at current brightness
            return
        fade_elapsed = elapsed_time - self.delay
        if fade_elapsed >= self.duration:
            self.brightness_array.fill(0.0)
            self._is_finished = True
            return
        # Linear fade from 1.0 to 0.0
        fade_factor = 1.0 - (fade_elapsed / self.duration)
        fade_factor = np.clip(fade_factor, 0.0, 1.0)
        self.brightness_array.fill(fade_factor)
