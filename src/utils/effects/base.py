# Base effect class for all effects
from abc import ABC, abstractmethod
from openrgb.utils import RGBColor, RGBContainer


class BaseEffect(ABC):
    def __init__(
        self, rgb_container: RGBContainer, duration: int | None, speed: float, **kwargs
    ):
        """
        Initializes the base effect with the specified RGB container, duration, speed, and additional parameters.

        Args:
            rgb_container (RGBContainer): The container managing RGB elements for the effect.
            duration (int | None): Duration of the effect in milliseconds. If None, the effect has no set duration.
            speed (float): Speed at which the effect progresses.
            **kwargs: Additional keyword arguments for effect customization.
        """
        self.rgb_container = rgb_container
        self.duration = duration
        self.speed = speed
        self.kwargs = kwargs
        self.current_frame = 0

    @abstractmethod
    def _calculate_next_frame(self) -> list[RGBColor]:
        """
        Generate the next frame of the effect.

        :return: A list of RGBColor objects representing the next frame.
        """
        ...

    @abstractmethod
    def update(self) -> bool:
        """
        Updates the RGB container to the next frame of the effect.
        Calculates the next frame using the effect's logic, sets the new colors on the RGB container,
        and displays the updated colors. If a duration is specified, increments the current frame count
        and returns True if the effect has reached its duration; otherwise, returns False.
        Returns:
            bool: True if the effect has completed its duration, False otherwise.
        """

        next_frame = self._calculate_next_frame()
        self.rgb_container.set_colors(next_frame)
        self.rgb_container.show(fast=True)

        if self.duration is not None:
            self.current_frame += 1
            if self.current_frame >= self.duration:
                return True

        return False
