#
# file: src/utils/effects/breathing.py (Upgraded)
#
import time
from typing import Optional, Unpack

import numpy as np

from .color_source import ColorSource
from .effect import Effect, EffectOptionsKwargs


class Breathing(Effect):
    """
    A "breathing" effect that smoothly modulates the brightness of a device.
    Supports two modes: a classic cosine wave or a trapezoidal wave for
    long-period on/off cycles with smooth transitions.
    """

    def __init__(
        self,
        rgb_container,
        color_source: ColorSource,
        cycle_duration: float = 4.0,
        min_brightness: float = 0.1,
        max_brightness: float = 1.0,
        delay: float = 0.0,
        duration: Optional[float] = None,
        # --- NEW parameters for trapezoidal wave ---
        on_duration: Optional[float] = None,
        off_duration: Optional[float] = None,
        transition_duration: float = 2.0,
        **kwargs: Unpack[EffectOptionsKwargs],
    ):
        """
        Initializes the Breathing effect.

        Args:
            cycle_duration: For cosine mode, the time for one full breath.
            min_brightness: The minimum brightness level (0.0 to 1.0).
            max_brightness: The maximum brightness level (0.0 to 1.0).
            delay: An initial delay in seconds before the effect starts.
            duration: If set, the effect will finish after this many seconds.
            on_duration: If set, activates trapezoid mode. Time to hold at max brightness.
            off_duration: If set, activates trapezoid mode. Time to hold at min brightness.
            transition_duration: Time for the fade-in and fade-out ramps.
            **kwargs: Standard effect options.
        """
        super().__init__(rgb_container, color_source, **kwargs)

        self.min_brightness = np.clip(min_brightness, 0.0, 1.0)
        self.max_brightness = np.clip(max_brightness, 0.0, 1.0)
        self.delay = delay
        self.duration = duration
        self.transition_duration = max(0.0, transition_duration)

        # Determine which mode to use based on provided parameters
        if on_duration is not None and off_duration is not None:
            self.mode = "trapezoid"
            self.on_duration = max(0.0, on_duration)
            self.off_duration = max(0.0, off_duration)
            # For trapezoid mode, the total cycle duration is calculated
            self.cycle_duration = (
                self.off_duration + self.on_duration + (2 * self.transition_duration)
            )
        else:
            self.mode = "cosine"
            self.cycle_duration = max(0.1, cycle_duration)

        if self.min_brightness > self.max_brightness:
            self.min_brightness = self.max_brightness

    def _update_brightness(self):
        """
        Calculates the uniform brightness for the current frame based on the
        selected wave form (cosine or trapezoid).
        """
        now = time.monotonic()
        elapsed_since_creation = now - self.start_time

        if self.duration is not None and elapsed_since_creation >= self.duration:
            self._is_finished = True
            return

        animation_time = max(0, elapsed_since_creation - self.delay)

        # --- Select the appropriate wave generation function ---
        if self.mode == "trapezoid":
            current_brightness = self._generate_trapezoid_wave(animation_time)
        else:  # Default to cosine
            current_brightness = self._generate_cosine_wave(animation_time)

        self.brightness_array.fill(current_brightness)

    def _generate_cosine_wave(self, t: float) -> float:
        """Generates a smooth brightness value using a cosine wave."""
        angle = t * (2 * np.pi) / self.cycle_duration
        normalized_wave = (np.cos(angle) + 1) / 2.0
        brightness_range = self.max_brightness - self.min_brightness
        return self.min_brightness + (normalized_wave * brightness_range)

    def _generate_trapezoid_wave(self, t: float) -> float:
        """Generates a trapezoidal wave for on/off cycles with transitions."""
        if self.cycle_duration == 0:
            return self.min_brightness

        # Find our position within the current cycle
        time_in_cycle = t % self.cycle_duration

        # Define the key time points within one cycle
        fade_in_end = self.transition_duration
        on_phase_end = fade_in_end + self.on_duration
        fade_out_end = on_phase_end + self.transition_duration
        # The off_phase follows, up to cycle_duration

        brightness = 0.0
        if time_in_cycle < fade_in_end:
            # Phase 1: Fading In
            if self.transition_duration > 0:
                progress = time_in_cycle / self.transition_duration
                brightness = self.min_brightness + progress * (
                    self.max_brightness - self.min_brightness
                )
            else:  # Instant on
                brightness = self.max_brightness

        elif time_in_cycle < on_phase_end:
            # Phase 2: Fully On
            brightness = self.max_brightness

        elif time_in_cycle < fade_out_end:
            # Phase 3: Fading Out
            if self.transition_duration > 0:
                progress = (time_in_cycle - on_phase_end) / self.transition_duration
                brightness = self.max_brightness - progress * (
                    self.max_brightness - self.min_brightness
                )
            else:  # Instant off
                brightness = self.min_brightness

        else:
            # Phase 4: Fully Off
            brightness = self.min_brightness

        return brightness
