#
# file: color_source.py
#
import time
import numpy as np

# ==============================================================================
#  Base Class with Caching
# ==============================================================================


class ColorSource:
    """
    Base class for color providers with an efficient caching mechanism.

    For static color sources, the hue and saturation arrays are generated only on
    the first call to `get_hs_arrays` and then stored for all subsequent requests.
    Dynamic sources can override get_hs_arrays to bypass caching.
    """

    def __init__(self):
        self._hues: np.ndarray | None = None
        self._sats: np.ndarray | None = None

    def _generate_arrays(self, num_leds: int) -> tuple[np.ndarray, np.ndarray]:
        """
        Subclasses must implement this method to perform the actual array generation.
        This method will only be called once for static sources.
        """
        raise NotImplementedError

    def get_hs_arrays(self, num_leds: int) -> tuple[np.ndarray, np.ndarray]:
        """
        Public method to get the hue and saturation arrays.
        Handles caching to avoid redundant calculations for static sources.
        """
        if self._hues is None or self._sats is None:
            # If not cached, generate the arrays using the subclass's logic
            self._hues, self._sats = self._generate_arrays(num_leds)

        return self._hues, self._sats


# ==============================================================================
#  Static Color Sources (Generate Once)
# ==============================================================================


class Gradient(ColorSource):
    """
    A color source representing a linear gradient between two HSV colors.
    The gradient is generated once and cached.
    """

    def __init__(self, start_hsv: tuple[float, float], end_hsv: tuple[float, float]):
        """
        Args:
            start_hsv (tuple[float, float]): The starting (Hue, Saturation) from 0.0 to 1.0.
            end_hsv (tuple[float, float]): The ending (Hue, Saturation) from 0.0 to 1.0.
        """
        super().__init__()
        self.start_hue, self.start_sat = start_hsv
        self.end_hue, self.end_sat = end_hsv

    def _generate_arrays(self, num_leds: int) -> tuple[np.ndarray, np.ndarray]:
        hues = np.linspace(self.start_hue, self.end_hue, num_leds, dtype=np.float32)
        sats = np.linspace(self.start_sat, self.end_sat, num_leds, dtype=np.float32)
        return hues, sats


class StaticColor(ColorSource):
    """A color source representing a single, uniform color."""

    def __init__(self, hsv: tuple[float, float]):
        """
        Args:
            hsv (tuple[float, float]): The (Hue, Saturation) to use, from 0.0 to 1.0.
        """
        super().__init__()
        self.hue, self.sat = hsv

    def _generate_arrays(self, num_leds: int) -> tuple[np.ndarray, np.ndarray]:
        hues = np.full(num_leds, self.hue, dtype=np.float32)
        sats = np.full(num_leds, self.sat, dtype=np.float32)
        return hues, sats


class ColorMap(ColorSource):
    """A color source that creates a static pattern by repeating a specific map of colors."""

    def __init__(self, hsv_map: list[tuple[float, float]]):
        """
        Args:
            hsv_map (list[tuple[float, float]]): A list of (Hue, Saturation) tuples to tile.
        """
        super().__init__()
        self.hsv_map = hsv_map

    def _generate_arrays(self, num_leds: int) -> tuple[np.ndarray, np.ndarray]:
        map_len = len(self.hsv_map)
        if map_len == 0:  # Handle empty map case
            return np.zeros(num_leds, dtype=np.float32), np.zeros(
                num_leds, dtype=np.float32
            )

        hues = np.array([h for h, s in self.hsv_map], dtype=np.float32)
        sats = np.array([s for h, s in self.hsv_map], dtype=np.float32)

        # Tile the map to fit the number of LEDs
        hues = np.tile(hues, (num_leds // map_len) + 1)[:num_leds]
        sats = np.tile(sats, (num_leds // map_len) + 1)[:num_leds]
        return hues, sats


# ==============================================================================
#  Dynamic Color Sources (Generate Every Frame)
# ==============================================================================


class ScrollingColorMap(ColorSource):
    """
    A dynamic color source that scrolls a base color map over time.
    """

    def __init__(self, hsv_map: list[tuple[float, float]], speed: float = 5.0):
        """
        Initializes the ScrollingColorMap.

        Args:
            hsv_map: The base list of (hue, saturation) tuples to scroll.
            speed: The speed of scrolling in "LED positions per second".
                   Positive values scroll one way, negative values the other.
        """
        super().__init__()
        self.base_hsv_map = hsv_map
        self.scroll_speed = speed

        self._base_hues: np.ndarray | None = None
        self._base_sats: np.ndarray | None = None
        self._start_time = time.monotonic()

    def _generate_base_arrays(self, num_leds: int):
        """Generates the full, tiled base arrays if they don't exist."""
        if self._base_hues is None or self._base_sats is None:
            map_len = len(self.base_hsv_map)
            if map_len == 0:
                self._base_hues = np.zeros(num_leds, dtype=np.float32)
                self._base_sats = np.zeros(num_leds, dtype=np.float32)
                return

            hues = np.array([h for h, s in self.base_hsv_map], dtype=np.float32)
            sats = np.array([s for h, s in self.base_hsv_map], dtype=np.float32)

            # Create arrays that are twice as long as needed to make seamless scrolling easier
            # and avoid visual artifacts from tiling a small map over a large area repeatedly.
            required_length = max(num_leds, map_len) * 2
            self._base_hues = np.tile(hues, (required_length // map_len) + 1)
            self._base_sats = np.tile(sats, (required_length // map_len) + 1)

    def get_hs_arrays(self, num_leds: int) -> tuple[np.ndarray, np.ndarray]:
        """
        Calculates and returns the scrolled hue and saturation arrays for the current frame.
        This method overrides the caching behavior of the parent BaseColorSource by directly
        performing the scroll on each call.
        """
        # 1. Ensure the base (unscrolled) arrays are generated once
        self._generate_base_arrays(num_leds)

        # 2. Calculate current scroll offset based on time
        elapsed_time = time.monotonic() - self._start_time
        offset = int(elapsed_time * self.scroll_speed)

        # 3. Roll the base arrays to create the scrolled effect
        # np.roll is very efficient for this. We then slice the result to the
        # correct number of LEDs.
        scrolled_hues = np.roll(self._base_hues, offset, axis=0)[:num_leds]
        scrolled_sats = np.roll(self._base_sats, offset, axis=0)[:num_leds]

        return scrolled_hues, scrolled_sats
