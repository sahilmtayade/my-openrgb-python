#
# file: base_effect.py
#
from abc import ABC, abstractmethod
import time
from openrgb.utils import RGBColor, RGBContainer

class BaseEffect(ABC):
    """
    Abstract base class for all lighting effects.

    Each effect is responsible for calculating its own frame of colors and
    for determining when its animation sequence is logically complete.
    """
    def __init__(
        self,
        rgb_container: RGBContainer,
        duration: int | None = None,
        speed: float = 1.0,
        **kwargs,
    ):
        """
        Initializes the base effect.

        Args:
            rgb_container: The OpenRGB container this effect will generate colors for.
                           It's used primarily to know the number of LEDs.
            duration: An optional duration in milliseconds for time-based effects.
            speed: A multiplier for the effect's speed. Its meaning is defined
                   by the subclass (e.g., LEDs/sec, cycles/sec).
            **kwargs: Additional keyword arguments for subclass customization.
        """
        self.rgb_container = rgb_container
        self.duration = duration
        self.speed = speed
        self.kwargs = kwargs
        
        self.start_time = time.monotonic()
        
        # This flag is critical. Subclasses MUST set this to True when they are done.
        self._is_finished = False

    @abstractmethod
    def _calculate_next_frame(self) -> list[RGBColor]:
        """
        Calculates and returns the list of colors for the current frame.

        This is the core logic of the effect. The implementation of this method
        in a subclass MUST set `self._is_finished = True` when the effect's
        logical animation is complete. For indefinite effects, this flag is
        never set.

        Returns:
            A list of RGBColor objects representing the next frame.
        """
        ...

    def calculate_frame(self) -> list[RGBColor]:
        """
        Public-facing method to get the effect's current frame.
        This should not be overridden by subclasses.
        """
        # This method provides a clean separation, allowing for future
        # potential wrapper logic without changing subclasses.
        return self._calculate_next_frame()

    def is_finished(self) -> bool:
        """
        Returns True if the effect has signaled that it is complete.
        This is used by the StageManager to know when to remove the effect.
        """
        return self._is_finished