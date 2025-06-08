#
# file: src/utils/effects/chase_ramp.py (Improved)
#
import time
from typing import Unpack

import numpy as np

from .color_source import ColorSource
from .effect import Effect, EffectOptionsKwargs


class ChaseRamp(Effect):
    """
    A comet that starts slow, continuously accelerates, and grows in width.
    The effect finishes in a high-speed flicker once it reaches max_speed.
    """

    def __init__(
        self,
        rgb_container,
        color_source: ColorSource,
        initial_speed: float = 5.0,
        acceleration: float = 2.0,
        max_speed: float = 200.0,
        initial_width: int = 5,
        max_width: int = 25,
        flicker_duration: float = 1.5,  # <-- NEW: Duration of the end state
        resolution_multiplier: int = 8,
        **kwargs: Unpack[EffectOptionsKwargs],
    ):
        """
        Initializes the ChaseRamp effect.

        Args:
            initial_speed: The starting speed of the comet in LEDs/sec.
            acceleration: How many LEDs/sec are added to the speed, per second.
            max_speed: The speed the comet must reach to trigger the end phase.
            initial_width: The comet's width in LEDs at initial_speed.
            max_width: The comet's width in LEDs at max_speed.
            flicker_duration: The time in seconds the effect will "flicker" at
                              max speed before finishing.
            resolution_multiplier: Controls the smoothness of the sub-pixel rendering.
        """
        super().__init__(rgb_container, color_source, **kwargs)

        # Physics and animation parameters
        self.initial_speed = initial_speed
        self.acceleration = acceleration
        self.max_speed = max_speed
        self.initial_width = initial_width
        self.max_width = max_width
        self.flicker_duration = flicker_duration
        self.resolution_multiplier = max(1, resolution_multiplier)

        # State variables
        self.current_speed = self.initial_speed
        self.head_position = -self.initial_width  # Start fully off-screen
        self._last_update_time: float = self.start_time

        # --- NEW: State for managing the end phase ---
        self._is_finishing = False
        self._finish_start_time: float | None = None

    def _update_brightness(self):
        """
        Calculates the comet's new position and width, handles the finishing
        state, and renders it smoothly to the brightness array.
        """
        now = time.monotonic()
        dt = now - self._last_update_time
        self._last_update_time = now

        # 1. Check and manage the finishing phase
        speed_range = self.max_speed - self.initial_speed
        if self._is_finishing:
            if (now - self._finish_start_time) >= self.flicker_duration:  # type: ignore
                self._is_finished = True
                self.brightness_array.fill(1.0)  # Finish fully lit
                return
            # If we are finishing, speed is locked at max_speed
            self.current_speed = self.max_speed
        else:
            # 2. If not finishing, update speed and check if we should start finishing
            # Accelerate speed, but clamp it at max_speed
            if speed_range > 0:
                self.current_speed += self.acceleration * dt
                if self.current_speed >= self.max_speed:
                    self.current_speed = self.max_speed
                    # --- TRIGGER THE FINISHING PHASE ---
                    self._finish_start_time = now
                    self._is_finishing = True

        # 3. Update position based on the current speed
        self.head_position += self.current_speed * dt

        # 4. Calculate Dynamic Width
        speed_progress = 0.0
        if speed_range > 0:
            speed_progress = np.clip(
                (self.current_speed - self.initial_speed) / speed_range, 0.0, 1.0
            )
        current_width = (
            self.initial_width + (self.max_width - self.initial_width) * speed_progress
        )

        # 5. High-Resolution Rendering
        high_res_leds = self.num_leds * self.resolution_multiplier
        high_res_width = int(current_width * self.resolution_multiplier)
        high_res_head_pos = self.head_position * self.resolution_multiplier

        high_res_pattern = np.linspace(1.0, 0.0, num=high_res_width, dtype=np.float32)
        high_res_canvas = np.zeros(high_res_leds, dtype=np.float32)

        stamp_len = min(high_res_width, high_res_leds)
        high_res_canvas[:stamp_len] = high_res_pattern[:stamp_len]

        rolled_canvas = np.roll(high_res_canvas, int(high_res_head_pos))

        # 6. Downsample using MAX for a bright, anti-aliased look
        reshaped_canvas = rolled_canvas.reshape(
            self.num_leds, self.resolution_multiplier
        )
        np.max(reshaped_canvas, axis=1, out=self.brightness_array)

        # 7. Final "flicker" state enhancement
        if self._is_finishing and self.options.dither_strength > 0:
            noise = np.random.uniform(
                0, self.options.dither_strength, self.brightness_array.shape
            )
            self.brightness_array = np.clip(self.brightness_array + noise, 0, 1)
