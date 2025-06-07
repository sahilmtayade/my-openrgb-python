# file: src/utils/effects/manual_ramp.py
import numpy as np
import time
from .effect import Effect


class ManualBrightnessRamp(Effect):
    """A diagnostic effect to test the hardware's true brightness resolution."""

    def _update_brightness(self):
        elapsed = time.monotonic() - self.start_time

        # Go from 0 to 255 over 30 seconds (very slow)
        level = elapsed / 50.0
        if level > 1.0:
            level = 1.0
            self._is_finished = True

        # We set the brightness directly. No interpolation.
        self.brightness_array.fill(level)
