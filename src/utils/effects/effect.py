#
# file: base_effect.py
#
from dataclasses import dataclass
import time
from typing import TypedDict, Unpack
import numpy as np
from abc import ABC, abstractmethod
from openrgb.utils import RGBColor, RGBContainer

# --- NEW: Import the colour library and our color source abstraction ---
import colour
from .color_source import ColorSource

DEFAULT_GAMMA = 2.9


@dataclass
class EffectOptions:
    speed: float = 1.0
    reverse: bool = False
    dither_strength: float = 0.0
    gamma: float = DEFAULT_GAMMA


class EffectOptionsKwargs(TypedDict, total=False):
    speed: float
    reverse: bool
    dither_strength: float
    gamma: float


class Effect(ABC):
    """
    Abstract base class for effects using a brightness-array architecture.
    This version uses the `colour-science` library for high-performance,
    accurate color conversions and supports a `reverse` option.
    """

    def __init__(
        self,
        rgb_container: RGBContainer,
        color_source: ColorSource,
        **options: Unpack[EffectOptionsKwargs],
    ):
        """
        Initializes the base effect.

        Args:
            rgb_container: The OpenRGB container the effect targets.
            color_source: A ColorSource object providing hue and saturation.
            speed: A multiplier for the effect's animation speed.
            reverse: If True, the effect's brightness array will be spatially
                     reversed before rendering.
        """
        self.rgb_container = rgb_container
        self.color_source = color_source
        self.options = EffectOptions(**options)
        self.start_time = time.monotonic()
        self.num_leds = len(self.rgb_container.leds)
        self._is_finished = False

        self.brightness_array = np.zeros(self.num_leds, dtype=np.float32)

    @abstractmethod
    def _update_brightness(self):
        """
        Core logic of the effect. Subclasses must implement this.
        This method should update `self.brightness_array` based on time and logic,
        and set `self._is_finished = True` when its animation is complete.
        """
        ...

    def is_finished(self) -> bool:
        """Returns True if the effect has signaled that it is complete."""
        return self._is_finished

    def calculate_frame(self) -> list[RGBColor]:
        """
        Generates the final RGB frame. This version includes dithering to
        compensate for low-precision hardware.
        """
        self._update_brightness()

        final_brightness = (
            np.flip(self.brightness_array)
            if self.options.reverse
            else self.brightness_array
        )

        # --- DITHERING LOGIC ---
        # If dithering is enabled, add a small amount of random noise to the
        # brightness values *before* quantization. This breaks up banding.
        if self.options.dither_strength > 0.0:
            # Generate uniform random noise in the range [-strength, +strength]
            noise = np.random.uniform(
                -self.options.dither_strength,
                self.options.dither_strength,
                final_brightness.shape,
            )
            # Add noise and clip to ensure values stay within the valid 0-1 range
            final_brightness = np.clip(final_brightness + noise, 0, 1)
        # --- END DITHERING ---

        # Apply gamma correction to the brightness values
        final_brightness = np.power(final_brightness, self.options.gamma)

        hues, sats = self.color_source.get_hs_arrays(self.num_leds)
        hsv_array = np.dstack((hues, sats, final_brightness))[0]

        rgb_float_array = colour.HSV_to_RGB(hsv_array)
        rgb_int_array = (np.clip(rgb_float_array, 0, 1) * 255).astype(np.uint8)

        return [RGBColor(r, g, b) for r, g, b in rgb_int_array]
