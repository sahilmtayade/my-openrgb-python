# A symmetrical gradient with a bright cyan core and deep blue edges.
from .utils.effects.color_source import MultiGradient

# --- Color palettes in HSV (Hue 0-1, Saturation 0-1, Value 0-1) --- # <-- CHANGED
LIQUID_HSV = (18 / 360, 1.0, 1.0)  # Fiery orange at full brightness # <-- CHANGED
RAM_CHASE_BOTTOM_HSV = (
    18 / 360,
    1.0,
    1.0,
)
RAM_CHASE_TOP_HSV = (
    0.0,
    0.0,
    1.0,
)
ocean_bands_gradient = MultiGradient(
    [
        ((0.6, 1.0, 0.5), 0.0),  # Start with a darker, deep blue (Value=0.5)
        ((0.5, 1.0, 1.0), 0.4),  # Fade into bright, full-value Cyan at 40%
        ((0.5, 1.0, 1.0), 0.6),  # Hold the bright Cyan for a solid band until 60%
        ((0.6, 1.0, 0.5), 1.0),  # Fade back out to the darker, deep blue at the end
    ]
)

# A flowing gradient from deep blue, through cyan, to a final bright green.
tropical_waters_gradient = MultiGradient(
    [
        ((0.66, 1.0, 1.0), 0.0),  # Start with a vibrant Deep Blue
        ((0.58, 1.0, 1.0), 0.5),  # NEW: Add an Azure stop halfway to Cyan
        ((0.5, 1.0, 1.0), 0.7),  # Transition to bright Cyan by the 40% mark
        ((132 / 360, 1.0, 1.0), 1.0),  # Finish with a bright Green at the end
    ]
)

# Alternating dark and light colors to create a shimmering effect when scrolled.
ocean_shimmer_gradient = MultiGradient(
    [
        ((0.55, 0.8, 0.4), 0.0),  # Start with a dark, murky Teal
        ((0.5, 1.0, 1.0), 0.25),  # Pulse to bright Cyan
        ((0.55, 0.8, 0.4), 0.5),  # Back to dark Teal in the middle
        ((0.33, 1.0, 1.0), 0.75),  # Pulse to bright Green
        ((0.55, 0.8, 0.4), 1.0),  # End with dark Teal
    ]
)

flame_gradient = MultiGradient(
    [
        (LIQUID_HSV, 0.0),  # Dim red/orange (Value = 0.4) # <-- CHANGED
        (LIQUID_HSV, 0.1),  # Dim red/orange (Value = 0.4) # <-- CHANGED
        ((0.0, 1.0, 1.0), 0.2),  # Bright red (Value = 1.0)   # <-- CHANGED
        ((0.0, 1.0, 1.0), 0.6),  # Still bright red           # <-- CHANGED
        ((0.0, 0.0, 1), 0.7),  # White
    ]
)
