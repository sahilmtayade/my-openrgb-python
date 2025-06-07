#
# file: color_source.py (updated)
#
import time
from typing import List, Unpack

import numpy as np

# ==============================================================================
#  Base Class with Caching and Reversal
# ==============================================================================


class ColorSource:
    """
    Base class for color providers with caching and a reversal option.
    """

    def __init__(self, reverse: bool = False):  # <-- NEW PARAMETER
        """
        Initializes the ColorSource.

        Args:
            reverse: If True, the generated color map will be spatially reversed.
        """
        self._hues: dict[int, np.ndarray] = {}
        self._sats: dict[int, np.ndarray] = {}
        self.reverse = reverse  # <-- STORE THE OPTION

    def _generate_arrays(self, num_leds: int) -> tuple[np.ndarray, np.ndarray]:
        """
        Subclasses must implement this to perform the actual array generation.
        """
        raise NotImplementedError

    def get_hs_arrays(self, num_leds: int) -> tuple[np.ndarray, np.ndarray]:
        """
        Public method to get the hue and saturation arrays.
        Handles caching and optional reversal for static sources.
        """
        if num_leds not in self._hues:
            # Generate and cache the arrays in their default (non-reversed) order
            hues, sats = self._generate_arrays(num_leds)
            self._hues[num_leds] = hues
            self._sats[num_leds] = sats

        # Retrieve the canonical arrays from the cache
        hues_to_return = self._hues[num_leds]
        sats_to_return = self._sats[num_leds]

        # --- NEW: Apply reversal if the flag is set ---
        if self.reverse:
            # np.flip is a highly efficient way to reverse numpy arrays
            return np.flip(hues_to_return), np.flip(sats_to_return)

        return hues_to_return, sats_to_return


# ==============================================================================
#  Static Color Sources (Updated to accept `reverse`)
# ==============================================================================


class Gradient(ColorSource):
    """A color source representing a linear gradient."""

    def __init__(
        self,
        start_hsv: tuple[float, float],
        end_hsv: tuple[float, float],
        start_pos: float = 0.0,
        end_pos: float = 1.0,
        reverse: bool = False,  # <-- NEW
    ):
        super().__init__(reverse=reverse)  # <-- PASS TO PARENT
        self.start_hue, self.start_sat = start_hsv
        self.end_hue, self.end_sat = end_hsv

        start_pos_clamped = max(0.0, min(1.0, start_pos))
        end_pos_clamped = max(0.0, min(1.0, end_pos))
        self.start_pos = min(start_pos_clamped, end_pos_clamped)
        self.end_pos = max(start_pos_clamped, end_pos_clamped)

    def _generate_arrays(self, num_leds: int) -> tuple[np.ndarray, np.ndarray]:
        # ... (generation logic is unchanged)
        if num_leds == 0:
            return np.array([]), np.array([])
        start_idx = round(self.start_pos * (num_leds - 1))
        end_idx = round(self.end_pos * (num_leds - 1))
        num_start_solid = start_idx
        start_hues = np.full(num_start_solid, self.start_hue, dtype=np.float32)
        start_sats = np.full(num_start_solid, self.start_sat, dtype=np.float32)
        gradient_width = end_idx - start_idx
        if gradient_width > 0:
            gradient_hues = np.linspace(
                self.start_hue, self.end_hue, num=gradient_width, dtype=np.float32
            )
            gradient_sats = np.linspace(
                self.start_sat, self.end_sat, num=gradient_width, dtype=np.float32
            )
        else:
            gradient_hues, gradient_sats = (
                np.array([], dtype=np.float32),
                np.array([], dtype=np.float32),
            )
        num_end_solid = num_leds - end_idx
        end_hues = np.full(num_end_solid, self.end_hue, dtype=np.float32)
        end_sats = np.full(num_end_solid, self.end_sat, dtype=np.float32)
        final_hues = np.concatenate((start_hues, gradient_hues, end_hues))
        final_sats = np.concatenate((start_sats, gradient_sats, end_sats))
        return final_hues, final_sats


