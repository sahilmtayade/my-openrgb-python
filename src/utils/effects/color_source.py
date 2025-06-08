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
            return (np.zeros(num_leds, dtype=np.float32),) * 3  # type: ignore
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
    A powerful, dynamic color source that smoothly scrolls another source's
    output using a high-resolution oversampling technique for sub-pixel accuracy.
    """

    def __init__(
        self,
        source: ColorSource,
        speed: float = 5.0,
        delay: float = 0.0,
        pause: float = 0.0,
        scroll_fraction: float | None = None,
        initial_roll_ratio: float = 0.0,
        mirrored: bool = True,
        resolution_multiplier: int = 16,
        reverse: bool = False,
    ):
        """
        Initializes the ScrollingColorSource.

        Args:
            source: The ColorSource to use as the base map.
            speed: Speed of scrolling in "LEDs per second".
            delay: Time in seconds to wait before scrolling begins.
            pause: Time in seconds to pause at the end of each scroll segment.
            scroll_fraction: If a number, defines the scroll distance per segment
                             in multiples of the device's LED count.
            initial_roll_ratio: A one-time roll of the base color map (0.0-1.0).
            mirrored: If True, creates a seamless back-and-forth scroll pattern.
            resolution_multiplier: Higher values create smoother sub-pixel scrolling.
            reverse: If True, the final output will be reversed.
        """
        super().__init__(reverse=reverse)
        self.source = source
        self.scroll_speed = speed
        self.delay = delay
        self.pause = max(0.0, pause)
        self.scroll_fraction = scroll_fraction
        self.initial_roll_ratio = initial_roll_ratio % 1.0
        self.mirrored = mirrored
        self.resolution_multiplier = max(1, resolution_multiplier)
        self._start_time = time.monotonic()
        self._base_hues: dict[int, np.ndarray] = {}
        self._base_sats: dict[int, np.ndarray] = {}
        self._base_vals: dict[int, np.ndarray] = {}

    def _generate_base_arrays(self, num_leds: int):
        """Generates a high-resolution, mirrored/tiled base map."""
        cache_key = num_leds * self.resolution_multiplier
        if cache_key not in self._base_hues:
            high_res_led_count = num_leds * self.resolution_multiplier
            h, s, v = self.source.get_hsv_arrays(high_res_led_count)

            if self.mirrored:
                h = np.concatenate((h, np.flip(h[1:-1])))
                s = np.concatenate((s, np.flip(s[1:-1])))
                v = np.concatenate((v, np.flip(v[1:-1])))

            roll_amt = int(len(h) * self.initial_roll_ratio)
            if roll_amt:
                h = np.roll(h, roll_amt)
                s = np.roll(s, roll_amt)
                v = np.roll(v, roll_amt)

            self._base_hues[cache_key] = h
            self._base_sats[cache_key] = s
            self._base_vals[cache_key] = v

    def get_hsv_arrays(
        self, num_leds: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if num_leds <= 0:
            return (np.array([]),) * 3  # type: ignore

        self._generate_base_arrays(num_leds)
        cache_key = num_leds * self.resolution_multiplier
        base_hues = self._base_hues[cache_key]
        base_sats = self._base_sats[cache_key]
        base_vals = self._base_vals[cache_key]

        time_since_start = max(0, (time.monotonic() - self._start_time) - self.delay)
        total_offset_float = 0.0

        if self.scroll_fraction is None:
            total_offset_float = time_since_start * self.scroll_speed
        else:
            scroll_dist_per_seg = num_leds * self.scroll_fraction
            scroll_time_per_seg = (
                scroll_dist_per_seg / self.scroll_speed
                if self.scroll_speed > 0
                else float("inf")
            )
            cycle_duration = scroll_time_per_seg + self.pause

            if cycle_duration > 0 and cycle_duration != float("inf"):
                num_completed = int(time_since_start / cycle_duration)
                time_in_cycle = time_since_start % cycle_duration
            else:
                num_completed, time_in_cycle = 0, time_since_start

            dist_past = num_completed * scroll_dist_per_seg
            dist_current = (
                time_in_cycle * self.scroll_speed
                if time_in_cycle < scroll_time_per_seg
                else scroll_dist_per_seg
            )
            total_offset_float = dist_past + dist_current

        high_res_offset = total_offset_float * self.resolution_multiplier

        rolled_h = np.roll(base_hues, -int(high_res_offset))
        rolled_s = np.roll(base_sats, -int(high_res_offset))
        rolled_v = np.roll(base_vals, -int(high_res_offset))

        # --- THE FIX IS HERE ---
        # After downsampling, we must slice the result to exactly num_leds to
        # guarantee the output shape is correct.
        final_hues = rolled_h[:: self.resolution_multiplier][:num_leds]
        final_sats = rolled_s[:: self.resolution_multiplier][:num_leds]
        final_vals = rolled_v[:: self.resolution_multiplier][:num_leds]
        # --- END OF FIX ---

        if self.reverse:
            return np.flip(final_hues), np.flip(final_sats), np.flip(final_vals)

        return final_hues, final_sats, final_vals


class ColorShift(ColorSource):
    """
    A dynamic color source where the entire device is a single, uniform color
    that transitions smoothly through a given gradient over time.
    """

    def __init__(
        self,
        gradient_source: MultiGradient,  # Takes a gradient to define the color path
        cycle_duration: float = 5.0,  # Time in seconds to complete one full cycle
        delay: float = 0.0,
        reverse: bool = False,  # Has no effect, but included for API consistency
    ):
        """
        Initializes the ColorShift source.

        Args:
            gradient_source: A MultiGradient that defines the colors and their
                             relative timing in the cycle.
            cycle_duration: The total time in seconds for one full color cycle.
            delay: Time in seconds to wait before the shifting begins.
            reverse: This parameter has no effect on a uniform color shift.
        """
        super().__init__(reverse=reverse)

        if not isinstance(gradient_source, MultiGradient) or not gradient_source.stops:
            raise ValueError(
                "ColorShift requires a non-empty MultiGradient as its source."
            )

        self.gradient_source = gradient_source
        self.cycle_duration = max(0.1, cycle_duration)
        self.delay = delay

        # --- Pre-process the gradient for fast interpolation ---
        # We extract the stops into separate numpy arrays for use with np.interp

        # Sort stops by position to be safe, though they should be already.
        sorted_stops = sorted(gradient_source.stops, key=lambda s: s[1])

        self.positions = np.array([pos for hsv, pos in sorted_stops])
        hues = [hsv[0] for hsv, pos in sorted_stops]
        sats = [hsv[1] for hsv, pos in sorted_stops]
        vals = [hsv[2] for hsv, pos in sorted_stops]

        # To handle circular hue interpolation, we need to check if the path
        # crosses the 0.0/1.0 boundary and adjust.
        self.hues = self._unwrap_hues(np.array(hues))
        self.sats = np.array(sats)
        self.vals = np.array(vals)
        self._start_time = time.monotonic()

    def reset(self):
        """Resets the animation's start time to the current moment."""
        self._start_time = time.monotonic()

    def _unwrap_hues(self, hues: np.ndarray) -> np.ndarray:
        """Adjusts hues for correct circular interpolation across the 0.0/1.0 boundary."""
        unwrapped = np.copy(hues)
        for i in range(1, len(unwrapped)):
            diff = unwrapped[i] - unwrapped[i - 1]
            if diff > 0.5:
                unwrapped[i:] -= 1.0
            elif diff < -0.5:
                unwrapped[i:] += 1.0
        return unwrapped

    def get_hsv_arrays(
        self, num_leds: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculates the uniform color for the current frame by interpolating
        along the gradient path. This is a dynamic source and does not use the
        parent class's caching.
        """
        # 1. Calculate the effective time, accounting for the delay.
        time_since_start = max(0, (time.monotonic() - self._start_time) - self.delay)

        # 2. Determine the current progress (0.0 to 1.0) through the cycle.
        #    We use modulo to make the progress loop.
        progress = (time_since_start / self.cycle_duration) % 1.0

        # 3. Interpolate to find the current H, S, and V values.
        current_hue = np.interp(progress, self.positions, self.hues) % 1.0
        current_sat = np.interp(progress, self.positions, self.sats)
        current_val = np.interp(progress, self.positions, self.vals)

        # 4. Create the final arrays by filling them with the uniform color.
        hues = np.full(num_leds, current_hue, dtype=np.float32)
        sats = np.full(num_leds, current_sat, dtype=np.float32)
        vals = np.full(num_leds, current_val, dtype=np.float32)

        return hues, sats, vals
