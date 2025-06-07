#
# file: color_source.py (Fully Updated)
#
import time
from typing import List

import numpy as np

# ==============================================================================
#  Base Class with HSV Caching and Reversal
# ==============================================================================


class ColorSource:
    """
    Base class for color providers with caching and a reversal option.
    Provides full HSV (Hue, Saturation, Value) data.
    """

    def __init__(self, reverse: bool = False):
        """
        Initializes the ColorSource.

        Args:
            reverse: If True, the generated color map will be spatially reversed.
        """
        self._hues: dict[int, np.ndarray] = {}
        self._sats: dict[int, np.ndarray] = {}
        self._vals: dict[int, np.ndarray] = {}  # Cache for Value/Brightness
        self.reverse = reverse

    def _generate_arrays(
        self, num_leds: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Subclasses must implement this to generate H, S, and V arrays."""
        raise NotImplementedError

    def get_hsv_arrays(
        self, num_leds: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Public method to get all three HSV arrays, with caching and reversal."""
        if num_leds not in self._hues:
            # Generate and cache the arrays in their default (non-reversed) order
            hues, sats, vals = self._generate_arrays(num_leds)
            self._hues[num_leds] = hues
            self._sats[num_leds] = sats
            self._vals[num_leds] = vals

        # Retrieve the canonical arrays from the cache
        hues_to_return = self._hues[num_leds]
        sats_to_return = self._sats[num_leds]
        vals_to_return = self._vals[num_leds]

        # Apply reversal if the flag is set
        if self.reverse:
            return (
                np.flip(hues_to_return),
                np.flip(sats_to_return),
                np.flip(vals_to_return),
            )

        return hues_to_return, sats_to_return, vals_to_return


# ==============================================================================
#  Static Color Sources (Updated for HSV)
# ==============================================================================


class StaticColor(ColorSource):
    """A color source representing a single, uniform HSV color."""

    def __init__(self, hsv: tuple[float, float, float], reverse: bool = False):
        super().__init__(reverse=reverse)
        self.hue, self.sat, self.val = hsv

    def _generate_arrays(
        self, num_leds: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        hues = np.full(num_leds, self.hue, dtype=np.float32)
        sats = np.full(num_leds, self.sat, dtype=np.float32)
        vals = np.full(num_leds, self.val, dtype=np.float32)
        return hues, sats, vals


class Gradient(ColorSource):
    """A color source representing a linear gradient between two HSV colors."""

    def __init__(
        self,
        start_hsv: tuple[float, float, float],
        end_hsv: tuple[float, float, float],
        start_pos: float = 0.0,
        end_pos: float = 1.0,
        reverse: bool = False,
    ):
        super().__init__(reverse=reverse)
        self.start_hue, self.start_sat, self.start_val = start_hsv
        self.end_hue, self.end_sat, self.end_val = end_hsv

        start_pos_clamped = max(0.0, min(1.0, start_pos))
        end_pos_clamped = max(0.0, min(1.0, end_pos))
        self.start_pos = min(start_pos_clamped, end_pos_clamped)
        self.end_pos = max(start_pos_clamped, end_pos_clamped)

    def _generate_arrays(
        self, num_leds: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if num_leds == 0:
            return np.array([]), np.array([]), np.array([])

        start_idx = round(self.start_pos * (num_leds - 1))
        end_idx = round(self.end_pos * (num_leds - 1))

        num_start_solid = start_idx
        start_hues = np.full(num_start_solid, self.start_hue, dtype=np.float32)
        start_sats = np.full(num_start_solid, self.start_sat, dtype=np.float32)
        start_vals = np.full(num_start_solid, self.start_val, dtype=np.float32)

        gradient_width = end_idx - start_idx
        if gradient_width > 0:
            gradient_hues = np.linspace(
                self.start_hue, self.end_hue, num=gradient_width, dtype=np.float32
            )
            gradient_sats = np.linspace(
                self.start_sat, self.end_sat, num=gradient_width, dtype=np.float32
            )
            gradient_vals = np.linspace(
                self.start_val, self.end_val, num=gradient_width, dtype=np.float32
            )
        else:
            gradient_hues, gradient_sats, gradient_vals = (
                np.array([], dtype=np.float32),
            ) * 3

        num_end_solid = num_leds - end_idx
        end_hues = np.full(num_end_solid, self.end_hue, dtype=np.float32)
        end_sats = np.full(num_end_solid, self.end_sat, dtype=np.float32)
        end_vals = np.full(num_end_solid, self.end_val, dtype=np.float32)

        final_hues = np.concatenate((start_hues, gradient_hues, end_hues))
        final_sats = np.concatenate((start_sats, gradient_sats, end_sats))
        final_vals = np.concatenate((start_vals, gradient_vals, end_vals))

        return final_hues, final_sats, final_vals


class MultiGradient(ColorSource):
    """A color source representing a gradient between multiple HSV color stops."""

    def __init__(
        self,
        stops: List[tuple[tuple[float, float, float], float]],
        reverse: bool = False,
    ):
        super().__init__(reverse=reverse)
        if not stops:
            self.stops = []
            return
        sanitized_stops = []
        for hsv, pos in stops:
            clamped_pos = max(0.0, min(1.0, pos))
            sanitized_stops.append((hsv, clamped_pos))
        self.stops = sorted(sanitized_stops, key=lambda stop: stop[1])

    def _generate_arrays(
        self, num_leds: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if num_leds == 0:
            return np.array([]), np.array([]), np.array([])
        if not self.stops:
            return (np.zeros(num_leds, dtype=np.float32),) * 3
        if len(self.stops) == 1:
            h, s, v = self.stops[0][0]
            return np.full(num_leds, h), np.full(num_leds, s), np.full(num_leds, v)

        all_hues, all_sats, all_vals = [], [], []

        first_hsv, first_pos = self.stops[0]
        first_idx = round(first_pos * (num_leds - 1))
        all_hues.append(np.full(first_idx, first_hsv[0]))
        all_sats.append(np.full(first_idx, first_hsv[1]))
        all_vals.append(np.full(first_idx, first_hsv[2]))

        for i in range(len(self.stops) - 1):
            start_hsv, start_pos = self.stops[i]
            end_hsv, end_pos = self.stops[i + 1]
            start_idx = round(start_pos * (num_leds - 1))
            end_idx = round(end_pos * (num_leds - 1))
            width = end_idx - start_idx
            if width > 0:
                all_hues.append(np.linspace(start_hsv[0], end_hsv[0], num=width))
                all_sats.append(np.linspace(start_hsv[1], end_hsv[1], num=width))
                all_vals.append(np.linspace(start_hsv[2], end_hsv[2], num=width))

        last_hsv, last_pos = self.stops[-1]
        last_idx = round(last_pos * (num_leds - 1))
        num_end = num_leds - last_idx
        if num_end > 0:
            all_hues.append(np.full(num_end, last_hsv[0]))
            all_sats.append(np.full(num_end, last_hsv[1]))
            all_vals.append(np.full(num_end, last_hsv[2]))

        final_hues = np.concatenate(all_hues).astype(np.float32)
        final_sats = np.concatenate(all_sats).astype(np.float32)
        final_vals = np.concatenate(all_vals).astype(np.float32)

        if len(final_hues) != num_leds:
            final_hues.resize(num_leds, refcheck=False)
            final_sats.resize(num_leds, refcheck=False)
            final_vals.resize(num_leds, refcheck=False)

        return final_hues, final_sats, final_vals


# ==============================================================================
#  Dynamic Color Sources (Updated for HSV)
# ==============================================================================


class ScrollingColorSource(ColorSource):
    """
    A dynamic source that scrolls another ColorSource's output over time.

    By default, it creates a seamlessly mirrored, back-and-forth scrolling
    pattern from the source's color map.
    """

    def __init__(
        self,
        source: ColorSource,
        speed: float = 5.0,
        delay: float = 0.0,
        mirrored: bool = True,  # <-- NEW PARAMETER, DEFAULTS TO TRUE
        reverse: bool = False,
    ):
        """
        Initializes the ScrollingColorSource.

        Args:
            source: The ColorSource to use as the base map.
            speed: The speed of scrolling in "LED positions per second".
            delay: The time in seconds to wait before the scrolling begins.
            mirrored: If True (default), creates a seamless back-and-forth
                      scrolling pattern (e.g., A->B becomes A->B->A).
                      If False, uses simple tiling (e.g., A->B becomes A->B->A->B),
                      which is useful for pre-designed repeating patterns.
            reverse: If True, the final scrolled output will be reversed.
        """
        super().__init__(reverse=reverse)
        self.source = source
        self.scroll_speed = speed
        self.delay = delay
        self.mirrored = mirrored  # <-- STORE THE NEW OPTION
        self._start_time = time.monotonic()
        self._base_hues: dict[int, np.ndarray] = {}
        self._base_sats: dict[int, np.ndarray] = {}
        self._base_vals: dict[int, np.ndarray] = {}

    def _generate_base_arrays(self, num_leds: int):
        """
        Generates the double-length base arrays for seamless scrolling.
        This now supports both mirrored and tiled modes.
        """
        if num_leds not in self._base_hues:
            # --- THIS IS THE CORE OF THE REFACTOR ---
            if self.mirrored:
                # 1. Get the standard, single-length color map from the source.
                h, s, v = self.source.get_hsv_arrays(num_leds)

                # 2. Create the mirrored, double-length arrays by concatenating
                #    the original array with a flipped version of itself.
                self._base_hues[num_leds] = np.concatenate((h, np.flip(h)))
                self._base_sats[num_leds] = np.concatenate((s, np.flip(s)))
                self._base_vals[num_leds] = np.concatenate((v, np.flip(v)))
            else:
                # --- Fallback to the original tiling behavior ---
                required_length = num_leds * 2
                h, s, v = self.source.get_hsv_arrays(required_length)
                self._base_hues[num_leds] = h
                self._base_sats[num_leds] = s
                self._base_vals[num_leds] = v

    def get_hsv_arrays(
        self, num_leds: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculates and returns the scrolled arrays. The generation logic
        is now handled by _generate_base_arrays.
        """
        self._generate_base_arrays(num_leds)
        base_hues = self._base_hues[num_leds]
        base_sats = self._base_sats[num_leds]
        base_vals = self._base_vals[num_leds]

        scroll_time = max(0, (time.monotonic() - self._start_time) - self.delay)
        offset = int(scroll_time * self.scroll_speed)

        scrolled_hues = np.roll(base_hues, offset)[:num_leds]
        scrolled_sats = np.roll(base_sats, offset)[:num_leds]
        scrolled_vals = np.roll(base_vals, offset)[:num_leds]

        if self.reverse:
            return (
                np.flip(scrolled_hues),
                np.flip(scrolled_sats),
                np.flip(scrolled_vals),
            )

        return scrolled_hues, scrolled_sats, scrolled_vals
