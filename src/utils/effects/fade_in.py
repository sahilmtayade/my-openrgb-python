import time
from typing import Unpack

import numpy as np

from .color_source import ColorSource
from .effect import Effect, EffectOptionsKwargs

class FadeIn(Effect):
    """
    An effect that smoothly fades all LEDs from black (off) to full brightness
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
        Initializes the FadeIn effect.

        Args:
            rgb_container: The OpenRGB device to target.
            color_source: The ColorSource that defines the colors to display.
            duration: The time in seconds over which to fade in.
            delay: The time in seconds to wait before starting the fade.
            **kwargs: Standard effect options.
        """
        super().__init__(rgb_container, color_source, **kwargs)
        self.duration = max(0.01, duration)
        self.delay = max(0.0, delay)

    def _update_brightness(self):
        """
        Gradually increases the brightness of all LEDs from zero to full over the duration, after an optional delay.
        """
        elapsed_time = time.monotonic() - self.start_time
        if elapsed_time < self.delay:
            # Before delay, keep LEDs off
            self.brightness_array.fill(0.0)
            return
        fade_elapsed = elapsed_time - self.delay
        if fade_elapsed >= self.duration:
            self.brightness_array.fill(1.0)
            self._is_finished = True
            return
        # Linear fade from 0.0 to 1.0
        fade_factor = fade_elapsed / self.duration
        fade_factor = np.clip(fade_factor, 0.0, 1.0)
        self.brightness_array.fill(fade_factor)
