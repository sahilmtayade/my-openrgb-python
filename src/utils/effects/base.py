#
# file: base_effect.py
#
import time
import numpy as np
from abc import ABC, abstractmethod
from openrgb.utils import RGBColor, RGBContainer
from .color_source import ColorSource  # Import our new class


class BaseEffect(ABC):
    """
    Abstract base class for effects using a brightness-array architecture.
    Effects inheriting from this should manipulate `self.brightness_array`.
    """

    def __init__(
        self,
        rgb_container: RGBContainer,
        color_source: ColorSource,
        speed: float = 1.0,
        **kwargs,
    ):
        self.rgb_container = rgb_container
        self.color_source = color_source
        self.speed = speed
        self.kwargs = kwargs

        self.start_time = time.monotonic()
        self.num_leds = len(self.rgb_container.leds)
        self._is_finished = False

        # The core of the new architecture: a numpy array for brightness (Value in HSV)
        self.brightness_array = np.zeros(self.num_leds, dtype=np.float32)

    @abstractmethod
    def _update_brightness(self):
        """
        Core logic of the effect. Subclasses must implement this.
        This method should update the `self.brightness_array` based on time
        and logic, and set `self._is_finished = True` when complete.
        """
        ...

    def is_finished(self) -> bool:
        """Returns True if the effect has signaled that it is complete."""
        return self._is_finished

    def calculate_frame(self) -> list[RGBColor]:
        """
        Public-facing method that generates the final RGB frame.
        1. Calls the subclass logic to update the brightness array.
        2. Combines brightness with the color source (H, S).
        3. Converts the final HSV data to a list of RGBColor objects.
        This should not be overridden.
        """
        # 1. Update the brightness values
        self._update_brightness()

        # 2. Get Hue and Saturation arrays from the color source
        hues, sats = self.color_source.get_hs_arrays(self.num_leds)

        # 3. Convert HSV arrays to a list of RGBColor objects for OpenRGB
        final_colors = []
        # We loop here because the OpenRGB library expects its own RGBColor object.
        # All the heavy math is already done vectorized in NumPy. This final
        # conversion loop is extremely fast and not a performance bottleneck.
        for h, s, v in zip(hues, sats, self.brightness_array):
            # Clamp brightness to ensure it's within the valid [0, 1] range
            v_clamped = max(0.0, min(1.0, v))

            # RGBColor.from_hsv expects H(0-360), S(0-100), V(0-100)
            rgb = RGBColor.from_hsv(h * 360, s * 100, v_clamped * 100)
            final_colors.append(rgb)

        return final_colors
