#
# file: src/utils/effects/static_brightness.py
#
from typing import Unpack

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
        **kwargs: Unpack[EffectOptionsKwargs],
    ):
        """
        Initializes the StaticBrightness effect.

        Args:
            rgb_container: The OpenRGB device to target.
            color_source: The ColorSource that defines the colors to display.
            brightness: The uniform brightness level (0.0 to 1.0) to apply.
            **kwargs: Standard effect options. Speed is not used by this effect.
        """
        super().__init__(rgb_container, color_source, **kwargs)

        # Clamp the brightness level to ensure it's in the valid [0, 1] range
        self.brightness_level = np.clip(brightness, 0.0, 1.0)

        # Pre-calculate the brightness array since it never changes.
        # This is a minor optimization.
        self.brightness_array.fill(self.brightness_level)

    def _update_brightness(self):
        """
        This effect's brightness is static, so this method does nothing after
        the initial setup in __init__.
        """
        # The brightness_array is already set. No per-frame update needed.
        pass
