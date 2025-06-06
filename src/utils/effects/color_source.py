#
# file: color_source.py
#
import numpy as np
from openrgb.utils import RGBColor

class ColorSource:
    """Base class for color providers."""
    def get_hs_arrays(self, num_leds: int) -> tuple[np.ndarray, np.ndarray]:
        """Returns two numpy arrays: one for hue, one for saturation."""
        raise NotImplementedError

class Gradient(ColorSource):
    """
    A color source representing a linear gradient between two HSV colors.
    Values are normalized from 0.0 to 1.0.
    """
    def __init__(self, start_hsv: tuple[float, float], end_hsv: tuple[float, float]):
        self.start_hue, self.start_sat = start_hsv
        self.end_hue, self.end_sat = end_hsv

    def get_hs_arrays(self, num_leds: int) -> tuple[np.ndarray, np.ndarray]:
        hues = np.linspace(self.start_hue, self.end_hue, num_leds, dtype=np.float32)
        sats = np.linspace(self.start_sat, self.end_sat, num_leds, dtype=np.float32)
        return hues, sats

class StaticColor(ColorSource):
    """A color source representing a single, uniform color."""
    def __init__(self, hsv: tuple[float, float]):
        self.hue, self.sat = hsv

    def get_hs_arrays(self, num_leds: int) -> tuple[np.ndarray, np.ndarray]:
        hues = np.full(num_leds, self.hue, dtype=np.float32)
        sats = np.full(num_leds, self.sat, dtype=np.float32)
        return hues, sats

class ColorMap(ColorSource):
    """A color source that repeats a specific map of colors."""
    def __init__(self, hsv_map: list[tuple[float, float]]):
        self.hsv_map = hsv_map

    def get_hs_arrays(self, num_leds: int) -> tuple[np.ndarray, np.ndarray]:
        map_len = len(self.hsv_map)
        hues = np.array([h for h, s in self.hsv_map], dtype=np.float32)
        sats = np.array([s for h, s in self.hsv_map], dtype=np.float32)
        # Tile the map to fit the number of LEDs
        hues = np.tile(hues, (num_leds // map_len) + 1)[:num_leds]
        sats = np.tile(sats, (num_leds // map_len) + 1)[:num_leds]
        return hues, sats