#
# file: src/utils/effects/static_brightness.py
#
import time
from typing import Optional, Unpack

import numpy as np

from .color_source import ColorSource

# Import the core framework components
from .effect import Effect, EffectOptionsKwargs


class StaticBrightness(Effect):
    """
    An effect that holds all LEDs at a constant, uniform brightness level.

    This effect is indefinite and will never finish on its own. It's ideal
    for creating idle background effects when combined with various ColorSource
    objects. For example, using this with a ScrollingColorMap creates a moving
    color zone effect.
    """

    def __init__(
        self,
        rgb_container,
        color_source: ColorSource,
        brightness: float = 1.0,  # Brightness from 0.0 to 1.0
        duration: Optional[float] = None,  # Duration in seconds, None for indefinite
        **kwargs: Unpack[EffectOptionsKwargs],
    ):
        """
        Initializes the StaticBrightness effect.

        Args:
            rgb_container: The OpenRGB device to target.
            color_source: The ColorSource that defines the colors to display.
            brightness: The uniform brightness level (0.0 to 1.0) to apply.
            duration: The time in seconds for which the effect should run. If None, runs indefinitely.
            **kwargs: Standard effect options. Speed is not used by this effect.
        """
        super().__init__(rgb_container, color_source, **kwargs)

        # Clamp the brightness level to ensure it's in the valid [0, 1] range
        self.brightness_level = np.clip(brightness, 0.0, 1.0)

        # Pre-calculate the brightness array since it never changes.
        # This is a minor optimization.
        self.brightness_array.fill(self.brightness_level)
        self.duration = duration
        self._start_time = None

    def _update_brightness(self):
        """
        This effect's brightness is static, but if duration is set, it will finish after the specified time.
        """

        if self._start_time is None:
            self._start_time = time.monotonic()
        if self.duration is not None:
            elapsed = time.monotonic() - self._start_time
            if elapsed >= self.duration:
                self._is_finished = True
