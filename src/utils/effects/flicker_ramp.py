#
# file: my_effects/staged_flicker_ramp.py (final version)
#
import time
from typing import List, Tuple, Unpack

import numpy as np

from .color_source import ColorSource

# Import the core framework components
from .effect import Effect, EffectOptionsKwargs


class FlickerRamp(Effect):
    """
    An effect that executes a series of full "FlickerRamp" animations where
    two comets cross the entire strip. The effect is defined by a total
    duration, and internally calculates timings for each stage.

    Each subsequent ramp is faster, and the pause between them shortens,
    until the effect resolves into a continuously lit state.
    """

    def __init__(
        self,
        rgb_container,
        color_source: ColorSource,
        comet_width: int = 8,
        total_duration: float = 8.0,  # <-- NEW PRIMARY PARAM
        num_stages: int = 6,
        pause_to_ramp_ratio: float = 1.2,  # <-- NEW
        convergence_factor: float = 0.7,  # <-- NEW
        **kwargs: Unpack[EffectOptionsKwargs],
    ):
        """
        Initializes the StagedFlickerRamp effect.

        Args:
            comet_width: The width of each comet.
            total_duration: The total time in seconds for the entire effect
                            to run before finishing in a fully 'on' state.
            num_stages: The number of ramp/pause stages to perform.
            pause_to_ramp_ratio: The duration of the first pause relative to
                                 the first ramp. E.g., 1.5 means the first
                                 pause is 50% longer than the first ramp.
            convergence_factor: How quickly stage durations shorten (0 to 1).
                                Smaller values mean faster acceleration.
            **kwargs: Standard effect options.
        """
        super().__init__(rgb_container, color_source, **kwargs)

        self.comet_width = max(1, comet_width)

        # --- Calculate initial timings from total_duration ---
        # This is the core of the new logic. We solve for the duration of the
        # first stage based on the sum of a geometric series.

        # 1. Validate inputs to prevent division by zero or weird behavior
        num_stages = max(1, num_stages)
        convergence_factor = max(0.0, min(0.999, convergence_factor))  # Keep below 1

        # 2. Calculate the sum of the geometric series: 1 + f + f^2 + ... + f^(n-1)
        # This represents the total number of "time units" in the effect.
        if convergence_factor == 1.0:  # Should be caught by min() but good practice
            geo_series_sum = num_stages
        else:
            geo_series_sum = (1 - convergence_factor**num_stages) / (
                1 - convergence_factor
            )

        # 3. Calculate the duration of the very first full cycle (ramp + pause)
        initial_cycle_duration = total_duration / geo_series_sum

        # 4. Distribute that duration between the first ramp and first pause
        # based on the provided ratio.
        ramp_duration = initial_cycle_duration / (1 + pause_to_ramp_ratio)
        pause_duration = initial_cycle_duration - ramp_duration

        # --- Pre-calculate the timeline of all stages (same as before) ---
        self._timeline: List[Tuple[float, float, str]] = []
        current_time = 0.0

        for i in range(num_stages):
            # Add the ramp segment
            start_ramp = current_time
            end_ramp = start_ramp + ramp_duration
            self._timeline.append((start_ramp, end_ramp, "ramp"))

            # Add the pause segment
            start_pause = end_ramp
            end_pause = start_pause + pause_duration
            self._timeline.append((start_pause, end_pause, "pause"))

            current_time = end_pause

            # Shorten durations for the next stage
            ramp_duration *= convergence_factor
            pause_duration *= convergence_factor

        self.total_duration = current_time

        # Pre-calculate comet patterns
        self.pattern_forward = np.linspace(
            1.0, 0.0, num=self.comet_width, dtype=np.float32
        )
        self.pattern_reverse = np.flip(self.pattern_forward)

    def _update_brightness(self):
        """
        Finds the current stage in the pre-calculated timeline and renders
        the appropriate frame (ramp, pause, or finished).
        """
        elapsed_time = time.monotonic() - self.start_time

        # If the total duration is over, the final state is fully ON.
        if elapsed_time >= self.total_duration:
            self._is_finished = True
            self.brightness_array.fill(1.0)
            return

        # Find the current active segment in our timeline
        for start_time, end_time, segment_type in self._timeline:
            if start_time <= elapsed_time < end_time:
                if segment_type == "pause":
                    self.brightness_array.fill(0.0)
                    return

                if segment_type == "ramp":
                    segment_duration = end_time - start_time
                    time_in_segment = elapsed_time - start_time
                    local_progress = time_in_segment / segment_duration

                    self._run_ramp(local_progress)
                    return

        # This part will be reached between the last pause and total_duration,
        # ensuring the strip is dark before the final "on" state.
        self.brightness_array.fill(0.0)

    def _run_ramp(self, progress: float):
        """
        Renders a single frame of a FlickerRamp animation where comets travel
        the full length of the strip.
        """
        eased_progress = progress**2
        self.brightness_array.fill(0.0)

        head_pos_fwd = eased_progress * self.num_leds
        head_pos_rev = self.num_leds - (eased_progress * self.num_leds)

        self._stamp_pattern(self.pattern_forward, head_pos_fwd, is_reversed=False)
        self._stamp_pattern(self.pattern_reverse, head_pos_rev, is_reversed=True)

    def _stamp_pattern(
        self, pattern: np.ndarray, head_position: float, is_reversed: bool
    ):
        """Helper function to stamp a comet pattern onto the brightness array."""
        int_head_pos = int(head_position)

        if not is_reversed:
            target_start = int_head_pos - self.comet_width
            target_end = int_head_pos
        else:
            target_start = int_head_pos
            target_end = int_head_pos + self.comet_width

        write_start = max(0, target_start)
        write_end = min(self.num_leds, target_end)

        if write_start >= write_end:
            return

        read_start = write_start - target_start
        read_end = write_end - target_start

        target_slice = self.brightness_array[write_start:write_end]
        pattern_slice = pattern[read_start:read_end]
        np.maximum(target_slice, pattern_slice, out=target_slice)
