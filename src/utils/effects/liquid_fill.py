#
# file: my_effects.py
#
import time
from typing import Unpack
import numpy as np

from ..debug_utils import debug_print

# Import the core framework components
from .effect import Effect, EffectOptionsKwargs
from .color_source import (
    ColorSource,
    StaticColor,
)  # Also import a ColorSource for easy testing


class LiquidFill(Effect):
    """
    An effect that "fills" a device with light. This version uses a
    configurable wavefront width to create a soft, smooth leading edge.
    """

    def __init__(
        self,
        rgb_container,
        color_source: ColorSource,
        wavefront_width: int = 7,  # <-- NEW PARAMETER
        **kwargs: Unpack[EffectOptionsKwargs],
    ):
        """
        Initializes the LiquidFill effect.

        Args:
            wavefront_width: The number of LEDs to use for the soft gradient
                             at the edge of the fill. A larger number creates
                             a softer, more blurry edge.
            ... (other args)
        """
        super().__init__(
            rgb_container,
            color_source,
            **kwargs,
        )

        # Ensure wavefront_width is at least 1 to avoid division by zero
        self.wavefront_width = max(1, wavefront_width)

        # Create a persistent array of LED indices
        self._led_indices = np.arange(self.num_leds, dtype=np.float32)

    def _update_brightness(self):
        """
        Calculates the brightness of each LED based on the current fill position
        and the desired wavefront width.
        """
        # 1. Calculate the precise, floating-point fill position
        elapsed_time = time.monotonic() - self.start_time
        position = elapsed_time * self.options.speed

        # 2. Check for completion
        # We check against num_leds + width so the tail of the wave has time to finish
        if position >= self.num_leds + self.wavefront_width:
            self._is_finished = True
            self.brightness_array.fill(1.0)
            return

        # 3. The new, improved calculation for a soft wavefront
        #
        # By dividing the result by wavefront_width before clipping, we stretch
        # the transition from 0.0 to 1.0 over that many LEDs.
        #
        # Example: width=5, position=10.7
        # LED 8: (10.7-8)/5 = 0.54 -> brightness 0.54
        # LED 9: (10.7-9)/5 = 0.34 -> brightness 0.34
        # LED 10: (10.7-10)/5 = 0.14 -> brightness 0.14

        np.clip(
            (position - self._led_indices) / self.wavefront_width,
            0,
            1,
            out=self.brightness_array,
        )
        debug_print(
            f"LiquidFill: position={position:.2f}, brightness={list(self.brightness_array)}"
        )