class MultiGradient(ColorSource):
    """A color source representing a gradient between multiple color stops."""

    def __init__(
        self, stops: List[tuple[tuple[float, float], float]], reverse: bool = False
    ):  # <-- NEW
        super().__init__(reverse=reverse)  # <-- PASS TO PARENT
        if not stops:
            self.stops = []
            return
        sanitized_stops = []
        for hsv, pos in stops:
            clamped_pos = max(0.0, min(1.0, pos))
            sanitized_stops.append((hsv, clamped_pos))
        self.stops = sorted(sanitized_stops, key=lambda stop: stop[1])

    def _generate_arrays(self, num_leds: int) -> tuple[np.ndarray, np.ndarray]:
        # ... (generation logic is unchanged)
        if num_leds == 0:
            return np.array([]), np.array([])
        if not self.stops:
            return np.zeros(num_leds, dtype=np.float32), np.zeros(
                num_leds, dtype=np.float32
            )
        if len(self.stops) == 1:
            h, s = self.stops[0][0]
            return np.full(num_leds, h, dtype=np.float32), np.full(
                num_leds, s, dtype=np.float32
            )
        all_hues, all_sats = [], []
        first_hsv, first_pos = self.stops[0]
        first_idx = round(first_pos * (num_leds - 1))
        all_hues.append(np.full(first_idx, first_hsv[0], dtype=np.float32))
        all_sats.append(np.full(first_idx, first_hsv[1], dtype=np.float32))
        for i in range(len(self.stops) - 1):
            start_hsv, start_pos = self.stops[i]
            end_hsv, end_pos = self.stops[i + 1]
            start_idx = round(start_pos * (num_leds - 1))
            end_idx = round(end_pos * (num_leds - 1))
            segment_width = end_idx - start_idx
            if segment_width > 0:
                all_hues.append(
                    np.linspace(
                        start_hsv[0], end_hsv[0], num=segment_width, dtype=np.float32
                    )
                )
                all_sats.append(
                    np.linspace(
                        start_hsv[1], end_hsv[1], num=segment_width, dtype=np.float32
                    )
                )
        last_hsv, last_pos = self.stops[-1]
        last_idx = round(last_pos * (num_leds - 1))
        num_end_solid = num_leds - last_idx
        if num_end_solid > 0:
            all_hues.append(np.full(num_end_solid, last_hsv[0], dtype=np.float32))
            all_sats.append(np.full(num_end_solid, last_hsv[1], dtype=np.float32))
        final_hues = np.concatenate(all_hues)
        final_sats = np.concatenate(all_sats)
        if len(final_hues) != num_leds:
            final_hues.resize(num_leds, refcheck=False)
            final_sats.resize(num_leds, refcheck=False)
        return final_hues, final_sats


class StaticColor(ColorSource):
    """A color source representing a single, uniform color."""

    def __init__(self, hsv: tuple[float, float], reverse: bool = False):  # <-- NEW
        super().__init__(
            reverse=reverse
        )  # <-- PASS TO PARENT (has no effect but good practice)
        self.hue, self.sat = hsv

    def _generate_arrays(self, num_leds: int) -> tuple[np.ndarray, np.ndarray]:
        hues = np.full(num_leds, self.hue, dtype=np.float32)
        sats = np.full(num_leds, self.sat, dtype=np.float32)
        return hues, sats


# ==============================================================================
#  Dynamic Color Sources (Updated to implement `reverse`)
# ==============================================================================


class ScrollingColorSource(ColorSource):
    """A dynamic color source that wraps another ColorSource and scrolls its output."""

    def __init__(
        self, source: ColorSource, speed: float = 5.0, reverse: bool = False
    ):  # <-- NEW
        """
        Args:
            source: The static ColorSource to use as the base map.
            speed: The speed of scrolling in "LED positions per second".
            reverse: If True, the final scrolled output will be reversed.
        """
        super().__init__(reverse=reverse)  # <-- PASS TO PARENT
        self.source = source
        self.scroll_speed = speed
        self._start_time = time.monotonic()
        self._base_hues: dict[int, np.ndarray] = {}
        self._base_sats: dict[int, np.ndarray] = {}

    def _generate_base_arrays(self, num_leds: int):
        if num_leds not in self._base_hues:
            required_length = num_leds * 2
            hues, sats = self.source.get_hs_arrays(required_length)
            self._base_hues[num_leds] = hues
            self._base_sats[num_leds] = sats

    def get_hs_arrays(self, num_leds: int) -> tuple[np.ndarray, np.ndarray]:
        """
        Calculates and returns the scrolled arrays. Since this method overrides the
        parent, it must implement the reversal logic itself.
        """
        self._generate_base_arrays(num_leds)
        base_hues = self._base_hues[num_leds]
        base_sats = self._base_sats[num_leds]

        elapsed_time = time.monotonic() - self._start_time
        offset = int(elapsed_time * self.scroll_speed)

        scrolled_hues = np.roll(base_hues, offset, axis=0)[:num_leds]
        scrolled_sats = np.roll(base_sats, offset, axis=0)[:num_leds]

        # --- NEW: Apply reversal to the final scrolled output ---
        if self.reverse:
            return np.flip(scrolled_hues), np.flip(scrolled_sats)

        return scrolled_hues, scrolled_sats
